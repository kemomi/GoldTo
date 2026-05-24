from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import asyncio
import re
from typing import Any

import httpx

from config import settings


WATCHED_BUCKETS: dict[str, tuple[str, ...]] = {
    "full": ("middleeast", "asia", "gov", "crisis", "finance"),
    "finance": ("markets", "centralbanks", "fin-regulation", "gccNews"),
    "commodity": (
        "commodity-news",
        "gold-silver",
        "supply-chain",
        "commodity-regulation",
        "markets",
        "finance",
    ),
}

MARKET_KEYWORDS: dict[str, tuple[str, ...]] = {
    "东南亚": (
        "singapore",
        "malaysia",
        "thailand",
        "vietnam",
        "philippines",
        "cambodia",
        "indonesia",
        "southeast asia",
        "asean",
        "changi",
        "bangkok",
        "kuala lumpur",
    ),
    "日韩": ("japan", "tokyo", "osaka", "korea", "south korea", "seoul", "rakuten", "qoo10"),
    "北美": ("united states", "u.s.", "us ", "america", "canada", "toronto", "vancouver", "new york"),
    "中东": ("middle east", "uae", "dubai", "abu dhabi", "qatar", "doha", "saudi", "riyadh", "gcc"),
    "澳洲": ("australia", "sydney", "melbourne", "brisbane"),
    "全球": ("global market", "worldwide", "international market", "global trade"),
}

TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "company": ("chow tai fook", "周大福", "ctf jewellery", "chow tai"),
    "competitor": (
        "cartier",
        "tiffany",
        "bulgari",
        "bvlgari",
        "van cleef",
        "chow sang sang",
        "lukfook",
        "周生生",
        "六福",
        "luxury jewelry",
        "luxury jewellery",
    ),
    "product": (
        "jewelry",
        "jewellery",
        "diamond",
        "gold jewellery",
        "gold jewelry",
        "bridal",
        "wedding",
        "luxury",
        "watch",
        "precious metals",
        "bullion",
    ),
    "macro": (
        "gold price",
        "gold market",
        "forex",
        "currency",
        "exchange rate",
        "central bank",
        "inflation",
        "consumer confidence",
        "retail sales",
        "tourism",
    ),
    "channel": (
        "mall",
        "airport",
        "duty free",
        "retail",
        "e-commerce",
        "ecommerce",
        "shopee",
        "lazada",
        "amazon",
        "rakuten",
        "qoo10",
    ),
    "compliance": (
        "tariff",
        "customs",
        "regulation",
        "regulatory",
        "sanctions",
        "aml",
        "kyc",
        "privacy",
        "consumer protection",
        "advertising law",
        "hallmark",
        "assay",
    ),
    "supply_chain": (
        "supply chain",
        "shipping",
        "freight",
        "logistics",
        " port ",
        "ports",
        "port congestion",
        "port disruption",
        "mine",
        "mining",
        "esg",
        "responsible sourcing",
        "diamond source",
    ),
    "reputation": (
        "boycott",
        "complaint",
        "recall",
        "scandal",
        "controversy",
        "lawsuit",
        "social media",
        "influencer",
    ),
}

OWNER_BY_CATEGORY = {
    "company": "管理层",
    "competitor": "品牌战略",
    "product": "产品团队",
    "macro": "财务与海外运营",
    "channel": "海外运营",
    "compliance": "合规法务",
    "supply_chain": "供应链",
    "reputation": "公关传播",
}

SIGNAL_TYPE_BY_CATEGORY = {
    "competitor": "risk",
    "compliance": "risk",
    "supply_chain": "risk",
    "reputation": "risk",
    "macro": "watch",
    "channel": "opportunity",
    "product": "opportunity",
    "company": "watch",
}

THREAT_SCORES = {
    "THREAT_LEVEL_CRITICAL": 1.0,
    "THREAT_LEVEL_HIGH": 0.85,
    "THREAT_LEVEL_MEDIUM": 0.62,
    "THREAT_LEVEL_LOW": 0.38,
    "THREAT_LEVEL_UNSPECIFIED": 0.2,
}

SOURCE_TYPE_BY_VARIANT = {
    "full": "news",
    "finance": "financial",
    "commodity": "commodity",
}


@dataclass
class WorldMonitorEvent:
    id: str
    title: str
    summary: str
    source: str
    url: str
    published_at_ms: int
    variant: str
    bucket: str
    importance_score: int
    corroboration_count: int
    is_alert: bool
    threat_level: str
    threat_category: str
    threat_confidence: float
    location_name: str = ""

    @property
    def text(self) -> str:
        return f"{self.title}\n{self.summary}\n{self.source}\n{self.bucket}\n{self.location_name}".lower()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "source": self.source,
            "url": self.url,
            "published_at": iso_from_ms(self.published_at_ms),
            "published_at_ms": self.published_at_ms,
            "variant": self.variant,
            "bucket": self.bucket,
            "importance_score": self.importance_score,
            "corroboration_count": self.corroboration_count,
            "is_alert": self.is_alert,
            "threat_level": self.threat_level,
            "threat_category": self.threat_category,
            "threat_confidence": self.threat_confidence,
            "location_name": self.location_name,
        }


@dataclass
class FilteredSignal:
    event: WorldMonitorEvent
    decision: str
    market: str
    category: str
    signal_type: str
    suggested_owner: str
    priority_score: float
    business_impact: float
    urgency: float
    strategic_relevance: float
    source_confidence: float
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        base = self.event.to_dict()
        base.update({
            "decision": self.decision,
            "market": self.market,
            "category": self.category,
            "signal_type": self.signal_type,
            "suggested_owner": self.suggested_owner,
            "priority_score": round(self.priority_score, 3),
            "scores": {
                "business_impact": round(self.business_impact, 3),
                "urgency": round(self.urgency, 3),
                "strategic_relevance": round(self.strategic_relevance, 3),
                "source_confidence": round(self.source_confidence, 3),
            },
            "reasons": self.reasons,
        })
        return base


async def fetch_worldmonitor_digest() -> dict[str, Any]:
    base_url = settings.worldmonitor_base_url.rstrip("/")
    raw: dict[str, Any] = {}
    events: list[WorldMonitorEvent] = []
    errors: dict[str, str] = {}

    async with httpx.AsyncClient(timeout=settings.worldmonitor_timeout) as client:
        async def fetch_variant(variant: str, buckets: tuple[str, ...]) -> tuple[str, dict[str, Any] | None, list[WorldMonitorEvent], str | None]:
            url = f"{base_url}/api/news/v1/list-feed-digest"
            try:
                resp = await client.get(url, params={"variant": variant, "lang": "en"})
                resp.raise_for_status()
                data = resp.json()
                return variant, data, _extract_events(data, variant, buckets), None
            except Exception as exc:
                return variant, None, [], str(exc)

        results = await asyncio.gather(
            *(fetch_variant(variant, buckets) for variant, buckets in WATCHED_BUCKETS.items())
        )

    for variant, data, variant_events, error in results:
        if data is not None:
            raw[variant] = data
        if variant_events:
            events.extend(variant_events)
        if error:
            errors[variant] = error

    return {
        "base_url": base_url,
        "watched_buckets": WATCHED_BUCKETS,
        "events": [e.to_dict() for e in events],
        "raw_counts": _count_raw(raw),
        "errors": errors,
    }


async def filter_worldmonitor_digest() -> dict[str, Any]:
    digest = await fetch_worldmonitor_digest()
    events = [WorldMonitorEvent(**_event_kwargs(item)) for item in digest["events"]]
    filtered = [_score_event(event) for event in events]
    filtered.sort(key=lambda item: item.priority_score, reverse=True)

    selected = [item for item in filtered if item.decision == "selected"]
    watchlist = [item for item in filtered if item.decision == "watchlist"]
    discarded = [item for item in filtered if item.decision == "discarded"]
    seed_text = build_seed_text(selected, watchlist)

    return {
        "source": digest["base_url"],
        "raw_counts": digest["raw_counts"],
        "errors": digest["errors"],
        "summary": {
            "total": len(filtered),
            "selected": len(selected),
            "watchlist": len(watchlist),
            "discarded": len(discarded),
        },
        "selected": [item.to_dict() for item in selected],
        "watchlist": [item.to_dict() for item in watchlist],
        "discarded": [item.to_dict() for item in discarded[:50]],
        "seed_text": seed_text,
    }


def build_seed_text(selected: list[FilteredSignal], watchlist: list[FilteredSignal]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# WorldMonitor 精选情报包",
        "",
        f"生成时间：{now}",
        "用途：作为周大福海外市场战略情报 Agent 的前置输入。",
        "",
        "## 筛选口径",
        "",
        "- 仅保留与周大福海外市场、黄金/钻石/珠宝、重点区域、竞品、渠道、合规、供应链、品牌声誉相关的信息。",
        "- 高优先级信息进入后续知识图谱和企业专家 Agent 会商。",
        "- 待观察信息供 Agent 参考，但不作为强预警。",
        "",
    ]

    grouped = _group_by_market(selected)
    lines.append("## 高优先级预警")
    lines.append("")
    if not selected:
        lines.append("暂无高优先级预警。")
    for market, items in grouped.items():
        lines.append(f"### {market}")
        for item in items[:8]:
            lines.extend(_signal_markdown(item))

    lines.extend(["", "## 待观察事项", ""])
    if not watchlist:
        lines.append("暂无待观察事项。")
    for item in watchlist[:12]:
        lines.extend(_signal_markdown(item))

    lines.extend(["", "## 来源说明", ""])
    lines.append("信息来源为本地 WorldMonitor 的新闻摘要接口，已经过规则筛选与优先级评分。")
    return "\n".join(lines)


def build_seed_text_from_dicts(items: list[dict[str, Any]]) -> str:
    signals = [_dict_to_signal(item) for item in items]
    selected = [item for item in signals if item.decision == "selected"]
    watchlist = [item for item in signals if item.decision != "selected"]
    return build_seed_text(selected, watchlist)


def _extract_events(data: dict[str, Any], variant: str, buckets: tuple[str, ...]) -> list[WorldMonitorEvent]:
    events: list[WorldMonitorEvent] = []
    categories = data.get("categories") or {}
    for bucket in buckets:
        category = categories.get(bucket) or {}
        items = category.get("items") or []
        for idx, item in enumerate(items):
            title = _clean(item.get("title") or "")
            summary = _clean(item.get("snippet") or "")
            source = _clean(item.get("source") or "")
            url = item.get("link") or ""
            event_hash = hashlib.md5(f"{variant}:{bucket}:{url}:{title}".encode("utf-8")).hexdigest()[:10]
            threat = item.get("threat") or {}
            events.append(WorldMonitorEvent(
                id=f"wm_{variant}_{bucket}_{event_hash}_{idx}",
                title=title,
                summary=summary,
                source=source,
                url=url,
                published_at_ms=int(item.get("publishedAt") or 0),
                variant=variant,
                bucket=bucket,
                importance_score=int(item.get("importanceScore") or 0),
                corroboration_count=int(item.get("corroborationCount") or 0),
                is_alert=bool(item.get("isAlert")),
                threat_level=threat.get("level") or "THREAT_LEVEL_UNSPECIFIED",
                threat_category=threat.get("category") or "general",
                threat_confidence=float(threat.get("confidence") or 0.3),
                location_name=_clean(item.get("locationName") or ""),
            ))
    return events


def _score_event(event: WorldMonitorEvent) -> FilteredSignal:
    text = event.text
    market, market_hits = _detect_market(text)
    category, category_hits = _detect_category(text)
    reasons: list[str] = []
    if market_hits:
        reasons.append(f"命中重点市场：{', '.join(market_hits[:3])}")
    if category_hits:
        reasons.append(f"命中业务主题：{', '.join(category_hits[:4])}")
    if event.is_alert:
        reasons.append("WorldMonitor 标记为 alert")
    if event.importance_score >= 60:
        reasons.append(f"WorldMonitor 重要性较高：{event.importance_score}")
    if event.threat_level in ("THREAT_LEVEL_HIGH", "THREAT_LEVEL_CRITICAL"):
        reasons.append(f"威胁等级较高：{event.threat_level}")

    direct_company = _contains_any(text, TOPIC_KEYWORDS["company"])
    strategic_relevance = 0.18
    if market != "其他":
        strategic_relevance += 0.28
    if category != "general":
        strategic_relevance += 0.35
    if direct_company:
        strategic_relevance = 1.0
        reasons.append("直接命中周大福相关词")
    strategic_relevance = min(strategic_relevance, 1.0)

    threat_score = THREAT_SCORES.get(event.threat_level, 0.2)
    business_impact = min(
        1.0,
        0.2
        + event.importance_score / 150
        + (0.2 if category in {"compliance", "supply_chain", "competitor"} else 0)
        + (0.15 if market in {"中东", "东南亚", "澳洲"} else 0)
        + (0.2 if direct_company else 0),
    )
    urgency = min(
        1.0,
        0.18
        + threat_score * 0.45
        + (0.2 if event.is_alert else 0)
        + _recency_score(event.published_at_ms) * 0.17,
    )
    source_confidence = min(
        1.0,
        0.35
        + event.threat_confidence * 0.25
        + min(event.corroboration_count, 4) * 0.08
        + (0.12 if event.source else 0)
        + (0.08 if event.url.startswith("http") else 0),
    )
    priority = (
        0.35 * business_impact
        + 0.25 * urgency
        + 0.25 * strategic_relevance
        + 0.15 * source_confidence
    )

    forced = direct_company or (
        category in {"compliance", "supply_chain", "competitor"}
        and market in {"中东", "东南亚", "澳洲", "日韩", "北美"}
    )
    if forced and priority < 0.7:
        priority = 0.7
        reasons.append("符合强制保留规则")

    if priority >= 0.7:
        decision = "selected"
    elif priority >= 0.5:
        decision = "watchlist"
    else:
        decision = "discarded"

    if not reasons:
        reasons.append("未命中周大福核心筛选口径，默认降级")

    return FilteredSignal(
        event=event,
        decision=decision,
        market=market,
        category=category,
        signal_type=SIGNAL_TYPE_BY_CATEGORY.get(category, "watch"),
        suggested_owner=OWNER_BY_CATEGORY.get(category, "管理层"),
        priority_score=priority,
        business_impact=business_impact,
        urgency=urgency,
        strategic_relevance=strategic_relevance,
        source_confidence=source_confidence,
        reasons=reasons,
    )


def _detect_market(text: str) -> tuple[str, list[str]]:
    best_market = "其他"
    best_hits: list[str] = []
    for market, keywords in MARKET_KEYWORDS.items():
        hits = [kw for kw in keywords if _keyword_hit(text, kw)]
        if len(hits) > len(best_hits):
            best_market = market
            best_hits = hits
    return best_market, best_hits


def _detect_category(text: str) -> tuple[str, list[str]]:
    best_category = "general"
    best_hits: list[str] = []
    for category, keywords in TOPIC_KEYWORDS.items():
        hits = [kw for kw in keywords if _keyword_hit(text, kw)]
        if len(hits) > len(best_hits):
            best_category = category
            best_hits = hits
    return best_category, best_hits


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(_keyword_hit(text, kw) for kw in keywords)


def _keyword_hit(text: str, keyword: str) -> bool:
    kw = keyword.lower()
    if kw.strip() != kw or " " in kw:
        return kw in text
    return re.search(rf"(?<![a-z0-9]){re.escape(kw)}(?![a-z0-9])", text) is not None


def _recency_score(ms: int) -> float:
    if not ms:
        return 0.2
    age = max(0, datetime.now(timezone.utc).timestamp() * 1000 - ms)
    day = 24 * 60 * 60 * 1000
    return max(0.0, min(1.0, 1 - age / (4 * day)))


def _signal_markdown(item: FilteredSignal) -> list[str]:
    event = item.event
    lines = [
        f"- **{event.title}**",
        f"  - 市场：{item.market}；类型：{item.category} / {item.signal_type}；优先级：{item.priority_score:.2f}",
        f"  - 建议负责部门：{item.suggested_owner}",
        f"  - 判断理由：{'；'.join(item.reasons)}",
    ]
    if event.summary:
        lines.append(f"  - 摘要：{event.summary}")
    lines.append(f"  - 来源：{event.source} ({event.url})")
    return lines


def _group_by_market(items: list[FilteredSignal]) -> dict[str, list[FilteredSignal]]:
    grouped: dict[str, list[FilteredSignal]] = {}
    for item in items:
        grouped.setdefault(item.market, []).append(item)
    return grouped


def _dict_to_signal(item: dict[str, Any]) -> FilteredSignal:
    event = WorldMonitorEvent(**_event_kwargs(item))
    return FilteredSignal(
        event=event,
        decision=item.get("decision", "selected"),
        market=item.get("market", "其他"),
        category=item.get("category", "general"),
        signal_type=item.get("signal_type", "watch"),
        suggested_owner=item.get("suggested_owner", "管理层"),
        priority_score=float(item.get("priority_score", 0.5)),
        business_impact=float((item.get("scores") or {}).get("business_impact", 0.5)),
        urgency=float((item.get("scores") or {}).get("urgency", 0.5)),
        strategic_relevance=float((item.get("scores") or {}).get("strategic_relevance", 0.5)),
        source_confidence=float((item.get("scores") or {}).get("source_confidence", 0.5)),
        reasons=list(item.get("reasons") or []),
    )


def _event_kwargs(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["id"],
        "title": item.get("title", ""),
        "summary": item.get("summary", ""),
        "source": item.get("source", ""),
        "url": item.get("url", ""),
        "published_at_ms": int(item.get("published_at_ms") or 0),
        "variant": item.get("variant", ""),
        "bucket": item.get("bucket", ""),
        "importance_score": int(item.get("importance_score") or 0),
        "corroboration_count": int(item.get("corroboration_count") or 0),
        "is_alert": bool(item.get("is_alert")),
        "threat_level": item.get("threat_level", "THREAT_LEVEL_UNSPECIFIED"),
        "threat_category": item.get("threat_category", "general"),
        "threat_confidence": float(item.get("threat_confidence") or 0.3),
        "location_name": item.get("location_name", ""),
    }


def _count_raw(raw: dict[str, Any]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for variant, data in raw.items():
        counts[variant] = {}
        for bucket, category in (data.get("categories") or {}).items():
            counts[variant][bucket] = len((category or {}).get("items") or [])
    return counts


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def iso_from_ms(ms: int) -> str:
    if not ms:
        return ""
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()
