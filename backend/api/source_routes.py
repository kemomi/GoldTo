"""
数据源管理 API — 健康检查、数据源配置、切换 Mock/真实模式
"""
from __future__ import annotations
from typing import Dict, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.database import get_db
from models.user import UserConfig
from config import settings
from sources.world_monitor import WorldMonitorSource
from sources.competitor import CompetitorSource
from sources.social_media import SocialMediaSource
from sources.product_trend import ProductTrendSource
from sources.legal_compliance import LegalComplianceSource

router = APIRouter(prefix="/api")


class SourceStatus(BaseModel):
    name: str
    category: str
    available: bool
    mode: str  # mock / real
    message: str = ""


class SourceConfigUpdate(BaseModel):
    enable_real_sources: bool
    news_api_key: str = ""


# ── Routes ──

@router.get("/sources/status")
async def get_sources_status():
    """获取所有数据源的健康状态和可用性。"""
    sources = [
        ("world_monitor", "地缘政治/市场", WorldMonitorSource()),
        ("competitor", "竞争对手", CompetitorSource()),
        ("social_media", "社交媒体", SocialMediaSource()),
        ("product_trend", "产品趋势", ProductTrendSource()),
        ("legal_compliance", "法律合规", LegalComplianceSource()),
    ]

    results = []
    for name, category, source in sources:
        is_available = source.is_available()
        results.append({
            "name": name,
            "category": category,
            "available": is_available,
            "mode": "real" if settings.use_real_sources and is_available else "mock",
            "message": "数据源正常" if is_available else "数据源不可用或配置不完整",
        })

    return {
        "global_mode": "real" if settings.use_real_sources else "mock",
        "sources": results,
    }


@router.get("/sources/config")
async def get_source_config():
    """获取当前数据源全局配置。"""
    return {
        "enable_real_sources": settings.use_real_sources,
        "news_api_key_configured": bool(settings.news_api_key),
        "source_timeout": settings.source_timeout,
        "llm_mode": "real" if not settings.is_mock else "mock",
        "llm_model": settings.llm_model_name if not settings.is_mock else None,
    }


@router.post("/sources/config")
async def update_source_config(data: SourceConfigUpdate, db: Session = Depends(get_db)):
    """更新数据源全局配置（切换 Mock/真实模式）。"""
    # 更新内存中的配置
    settings.enable_real_sources = data.enable_real_sources
    if data.news_api_key:
        settings.news_api_key = data.news_api_key

    # 同时保存到用户配置中（持久化）
    user = db.query(UserConfig).first()
    if not user:
        user = UserConfig(id=1)
        db.add(user)

    # 使用 briefing_sections 字段存储数据源偏好（临时方案）
    user.briefing_sections = ["real_sources" if data.enable_real_sources else "mock_sources"]
    db.commit()

    mode = "真实数据源" if data.enable_real_sources else "Mock 数据"
    return {
        "message": f"已切换到 {mode} 模式",
        "enable_real_sources": settings.use_real_sources,
    }


@router.post("/sources/test/{source_name}")
async def test_source(source_name: str):
    """测试单个数据源，返回样例数据。"""
    source_map = {
        "world_monitor": WorldMonitorSource(),
        "competitor": CompetitorSource(),
        "social_media": SocialMediaSource(),
        "product_trend": ProductTrendSource(),
        "legal_compliance": LegalComplianceSource(),
    }

    source = source_map.get(source_name)
    if not source:
        return {"error": f"未知数据源: {source_name}"}

    import asyncio
    try:
        events = await source.collect(
            config={
                "industry": "新能源汽车",
                "focus_targets": ["电池", "充电"],
                "competitor_list": ["Tesla", "BYD"],
                "product_keywords": ["电动车", "锂电池"],
                "social_keywords": ["新能源", "自动驾驶"],
            },
            limit=3,
        )
        return {
            "source": source_name,
            "mode": "real" if settings.use_real_sources else "mock",
            "events_count": len(events),
            "events": [
                {
                    "title": e.title,
                    "source": e.source,
                    "category": e.category,
                    "summary": e.summary[:100] + "..." if len(e.summary) > 100 else e.summary,
                    "relevance": e.relevance,
                }
                for e in events
            ],
        }
    except Exception as e:
        return {"source": source_name, "error": str(e), "mode": "mock"}
