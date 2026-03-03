"""
Query the pimrepository Neon database for policy records and their documents.

Extracted from scripts/ingest_from_pimrepo.py so both the CLI script
and the /api/reindex endpoint can share the same logic.
"""

from __future__ import annotations

import logging

import psycopg

from app.config import settings

logger = logging.getLogger(__name__)


def fetch_records_with_docs(
    country: str | None = None,
    record_id: str | None = None,
) -> list[dict]:
    """Query pimrepository DB for records and their documents."""
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            # Fetch policy records
            query = """
                SELECT
                    r.id, r.country, r.name_eng, r.name_orig,
                    r.year, r.source, r.year_revised, r.overview,
                    r.policy_guidance_tier, r.strategy_tier,
                    r.link, r.pages, r.tokens
                FROM policy_records r
                WHERE 1=1
            """
            params: list = []

            if record_id:
                query += " AND r.id = %s"
                params.append(record_id)
            elif country:
                query += " AND (r.country ILIKE %s OR r.country = %s)"
                params.extend([f"%{country}%", country])

            query += " ORDER BY r.country, r.name_eng"
            cur.execute(query, params)

            columns = [desc[0] for desc in cur.description]
            records = [dict(zip(columns, row)) for row in cur.fetchall()]

            # Fetch documents for each record
            for record in records:
                cur.execute(
                    """
                    SELECT id, lang_type, lang_code, lang_label,
                           blob_url, file_name, file_size
                    FROM documents
                    WHERE record_id = %s
                    """,
                    [str(record["id"])],
                )
                doc_cols = [desc[0] for desc in cur.description]
                record["documents"] = [
                    dict(zip(doc_cols, row)) for row in cur.fetchall()
                ]

    return records


def resolve_country_name(country_code_or_name: str) -> str | None:
    """Look up full country name from the countries table."""
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            # Try ISO3 lookup first
            cur.execute(
                "SELECT name FROM countries WHERE iso3 = %s",
                [country_code_or_name.upper()],
            )
            row = cur.fetchone()
            if row:
                return row[0]
            # Already a name
            return country_code_or_name
