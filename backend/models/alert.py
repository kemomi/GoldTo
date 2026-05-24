"""
Alert models — 情报预警规则与告警日志
"""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func

from models.database import Base


class AlertRule(Base):
    """预警规则配置 — 单用户 MVP 只有一条记录。"""
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    enabled = Column(Boolean, default=True)
    min_relevance = Column(Float, default=0.85)
    keywords = Column(JSON, default=list)       # ["AI", "芯片"]
    categories = Column(JSON, default=list)     # ["market", "tech"]
    channels = Column(JSON, default=list)       # ["email", "feishu"]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "enabled": self.enabled,
            "min_relevance": self.min_relevance,
            "keywords": self.keywords or [],
            "categories": self.categories or [],
            "channels": self.channels or [],
        }


class AlertLog(Base):
    """告警触发日志 — 每次触发产生一条记录。"""
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("alert_rules.id"))
    event_id = Column(Integer, ForeignKey("briefing_events.id"))
    event_title = Column(String(512), default="")
    event_source = Column(String(128), default="")
    event_category = Column(String(64), default="")
    event_relevance = Column(Float, default=0.0)
    event_url = Column(String(1024), nullable=True)
    matched_reason = Column(String(64), default="")   # "relevance" | "keyword"
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    push_status = Column(JSON, default=dict)
    pushed_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "event_id": self.event_id,
            "event_title": self.event_title,
            "event_source": self.event_source,
            "event_category": self.event_category,
            "event_relevance": self.event_relevance,
            "event_url": self.event_url,
            "matched_reason": self.matched_reason,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "push_status": self.push_status or {},
            "pushed_at": self.pushed_at.isoformat() if self.pushed_at else None,
        }
