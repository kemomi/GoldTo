"""
Daily Briefing model — 每日简报历史记录
"""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from models.database import Base


class DailyBriefing(Base):
    """每日简报主表 — 每个推送周期生成一条。"""
    __tablename__ = "daily_briefings"

    id = Column(Integer, primary_key=True, index=True)
    briefing_id = Column(String(32), unique=True, index=True)
    date = Column(String(10), index=True)
    status = Column(String(32), default="draft")

    title = Column(String(256), default="")
    summary = Column(Text, default="")
    full_content = Column(Text, default="")
    risk_assessment = Column(JSON, default=dict)
    recommendations = Column(JSON, default=list)

    events_count = Column(Integer, default=0)
    sources_count = Column(Integer, default=0)
    agents_count = Column(Integer, default=0)

    push_status = Column(JSON, default=dict)
    pushed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    events = relationship("BriefingEvent", back_populates="briefing", cascade="all, delete-orphan")

    def to_dict(self, include_content: bool = True) -> dict:
        d = {
            "id": self.id,
            "briefing_id": self.briefing_id,
            "date": self.date,
            "status": self.status,
            "title": self.title,
            "summary": self.summary,
            "risk_assessment": self.risk_assessment or {},
            "recommendations": self.recommendations or [],
            "events_count": self.events_count,
            "sources_count": self.sources_count,
            "agents_count": self.agents_count,
            "push_status": self.push_status or {},
            "pushed_at": self.pushed_at.isoformat() if self.pushed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_content:
            d["full_content"] = self.full_content
        d["events"] = [e.to_dict() for e in self.events] if self.events else []
        return d


class BriefingEvent(Base):
    """简报中包含的单个事件 — 用于溯源和详情展示。"""
    __tablename__ = "briefing_events"

    id = Column(Integer, primary_key=True, index=True)
    briefing_id = Column(Integer, ForeignKey("daily_briefings.id"))

    title = Column(String(512), default="")
    source = Column(String(128), default="")
    category = Column(String(64), default="")
    summary = Column(Text, default="")
    timestamp = Column(String(32), default="")
    relevance = Column(Float, default=0.0)
    url = Column(String(1024), nullable=True)
    raw_data = Column(JSON, default=dict)
    sources_reference = Column(JSON, default=list)

    briefing = relationship("DailyBriefing", back_populates="events")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "source": self.source,
            "category": self.category,
            "summary": self.summary,
            "timestamp": self.timestamp,
            "relevance": self.relevance,
            "url": self.url,
            "sources_reference": self.sources_reference or [],
        }
