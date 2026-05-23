from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_demo_path_brief_simulation_and_chat_flow():
    brief = client.get("/api/briefs/today")
    assert brief.status_code == 200
    assert brief.json()["top_events"][0]["event_id"] == "hk-csg-pricecut-20260523"

    simulation = client.post("/api/events/hk-csg-pricecut-20260523/simulate")
    assert simulation.status_code == 200
    assert simulation.json()["recommended_option_id"] == "local_follow"

    chat = client.post(
        "/api/chat",
        json={"question": "综合多方因素最优选择哪种应对级别，各岗位后续该落实哪些相关工作？"},
    )
    assert chat.status_code == 200
    assert "局部跟进" in chat.json()["answer"]
