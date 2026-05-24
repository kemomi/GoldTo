"""
World Monitor 数据源抽象层 — 简化版
MVP 中提供 Mock 数据源和 RSS 数据源
"""
from __future__ import annotations
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional
import httpx
import xml.etree.ElementTree as ET


@dataclass
class IntelEvent:
    title: str
    source: str
    category: str  # geopolitics, market, policy, tech, energy
    summary: str
    timestamp: str
    relevance: float  # 0-1


class DataSource:
    """Base class for intelligence data sources."""

    async def collect(self, topic: str, limit: int = 10) -> List[IntelEvent]:
        raise NotImplementedError


class MockDataSource(DataSource):
    """
    Mock 数据源 — 无需网络，根据主题返回模拟事件。
    灵感来自 worldmonitor-main 的多维度数据层概念。
    """

    _TEMPLATES = {
        "geopolitics": [
            {"title": "中东紧张局势升级", "summary": "某地区发生冲突，国际油价盘中跳涨3%，避险情绪升温。"},
            {"title": "大国领导人会晤", "summary": "双方就贸易与合作达成初步共识，市场反应积极。"},
            {"title": "某国宣布制裁措施", "summary": "针对特定行业实施出口管制，供应链或受扰动。"},
            {"title": "区域军事演习开始", "summary": "多国参与海上联合演习，地区安全态势引关注。"},
        ],
        "market": [
            {"title": "美股三大指数集体收跌", "summary": "受通胀数据超预期影响，科技股领跌，纳指跌1.8%。"},
            {"title": "原油突破80美元关口", "summary": "供应收紧预期推动油价上行，能源股普遍走强。"},
            {"title": "黄金价格创三个月新高", "summary": "避险需求推动金价上涨，央行购金数据超预期。"},
            {"title": "某加密货币大幅波动", "summary": "监管传闻引发抛售，24小时内跌幅超15%。"},
        ],
        "policy": [
            {"title": "央行维持利率不变", "summary": "货币政策会议决定按兵不动，市场聚焦后续指引。"},
            {"title": "新能源补贴政策出台", "summary": "补贴退坡幅度低于预期，光伏、储能板块受益。"},
            {"title": "数据安全法规修订", "summary": "新增跨境数据流动限制，科技企业合规成本上升。"},
            {"title": "财政刺激计划公布", "summary": "总规模超市场预期，基建和消费板块受提振。"},
        ],
        "tech": [
            {"title": "AI 大模型发布新版本", "summary": "参数规模翻倍，推理成本降低40%，行业格局或重塑。"},
            {"title": "半导体巨头扩产", "summary": "投资500亿美元建设新厂，缓解芯片短缺预期。"},
            {"title": "量子计算取得突破", "summary": "某团队实现1000量子比特稳定运行，商业化进程提速。"},
            {"title": "卫星互联网星座发射", "summary": "首批组网卫星成功入轨，全球覆盖计划进入实施阶段。"},
        ],
        "energy": [
            {"title": "天然气库存低于预期", "summary": "冬季取暖需求上升，欧洲气价跳涨12%。"},
            {"title": "核电站检修延期", "summary": "发电量缺口由火电填补，碳排放短期上升。"},
            {"title": "锂矿供应协议签署", "summary": "长期供应合同锁定价格，电动车成本预期下降。"},
            {"title": "海上风电项目获批", "summary": "装机容量达2GW，创区域单体项目纪录。"},
        ],
    }

    async def collect(self, topic: str, limit: int = 10) -> List[IntelEvent]:
        """根据 topic 关键词匹配相关类别的模拟事件。"""
        topic_lower = topic.lower()
        matched_categories = []

        # 简单关键词匹配
        keyword_map = {
            "geopolitics": ["地缘", "冲突", "战争", "制裁", "外交", "中东", "军事", "politics", "geopolitic", "conflict", "war"],
            "market": ["市场", "股市", "油价", "黄金", "通胀", "指数", "stock", "market", "oil", "gold", "crypto"],
            "policy": ["政策", "央行", "利率", "补贴", "法规", "财政", "policy", "central bank", "rate", "regulation"],
            "tech": ["科技", "AI", "芯片", "半导体", "量子", "卫星", "tech", "AI", "chip", "semiconductor", "quantum"],
            "energy": ["能源", "天然气", "核电", "风电", "锂", "储能", "energy", "gas", "nuclear", "wind", "lithium"],
        }

        for cat, keywords in keyword_map.items():
            if any(kw in topic_lower for kw in keywords):
                matched_categories.append(cat)

        # 如果没有匹配到，随机选 2-3 个类别
        if not matched_categories:
            matched_categories = random.sample(list(self._TEMPLATES.keys()), k=min(3, len(self._TEMPLATES)))

        events: List[IntelEvent] = []
        now = datetime.utcnow()

        for cat in matched_categories:
            templates = self._TEMPLATES.get(cat, [])
            for t in templates:
                events.append(IntelEvent(
                    title=t["title"],
                    source=random.choice(["Reuters", "Bloomberg", "FT", "WSJ", "Xinhua", "World Monitor"]),
                    category=cat,
                    summary=t["summary"],
                    timestamp=(now - timedelta(hours=random.randint(1, 48))).isoformat() + "Z",
                    relevance=round(random.uniform(0.6, 0.95), 2),
                ))

        # 随机打乱并截取
        random.shuffle(events)
        return events[:limit]


class RSSDataSource(DataSource):
    """
    RSS 数据源 — 抓取公开 RSS  feeds。
    MVP 中保留结构，默认使用 Mock 数据源以避免网络依赖。
    """

    _FEEDS = [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.reutersagency.com/feed/?best-topics=business-finance",
    ]

    async def collect(self, topic: str, limit: int = 10) -> List[IntelEvent]:
        events: List[IntelEvent] = []
        async with httpx.AsyncClient(timeout=10.0) as client:
            for feed_url in self._FEEDS:
                try:
                    resp = await client.get(feed_url)
                    resp.raise_for_status()
                    root = ET.fromstring(resp.text)
                    items = root.findall(".//item")[:limit]
                    for item in items:
                        title = item.findtext("title", "")
                        if topic.lower() not in title.lower():
                            continue
                        events.append(IntelEvent(
                            title=title,
                            source=feed_url,
                            category="news",
                            summary=item.findtext("description", "")[:200],
                            timestamp=item.findtext("pubDate", datetime.utcnow().isoformat()),
                            relevance=0.7,
                        ))
                except Exception:
                    continue
        return events
