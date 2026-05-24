"""
World Monitor 数据源 — 地缘政治、宏观经济、市场动态
支持 RSS 真实数据源 + Mock 兜底
"""
from __future__ import annotations
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import httpx
import xml.etree.ElementTree as ET

from sources.base import DataSource, IntelEvent
from config import settings


class WorldMonitorSource(DataSource):
    """
    地缘政治与宏观经济监测数据源。
    优先使用 RSS 真实数据源，失败时回退到 Mock。
    """
    name = "world_monitor"
    categories = ["geopolitics", "market", "policy", "energy"]
    recommended_sources = [
        {"name": "BBC News", "url": "https://www.bbc.com/news", "desc": "国际政治与冲突报道"},
        {"name": "Reuters", "url": "https://www.reuters.com", "desc": "全球金融市场与宏观经济"},
        {"name": "Bloomberg", "url": "https://www.bloomberg.com", "desc": "商业新闻与市场数据"},
        {"name": "新华社", "url": "http://www.xinhuanet.com", "desc": "中国官方新闻与政策解读"},
        {"name": "财联社", "url": "https://www.cls.cn", "desc": "中国财经快讯与政策跟踪"},
    ]

    # 公开 RSS 源（无需 API Key，优先国内可访问）
    _RSS_FEEDS = [
        {"url": "https://www.36kr.com/feed", "lang": "zh", "source": "36氪"},
        {"url": "https://www.cls.cn/telegraph", "lang": "zh", "source": "财联社", "is_html": True},
        {"url": "https://rsshub.app/wallstreetcn/global", "lang": "zh", "source": "华尔街见闻"},
    ]

    # Mock 数据模板（保留作为 fallback）
    _TEMPLATES = {
        "geopolitics": [
            {"title": "中东紧张局势升级", "summary": "某地区发生冲突，国际油价盘中跳涨3%，避险情绪升温。", "impact": "high", "url": "https://www.bbc.com/news/world-middle-east"},
            {"title": "大国领导人会晤", "summary": "双方就贸易与合作达成初步共识，市场反应积极。", "impact": "medium", "url": "https://www.reuters.com/world"},
            {"title": "某国宣布制裁措施", "summary": "针对特定行业实施出口管制，供应链或受扰动。", "impact": "high", "url": "https://www.bloomberg.com/news/politics"},
            {"title": "区域军事演习开始", "summary": "多国参与海上联合演习，地区安全态势引关注。", "impact": "medium", "url": "https://www.bbc.com/news/world"},
        ],
        "market": [
            {"title": "美股三大指数集体收跌", "summary": "受通胀数据超预期影响，科技股领跌，纳指跌1.8%。", "impact": "high", "url": "https://www.bloomberg.com/markets"},
            {"title": "原油突破80美元关口", "summary": "供应收紧预期推动油价上行，能源股普遍走强。", "impact": "medium", "url": "https://www.reuters.com/markets/commodities"},
            {"title": "黄金价格创三个月新高", "summary": "避险需求推动金价上涨，央行购金数据超预期。", "impact": "medium", "url": "https://www.cls.cn/depth"},
            {"title": "某加密货币大幅波动", "summary": "监管传闻引发抛售，24小时内跌幅超15%。", "impact": "high", "url": "https://www.bloomberg.com/crypto"},
        ],
        "policy": [
            {"title": "央行维持利率不变", "summary": "货币政策会议决定按兵不动，市场聚焦后续指引。", "impact": "medium", "url": "http://www.xinhuanet.com/politics"},
            {"title": "新能源补贴政策出台", "summary": "补贴退坡幅度低于预期，光伏、储能板块受益。", "impact": "medium", "url": "https://www.cls.cn/depth"},
            {"title": "数据安全法规修订", "summary": "新增跨境数据流动限制，科技企业合规成本上升。", "impact": "high", "url": "https://flk.npc.gov.cn"},
            {"title": "财政刺激计划公布", "summary": "总规模超市场预期，基建和消费板块受提振。", "impact": "medium", "url": "http://www.xinhuanet.com/politics"},
        ],
        "energy": [
            {"title": "天然气库存低于预期", "summary": "冬季取暖需求上升，欧洲气价跳涨12%。", "impact": "high", "url": "https://www.reuters.com/business/energy"},
            {"title": "核电站检修延期", "summary": "发电量缺口由火电填补，碳排放短期上升。", "impact": "medium", "url": "https://www.bloomberg.com/news/energy"},
            {"title": "锂矿供应协议签署", "summary": "长期供应合同锁定价格，电动车成本预期下降。", "impact": "low", "url": "https://www.cls.cn/depth"},
            {"title": "海上风电项目获批", "summary": "装机容量达2GW，创区域单体项目纪录。", "impact": "low", "url": "https://www.bloomberg.com/news/energy"},
        ],
    }

    async def collect(self, config: Dict[str, Any], limit: int = 10) -> List[IntelEvent]:
        """根据用户配置的智能匹配返回相关事件。优先真实数据源。"""
        if settings.use_real_sources:
            try:
                events = await self._collect_rss(config, limit)
                if events:
                    return events
            except Exception as e:
                print(f"[WorldMonitor] RSS failed, falling back to mock: {e}")
        return await self._collect_mock(config, limit)

    async def _collect_rss(self, config: Dict[str, Any], limit: int) -> List[IntelEvent]:
        """从 RSS 源采集真实新闻。"""
        focus_targets = [kw.lower() for kw in config.get("focus_targets", [])]
        industry = (config.get("industry", "") or "").lower()
        keywords = [kw for kw in (focus_targets + [industry]) if kw]

        events: List[IntelEvent] = []
        now = datetime.utcnow()

        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            for feed in self._RSS_FEEDS:
                if len(events) >= limit:
                    break
                try:
                    resp = await client.get(feed["url"])
                    resp.raise_for_status()
                    root = ET.fromstring(resp.text)
                    items = root.findall(".//item")

                    for item in items[:limit]:
                        title = item.findtext("title", "")
                        desc = item.findtext("description", "")
                        pub_date = item.findtext("pubDate", "")
                        link = item.findtext("link", "")

                        # 关键词过滤
                        text = f"{title} {desc}".lower()
                        if keywords and not any(kw in text for kw in keywords):
                            continue

                        # 分类推断
                        category = self._infer_category(title + " " + desc)

                        events.append(IntelEvent(
                            title=title[:120],
                            source=feed["source"],
                            category=category,
                            summary=desc[:200] if desc else title,
                            timestamp=self._parse_rss_date(pub_date) or (now - timedelta(hours=random.randint(1, 24))).isoformat() + "Z",
                            relevance=self._calc_relevance(title + " " + desc, keywords),
                            impact_level="medium",
                            tags=[category, "world_monitor"],
                            url=link,
                            sources_reference=self.recommended_sources,
                        ))

                        if len(events) >= limit:
                            break
                except Exception as e:
                    print(f"[WorldMonitor] RSS {feed['source']} error: {e}")
                    continue

        return events[:limit]

    async def _collect_mock(self, config: Dict[str, Any], limit: int = 10) -> List[IntelEvent]:
        """Mock 数据生成（fallback）。"""
        focus_targets = [kw.lower() for kw in config.get("focus_targets", [])]
        industry = (config.get("industry", "") or "").lower()
        keywords = [kw for kw in (focus_targets + [industry]) if kw]

        matched_categories = []
        keyword_map = {
            "geopolitics": ["地缘", "冲突", "战争", "制裁", "外交", "中东", "军事", "politics", "geopolitic", "conflict", "war", "sanction"],
            "market": ["市场", "股市", "油价", "黄金", "通胀", "指数", "stock", "market", "oil", "gold", "crypto", "investment"],
            "policy": ["政策", "央行", "利率", "补贴", "法规", "财政", "policy", "central bank", "rate", "regulation", "tax"],
            "energy": ["能源", "天然气", "核电", "风电", "锂", "储能", "energy", "gas", "nuclear", "wind", "lithium", "solar"],
        }

        for cat, cat_keywords in keyword_map.items():
            if any(kw in keywords for kw in cat_keywords):
                matched_categories.append(cat)

        if not matched_categories:
            matched_categories = random.sample(list(self._TEMPLATES.keys()), k=min(2, len(self._TEMPLATES)))

        events: List[IntelEvent] = []
        now = datetime.utcnow()
        sources = ["Reuters", "Bloomberg", "FT", "WSJ", "Xinhua", "World Monitor", "CNBC"]

        for cat in matched_categories:
            templates = self._TEMPLATES.get(cat, [])
            for t in templates:
                events.append(IntelEvent(
                    title=t["title"],
                    source=random.choice(sources),
                    category=cat,
                    summary=t["summary"],
                    timestamp=(now - timedelta(hours=random.randint(1, 24))).isoformat() + "Z",
                    relevance=round(random.uniform(0.65, 0.95), 2),
                    impact_level=t.get("impact", "medium"),
                    tags=[cat, "world_monitor"],
                    url=t.get("url", "https://www.bbc.com/news"),
                    sources_reference=self.recommended_sources,
                ))

        random.shuffle(events)
        return events[:limit]

    @staticmethod
    def _infer_category(text: str) -> str:
        """根据文本内容推断情报类别。"""
        text_lower = text.lower()
        scores = {
            "geopolitics": sum(1 for kw in ["war", "conflict", "sanction", "military", "tension", "strike", "attack", "missile", "地缘", "冲突", "战争", "制裁"] if kw in text_lower),
            "market": sum(1 for kw in ["stock", "market", "index", "nasdaq", "dow", "rally", "plunge", "inflation", "股市", "指数", "市场", "通胀"] if kw in text_lower),
            "policy": sum(1 for kw in ["fed", "ecb", "rate", "central bank", "government", "regulation", "policy", "央行", "利率", "政策", "法规"] if kw in text_lower),
            "energy": sum(1 for kw in ["oil", "gas", "crude", "opec", "energy", "renewable", "solar", "wind", "石油", "天然气", "能源", "核电"] if kw in text_lower),
        }
        return max(scores, key=scores.get) if max(scores.values()) > 0 else "market"

    @staticmethod
    def _parse_rss_date(date_str: str) -> str:
        """解析 RSS 日期为 ISO 格式。"""
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.isoformat() + "Z"
        except Exception:
            return None

    @staticmethod
    def _calc_relevance(text: str, keywords: List[str]) -> float:
        """计算文本与关键词的相关性得分。"""
        if not keywords:
            return 0.75
        text_lower = text.lower()
        matches = sum(1 for kw in keywords if kw in text_lower)
        return min(0.95, 0.6 + matches * 0.1)
