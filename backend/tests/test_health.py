def test_health_returns_ok(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_capabilities_reports_ai_disabled(client):
    response = client.get("/api/v1/health/capabilities")
    assert response.status_code == 200
    body = response.json()
    assert body["ai_enabled"] is False
    assert body["module_count"] >= 1
    assert ".pdf" in body["allowed_extensions"]


def test_root_is_reachable(client):
    assert client.get("/").status_code == 200
