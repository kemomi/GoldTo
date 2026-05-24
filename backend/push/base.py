"""
推送服务抽象基类 — 所有推送渠道必须实现此接口
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
import abc


@dataclass
class PushResult:
    """推送结果"""
    success: bool
    channel: str
    message: str = ""
    detail: Dict[str, Any] = None

    def __post_init__(self):
        if self.detail is None:
            self.detail = {}


class PushService(abc.ABC):
    """
    推送服务抽象基类。
    每个具体推送渠道需实现:
      - channel_name: 渠道标识
      - send(title, content, config): 发送推送
      - validate_config(config): 验证配置是否完整
    """

    channel_name: str = "abstract"

    @abc.abstractmethod
    async def send(self, title: str, content: str, config: Dict[str, Any]) -> PushResult:
        """
        发送推送。
        :param title: 标题
        :param content: 内容（Markdown 或纯文本）
        :param config: 渠道配置（来自 UserConfig 的对应字段）
        :return: PushResult
        """
        raise NotImplementedError

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """检查配置是否足够发送推送。子类可覆盖。"""
        return True

    def _truncate(self, text: str, max_len: int = 4000) -> str:
        """截断长文本，防止超出渠道限制。"""
        if len(text) <= max_len:
            return text
        return text[:max_len - 20] + "\n\n...（内容已截断）"
