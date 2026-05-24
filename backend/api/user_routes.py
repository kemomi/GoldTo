"""
用户配置 API — 读取/更新用户推送设置、行业、关注目标等
"""
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models.database import get_db
from models.user import UserConfig, PushChannel

router = APIRouter(prefix="/api")


# ── Schemas ──

class UserConfigOut(BaseModel):
    id: int
    nickname: str
    email: Optional[str]
    industry: str
    focus_targets: list
    competitor_list: list
    product_keywords: list
    social_keywords: list
    push_channels: list
    push_time: str
    timezone: str
    push_enabled: bool
    briefing_language: str
    briefing_detail_level: str
    briefing_sections: list
    # 渠道配置（非敏感字段）
    email_smtp_host: Optional[str] = None
    email_smtp_port: int = 587
    email_smtp_user: Optional[str] = None
    email_sender: Optional[str] = None
    feishu_webhook: Optional[str] = None
    feishu_app_id: Optional[str] = None
    wecom_webhook: Optional[str] = None
    dingtalk_webhook: Optional[str] = None

    class Config:
        from_attributes = True


class UserConfigUpdate(BaseModel):
    nickname: Optional[str] = None
    email: Optional[str] = None
    industry: Optional[str] = None
    focus_targets: Optional[list] = None
    competitor_list: Optional[list] = None
    product_keywords: Optional[list] = None
    social_keywords: Optional[list] = None
    push_channels: Optional[list] = None
    push_time: Optional[str] = None
    timezone: Optional[str] = None
    push_enabled: Optional[bool] = None
    briefing_language: Optional[str] = None
    briefing_detail_level: Optional[str] = None
    briefing_sections: Optional[list] = None


class ChannelConfigUpdate(BaseModel):
    email_smtp_host: Optional[str] = None
    email_smtp_port: Optional[int] = Field(default=None, ge=1, le=65535)
    email_smtp_user: Optional[str] = None
    email_smtp_pass: Optional[str] = None
    email_sender: Optional[str] = None
    feishu_webhook: Optional[str] = None
    feishu_app_id: Optional[str] = None
    feishu_app_secret: Optional[str] = None
    wecom_webhook: Optional[str] = None
    dingtalk_webhook: Optional[str] = None


class PushTestRequest(BaseModel):
    channel: str
    title: str = "GoldTo 推送测试"
    content: str = "这是一条测试消息，验证推送渠道配置是否正确。"


# ── Helpers ──

def _get_or_create_user(db: Session) -> UserConfig:
    """MVP: 单用户模式，自动创建 id=1 的配置记录。"""
    user = db.query(UserConfig).first()
    if not user:
        user = UserConfig(id=1)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


# ── Routes ──

@router.get("/user/config", response_model=UserConfigOut)
async def get_user_config(db: Session = Depends(get_db)):
    """获取当前用户配置。"""
    user = _get_or_create_user(db)
    return user


@router.patch("/user/config")
async def update_user_config(data: UserConfigUpdate, db: Session = Depends(get_db)):
    """更新用户配置（基础信息、行业、关注目标、推送偏好）。"""
    user = _get_or_create_user(db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return {"message": "配置已更新", "config": user.to_dict()}


@router.patch("/user/channels")
async def update_channel_config(data: ChannelConfigUpdate, db: Session = Depends(get_db)):
    """更新推送渠道敏感配置（SMTP、Webhook 等）。"""
    user = _get_or_create_user(db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return {"message": "渠道配置已更新"}


@router.post("/user/push-test")
async def test_push_channel(req: PushTestRequest, db: Session = Depends(get_db)):
    """测试单个推送渠道。"""
    user = _get_or_create_user(db)
    user_dict = user.to_dict()

    from push.email import EmailPushService
    from push.feishu import FeishuPushService
    from push.wecom import WecomPushService

    services = {
        PushChannel.EMAIL: EmailPushService(),
        PushChannel.FEISHU: FeishuPushService(),
        PushChannel.WECOM: WecomPushService(),
    }

    service = services.get(req.channel)
    if not service:
        raise HTTPException(400, f"不支持的推送渠道: {req.channel}")

    import asyncio
    result = await service.send(req.title, req.content, user_dict)

    return {
        "success": result.success,
        "channel": req.channel,
        "message": result.message,
        "detail": result.detail,
    }


@router.get("/user/push-channels")
async def list_push_channels():
    """获取支持的推送渠道列表。"""
    return {
        "channels": [
            {"id": PushChannel.EMAIL, "name": "邮件", "icon": "Mail", "configurable": True},
            {"id": PushChannel.FEISHU, "name": "飞书", "icon": "MessageSquare", "configurable": True},
            {"id": PushChannel.WECOM, "name": "企业微信", "icon": "Building2", "configurable": True},
            {"id": PushChannel.DINGTALK, "name": "钉钉", "icon": "AtSign", "configurable": True},
        ]
    }
