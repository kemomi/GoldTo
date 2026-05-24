"""
GoldTo Push Services — 多渠道推送服务
"""
from push.base import PushService, PushResult
from push.email import EmailPushService
from push.feishu import FeishuPushService
from push.wecom import WecomPushService

__all__ = [
    "PushService", "PushResult",
    "EmailPushService", "FeishuPushService", "WecomPushService",
]
