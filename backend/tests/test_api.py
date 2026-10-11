import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "CloudSentinel"
    assert data["api_status"] == "ONLINE"


def test_api_nodes_list():
    with TestClient(app) as test_client:
        response = test_client.get("/api/nodes")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "nodes" in data
        assert data["summary"]["total_nodes"] >= 5


def test_api_system_status():
    response = client.get("/api/system/status")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "CloudSentinel"
    assert "docker_connected" in data
    assert "docker_engine_mode" in data


def test_api_reports_summary():
    response = client.get("/api/reports/summary")
    assert response.status_code == 200
    data = response.json()
    assert "infrastructure" in data
    assert "self_healing" in data


def test_fault_injection_security_constraint():
    # Attempting fault on invalid node should be rejected with 400
    response = client.post("/api/faults/cpu", json={
        "node_id": "malicious-host-target",
        "duration": 10.0,
        "intensity": 0.5
    })
    assert response.status_code == 400
    assert "Security constraint" in response.json()["detail"]
