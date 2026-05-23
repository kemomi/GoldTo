from app.models import EventRecord, ThresholdConfig
from app.services.generate_brief import generate_daily_brief
from app.services.score_events import score_and_rank_events


def _event(event_id: str, district: str, product_focus: str, pct: float) -> EventRecord:
    return EventRecord(
        event_id=event_id,
        market="HK",
        brand="周生生",
        district=district,
        event_type="price_change",
        product_focus=product_focus,
        title=event_id,
        summary_zh=event_id,
        source_url="https://example.com",
        source_id=event_id,
        occurred_at="2026-05-23T08:00:00+08:00",
        price_change_pct=pct,
        is_core_district=district == "尖沙咀",
        confidence=0.91,
        evidence=["https://example.com"],
    )


def test_scoring_respects_thresholds_and_core_district_priority():
    config = ThresholdConfig(must_report_price_change_pct=5.0, optional_price_change_pct=2.0)
    events = [
        _event("non-core", "新界", "other", 5.0),
        _event("core-wedding", "尖沙咀", "wedding", 5.0),
        _event("ignore", "新界", "other", 1.0),
    ]

    ranked, manual_review = score_and_rank_events(events, config)
    brief = generate_daily_brief(ranked, manual_review)

    assert ranked[0].event_id == "core-wedding"
    assert ranked[0].report_level == "must_report"
    assert ranked[-1].report_level == "ignore"
    assert brief.top_events[0].event_id == "core-wedding"
    assert "整体竞争烈度" in brief.overview
