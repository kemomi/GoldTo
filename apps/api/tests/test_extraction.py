import requests

from app.services.extract_events import extract_event_candidates
from app.services.fetch_sources import fetch_source_records


def test_fetch_falls_back_to_fixture_and_extracts_price_cut(monkeypatch):
    def raise_offline(*args, **kwargs):
        raise RuntimeError("offline")

    monkeypatch.setattr("app.services.fetch_sources.requests.get", raise_offline)

    records = fetch_source_records()
    events = extract_event_candidates(records)
    top = next(event for event in events if event.event_id == "hk-csg-pricecut-20260523")

    assert top.market == "HK"
    assert top.brand == "周生生"
    assert top.price_change_pct == 8.0
    assert top.is_core_district is True
    assert top.product_focus == "wedding"


def test_fetch_falls_back_to_fixtures_and_extracts_all_events(monkeypatch):
    def raise_offline(*args, **kwargs):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr("app.services.fetch_sources.requests.get", raise_offline)

    records = fetch_source_records()
    by_source = {record.source_id: record for record in records}
    events = extract_event_candidates(records)
    by_event = {event.event_id: event for event in events}

    assert set(by_source) == {
        "hk-csg-official",
        "hk-harbour-city-mall",
        "sg-pandora-official",
        "us-ebay-platform",
        "us-ftc-jewelry-guides",
        "us-nationaljeweler-bridal",
    }
    assert by_source["hk-csg-official"].captured_at == "2026-05-23T08:00:00+00:00"
    assert by_source["hk-harbour-city-mall"].captured_at == "2026-05-23T10:00:00+00:00"
    assert by_source["sg-pandora-official"].captured_at == "2026-05-23T09:00:00+00:00"
    assert by_source["us-ebay-platform"].captured_at == "2026-05-23T09:00:00+00:00"
    assert by_source["us-ftc-jewelry-guides"].captured_at == "2026-05-23T09:00:00+00:00"
    assert by_source["us-nationaljeweler-bridal"].captured_at == "2026-05-23T09:00:00+00:00"
    assert all(record.fetch_status == "fixture_fallback" for record in records)
    assert all(record.fallback_reason for record in records)

    assert set(by_event) == {
        "hk-csg-pricecut-20260523",
        "hk-mall-promo-20260523",
        "sg-pandora-expansion-20260523",
        "us-ebay-policy-20260523",
        "us-ftc-guidance-20260523",
        "us-bridal-trend-20260523",
    }

    hk_price_cut = by_event["hk-csg-pricecut-20260523"]
    assert hk_price_cut.market == "HK"
    assert hk_price_cut.brand == "周生生"
    assert hk_price_cut.event_type == "price_change"
    assert hk_price_cut.price_change_pct == 8.0
    assert hk_price_cut.is_core_district is True
    assert hk_price_cut.product_focus == "wedding"
    assert hk_price_cut.occurred_at == "2026-05-23T08:00:00+00:00"
    assert hk_price_cut.source_type == "competitor_official"
    assert hk_price_cut.fetch_status == "fixture_fallback"
    assert hk_price_cut.fallback_reason is not None

    hk_mall_promo = by_event["hk-mall-promo-20260523"]
    assert hk_mall_promo.event_type == "promotion"
    assert hk_mall_promo.price_change_pct is None
    assert hk_mall_promo.product_focus == "wedding"
    assert hk_mall_promo.source_type == "mall_official"
    assert hk_mall_promo.fetch_status == "fixture_fallback"
    assert hk_mall_promo.fallback_reason is not None

    sg_pandora = by_event["sg-pandora-expansion-20260523"]
    assert sg_pandora.event_type == "promotion"
    assert sg_pandora.source_type == "competitor_official"
    assert sg_pandora.fetch_status == "fixture_fallback"
    assert sg_pandora.fallback_reason is not None

    us_ebay = by_event["us-ebay-policy-20260523"]
    assert us_ebay.event_type == "platform_update"
    assert us_ebay.source_type == "platform_announcement"
    assert us_ebay.fetch_status == "fixture_fallback"

    us_ftc = by_event["us-ftc-guidance-20260523"]
    assert us_ftc.event_type == "compliance_update"
    assert us_ftc.source_type == "regulation_update"

    us_bridal = by_event["us-bridal-trend-20260523"]
    assert us_bridal.event_type == "industry_trend"
    assert us_bridal.product_focus == "wedding"
    assert us_bridal.confidence == 0.82
    assert us_bridal.fetch_status == "fixture_fallback"


def test_fetch_logs_and_falls_back_on_parse_failure(monkeypatch, caplog):
    class BrokenResponse:
        text = "<html><body><p>missing title</p></body></html>"

        def raise_for_status(self):
            return None

    def return_broken_response(*args, **kwargs):
        return BrokenResponse()

    monkeypatch.setenv("APP_ENABLE_LIVE_SOURCES", "true")
    monkeypatch.setattr("app.services.fetch_sources.requests.get", return_broken_response)

    with caplog.at_level("WARNING", logger="app.services.fetch_sources"):
        records = fetch_source_records()

    assert records[0].captured_at == "2026-05-23T08:00:00+00:00"
    assert "fixture fallback" in caplog.text


def test_fetch_uses_fixture_without_network_when_live_sources_disabled(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("requests.get should not be called when live sources are disabled")

    monkeypatch.setattr("app.services.fetch_sources.requests.get", fail_if_called)

    records = fetch_source_records()

    assert records[0].title == "周生生尖沙咀婚嫁黄金限时 8% 优惠"
    assert records[0].url == "https://www.chowsangsang.com/en/product/Promotion-Wedding-ChineseWeddings"
