from app.models import EventRecord, ThresholdConfig
from app.services.generate_brief import generate_daily_brief
from app.services.score_events import score_and_rank_events


def _event(
    event_id: str,
    district: str,
    product_focus: str,
    pct: float,
    *,
    market: str = "HK",
    confidence: float = 0.91,
) -> EventRecord:
    return EventRecord(
        event_id=event_id,
        market=market,
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
        confidence=confidence,
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


def test_low_confidence_event_goes_to_manual_review():
    config = ThresholdConfig(must_report_price_change_pct=5.0, optional_price_change_pct=2.0)
    events = [
        _event("needs-review", "尖沙咀", "gold", 8.0, confidence=0.74),
        _event("ranked", "新界", "other", 5.0),
    ]

    ranked, manual_review = score_and_rank_events(events, config)

    assert [event.event_id for event in ranked] == ["ranked"]
    assert [event.event_id for event in manual_review] == ["needs-review"]
    assert manual_review[0].report_level == "manual_review"


def test_scoring_classifies_optional_and_ignore_by_threshold():
    config = ThresholdConfig(must_report_price_change_pct=5.0, optional_price_change_pct=2.0)
    events = [
        _event("optional", "新界", "other", 2.0),
        _event("ignore", "新界", "other", 1.9),
    ]

    ranked, manual_review = score_and_rank_events(events, config)

    assert manual_review == []
    assert ranked[0].event_id == "optional"
    assert ranked[0].report_level == "optional"
    assert ranked[1].event_id == "ignore"
    assert ranked[1].report_level == "ignore"


def test_generate_daily_brief_keeps_one_top_event_per_market():
    config = ThresholdConfig(must_report_price_change_pct=5.0, optional_price_change_pct=2.0)
    events = [
        _event("hk-top", "尖沙咀", "wedding", 6.0, market="HK"),
        _event("hk-second", "新界", "other", 5.5, market="HK"),
        _event("sg-top", "尖沙咀", "gold", 5.2, market="SG"),
    ]

    ranked, manual_review = score_and_rank_events(events, config)
    brief = generate_daily_brief(ranked, manual_review)

    assert [event.event_id for event in brief.top_events] == ["hk-top", "sg-top"]
    assert [event.market for event in brief.top_events] == ["HK", "SG"]


def test_generate_daily_brief_returns_expected_structure_and_key_fields():
    config = ThresholdConfig(must_report_price_change_pct=5.0, optional_price_change_pct=2.0)
    events = [
        _event("hk-top", "尖沙咀", "wedding", 6.0, market="HK"),
        _event("review", "新界", "other", 9.0, market="MO", confidence=0.5),
    ]

    ranked, manual_review = score_and_rank_events(events, config)
    brief = generate_daily_brief(ranked, manual_review)

    assert brief.overview == "今日五大市场整体竞争烈度偏高，香港婚嫁黄金相关异动对晨会优先级最高。"
    assert [event.event_id for event in brief.top_events] == ["hk-top"]
    assert brief.compliance_alerts == ["美国贵金属标识与钻石溯源内容需持续关注。"]
    assert brief.opportunities == ["新加坡高端婚嫁珠宝内容热度可作为新品观察线索。"]
    assert set(brief.role_actions) == {"hq", "ops", "marketing"}
    assert brief.role_actions["hq"] == "总部管理层重点关注香港核心商圈应对级别是否上收决策。"
    assert brief.role_actions["ops"] == "区域运营今日优先巡检尖沙咀商圈并准备局部促销预案。"
    assert brief.role_actions["marketing"] == "市场策略岗同步检查婚嫁黄金内容方向与投放素材。"
    assert [event.event_id for event in brief.manual_review] == ["review"]
