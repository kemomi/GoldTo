from pathlib import Path

from app.models import EventRecord, ThresholdConfig
from app.repository import EventRepository


def test_repository_round_trips_events_and_thresholds(tmp_path: Path):
    repo = EventRepository(tmp_path / "demo.sqlite")
    repo.init_db()

    repo.save_thresholds(ThresholdConfig(must_report_price_change_pct=5.0, optional_price_change_pct=2.0))
    repo.save_events(
        [
            EventRecord(
                event_id="hk-csg-pricecut-20260523",
                market="HK",
                brand="周生生",
                district="尖沙咀",
                event_type="price_change",
                product_focus="wedding",
                title="周生生尖沙咀婚嫁黄金限时 8% 优惠",
                summary_zh="周生生在香港尖沙咀核心婚嫁商圈推出 8% 限时优惠。",
                source_url="https://example.com/hk-csg-pricecut",
                source_id="hk-csg-official",
                occurred_at="2026-05-23T08:00:00+08:00",
                price_change_pct=8.0,
                is_core_district=True,
                confidence=0.92,
                report_level="must_report",
                evidence=["https://example.com/hk-csg-pricecut"],
            )
        ]
    )

    stored = repo.list_events()
    config = repo.load_thresholds()

    assert stored[0].event_id == "hk-csg-pricecut-20260523"
    assert stored[0].price_change_pct == 8.0
    assert config.must_report_price_change_pct == 5.0
    assert config.optional_price_change_pct == 2.0
