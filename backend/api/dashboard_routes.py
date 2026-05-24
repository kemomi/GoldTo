"""
Dashboard API — 情报趋势分析与可视化数据接口
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.database import get_db
from models.briefing import DailyBriefing, BriefingEvent

router = APIRouter(prefix="/api")


# ── Helpers ──

def _event_date_col():
    """Extract YYYY-MM-DD from BriefingEvent.timestamp (ISO format string)."""
    return func.substr(BriefingEvent.timestamp, 1, 10)


# ── Routes ──

@router.get("/dashboard/overview")
async def dashboard_overview(db: Session = Depends(get_db)):
    """KPI 概览数据。"""
    briefing_count = db.query(DailyBriefing).count()
    event_count = db.query(BriefingEvent).count()
    avg_relevance = db.query(func.avg(BriefingEvent.relevance)).scalar() or 0.0
    source_kinds = db.query(func.count(func.distinct(BriefingEvent.source))).scalar() or 0
    active_days = db.query(func.count(func.distinct(DailyBriefing.date))).scalar() or 0

    return {
        "success": True,
        "data": {
            "briefing_count": briefing_count,
            "event_count": event_count,
            "avg_relevance": round(avg_relevance * 100, 1),
            "source_kinds": int(source_kinds),
            "active_days": int(active_days),
        },
    }


@router.get("/dashboard/trends")
async def dashboard_trends(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """每日趋势：事件数 + 平均相关度（按日期聚合）。"""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    date_col = _event_date_col()

    rows = (
        db.query(
            date_col.label("date"),
            func.count(BriefingEvent.id).label("event_count"),
            func.avg(BriefingEvent.relevance).label("avg_relevance"),
        )
        .filter(date_col >= cutoff)
        .group_by(date_col)
        .order_by(date_col.asc())
        .all()
    )

    # Fill missing dates with zeros
    data = []
    date_map = {r.date: r for r in rows}
    for i in range(days, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        if d in date_map:
            r = date_map[d]
            data.append({
                "date": d,
                "event_count": r.event_count,
                "avg_relevance": round((r.avg_relevance or 0.0) * 100, 1),
            })
        else:
            data.append({"date": d, "event_count": 0, "avg_relevance": 0.0})

    return {"success": True, "data": data}


@router.get("/dashboard/categories")
async def dashboard_categories(db: Session = Depends(get_db)):
    """类别分布：每个类别的数量 + 平均相关度。"""
    rows = (
        db.query(
            BriefingEvent.category,
            func.count(BriefingEvent.id).label("count"),
            func.avg(BriefingEvent.relevance).label("avg_relevance"),
        )
        .filter(BriefingEvent.category != "")
        .group_by(BriefingEvent.category)
        .order_by(func.count(BriefingEvent.id).desc())
        .all()
    )

    return {
        "success": True,
        "data": [
            {
                "category": r.category,
                "count": r.count,
                "avg_relevance": round((r.avg_relevance or 0.0) * 100, 1),
            }
            for r in rows
        ],
    }


@router.get("/dashboard/sources")
async def dashboard_sources(
    limit: int = Query(10, ge=1, le=30),
    db: Session = Depends(get_db),
):
    """来源分布：每个来源的事件数量（Top N）。"""
    rows = (
        db.query(
            BriefingEvent.source,
            func.count(BriefingEvent.id).label("count"),
        )
        .filter(BriefingEvent.source != "")
        .group_by(BriefingEvent.source)
        .order_by(func.count(BriefingEvent.id).desc())
        .limit(limit)
        .all()
    )

    return {
        "success": True,
        "data": [
            {"source": r.source, "count": r.count}
            for r in rows
        ],
    }


@router.get("/dashboard/high-relevance")
async def dashboard_high_relevance(
    limit: int = Query(20, ge=1, le=50),
    min_relevance: float = Query(0.7, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
):
    """高相关性事件列表。"""
    events = (
        db.query(BriefingEvent)
        .filter(BriefingEvent.relevance >= min_relevance)
        .order_by(BriefingEvent.timestamp.desc())
        .limit(limit)
        .all()
    )

    # Enrich with briefing date for navigation
    result = []
    for ev in events:
        d = ev.to_dict()
        d["briefing_date"] = ev.briefing.date if ev.briefing else None
        d["briefing_id"] = ev.briefing.briefing_id if ev.briefing else None
        result.append(d)

    return {"success": True, "data": result}
