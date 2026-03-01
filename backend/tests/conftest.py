"""
Shared pytest fixtures for the PIM AI Coach backend test suite.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

TEST_API_KEY = "test-secret-key-for-tests"


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    """Headers with a valid API key for authenticated endpoints."""
    return {"X-API-Key": TEST_API_KEY}


@pytest.fixture()
def client():
    """
    FastAPI TestClient with PIM_ADMIN_API_KEY set to the test key.

    Patches the settings singleton so auth works in tests.
    """
    from app.config import settings

    original_key = settings.admin_api_key
    object.__setattr__(settings, "admin_api_key", TEST_API_KEY)

    from app.main import app

    with TestClient(app) as c:
        yield c

    object.__setattr__(settings, "admin_api_key", original_key)


@pytest.fixture()
def mock_rag_query():
    """Mock rag_query to return a canned response without calling LLMs."""
    canned = {
        "answer": "This is a test answer about PIM policies.",
        "sources": [
            {
                "content": "Sample document content...",
                "metadata": {
                    "country": "COL",
                    "country_name": "Colombia",
                    "name_eng": "Public Investment Framework",
                    "year": 2020,
                    "policy_guidance_tier": 1,
                },
            }
        ],
    }
    with patch("app.api.chat.rag_query", new_callable=AsyncMock, return_value=canned) as mock:
        yield mock


@pytest.fixture()
def mock_ingest():
    """Mock ingestion pipeline functions."""
    from app.ingestion.pipeline import IngestResult

    result = IngestResult(record_id="REC-001", chunks_created=5, source="https://example.com/doc.pdf")

    with (
        patch("app.api.ingest.ingest_document", new_callable=AsyncMock, return_value=result) as mock_doc,
        patch("app.api.ingest.delete_document_chunks", new_callable=AsyncMock, return_value=5) as mock_del,
    ):
        yield {"ingest_document": mock_doc, "delete_document_chunks": mock_del}
