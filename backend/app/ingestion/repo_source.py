"""
Fetch policy records and their documents from the PIM Policy Repository
export API.

Replaces the previous direct-database approach with an HTTP call to the
repository's public export endpoint, converting the camelCase JSON
response to the snake_case convention used throughout this codebase.
"""

from __future__ import annotations

import logging

import asyncio

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# -- camelCase → snake_case field mappings --------------------------------- #

_RECORD_FIELD_MAP = {
    "id": "id",
    "country": "country",
    "countryName": "country_name",
    "nameEng": "name_eng",
    "nameOrig": "name_orig",
    "year": "year",
    "source": "source",
    "yearRevised": "year_revised",
    "overview": "overview",
    "policyGuidanceTier": "policy_guidance_tier",
    "strategyTier": "strategy_tier",
    "link": "link",
    "pages": "pages",
    "tokens": "tokens",
}

_DOC_FIELD_MAP = {
    "id": "id",
    "recordId": "record_id",
    "langType": "lang_type",
    "langCode": "lang_code",
    "langLabel": "lang_label",
    "blobUrl": "blob_url",
    "fileName": "file_name",
    "fileSize": "file_size",
}


def _map_record(api_record: dict) -> dict:
    """Convert a single API record from camelCase to snake_case."""
    record = {
        snake: api_record.get(camel)
        for camel, snake in _RECORD_FIELD_MAP.items()
    }
    record["documents"] = [
        {snake: doc.get(camel) for camel, snake in _DOC_FIELD_MAP.items()}
        for doc in api_record.get("documents", [])
    ]
    return record


async def fetch_records_with_docs(
    lang: str | None = "ENG",
    country: str | None = None,
    record_id: str | None = None,
) -> list[dict]:
    """Fetch policy records from the PIM Policy Repository export API.

    Args:
        lang: Language filter sent to the API ("ENG", "ORI", or None for all).
        country: Optional client-side filter by ISO3 country code.
        record_id: Optional client-side filter by record id.

    Returns:
        List of record dicts (snake_case keys), each with a ``documents``
        list — the same shape the rest of the pipeline expects.
    """
    params: dict[str, str] = {}
    if lang:
        params["lang"] = lang

    url = settings.policy_repo_api_url
    logger.info("Fetching records from %s (params=%s)", url, params)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, params=params, follow_redirects=True)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError(
            f"Failed to fetch records from policy repository API: {exc}"
        ) from exc

    data = response.json()
    api_records = data.get("records", [])

    records = [_map_record(r) for r in api_records]
    logger.info(
        "Fetched %d records (%d from API, lang=%s)",
        len(records), data.get("count", "?"), lang,
    )

    # Client-side filtering (country / record_id) — the API doesn't
    # support these query params, so we filter after fetch.
    if record_id:
        records = [r for r in records if str(r["id"]) == str(record_id)]
    elif country:
        country_upper = country.upper()
        records = [
            r for r in records
            if (r.get("country") or "").upper() == country_upper
        ]

    return records


def fetch_records_with_docs_sync(
    lang: str | None = "ENG",
    country: str | None = None,
    record_id: str | None = None,
) -> list[dict]:
    """Synchronous wrapper for use in non-async contexts (e.g. scripts)."""
    params: dict[str, str] = {}
    if lang:
        params["lang"] = lang

    url = settings.policy_repo_api_url

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.get(url, params=params, follow_redirects=True)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError(
            f"Failed to fetch records from policy repository API: {exc}"
        ) from exc

    data = response.json()
    records = [_map_record(r) for r in data.get("records", [])]

    if record_id:
        records = [r for r in records if str(r["id"]) == str(record_id)]
    elif country:
        country_upper = country.upper()
        records = [
            r for r in records
            if (r.get("country") or "").upper() == country_upper
        ]

    return records


async def resolve_country_name(country_code: str) -> str | None:
    """Look up full country name by fetching records for the given ISO3 code.

    Returns the country name from the first matching record, or the original
    code if no records are found.
    """
    records = await fetch_records_with_docs(lang=None, country=country_code)
    if records:
        return records[0].get("country_name") or country_code
    return country_code
