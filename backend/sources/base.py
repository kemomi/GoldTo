"""
数据源抽象基类 — 所有情报数据源必须实现此接口
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import abc


@dataclass
class IntelEvent:
    """标准化情报事件结构 — 所有数据源返回统一格式。"""
    title: str
    source: str
    category: str                          # 数据源类别标识
    summary: str
    timestamp: str = ""
    relevance: float = 0.0                 # 0-1 相关性得分
    url: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    sentiment: Optional[str] = None        # positive / neutral / negative
    geography: Optional[str] = None        # 影响地域
    impact_level: Optional[str] = None     # high / medium / low
    # 该事件的信息来源参考（供用户查验真伪）
    sources_reference: List[Dict[str, str]] = field(default_factory=list)


class DataSource(abc.ABC):
    """
    数据源抽象基类。
    每个具体数据源需实现:
      - name: 数据源名称
      - categories: 该数据源覆盖的情报类别
      - recommended_sources: 该类别推荐的2-5个信息源（名称+URL）
      - collect(config, limit): 采集情报事件
    """

    name: str = "abstract"
    categories: List[str] = []
    # 推荐信息源列表：[(名称, URL, 说明), ...]
    recommended_sources: List[Dict[str, str]] = []

    @abc.abstractmethod
    async def collect(self, config: Dict[str, Any], limit: int = 10) -> List[IntelEvent]:
        """
        采集情报事件。
        :param config: 用户配置字典（industry, focus_targets, competitor_list 等）
        :param limit: 最多返回事件数
        :return: IntelEvent 列表
        """
        raise NotImplementedError

    def is_available(self) -> bool:
        """检查数据源是否可用（如 API Key 是否配置）。"""
        return True

    def get_sources_reference(self) -> List[Dict[str, str]]:
        """返回该数据源的推荐信息源列表，用于简报溯源。"""
        return self.recommended_sources
