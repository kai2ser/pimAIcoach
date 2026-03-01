"""
Tests for API endpoints.
"""


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_health_no_auth_required(self, client):
        """Health endpoint should work without any API key."""
        response = client.get("/health")
        assert response.status_code == 200


class TestChatEndpoint:
    """Tests for POST /api/chat."""

    def test_chat_no_auth_required(self, client, mock_rag_query):
        """Chat endpoint should work without an API key."""
        response = client.post(
            "/api/chat",
            json={"question": "What are best practices for project appraisal?"},
        )
        assert response.status_code == 200

    def test_chat_returns_answer_and_sources(self, client, mock_rag_query):
        response = client.post(
            "/api/chat",
            json={"question": "Tell me about PIM in Colombia"},
        )
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert isinstance(data["sources"], list)
        assert len(data["sources"]) > 0
        assert "content" in data["sources"][0]
        assert "metadata" in data["sources"][0]

    def test_chat_with_history(self, client, mock_rag_query):
        response = client.post(
            "/api/chat",
            json={
                "question": "And what about Kenya?",
                "chat_history": [
                    {"role": "user", "content": "Tell me about PIM in Colombia"},
                    {"role": "assistant", "content": "Colombia has..."},
                ],
            },
        )
        assert response.status_code == 200

    def test_chat_with_filters(self, client, mock_rag_query):
        response = client.post(
            "/api/chat",
            json={
                "question": "What legislation exists?",
                "filters": {"country": "COL", "policy_guidance_tier": 1},
            },
        )
        assert response.status_code == 200


class TestAdminEndpoints:
    """Tests for GET/PUT /api/config."""

    def test_get_config_requires_auth(self, client):
        response = client.get("/api/config")
        assert response.status_code == 401

    def test_get_config_with_auth(self, client, auth_headers):
        response = client.get("/api/config", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "chunker" in data
        assert "llm_provider" in data
        assert "retriever_type" in data

    def test_put_config_requires_auth(self, client):
        response = client.put("/api/config", json={"llm_temperature": 0.5})
        assert response.status_code == 401

    def test_put_config_with_auth(self, client, auth_headers):
        response = client.put(
            "/api/config",
            headers=auth_headers,
            json={"llm_temperature": 0.5},
        )
        assert response.status_code == 200
        assert response.json()["llm_temperature"] == 0.5


class TestIngestEndpoints:
    """Tests for /api/ingest/* endpoints."""

    def test_ingest_url_requires_auth(self, client):
        response = client.post(
            "/api/ingest/url",
            json={
                "source_url": "https://example.com/doc.pdf",
                "record_id": "REC-001",
                "country": "COL",
            },
        )
        assert response.status_code == 401

    def test_ingest_url_with_auth(self, client, auth_headers, mock_ingest):
        response = client.post(
            "/api/ingest/url",
            headers=auth_headers,
            json={
                "source_url": "https://example.com/doc.pdf",
                "record_id": "REC-001",
                "country": "COL",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["record_id"] == "REC-001"
        assert data["chunks_created"] == 5

    def test_delete_requires_auth(self, client):
        response = client.delete("/api/ingest/REC-001")
        assert response.status_code == 401

    def test_delete_with_auth(self, client, auth_headers, mock_ingest):
        response = client.delete("/api/ingest/REC-001", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["record_id"] == "REC-001"
        assert response.json()["deleted"] == 5
