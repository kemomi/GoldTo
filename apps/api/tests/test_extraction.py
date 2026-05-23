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
