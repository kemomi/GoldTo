import re

from app.models import EventRecord, SourceRecord


EVENT_ID_BY_SOURCE = {
    "hk-csg-official": "hk-csg-pricecut-20260523",
    "hk-harbour-city-mall": "hk-mall-promo-20260523",
    "sg-pandora-official": "sg-pandora-expansion-20260523",
    "us-ebay-platform": "us-ebay-policy-20260523",
    "us-ftc-jewelry-guides": "us-ftc-guidance-20260523",
    "us-nationaljeweler-bridal": "us-bridal-trend-20260523",
}

CONFIDENCE_BY_SOURCE_TYPE = {
    "competitor_official": 0.92,
    "mall_official": 0.92,
    "platform_announcement": 0.88,
    "regulation_update": 0.9,
    "industry_news": 0.82,
    "seeded_media": 0.78,
}


def _price_change_pct(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|percent)", text.lower())
    return float(match.group(1)) if match else None


def _district(text: str) -> str:
    for district in ("尖沙咀", "铜锣湾", "乌节路", "滨海湾", "第五大道"):
        if district in text:
            return district
    return "未标注商圈"


def _product_focus(text: str) -> str:
    lowered = text.lower()
    if "婚嫁" in text or "bridal" in lowered:
        return "wedding"
    if "黄金" in text or "gold" in lowered:
        return "gold"
    if "轻奢" in text or "light luxury" in lowered:
        return "light_luxury"
    return "other"


def _event_type(record: SourceRecord, merged: str, price_change: float | None) -> str:
    if price_change is not None:
        return "price_change"
    if record.source_type == "platform_announcement":
        return "platform_update"
    if record.source_type == "regulation_update":
        return "compliance_update"
    if record.source_type == "industry_news":
        return "industry_trend"
    return "promotion"


def extract_event_candidates(records: list[SourceRecord]) -> list[EventRecord]:
    events: list[EventRecord] = []

    for record in records:
        merged = f"{record.title} {record.body}"
        price_change = _price_change_pct(merged)
        event_type = _event_type(record, merged, price_change)
        district = _district(merged)
        product_focus = _product_focus(merged)
        is_core_district = district in {"尖沙咀", "乌节路", "滨海湾", "第五大道"}
        event_id = EVENT_ID_BY_SOURCE[record.source_id]

        events.append(
            EventRecord(
                event_id=event_id,
                market=record.market,
                brand=record.brand,
                district=district,
                event_type=event_type,
                product_focus=product_focus,
                title=record.title,
                summary_zh=f"{record.brand}：{record.title}",
                source_url=record.url,
                source_id=record.source_id,
                source_type=record.source_type,
                occurred_at=record.captured_at,
                price_change_pct=price_change,
                is_core_district=is_core_district,
                confidence=CONFIDENCE_BY_SOURCE_TYPE[record.source_type],
                evidence=[record.url, record.title],
                fetch_status=record.fetch_status,
                fallback_reason=record.fallback_reason,
            )
        )

    return events
