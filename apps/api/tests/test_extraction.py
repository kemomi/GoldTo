import requests

from app.services.extract_events import extract_event_candidates
from app.services.fetch_sources import fetch_source_records


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
        "us-signet-seed",
    }
    assert by_source["hk-csg-official"].captured_at == "2026-05-23T08:00:00+00:00"
    assert by_source["hk-harbour-city-mall"].captured_at == "2026-05-23T10:00:00+00:00"
    assert by_source["us-signet-seed"].captured_at == "2026-05-23T09:00:00-04:00"

    assert set(by_event) == {
        "hk-csg-pricecut-20260523",
        "hk-mall-promo-20260523",
        "us-signet-bridal-20260523",
    }

    hk_price_cut = by_event["hk-csg-pricecut-20260523"]
    assert hk_price_cut.market == "HK"
    assert hk_price_cut.brand == "周生生"
    assert hk_price_cut.event_type == "price_change"
    assert hk_price_cut.price_change_pct == 8.0
    assert hk_price_cut.is_core_district is True
    assert hk_price_cut.product_focus == "wedding"
    assert hk_price_cut.occurred_at == "2026-05-23T08:00:00+00:00"

    hk_mall_promo = by_event["hk-mall-promo-20260523"]
    assert hk_mall_promo.event_type == "promotion"
    assert hk_mall_promo.price_change_pct is None
    assert hk_mall_promo.product_focus == "wedding"

    us_signet = by_event["us-signet-bridal-20260523"]
    assert us_signet.event_type == "price_change"
    assert us_signet.price_change_pct == 5.0
    assert us_signet.product_focus == "wedding"
    assert us_signet.confidence == 0.78
    assert us_signet.occurred_at == "2026-05-23T09:00:00-04:00"


def test_fetch_logs_and_falls_back_on_parse_failure(monkeypatch, caplog):
    class BrokenResponse:
        text = "<html><body><p>missing title</p></body></html>"

        def raise_for_status(self):
            return None

    def return_broken_response(*args, **kwargs):
        return BrokenResponse()

    monkeypatch.setattr("app.services.fetch_sources.requests.get", return_broken_response)

    with caplog.at_level("WARNING", logger="app.services.fetch_sources"):
        records = fetch_source_records()

    assert records[0].captured_at == "2026-05-23T08:00:00+00:00"
    assert "fixture fallback" in caplog.text
