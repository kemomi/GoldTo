from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_today_brief_contract_contains_required_sections():
    response = client.get("/api/briefs/today")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) >= {"overview", "top_events", "compliance_alerts", "opportunities", "role_actions", "manual_review"}
    assert payload["top_events"][0]["source_url"].startswith("https://")
