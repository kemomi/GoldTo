"""
企业微信推送服务 — 通过群机器人 Webhook 发送消息
参考文档: https://developer.work.weixin.qq.com/document/path/91770
"""
from __future__ import annotations
from typing import Dict, Any
import re
import httpx

from push.base import PushService, PushResult


class WecomPushService(PushService):
    """通过企业微信 Webhook 发送推送。"""
    channel_name = "wecom"

    def validate_config(self, config: Dict[str, Any]) -> bool:
        return bool(config.get("wecom_webhook"))

    async def send(self, title: str, content: str, config: Dict[str, Any]) -> PushResult:
        if not self.validate_config(config):
            return PushResult(
                success=False,
                channel=self.channel_name,
                message="企业微信 Webhook 未配置",
            )

        webhook = config["wecom_webhook"]
        text_content = self._strip_markdown(content)

        # 企业微信支持 markdown 消息
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": self._truncate(f"**{title}**\n\n{text_content}", 4000),
            },
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(webhook, json=payload)
                data = resp.json()

            if data.get("errcode") == 0:
                return PushResult(
                    success=True,
                    channel=self.channel_name,
                    message="企业微信推送成功",
                    detail={"webhook": webhook[:40] + "..."},
                )
            else:
                return PushResult(
                    success=False,
                    channel=self.channel_name,
                    message=f"企业微信返回错误: {data.get('errmsg', 'unknown')}",
                    detail={"errcode": data.get("errcode")},
                )

        except Exception as e:
            return PushResult(
                success=False,
                channel=self.channel_name,
                message=f"企业微信推送失败: {str(e)}",
            )

    def _strip_markdown(self, text: str) -> str:
        """去除 Markdown 标记，转换为企业微信兼容格式。"""
        text = re.sub(r"#+\s*", "", text)
        text = re.sub(r"\*\*|__", "**", text)
        text = re.sub(r"\*|_", "", text)
        text = re.sub(r"`{1,3}[^`]*`{1,3}", "", text)
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
        text = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", r"[\1](\2)", text)
        return text.strip()
