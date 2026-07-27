import pytest
from src.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "rlm-secure"


def test_metrics(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["service"] == "rlm-secure"


def test_vote_success(client):
    resp = client.post("/vote", json={"choice": "yes"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["choice"] == "yes"


def test_vote_missing_choice(client):
    resp = client.post("/vote", json={})
    assert resp.status_code == 400


def test_validate_plaintext(client):
    resp = client.post("/validate", json={"target": "http://example.local/api"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "flagged"
    assert any("http" in item["message"].lower() for item in data["findings"])


def test_validate_clean(client):
    resp = client.post("/validate", json={"target": "https://example.local/api"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "pass"


def test_validate_missing_target(client):
    resp = client.post("/validate", json={})
    assert resp.status_code == 400


def test_status(client):
    resp = client.get("/status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["service"] == "rlm-secure"
