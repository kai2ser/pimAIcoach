"""
Query the pimrepository Neon database for policy records and their documents.

Uses a single JOIN query to avoid N+1 patterns, and caches country name
lookups for the lifetime of the process.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from functools import lru_cache

import psycopg

from app.config import settings

logger = logging.getLogger(__name__)


def fetch_records_with_docs(
    country: str | None = None,
    record_id: str | None = None,
) -> list[dict]:
    """Query pimrepository DB for records and their documents using a single JOIN."""
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            query = """
                SELECT
                    r.id, r.country, r.name_eng, r.name_orig,
                    r.year, r.source, r.year_revised, r.overview,
                    r.policy_guidance_tier, r.strategy_tier,
                    r.link, r.pages, r.tokens,
                    d.id AS doc_id, d.lang_type, d.lang_code, d.lang_label,
                    d.blob_url, d.file_name, d.file_size
                FROM policy_records r
                LEFT JOIN documents d ON d.record_id = r.id::text
                WHERE 1=1
            """
            params: list = []

            if record_id:
                query += " AND r.id = %s"
                params.append(record_id)
            elif country:
                query += " AND (r.country ILIKE %s OR r.country = %s)"
                params.extend([f"%{country}%", country])

            query += " ORDER BY r.country, r.name_eng, d.lang_type"
            cur.execute(query, params)

            columns = [desc[0] for desc in cur.description]
            rows = [dict(zip(columns, row)) for row in cur.fetchall()]

    # Group rows by record (many docs per record from the JOIN)
    record_cols = {
        "id", "country", "name_eng", "name_orig", "year", "source",
        "year_revised", "overview", "policy_guidance_tier", "strategy_tier",
        "link", "pages", "tokens",
    }
    doc_col_map = {
        "doc_id": "id", "lang_type": "lang_type", "lang_code": "lang_code",
        "lang_label": "lang_label", "blob_url": "blob_url",
        "file_name": "file_name", "file_size": "file_size",
    }

    records_by_id: dict[str, dict] = {}
    for row in rows:
        rid = str(row["id"])
        if rid not in records_by_id:
            records_by_id[rid] = {
                k: row[k] for k in record_cols if k in row
            }
            records_by_id[rid]["documents"] = []

        # Add document if present (LEFT JOIN can produce NULL doc rows)
        if row.get("doc_id") is not None:
            doc = {v: row[k] for k, v in doc_col_map.items() if k in row}
            records_by_id[rid]["documents"].append(doc)

    return list(records_by_id.values())


@lru_cache(maxsize=256)
def resolve_country_name(country_code_or_name: str) -> str | None:
    """Look up full country name from the countries table (cached)."""
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT name FROM countries WHERE iso3 = %s",
                [country_code_or_name.upper()],
            )
            row = cur.fetchone()
            if row:
                return row[0]
            return country_code_or_name
