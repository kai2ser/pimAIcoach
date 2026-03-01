"""
Tests for API key authentication.
"""

from unittest.mock import patch


class TestAuthDependency:
    """Tests for require_api_key via the admin config endpoint."""

    def test_no_key_returns_401(self, client):
        response = client.get("/api/config")
        assert response.status_code == 401
        assert "Missing API key" in response.json()["detail"]

    def test_wrong_key_returns_403(self, client):
        response = client.get("/api/config", headers={"X-API-Key": "wrong-key"})
        assert response.status_code == 403
        assert "Invalid API key" in response.json()["detail"]

    def test_valid_api_key_header(self, client, auth_headers):
        response = client.get("/api/config", headers=auth_headers)
        assert response.status_code == 200

    def test_valid_bearer_token(self, client):
        from tests.conftest import TEST_API_KEY

        response = client.get(
            "/api/config",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        )
        assert response.status_code == 200

    def test_no_configured_key_returns_500(self):
        """If PIM_ADMIN_API_KEY is empty, server returns 500."""
        from app.config import settings
        from app.main import app
        from fastapi.testclient import TestClient

        original_key = settings.admin_api_key
        object.__setattr__(settings, "admin_api_key", "")

        with TestClient(app) as c:
            response = c.get(
                "/api/config",
                headers={"X-API-Key": "anything"},
            )
            assert response.status_code == 500
            assert "not configured" in response.json()["detail"]

        object.__setattr__(settings, "admin_api_key", original_key)
