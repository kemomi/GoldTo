"""
信息筛选引擎 — 基于用户配置的相关性打分、去重、摘要
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any
from collections import OrderedDict

from sources.base import IntelEvent


@dataclass
class FilterConfig:
    """筛选配置"""
    min_relevance: float = 0.5           # 最低相关性阈值
    max_events: int = 20                 # 最大事件数
    dedup_threshold: float = 0.85        # 去重相似度阈值（基于标题）
    require_sentiment: bool = False      # 是否要求情感分析
    priority_categories: List[str] = field(default_factory=list)


class RelevanceEngine:
    """
    情报事件筛选引擎。
    功能：
      1. 相关性打分增强（基于用户关键词加权）
      2. 跨数据源去重（相似标题合并）
      3. 分类排序（按优先级类别 + 相关性）
      4. 截断控制（按 max_events 截取）
    """

    def __init__(self, config: FilterConfig = None):
        self.config = config or FilterConfig()

    def filter(self, events: List[IntelEvent], user_config: Dict[str, Any]) -> List[IntelEvent]:
        """
        主入口：对原始事件列表进行筛选、打分、去重、排序。
        """
        # 1. 相关性增强打分
        scored = self._rescore(events, user_config)

        # 2. 阈值过滤
        filtered = [e for e in scored if e.relevance >= self.config.min_relevance]

        # 3. 去重
        deduped = self._deduplicate(filtered)

        # 4. 排序（优先级类别 + 相关性 + 时间）
        sorted_events = self._sort(deduped, user_config)

        # 5. 截断
        return sorted_events[:self.config.max_events]

    def _rescore(self, events: List[IntelEvent], user_config: Dict[str, Any]) -> List[IntelEvent]:
        """基于用户关键词重新计算相关性得分。"""
        focus_targets = [kw.lower() for kw in user_config.get("focus_targets", [])]
        competitors = [kw.lower() for kw in user_config.get("competitor_list", [])]
        products = [kw.lower() for kw in user_config.get("product_keywords", [])]
        social = [kw.lower() for kw in user_config.get("social_keywords", [])]
        industry = (user_config.get("industry", "") or "").lower()

        all_keywords = OrderedDict()
        for kw in focus_targets + competitors + products + social:
            if kw:
                all_keywords[kw] = 1.0
        if industry:
            all_keywords[industry] = 0.8

        for event in events:
            text = f"{event.title} {event.summary}".lower()
            bonus = 0.0
            for kw, weight in all_keywords.items():
                if kw in text:
                    bonus += 0.1 * weight

            # 高影响事件额外加分
            if event.impact_level == "high":
                bonus += 0.05
            elif event.impact_level == "low":
                bonus -= 0.05

            event.relevance = min(1.0, max(0.0, event.relevance + bonus))

        return events

    def _deduplicate(self, events: List[IntelEvent]) -> List[IntelEvent]:
        """基于标题相似度去重。"""
        unique: List[IntelEvent] = []

        for event in events:
            is_dup = False
            for existing in unique:
                sim = self._title_similarity(event.title, existing.title)
                if sim >= self.config.dedup_threshold:
                    # 保留相关性更高的
                    if event.relevance > existing.relevance:
                        existing.title = event.title
                        existing.summary = event.summary
                        existing.relevance = event.relevance
                        existing.source = f"{existing.source}, {event.source}"
                    is_dup = True
                    break

            if not is_dup:
                unique.append(event)

        return unique

    def _sort(self, events: List[IntelEvent], user_config: Dict[str, Any]) -> List[IntelEvent]:
        """排序：优先级类别 > 相关性 > 时间（新在前）。"""
        priority = self.config.priority_categories or [
            "competitor", "legal", "market", "geopolitics", "social", "product", "policy", "energy", "tech"
        ]

        def sort_key(e: IntelEvent):
            cat_rank = priority.index(e.category) if e.category in priority else 999
            # 时间戳转数值（越新越大）
            ts_val = e.timestamp or ""
            return (cat_rank, -e.relevance, -ord(ts_val[0]) if ts_val else 0)

        return sorted(events, key=sort_key)

    @staticmethod
    def _title_similarity(a: str, b: str) -> float:
        """简单的标题相似度（Jaccard on character bigrams）。"""
        if not a or not b:
            return 0.0

        def bigrams(s: str):
            return set(s[i:i+2] for i in range(len(s) - 1))

        ba = bigrams(a.lower())
        bb = bigrams(b.lower())
        inter = len(ba & bb)
        union = len(ba | bb)
        return inter / union if union > 0 else 0.0
