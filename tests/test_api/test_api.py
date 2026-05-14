import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_list_agents(client):
    resp = client.get("/api/v1/agent/list")
    assert resp.status_code == 200
    agents = resp.json()["agents"]
    assert len(agents) >= 2


def test_review_status(client):
    resp = client.get("/api/v1/review/status")
    assert resp.status_code == 200
    assert "available_tools" in resp.json()


def test_workflow_templates(client):
    resp = client.get("/api/v1/workflow/templates")
    assert resp.status_code == 200
    assert "pr-review" in resp.json()["templates"]


def test_openapi_docs(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    assert spec["info"]["title"] == "DevFlow AI"
    assert "/api/v1/review" in spec["paths"]
    assert "/api/v1/workflow" in spec["paths"]
    assert "/api/v1/agent/list" in spec["paths"]
    assert "/api/v1/knowledge/search" in spec["paths"]
