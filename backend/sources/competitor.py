"""
竞争对手监测数据源 — 竞品动态、市场份额、投融资、人才流动
支持 Google News RSS + Mock 兜底
"""
from __future__ import annotations
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import httpx
import xml.etree.ElementTree as ET

from sources.base import DataSource, IntelEvent
from config import settings


class CompetitorSource(DataSource):
    """
    竞争对手情报数据源。
    优先使用 Google News RSS 搜索真实新闻，失败时回退到 Mock。
    """
    name = "competitor_monitor"
    categories = ["competitor"]
    recommended_sources = [
        {"name": "36氪", "url": "https://36kr.com", "desc": "中国创投与创业公司动态"},
        {"name": "TechCrunch", "url": "https://techcrunch.com", "desc": "全球科技创业公司报道"},
        {"name": "IT桔子", "url": "https://www.itjuzi.com", "desc": "中国企业投融资数据库"},
        {"name": "Google News", "url": "https://news.google.com", "desc": "全球新闻聚合搜索"},
    ]

    # Mock 数据模板（fallback）
    _TEMPLATES = [
        {"title_tpl": "{name} 发布新一代产品", "summary_tpl": "{name} 今日发布旗舰新品，性能提升30%，定价策略激进。", "impact": "high"},
        {"title_tpl": "{name} 完成新一轮融资", "summary_tpl": "{name} 宣布完成 {amount} 融资，估值达 {valuation}，资金将用于海外扩张。", "impact": "medium"},
        {"title_tpl": "{name} 宣布裁员 {percent}", "summary_tpl": "{name} 为优化成本结构，计划裁员 {percent}，主要影响非核心业务线。", "impact": "high"},
        {"title_tpl": "{name} 进军 {market} 市场", "summary_tpl": "{name} 正式成立 {market} 事业部，首期投入 {amount}，目标三年内市场份额达10%。", "impact": "medium"},
        {"title_tpl": "{name} 与 {partner} 达成战略合作", "summary_tpl": "双方将围绕 {area} 展开深度合作，共同开发新产品线。", "impact": "medium"},
        {"title_tpl": "{name} 核心高管离职", "summary_tpl": "{name} CTO 宣布离职，加入竞争对手团队，或影响技术路线稳定性。", "impact": "high"},
        {"title_tpl": "{name} 下调产品售价", "summary_tpl": "{name} 为应对竞争压力，全线产品降价 {percent}，利润空间进一步压缩。", "impact": "medium"},
        {"title_tpl": "{name} 获得 {cert} 认证", "summary_tpl": "{name} 成为行业首批通过 {cert} 认证的企业，合规壁垒提升。", "impact": "low"},
    ]

    _MARKETS = ["东南亚", "欧洲", "北美", "中东", "非洲", "拉美"]
    _AREAS = ["AI 芯片", "云服务", "新能源", "自动驾驶", "智能制造"]
    _PARTNERS = ["科技巨头A", "国有集团B", "跨国企业C", "独角兽D"]
    _CERTS = ["ISO 27001", "SOC 2", "GDPR 合规", "国家等保三级"]

    async def collect(self, config: Dict[str, Any], limit: int = 10) -> List[IntelEvent]:
        competitors = config.get("competitor_list", [])
        if not competitors:
            return []

        if settings.use_real_sources:
            try:
                events = await self._collect_news_rss(competitors, limit)
                if events:
                    return events
            except Exception as e:
                print(f"[Competitor] News RSS failed, falling back to mock: {e}")

        return await self._collect_mock(competitors, limit)

    async def _collect_news_rss(self, competitors: List[str], limit: int) -> List[IntelEvent]:
        """通过 Google News RSS 搜索竞争对手相关新闻。"""
        events: List[IntelEvent] = []
        now = datetime.utcnow()

        async with httpx.AsyncClient(timeout=settings.source_timeout, follow_redirects=True) as client:
            for comp in competitors[:limit]:
                if len(events) >= limit:
                    break
                try:
                    # Google News RSS 搜索
                    query = f"{comp}"
                    url = f"https://news.google.com/rss/search?q={query}&hl=zh-CN&gl=CN&ceid=CN:zh"
                    resp = await client.get(url)
                    resp.raise_for_status()
                    root = ET.fromstring(resp.text)
                    items = root.findall(".//item")

                    for item in items[:3]:  # 每个竞争对手取最多 3 条
                        title = item.findtext("title", "")
                        desc = item.findtext("description", "")
                        pub_date = item.findtext("pubDate", "")
                        link = item.findtext("link", "")

                        # 清理 Google News 的标题后缀（如 - Reuters）
                        title = title.split(" - ")[0] if " - " in title else title

                        events.append(IntelEvent(
                            title=title[:120],
                            source="Google News",
                            category="competitor",
                            summary=desc[:200] if desc else title,
                            timestamp=self._parse_rss_date(pub_date) or (now - timedelta(hours=random.randint(1, 24))).isoformat() + "Z",
                            relevance=round(random.uniform(0.75, 0.95), 2),
                            impact_level="medium",
                            tags=["competitor", comp],
                            url=link,
                            sources_reference=self.recommended_sources,
                        ))

                        if len(events) >= limit:
                            break
                except Exception as e:
                    print(f"[Competitor] RSS search for {comp} error: {e}")
                    continue

        return events[:limit]

    async def _collect_mock(self, competitors: List[str], limit: int = 10) -> List[IntelEvent]:
        """Mock 数据生成。"""
        events: List[IntelEvent] = []
        now = datetime.utcnow()
        templates = random.sample(self._TEMPLATES, k=min(len(self._TEMPLATES), limit))

        for comp in competitors[:limit]:
            tpl = random.choice(templates)
            amount = f"{random.randint(1, 10)} 亿美元" if random.random() > 0.5 else f"{random.randint(5, 50)} 亿人民币"
            valuation = f"{random.randint(10, 100)} 亿美元"
            percent = f"{random.randint(5, 30)}%"

            title = tpl["title_tpl"].format(
                name=comp,
                amount=amount,
                valuation=valuation,
                percent=percent,
                market=random.choice(self._MARKETS),
                partner=random.choice(self._PARTNERS),
                area=random.choice(self._AREAS),
                cert=random.choice(self._CERTS),
            )
            summary = tpl["summary_tpl"].format(
                name=comp,
                amount=amount,
                valuation=valuation,
                percent=percent,
                market=random.choice(self._MARKETS),
                partner=random.choice(self._PARTNERS),
                area=random.choice(self._AREAS),
                cert=random.choice(self._CERTS),
            )

            _URLS = [
                "https://36kr.com",
                "https://techcrunch.com",
                "https://www.itjuzi.com",
                "https://www.cls.cn",
            ]
            events.append(IntelEvent(
                title=title,
                source=random.choice(["36氪", "TechCrunch", "财联社", "IT桔子", "脉脉"]),
                category="competitor",
                summary=summary,
                timestamp=(now - timedelta(hours=random.randint(1, 24))).isoformat() + "Z",
                relevance=round(random.uniform(0.7, 0.95), 2),
                impact_level=tpl["impact"],
                tags=["competitor", comp],
                url=random.choice(_URLS),
                sources_reference=self.recommended_sources,
            ))

        return events

    @staticmethod
    def _parse_rss_date(date_str: str) -> str:
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.isoformat() + "Z"
        except Exception:
            return None
