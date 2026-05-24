"""
User configuration model — 行业、关注目标、推送渠道、定时设置
"""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func

from models.database import Base


class PushChannel:
    """推送渠道常量"""
    EMAIL = "email"
    FEISHU = "feishu"
    WECOM = "wecom"
    DINGTALK = "dingtalk"
    ALL = [EMAIL, FEISHU, WECOM, DINGTALK]


class UserConfig(Base):
    """
    用户配置表 — MVP 阶段先支持单用户（id=1）。
    后续扩展为多用户时，增加 user_id / auth 字段即可。
    """
    __tablename__ = "user_configs"

    id = Column(Integer, primary_key=True, index=True)

    # ── 基础信息 ──
    nickname = Column(String(64), default="用户")
    email = Column(String(256), nullable=True)

    # ── 行业与关注目标 ──
    industry = Column(String(128), default="")
    focus_targets = Column(JSON, default=list)
    competitor_list = Column(JSON, default=list)
    product_keywords = Column(JSON, default=list)
    social_keywords = Column(JSON, default=list)

    # ── 推送设置 ──
    push_channels = Column(JSON, default=list)
    push_time = Column(String(8), default="08:00")
    timezone = Column(String(32), default="Asia/Shanghai")
    push_enabled = Column(Boolean, default=True)

    # ── 渠道配置 ──
    email_smtp_host = Column(String(128), nullable=True)
    email_smtp_port = Column(Integer, default=587)
    email_smtp_user = Column(String(256), nullable=True)
    email_smtp_pass = Column(String(256), nullable=True)
    email_sender = Column(String(256), nullable=True)

    feishu_webhook = Column(String(512), nullable=True)
    feishu_app_id = Column(String(128), nullable=True)
    feishu_app_secret = Column(String(256), nullable=True)

    wecom_webhook = Column(String(512), nullable=True)
    dingtalk_webhook = Column(String(512), nullable=True)

    # ── 简报偏好 ──
    briefing_language = Column(String(16), default="zh")
    briefing_detail_level = Column(String(16), default="standard")
    briefing_sections = Column(JSON, default=list)

    # ── 元数据 ──
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self, include_channels: bool = True) -> dict:
        d = {
            "id": self.id,
            "nickname": self.nickname,
            "email": self.email,
            "industry": self.industry,
            "focus_targets": self.focus_targets or [],
            "competitor_list": self.competitor_list or [],
            "product_keywords": self.product_keywords or [],
            "social_keywords": self.social_keywords or [],
            "push_channels": self.push_channels or [],
            "push_time": self.push_time,
            "timezone": self.timezone,
            "push_enabled": self.push_enabled,
            "briefing_language": self.briefing_language,
            "briefing_detail_level": self.briefing_detail_level,
            "briefing_sections": self.briefing_sections or [],
        }
        if include_channels:
            d.update({
                "email_smtp_host": self.email_smtp_host,
                "email_smtp_port": self.email_smtp_port,
                "email_smtp_user": self.email_smtp_user,
                "email_sender": self.email_sender,
                "feishu_webhook": self.feishu_webhook,
                "feishu_app_id": self.feishu_app_id,
                "wecom_webhook": self.wecom_webhook,
                "dingtalk_webhook": self.dingtalk_webhook,
                # 密码字段不返回
            })
        return d
