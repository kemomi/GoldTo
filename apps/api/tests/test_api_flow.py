from fastapi.testclient import TestClient

from app.main import app
from app.models import BriefResponse, EventRecord
from app.services.chat import answer_demo_question
from app.services.simulate_response import simulate_response

client = TestClient(app)


def test_brief_simulation_and_threshold_update_flow():
    brief = client.get("/api/briefs/today")
    assert brief.status_code == 200
    assert brief.json()["top_events"][0]["event_id"] == "hk-csg-pricecut-20260523"

    simulation = client.post("/api/events/hk-csg-pricecut-20260523/simulate")
    assert simulation.status_code == 200
    assert simulation.json()["recommended_option_id"] == "local_follow"

    config = client.patch(
        "/api/config/thresholds",
        json={"must_report_price_change_pct": 6.0, "optional_price_change_pct": 3.0},
    )
    assert config.status_code == 200
    assert config.json()["must_report_price_change_pct"] == 6.0

    chat = client.post(
        "/api/chat",
        json={"question": "综合多方因素最优选择哪种应对级别，各岗位后续该落实哪些相关工作"},
    )
    assert chat.status_code == 200
    assert "局部跟进" in chat.json()["answer"]


def _event(
    event_id: str = "demo-event",
    *,
    district: str = "尖沙咀",
    price_change_pct: float | None = 8.0,
    is_core_district: bool = True,
    confidence: float = 0.92,
) -> EventRecord:
    return EventRecord(
        event_id=event_id,
        market="HK",
        brand="周生生",
        district=district,
        event_type="price_change",
        product_focus="wedding",
        title="示例事件",
        summary_zh="示例摘要",
        source_url="https://example.com/event",
        source_id="demo-source",
        occurred_at="2026-05-23T08:00:00+08:00",
        price_change_pct=price_change_pct,
        is_core_district=is_core_district,
        confidence=confidence,
        report_level="must_report",
        evidence=["https://example.com/event"],
    )


def _brief(*events: EventRecord) -> BriefResponse:
    return BriefResponse(
        overview="示例简报",
        top_events=list(events),
        compliance_alerts=[],
        opportunities=[],
        role_actions={},
    )


def test_chat_with_empty_top_events_returns_safe_answer(monkeypatch):
    import app.routes.chat as chat_route

    monkeypatch.setattr(chat_route, "build_today_brief", lambda: (_brief(), object()))

    response = client.post("/api/chat", json={"question": "今天风险等级最高的是什么"})

    assert response.status_code == 200
    assert "暂无" in response.json()["answer"]
    assert response.json()["cited_event_ids"] == []


def test_non_local_follow_recommendation_uses_matching_chat_label():
    brief = _brief(_event(event_id="hold-event", district="新界", price_change_pct=4.0, is_core_district=False))
    simulation = simulate_response(_event(event_id="hold-event", district="新界", price_change_pct=4.0, is_core_district=False))

    chat = answer_demo_question("综合多方因素最优选择哪种应对级别，各岗位后续该落实哪些相关工作", brief, simulation)

    assert simulation.recommended_option_id == "hold"
    assert "局部跟进" not in simulation.recommended_reason
    assert "保持不动" in chat.answer
    assert "局部跟进" not in chat.answer


def test_low_confidence_strategy_question_uses_escalation_option():
    brief = _brief(_event(event_id="review-event", confidence=0.7))
    simulation = simulate_response(_event(event_id="review-event", confidence=0.7))

    chat = answer_demo_question("请说明不同应对策略", brief, simulation)

    assert simulation.recommended_option_id == "escalate_attention"
    assert chat.answer != ""
    assert "升级关注" in chat.answer


def test_unknown_event_simulation_returns_404():
    response = client.post("/api/events/unknown-event/simulate")

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"
