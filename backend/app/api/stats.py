"""
Collection statistics endpoints — public summary of the RAG vector store.

  GET /api/stats        — aggregate totals (cached 60s)
  GET /api/stats/detail — per-country, per-tier, per-year breakdowns (cached 60s)

Uses the shared cached SQLAlchemy engine to avoid creating new connection
pools per request.
"""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy import text

from app.config import settings
from app.ratelimit import stats_limiter
from app.vectorstore.store import _get_pg_engine

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stats"])

# ── In-memory caches ─────────────────────────────────────────────────────────

_CACHE_TTL_SECONDS = 60
_cache: dict = {"data": None, "expires_at": 0.0}
_detail_cache: dict = {"data": None, "expires_at": 0.0}


def invalidate_stats_cache() -> None:
    """Clear stats caches — call after ingestion or deletion."""
    _cache["data"] = None
    _cache["expires_at"] = 0.0
    _detail_cache["data"] = None
    _detail_cache["expires_at"] = 0.0


# ── Models ───────────────────────────────────────────────────────────────────

class CollectionStats(BaseModel):
    total_chunks: int
    total_documents: int
    total_tokens: int | None
    lang_eng_documents: int
    lang_ori_documents: int
    last_updated: str | None
    collection_name: str


class CountryBreakdown(BaseModel):
    country: str
    country_name: str | None
    documents: int
    chunks: int


class TierBreakdown(BaseModel):
    tier: int | None
    label: str
    documents: int


class YearBreakdown(BaseModel):
    year: str | None
    documents: int


class DetailedStats(BaseModel):
    summary: CollectionStats
    by_country: list[CountryBreakdown]
    by_tier: list[TierBreakdown]
    by_year: list[YearBreakdown]
    embedding_model: str
    vector_store: str
    chunk_size: int
    chunk_overlap: int
    retriever_type: str


_TIER_LABELS = {
    1: "Primary Legislation",
    2: "Secondary Regulations",
    3: "Procedural Guidelines",
    4: "Strategies",
}


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=CollectionStats)
async def get_stats(request: Request):
    """Return aggregate statistics (cached 60s)."""
    stats_limiter.check(request)
    now = time.monotonic()
    if _cache["data"] is not None and now < _cache["expires_at"]:
        return _cache["data"]
    result = _fetch_stats()
    _cache["data"] = result
    _cache["expires_at"] = now + _CACHE_TTL_SECONDS
    return result


@router.get("/stats/detail", response_model=DetailedStats)
async def get_stats_detail(request: Request):
    """Return detailed breakdowns by country, tier, and year (cached 60s)."""
    stats_limiter.check(request)
    now = time.monotonic()
    if _detail_cache["data"] is not None and now < _detail_cache["expires_at"]:
        return _detail_cache["data"]
    result = _fetch_detailed_stats()
    _detail_cache["data"] = result
    _detail_cache["expires_at"] = now + _CACHE_TTL_SECONDS
    return result


# ── Shared helpers ───────────────────────────────────────────────────────────

def _get_collection_uuid(conn) -> str | None:
    row = conn.execute(
        text("SELECT uuid FROM langchain_pg_collection WHERE name = :name"),
        {"name": settings.collection_name},
    ).fetchone()
    return row[0] if row else None


def _empty_summary() -> CollectionStats:
    return CollectionStats(
        total_chunks=0, total_documents=0, total_tokens=None,
        lang_eng_documents=0, lang_ori_documents=0,
        last_updated=None, collection_name=settings.collection_name,
    )


# ── Queries ──────────────────────────────────────────────────────────────────

def _fetch_stats() -> CollectionStats:
    engine = _get_pg_engine()
    with engine.connect() as conn:
        coll_uuid = _get_collection_uuid(conn)
        if coll_uuid is None:
            return _empty_summary()

        # Single consolidated query for summary + latest year
        row = conn.execute(
            text("""
                SELECT
                    COUNT(*)                                             AS total_chunks,
                    COUNT(DISTINCT cmetadata->>'record_id')              AS total_documents,
                    SUM(DISTINCT (cmetadata->>'tokens')::int)
                        FILTER (WHERE cmetadata->>'tokens' IS NOT NULL)  AS total_tokens,
                    COUNT(DISTINCT cmetadata->>'record_id')
                        FILTER (WHERE cmetadata->>'lang_type' = 'ENG')   AS lang_eng_documents,
                    COUNT(DISTINCT cmetadata->>'record_id')
                        FILTER (WHERE cmetadata->>'lang_type' = 'ORI')   AS lang_ori_documents,
                    MAX(cmetadata->>'year')
                        FILTER (WHERE cmetadata->>'year' IS NOT NULL)    AS latest_year
                FROM langchain_pg_embedding
                WHERE collection_id = :coll_id
            """),
            {"coll_id": coll_uuid},
        ).fetchone()

    return CollectionStats(
        total_chunks=row[0] or 0,
        total_documents=row[1] or 0,
        total_tokens=row[2],
        lang_eng_documents=row[3] or 0,
        lang_ori_documents=row[4] or 0,
        last_updated=row[5],
        collection_name=settings.collection_name,
    )


def _fetch_detailed_stats() -> DetailedStats:
    summary = _fetch_stats()
    engine = _get_pg_engine()

    by_country: list[CountryBreakdown] = []
    by_tier: list[TierBreakdown] = []
    by_year: list[YearBreakdown] = []

    with engine.connect() as conn:
        coll_uuid = _get_collection_uuid(conn)
        if coll_uuid is not None:
            # Per-country
            rows = conn.execute(
                text("""
                    SELECT
                        cmetadata->>'country'      AS country,
                        cmetadata->>'country_name'  AS country_name,
                        COUNT(DISTINCT cmetadata->>'record_id') AS documents,
                        COUNT(*)                     AS chunks
                    FROM langchain_pg_embedding
                    WHERE collection_id = :coll_id
                    GROUP BY cmetadata->>'country', cmetadata->>'country_name'
                    ORDER BY documents DESC
                """),
                {"coll_id": coll_uuid},
            ).fetchall()
            by_country = [
                CountryBreakdown(country=r[0] or "Unknown", country_name=r[1], documents=r[2], chunks=r[3])
                for r in rows
            ]

            # Per-tier
            rows = conn.execute(
                text("""
                    SELECT
                        (cmetadata->>'policy_guidance_tier')::int AS tier,
                        COUNT(DISTINCT cmetadata->>'record_id')  AS documents
                    FROM langchain_pg_embedding
                    WHERE collection_id = :coll_id
                      AND cmetadata->>'policy_guidance_tier' IS NOT NULL
                    GROUP BY (cmetadata->>'policy_guidance_tier')::int
                    ORDER BY tier
                """),
                {"coll_id": coll_uuid},
            ).fetchall()
            by_tier = [
                TierBreakdown(tier=r[0], label=_TIER_LABELS.get(r[0], f"Tier {r[0]}"), documents=r[1])
                for r in rows
            ]

            # Per-year
            rows = conn.execute(
                text("""
                    SELECT
                        cmetadata->>'year'                       AS year,
                        COUNT(DISTINCT cmetadata->>'record_id')  AS documents
                    FROM langchain_pg_embedding
                    WHERE collection_id = :coll_id
                      AND cmetadata->>'year' IS NOT NULL
                    GROUP BY cmetadata->>'year'
                    ORDER BY cmetadata->>'year'
                """),
                {"coll_id": coll_uuid},
            ).fetchall()
            by_year = [YearBreakdown(year=r[0], documents=r[1]) for r in rows]

    return DetailedStats(
        summary=summary,
        by_country=by_country,
        by_tier=by_tier,
        by_year=by_year,
        embedding_model=f"{settings.embedding_model} ({settings.embedding_model_name})",
        vector_store=settings.vector_store,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        retriever_type=settings.retriever_type,
    )
