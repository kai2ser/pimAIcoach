"""
Collection statistics endpoint — public summary of the RAG vector store.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stats"])


class CollectionStats(BaseModel):
    """Summary statistics for the ingested document collection."""

    total_chunks: int
    total_documents: int
    total_tokens: int | None
    lang_eng_documents: int
    lang_ori_documents: int
    last_updated: str | None
    collection_name: str


@router.get("/stats", response_model=CollectionStats)
async def get_stats():
    """
    Return aggregate statistics about the vector store collection.

    Queries the pgvector ``langchain_pg_embedding`` table directly so
    the frontend can display live numbers without authentication.
    """
    collection_name = settings.collection_name

    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        # Resolve the internal collection UUID used by langchain_postgres
        row = conn.execute(
            text("SELECT uuid FROM langchain_pg_collection WHERE name = :name"),
            {"name": collection_name},
        ).fetchone()

        if row is None:
            return CollectionStats(
                total_chunks=0,
                total_documents=0,
                total_tokens=None,
                lang_eng_documents=0,
                lang_ori_documents=0,
                last_updated=None,
                collection_name=collection_name,
            )

        coll_uuid = row[0]

        # Aggregate chunk-level stats using the JSONB cmetadata column
        stats = conn.execute(
            text("""
                SELECT
                    COUNT(*)                                             AS total_chunks,
                    COUNT(DISTINCT cmetadata->>'record_id')              AS total_documents,
                    SUM(DISTINCT (cmetadata->>'tokens')::int)
                        FILTER (WHERE cmetadata->>'tokens' IS NOT NULL)  AS total_tokens,
                    COUNT(DISTINCT cmetadata->>'record_id')
                        FILTER (WHERE cmetadata->>'lang_type' = 'ENG')   AS lang_eng_documents,
                    COUNT(DISTINCT cmetadata->>'record_id')
                        FILTER (WHERE cmetadata->>'lang_type' = 'ORI')   AS lang_ori_documents
                FROM langchain_pg_embedding
                WHERE collection_id = :coll_id
            """),
            {"coll_id": coll_uuid},
        ).fetchone()

        # Most recent ingestion timestamp (if stored in metadata)
        last_row = conn.execute(
            text("""
                SELECT MAX(cmetadata->>'year') AS latest_year
                FROM langchain_pg_embedding
                WHERE collection_id = :coll_id
                  AND cmetadata->>'year' IS NOT NULL
            """),
            {"coll_id": coll_uuid},
        ).fetchone()

    return CollectionStats(
        total_chunks=stats[0] or 0,
        total_documents=stats[1] or 0,
        total_tokens=stats[2],
        lang_eng_documents=stats[3] or 0,
        lang_ori_documents=stats[4] or 0,
        last_updated=last_row[0] if last_row else None,
        collection_name=collection_name,
    )
