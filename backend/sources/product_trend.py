"""
产品趋势数据源 — 新品发布、技术突破、供应链变化
支持 Hacker News API + Mock 兜底
"""
from __future__ import annotations
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import httpx

from sources.base import DataSource, IntelEvent
from config import settings


class ProductTrendSource(DataSource):
    """
    产品与技术趋势数据源。
    优先使用 Hacker News Algolia API 搜索，失败时回退到 Mock。
    """
    name = "product_trend"
    categories = ["product", "tech"]
    recommended_sources = [
        {"name": "Product Hunt", "url": "https://www.producthunt.com", "desc": "全球新产品发布平台"},
        {"name": "Hacker News", "url": "https://news.ycombinator.com", "desc": "技术与创业社区热点"},
        {"name": "GitHub Trending", "url": "https://github.com/trending", "desc": "开源技术趋势"},
        {"name": "Gartner", "url": "https://www.gartner.com", "desc": "行业研究与技术成熟度曲线"},
    ]

    _TEMPLATES = [
        {"title_tpl": "{product} 类新品密集发布", "summary_tpl": "过去24小时内有 {count} 家厂商发布 {product} 相关产品，功能同质化严重，价格战风险上升。", "impact": "high"},
        {"title_tpl": "{tech} 技术取得关键突破", "summary_tpl": "{company} 实验室宣布 {tech} 效率提升 {percent}，商业化时间表提前至 {year} 年。", "impact": "medium"},
        {"title_tpl": "{product} 核心元器件供应紧张", "summary_tpl": "受 {reason} 影响，{product} 所需 {component} 交货周期延长至 {weeks} 周，成本上涨 {percent}。", "impact": "high"},
        {"title_tpl": "消费者调研：{product} 偏好转向 {feature}", "summary_tpl": "{percent} 的受访者表示更看重 {feature}，传统 {old_feature} 关注度下降 {drop}。", "impact": "medium"},
    ]

    _COMPANIES = ["科技巨头A", "独角兽B", "行业龙头C", "初创公司D", "研究所E"]
    _REASONS = ["地缘政治", "自然灾害", "产能转移", "环保限产", "原材料涨价"]
    _COMPONENTS = ["芯片", "传感器", "电池", "显示屏", "模组"]
    _FEATURES = ["智能化", "性价比", "环保材料", "定制化", "快速交付"]
    _OLD_FEATURES = ["品牌溢价", "功能堆砌", "渠道覆盖", "售后服务"]

    async def collect(self, config: Dict[str, Any], limit: int = 10) -> List[IntelEvent]:
        keywords = config.get("product_keywords", [])
        industry = config.get("industry", "")
        all_keywords = [kw for kw in (keywords + [industry]) if kw]
        if not all_keywords:
            return []

        if settings.use_real_sources:
            try:
                events = await self._collect_hackernews(all_keywords, limit)
                if events:
                    return events
            except Exception as e:
                print(f"[ProductTrend] HN API failed, falling back to mock: {e}")

        return await self._collect_mock(all_keywords, limit)

    async def _collect_hackernews(self, keywords: List[str], limit: int) -> List[IntelEvent]:
        """从 Hacker News Algolia API 搜索技术/产品趋势。"""
        events: List[IntelEvent] = []
        now = datetime.utcnow()

        async with httpx.AsyncClient(timeout=settings.source_timeout) as client:
            for kw in keywords[:limit]:
                if len(events) >= limit:
                    break
                try:
                    url = f"https://hn.algolia.com/api/v1/search?query={kw}&hitsPerPage=3"
                    resp = await client.get(url)
                    resp.raise_for_status()
                    data = resp.json()
                    hits = data.get("hits", [])

                    for hit in hits:
                        title = hit.get("title", "") or hit.get("story_title", "")
                        story_text = hit.get("story_text", "") or ""
                        author = hit.get("author", "")
                        points = hit.get("points", 0)
                        created = hit.get("created_at_i", 0)
                        object_id = hit.get("objectID", "")
                        url_link = f"https://news.ycombinator.com/item?id={object_id}"

                        if not title:
                            continue

                        events.append(IntelEvent(
                            title=title[:120],
                            source="Hacker News",
                            category="tech",
                            summary=story_text[:200] if story_text else title,
                            timestamp=datetime.utcfromtimestamp(created).isoformat() + "Z" if created else (now - timedelta(hours=random.randint(1, 24))).isoformat() + "Z",
                            relevance=min(0.95, 0.6 + (points / 500)),
                            impact_level="medium",
                            tags=["tech", kw],
                            url=url_link,
                            sources_reference=self.recommended_sources,
                        ))

                        if len(events) >= limit:
                            break
                except Exception as e:
                    print(f"[ProductTrend] HN search for {kw} error: {e}")
                    continue

        return events[:limit]

    async def _collect_mock(self, keywords: List[str], limit: int = 10) -> List[IntelEvent]:
        """Mock 数据生成。"""
        events: List[IntelEvent] = []
        now = datetime.utcnow()

        for kw in keywords[:limit]:
            tpl = random.choice(self._TEMPLATES)
            percent = f"{random.randint(10, 50)}%"
            year = datetime.now().year + random.randint(0, 2)

            title = tpl["title_tpl"].format(
                product=kw,
                tech=kw,
                company=random.choice(self._COMPANIES),
            )
            summary = tpl["summary_tpl"].format(
                product=kw,
                tech=kw,
                company=random.choice(self._COMPANIES),
                count=random.randint(3, 12),
                percent=percent,
                year=year,
                reason=random.choice(self._REASONS),
                component=random.choice(self._COMPONENTS),
                weeks=random.randint(4, 20),
                feature=random.choice(self._FEATURES),
                old_feature=random.choice(self._OLD_FEATURES),
                drop=f"{random.randint(10, 40)}%",
            )

            _URLS = [
                "https://www.producthunt.com",
                "https://news.ycombinator.com",
                "https://github.com/trending",
                "https://www.gartner.com",
            ]
            events.append(IntelEvent(
                title=title,
                source=random.choice(["Gartner", "IDC", "亿欧", "艾瑞咨询", "行业研究院"]),
                category="product",
                summary=summary,
                timestamp=(now - timedelta(hours=random.randint(1, 24))).isoformat() + "Z",
                relevance=round(random.uniform(0.6, 0.92), 2),
                impact_level=tpl["impact"],
                tags=["product", kw],
                url=random.choice(_URLS),
                sources_reference=self.recommended_sources,
            ))

        return events
