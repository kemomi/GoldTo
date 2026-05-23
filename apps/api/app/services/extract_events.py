import re

from app.models import EventRecord, SourceRecord


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


def extract_event_candidates(records: list[SourceRecord]) -> list[EventRecord]:
    events: list[EventRecord] = []

    for record in records:
        merged = f"{record.title} {record.body}"
        price_change = _price_change_pct(merged)
        event_type = "price_change" if price_change is not None else "promotion"
        district = _district(merged)
        product_focus = _product_focus(merged)
        is_core_district = district in {"尖沙咀", "乌节路", "滨海湾", "第五大道"}

        event_id = {
            "hk-csg-official": "hk-csg-pricecut-20260523",
            "hk-harbour-city-mall": "hk-mall-promo-20260523",
            "us-signet-seed": "us-signet-bridal-20260523",
        }[record.source_id]

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
                occurred_at=record.captured_at,
                price_change_pct=price_change,
                is_core_district=is_core_district,
                confidence=0.92 if record.source_type != "seeded_media" else 0.78,
                evidence=[record.url],
            )
        )

    return events
