"""
Alert API — 预警规则配置与告警历史查询
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.database import get_db
from models.alert import AlertRule, AlertLog

router = APIRouter(prefix="/api")


# ── Schemas ──

class AlertRuleSchema(BaseModel):
    enabled: bool = True
    min_relevance: float = 0.85
    keywords: list = []
    categories: list = []
    channels: list = []

    class Config:
        from_attributes = True


# ── Routes ──

@router.get("/alert-rule")
async def get_alert_rule(db: Session = Depends(get_db)):
    """获取当前预警规则（单用户 MVP，取第一条）。"""
    rule = db.query(AlertRule).first()
    if not rule:
        # 返回默认规则
        return {"success": True, "data": {
            "enabled": False,
            "min_relevance": 0.85,
            "keywords": [],
            "categories": [],
            "channels": [],
        }}
    return {"success": True, "data": rule.to_dict()}


@router.post("/alert-rule")
async def save_alert_rule(rule_data: AlertRuleSchema, db: Session = Depends(get_db)):
    """保存或更新预警规则。"""
    rule = db.query(AlertRule).first()
    if rule:
        rule.enabled = rule_data.enabled
        rule.min_relevance = rule_data.min_relevance
        rule.keywords = rule_data.keywords
        rule.categories = rule_data.categories
        rule.channels = rule_data.channels
    else:
        rule = AlertRule(
            enabled=rule_data.enabled,
            min_relevance=rule_data.min_relevance,
            keywords=rule_data.keywords,
            categories=rule_data.categories,
            channels=rule_data.channels,
        )
        db.add(rule)
    db.commit()
    db.refresh(rule)
    return {"success": True, "data": rule.to_dict()}


@router.get("/alerts")
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="all | sent | failed | pending"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """查询告警历史列表。"""
    query = db.query(AlertLog).order_by(AlertLog.triggered_at.desc())

    if date_from:
        query = query.filter(func.date(AlertLog.triggered_at) >= date_from)
    if date_to:
        query = query.filter(func.date(AlertLog.triggered_at) <= date_to)

    if status and status != "all":
        # sent = 至少一个渠道成功
        # failed = 所有渠道都失败或未推送
        # pending = push_status 为空
        if status == "pending":
            query = query.filter(AlertLog.push_status == {})
        elif status == "sent":
            # 简化处理：push_status 中有值为 "sent" 的
            pass  # 前端过滤更灵活，这里不处理
        elif status == "failed":
            pass

    total = query.count()
    logs = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "success": True,
        "total": total,
        "page": page,
        "page_size": page_size,
        "alerts": [log.to_dict() for log in logs],
    }


@router.get("/alerts/stats")
async def get_alert_stats(db: Session = Depends(get_db)):
    """告警统计概览。"""
    today = datetime.now().strftime("%Y-%m-%d")
    today_start = datetime.strptime(today, "%Y-%m-%d")
    today_end = today_start + timedelta(days=1)

    today_total = db.query(AlertLog).filter(
        AlertLog.triggered_at >= today_start,
        AlertLog.triggered_at < today_end,
    ).count()

    today_sent = db.query(AlertLog).filter(
        AlertLog.triggered_at >= today_start,
        AlertLog.triggered_at < today_end,
        AlertLog.pushed_at.isnot(None),
    ).count()

    total_all = db.query(AlertLog).count()

    # 触发原因分布
    reason_dist = (
        db.query(AlertLog.matched_reason, func.count(AlertLog.id))
        .group_by(AlertLog.matched_reason)
        .all()
    )

    return {
        "success": True,
        "data": {
            "today_total": today_total,
            "today_sent": today_sent,
            "total_all": total_all,
            "reason_distribution": [
                {"reason": r[0] or "unknown", "count": r[1]} for r in reason_dist
            ],
        },
    }
