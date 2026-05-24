"""
简报管理 API — 每日简报历史查询、详情查看、手动触发
"""
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_, and_, exists
from sqlalchemy.orm import Session

from models.database import get_db
from models.briefing import DailyBriefing, BriefingEvent
from models.user import UserConfig

router = APIRouter(prefix="/api")


# ── Schemas ──

class BriefingListItem(BaseModel):
    id: int
    briefing_id: str
    date: str
    status: str
    title: str
    summary: str
    events_count: int
    sources_count: int
    agents_count: int
    push_status: dict
    pushed_at: Optional[str]
    created_at: Optional[str]

    class Config:
        from_attributes = True


class BriefingDetail(BriefingListItem):
    full_content: str
    events: list
    risk_assessment: dict
    recommendations: list

    class Config:
        from_attributes = True


# ── Routes ──

@router.get("/briefings")
async def list_briefings(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="关键词搜索简报标题/摘要/全文"),
    date_from: Optional[str] = Query(None, description="起始日期 YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    category: Optional[str] = Query(None, description="事件类别筛选"),
    source: Optional[str] = Query(None, description="信息来源筛选"),
    min_relevance: Optional[float] = Query(None, ge=0.0, le=1.0, description="最小相关度 0~1"),
    db: Session = Depends(get_db),
):
    """分页查询简报历史，支持全文搜索与多维度筛选。"""
    query = db.query(DailyBriefing).order_by(DailyBriefing.date.desc())

    if status:
        query = query.filter(DailyBriefing.status == status)

    if q:
        term = f"%{q}%"
        query = query.filter(
            or_(
                DailyBriefing.title.ilike(term),
                DailyBriefing.summary.ilike(term),
                DailyBriefing.full_content.ilike(term),
            )
        )

    if date_from:
        query = query.filter(DailyBriefing.date >= date_from)
    if date_to:
        query = query.filter(DailyBriefing.date <= date_to)

    if category:
        query = query.filter(
            exists().where(
                BriefingEvent.briefing_id == DailyBriefing.id,
                BriefingEvent.category == category,
            )
        )

    if source:
        query = query.filter(
            exists().where(
                BriefingEvent.briefing_id == DailyBriefing.id,
                BriefingEvent.source == source,
            )
        )

    if min_relevance is not None:
        query = query.filter(
            exists().where(
                BriefingEvent.briefing_id == DailyBriefing.id,
                BriefingEvent.relevance >= min_relevance,
            )
        )

    total = query.count()
    briefings = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "briefings": [b.to_dict(include_content=False) for b in briefings],
    }


@router.get("/briefings/{briefing_id}")
async def get_briefing(briefing_id: str, db: Session = Depends(get_db)):
    """获取简报详情（含完整内容和事件列表）。"""
    briefing = db.query(DailyBriefing).filter(DailyBriefing.briefing_id == briefing_id).first()
    if not briefing:
        raise HTTPException(404, f"简报 '{briefing_id}' 不存在")
    return briefing.to_dict(include_content=True)


@router.get("/briefings/{briefing_id}/events")
async def get_briefing_events(briefing_id: str, db: Session = Depends(get_db)):
    """获取简报包含的事件列表。"""
    briefing = db.query(DailyBriefing).filter(DailyBriefing.briefing_id == briefing_id).first()
    if not briefing:
        raise HTTPException(404, f"简报 '{briefing_id}' 不存在")
    return {"events": [e.to_dict() for e in briefing.events]}


@router.post("/briefings/generate")
async def generate_briefing_now(db: Session = Depends(get_db)):
    """手动触发今日简报生成（不等待定时任务）。"""
    from scheduler.daily_briefing_job import DailyBriefingJob
    from datetime import datetime
    from models.briefing import DailyBriefing, BriefingEvent

    today = datetime.now().strftime("%Y-%m-%d")
    briefing_id = f"{today.replace('-', '')}-1"

    # 强制重新生成：删除今日已有的简报记录（包括关联事件）
    existing = db.query(DailyBriefing).filter_by(briefing_id=briefing_id).first()
    if existing:
        db.query(BriefingEvent).filter_by(briefing_id=existing.id).delete()
        db.delete(existing)
        db.commit()

    job = DailyBriefingJob()
    # 在后台线程中运行（避免阻塞 HTTP 响应）
    import threading
    t = threading.Thread(target=job.run, daemon=True)
    t.start()

    return {
        "message": "简报生成任务已启动",
        "note": "生成完成后将通过配置的渠道自动推送",
    }


@router.get("/briefings/today/status")
async def today_briefing_status(db: Session = Depends(get_db)):
    """查询今日简报生成状态。"""
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    briefing = db.query(DailyBriefing).filter(DailyBriefing.date == today).first()

    if not briefing:
        return {"date": today, "status": "not_started", "briefing_id": None}

    return {
        "date": today,
        "status": briefing.status,
        "briefing_id": briefing.briefing_id,
        "events_count": briefing.events_count,
        "pushed_at": briefing.pushed_at.isoformat() if briefing.pushed_at else None,
    }
