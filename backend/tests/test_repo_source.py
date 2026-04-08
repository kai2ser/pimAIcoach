"""
Tests for the repo_source module — API-based record fetching.
"""

from unittest.mock import patch, MagicMock, AsyncMock

import httpx
import pytest

from app.ingestion.repo_source import fetch_records_with_docs, resolve_country_name


# Sample API response matching the real export endpoint shape
_SAMPLE_API_RESPONSE = {
    "count": 2,
    "lang": "ENG",
    "exportedAt": "2026-04-08T10:00:00Z",
    "records": [
        {
            "id": "rec-1",
            "country": "COL",
            "countryName": "Colombia",
            "nameEng": "Public Investment Framework",
            "nameOrig": "Marco de Inversión Pública",
            "year": 2020,
            "source": "Ministry",
            "yearRevised": None,
            "overview": "Framework overview",
            "policyGuidanceTier": 1,
            "strategyTier": None,
            "link": "https://example.com/col",
            "pages": 42,
            "tokens": 15000,
            "documents": [
                {
                    "id": "doc-1",
                    "recordId": "rec-1",
                    "langType": "ENG",
                    "langCode": "en",
                    "langLabel": "English",
                    "blobUrl": "https://blob.example.com/doc1.pdf",
                    "fileName": "framework.pdf",
                    "fileSize": 123456,
                }
            ],
        },
        {
            "id": "rec-2",
            "country": "KEN",
            "countryName": "Kenya",
            "nameEng": "Budget Act",
            "nameOrig": None,
            "year": 2015,
            "source": "Parliament",
            "yearRevised": 2023,
            "overview": "Budget legislation",
            "policyGuidanceTier": 1,
            "strategyTier": None,
            "link": None,
            "pages": 20,
            "tokens": None,
            "documents": [],
        },
    ],
}


def _mock_async_response(json_data: dict, status_code: int = 200):
    """Create a mock httpx.Response."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data
    mock_response.raise_for_status.return_value = None
    return mock_response


def _setup_async_client_mock(mock_client_cls, response):
    """Configure AsyncMock for httpx.AsyncClient context manager."""
    mock_client = AsyncMock()
    mock_client.get.return_value = response
    mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_client


class TestFetchRecordsWithDocs:
    """Tests for fetch_records_with_docs API call."""

    @pytest.mark.asyncio
    @patch("app.ingestion.repo_source.httpx.AsyncClient")
    async def test_returns_snake_case_records(self, mock_client_cls):
        """API camelCase fields are mapped to snake_case."""
        _setup_async_client_mock(mock_client_cls, _mock_async_response(_SAMPLE_API_RESPONSE))

        records = await fetch_records_with_docs(lang="ENG")

        assert len(records) == 2
        rec = records[0]
        assert rec["country"] == "COL"
        assert rec["country_name"] == "Colombia"
        assert rec["name_eng"] == "Public Investment Framework"
        assert rec["name_orig"] == "Marco de Inversión Pública"
        assert rec["policy_guidance_tier"] == 1
        assert rec["year"] == 2020

    @pytest.mark.asyncio
    @patch("app.ingestion.repo_source.httpx.AsyncClient")
    async def test_documents_mapped_correctly(self, mock_client_cls):
        """Nested documents array is also mapped to snake_case."""
        _setup_async_client_mock(mock_client_cls, _mock_async_response(_SAMPLE_API_RESPONSE))

        records = await fetch_records_with_docs(lang="ENG")

        doc = records[0]["documents"][0]
        assert doc["blob_url"] == "https://blob.example.com/doc1.pdf"
        assert doc["lang_type"] == "ENG"
        assert doc["lang_code"] == "en"
        assert doc["file_name"] == "framework.pdf"

    @pytest.mark.asyncio
    @patch("app.ingestion.repo_source.httpx.AsyncClient")
    async def test_lang_param_passed_to_api(self, mock_client_cls):
        """The lang parameter is forwarded as a query param."""
        mock_client = _setup_async_client_mock(
            mock_client_cls, _mock_async_response({"count": 0, "records": []})
        )

        await fetch_records_with_docs(lang="ORI")

        call_kwargs = mock_client.get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params", {})
        assert params == {"lang": "ORI"}

    @pytest.mark.asyncio
    @patch("app.ingestion.repo_source.httpx.AsyncClient")
    async def test_no_lang_param_when_none(self, mock_client_cls):
        """No lang query param sent when lang=None (fetch all)."""
        mock_client = _setup_async_client_mock(
            mock_client_cls, _mock_async_response({"count": 0, "records": []})
        )

        await fetch_records_with_docs(lang=None)

        call_kwargs = mock_client.get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params", {})
        assert params == {}

    @pytest.mark.asyncio
    @patch("app.ingestion.repo_source.httpx.AsyncClient")
    async def test_country_filter(self, mock_client_cls):
        """Client-side country filter works."""
        _setup_async_client_mock(mock_client_cls, _mock_async_response(_SAMPLE_API_RESPONSE))

        records = await fetch_records_with_docs(lang="ENG", country="KEN")

        assert len(records) == 1
        assert records[0]["country"] == "KEN"

    @pytest.mark.asyncio
    @patch("app.ingestion.repo_source.httpx.AsyncClient")
    async def test_api_error_raises_runtime_error(self, mock_client_cls):
        """HTTP errors are wrapped in RuntimeError."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        with pytest.raises(RuntimeError, match="Failed to fetch"):
            await fetch_records_with_docs()


class TestResolveCountryName:
    """Tests for resolve_country_name via API."""

    @pytest.mark.asyncio
    @patch("app.ingestion.repo_source.httpx.AsyncClient")
    async def test_resolves_known_country(self, mock_client_cls):
        """Returns country name from API response."""
        _setup_async_client_mock(mock_client_cls, _mock_async_response(_SAMPLE_API_RESPONSE))

        result = await resolve_country_name("COL")
        assert result == "Colombia"

    @pytest.mark.asyncio
    @patch("app.ingestion.repo_source.httpx.AsyncClient")
    async def test_returns_code_when_not_found(self, mock_client_cls):
        """Falls back to the input code if no records match."""
        _setup_async_client_mock(
            mock_client_cls, _mock_async_response({"count": 0, "records": []})
        )

        result = await resolve_country_name("ZZZ")
        assert result == "ZZZ"
