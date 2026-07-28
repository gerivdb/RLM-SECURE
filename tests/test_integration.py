"""Integration tests for RLM-SECURE API."""

from __future__ import annotations

import pytest

from src.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestHealthzIntegration:
    """Integration tests for /healthz endpoint (used by KIX orchestrator)."""

    def test_healthz_for_kix(self, client):
        """Healthz endpoint returns simple OK for KIX probing."""
        resp = client.get("/healthz")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"


class TestValidateIntegration:
    """Integration tests for /validate endpoint with other endpoints."""

    def test_validate_creates_audit_trail(self, client):
        """Validate should log entry and return consistent status."""
        # Clear initial state via health check
        health_resp = client.get("/health")
        assert health_resp.status_code == 200

        # Validate a flagged target
        validate_resp = client.post(
            "/validate", json={"target": "http://insecure.local/api"}
        )
        assert validate_resp.status_code == 200
        data = validate_resp.get_json()
        assert data["status"] == "flagged"
        assert "validate-" in data["id"]
        assert len(data["findings"]) >= 1

        # Check metrics recorded the validation
        metrics_resp = client.get("/metrics")
        assert metrics_resp.status_code == 200
        metrics = metrics_resp.get_json()
        assert metrics["service"] == "rlm-secure"

    def test_validate_clean_target(self, client):
        """Validate should pass clean targets."""
        resp = client.post("/validate", json={"target": "https://secure.example.com"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "pass"
        assert data["findings"] == []

    def test_validate_credential_detection(self, client):
        """Validate should detect possible credentials in URLs."""
        resp = client.post("/validate", json={"target": "https://user:pass@example.com"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "flagged"
        assert any("credential" in f["message"].lower() for f in data["findings"])


class TestVoteIntegration:
    """Integration tests for /vote endpoint."""

    def test_vote_flow(self, client):
        """Test complete vote flow with health check."""
        # Ensure service is healthy
        health_resp = client.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.get_json()["status"] == "ok"

        # Cast vote
        vote_resp = client.post("/vote", json={"choice": "approve"})
        assert vote_resp.status_code == 200
        data = vote_resp.get_json()
        assert data["choice"] == "approve"
        assert data["count"] == 1

    def test_vote_multiple_choices(self, client):
        """Test multiple votes with different choices."""
        for choice in ["approve", "reject", "abstain"]:
            resp = client.post("/vote", json={"choice": choice})
            assert resp.status_code == 200
            assert resp.get_json()["choice"] == choice


class TestFullRoundtrip:
    """Full integration roundtrip tests."""

    def test_full_secure_check_cycle(self, client):
        """
        Full roundtrip: health → validate → status → metrics.
        Simulates a typical security check cycle.
        """
        # 1. Health check
        health = client.get("/health")
        assert health.status_code == 200
        assert health.get_json()["status"] == "ok"

        # 2. Validate multiple targets
        targets = [
            "http://insecure.api.local",
            "https://secure.api.local",
            "https://user:secret@legacy.local",
        ]

        for target in targets:
            resp = client.post("/validate", json={"target": target})
            assert resp.status_code == 200
            assert "validate-" in resp.get_json()["id"]

        # 3. Status check
        status = client.get("/status")
        assert status.status_code == 200
        assert status.get_json()["service"] == "rlm-secure"

        # 4. Metrics check
        metrics = client.get("/metrics")
        assert metrics.status_code == 200
        assert "checks" in metrics.get_json()
        assert "passed" in metrics.get_json()
        assert "failed" in metrics.get_json()

    def test_error_handling_integration(self, client):
        """Test error handling across endpoints."""
        # Missing choice on vote
        resp = client.post("/vote", json={})
        assert resp.status_code == 400
        assert "error" in resp.get_json()

        # Missing target on validate
        resp = client.post("/validate", json={})
        assert resp.status_code == 400
        assert "error" in resp.get_json()