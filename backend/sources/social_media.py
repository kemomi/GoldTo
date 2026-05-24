"""
社交媒体声量数据源 — 品牌舆情、热点话题、用户反馈
支持 Reddit API + Mock 兜底
"""
from __future__ import annotations
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import httpx

from sources.base import DataSource, IntelEvent
from config import settings


class SocialMediaSource(DataSource):
    """
    社交媒体舆情监测数据源。
    优先使用 Reddit 搜索真实帖子，失败时回退到 Mock。
    """
    name = "social_media"
    categories = ["social"]
    recommended_sources = [
        {"name": "微博热搜", "url": "https://weibo.com", "desc": "中文社交媒体热点话题"},
        {"name": "Twitter/X Trends", "url": "https://x.com/explore", "desc": "全球社交媒体实时趋势"},
        {"name": "Reddit", "url": "https://www.reddit.com", "desc": "英文社区讨论与舆情"},
        {"name": "知乎", "url": "https://www.zhihu.com", "desc": "中文深度讨论与行业观点"},
    ]

    _TEMPLATES = [
        {"title_tpl": "#{topic} 登上热搜榜 TOP{rank}", "summary_tpl": "{platform} 上 #{topic} 话题阅读量突破 {views}，讨论量 {comments}，情感倾向偏 {sentiment}。", "impact": "high"},
        {"title_tpl": "KOL {kol} 点评 {topic}", "summary_tpl": "头部博主 {kol} 发布 {topic} 相关分析视频，获赞 {likes}，引发大量二次传播。", "impact": "medium"},
        {"title_tpl": "{platform} 用户对 {topic} 反馈 {sentiment}", "summary_tpl": "抽样分析显示，{platform} 上关于 {topic} 的 {count} 条评论中，{positive}% 正面，{negative}% 负面，主要槽点集中在 {pain_point}。", "impact": "medium"},
    ]

    _PLATFORMS = ["微博", "抖音", "小红书", "B站", "知乎", "Twitter/X", "LinkedIn"]
    _KOLS = ["科技君", "财经观察", "产品拆解王", "行业瞭望", "深度商业", "创投笔记"]
    _PAIN_POINTS = ["价格", "服务体验", "产品质量", "售后响应", "功能缺失"]

    async def collect(self, config: Dict[str, Any], limit: int = 10) -> List[IntelEvent]:
        keywords = config.get("social_keywords", []) + config.get("product_keywords", [])
        if not keywords:
            return []

        if settings.use_real_sources:
            try:
                events = await self._collect_reddit(keywords, limit)
                if events:
                    return events
            except Exception as e:
                print(f"[SocialMedia] Reddit failed, falling back to mock: {e}")

        return await self._collect_mock(keywords, limit)

    async def _collect_reddit(self, keywords: List[str], limit: int) -> List[IntelEvent]:
        """从 Reddit 搜索相关帖子。"""
        events: List[IntelEvent] = []
        now = datetime.utcnow()

        async with httpx.AsyncClient(timeout=settings.source_timeout, follow_redirects=True) as client:
            for kw in keywords[:limit]:
                if len(events) >= limit:
                    break
                try:
                    url = f"https://www.reddit.com/r/all/search.json?q={kw}&limit=3"
                    headers = {"User-Agent": "GoldTo-Intelligence/1.0"}
                    resp = await client.get(url, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                    posts = data.get("data", {}).get("children", [])

                    for post in posts:
                        p = post.get("data", {})
                        title = p.get("title", "")
                        text = p.get("selftext", "")[:200]
                        subreddit = p.get("subreddit", "")
                        ups = p.get("ups", 0)
                        created = p.get("created_utc", 0)
                        url_link = f"https://reddit.com{p.get('permalink', '')}"

                        # 简单情感判断
                        sentiment = "neutral"
                        if ups > 100:
                            sentiment = "positive"

                        events.append(IntelEvent(
                            title=title[:120],
                            source=f"r/{subreddit}",
                            category="social",
                            summary=text or title,
                            timestamp=datetime.utcfromtimestamp(created).isoformat() + "Z" if created else (now - timedelta(hours=random.randint(1, 12))).isoformat() + "Z",
                            relevance=min(0.95, 0.55 + (ups / 1000)),
                            impact_level="medium",
                            sentiment=sentiment,
                            tags=["social", kw, subreddit],
                            url=url_link,
                            sources_reference=self.recommended_sources,
                        ))

                        if len(events) >= limit:
                            break
                except Exception as e:
                    print(f"[SocialMedia] Reddit search for {kw} error: {e}")
                    continue

        return events[:limit]

    async def _collect_mock(self, keywords: List[str], limit: int = 10) -> List[IntelEvent]:
        """Mock 数据生成。"""
        events: List[IntelEvent] = []
        now = datetime.utcnow()

        for kw in keywords[:limit]:
            tpl = random.choice(self._TEMPLATES)
            sentiment = random.choice(["positive", "neutral", "negative"])
            sentiment_cn = {"positive": "正面", "neutral": "中性", "negative": "负面"}[sentiment]

            title = tpl["title_tpl"].format(
                topic=kw,
                rank=random.randint(1, 20),
                kol=random.choice(self._KOLS),
                platform=random.choice(self._PLATFORMS),
            )
            summary = tpl["summary_tpl"].format(
                topic=kw,
                platform=random.choice(self._PLATFORMS),
                views=f"{random.randint(1, 50)} 亿" if random.random() > 0.5 else f"{random.randint(100, 900)} 万",
                comments=f"{random.randint(1, 20)} 万",
                sentiment=sentiment_cn,
                kol=random.choice(self._KOLS),
                likes=f"{random.randint(1, 50)} 万",
                count=random.randint(1000, 10000),
                positive=random.randint(40, 80),
                negative=random.randint(5, 30),
                pain_point=random.choice(self._PAIN_POINTS),
            )

            _URLS = [
                "https://weibo.com",
                "https://x.com",
                "https://www.reddit.com",
                "https://www.zhihu.com",
            ]
            events.append(IntelEvent(
                title=title,
                source=random.choice(self._PLATFORMS),
                category="social",
                summary=summary,
                timestamp=(now - timedelta(hours=random.randint(1, 12))).isoformat() + "Z",
                relevance=round(random.uniform(0.55, 0.9), 2),
                impact_level=tpl["impact"],
                sentiment=sentiment,
                tags=["social", kw],
                url=random.choice(_URLS),
                sources_reference=self.recommended_sources,
            ))

        return events
