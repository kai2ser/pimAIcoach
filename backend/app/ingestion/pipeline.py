"""
Ingestion pipeline — orchestrates load → chunk → enrich → store.

Usage:
    from app.ingestion.pipeline import ingest_document

    result = await ingest_document(
        source="https://blob.vercel-storage.com/...",
        metadata=PolicyMetadata(record_id="...", country="COL", ...),
    )
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import text

from app.config import settings
from app.ingestion.loaders import load_from_path, load_from_url, load_from_bytes
from app.ingestion.chunkers import chunk_documents
from app.ingestion.metadata import PolicyMetadata, enrich_chunks
from app.vectorstore.store import get_vector_store, _get_pg_engine

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    record_id: str
    chunks_created: int
    source: str


async def ingest_document(
    metadata: PolicyMetadata,
    source: str | None = None,
    file_path: str | None = None,
    file_bytes: bytes | None = None,
    filename: str | None = None,
    chunker_strategy: str | None = None,
) -> IngestResult:
    """
    Full ingestion pipeline for a single document.

    Provide one of: source (URL), file_path, or file_bytes + filename.
    """
    loop = asyncio.get_event_loop()

    # Step 1: Load
    if file_path:
        logger.info("Loading from path: %s", file_path)
        raw_docs = await loop.run_in_executor(None, load_from_path, file_path)
    elif source:
        logger.info("Loading from URL: %s", source)
        raw_docs = await load_from_url(source, filename)
    elif file_bytes and filename:
        logger.info("Loading from bytes: %s", filename)
        raw_docs = await loop.run_in_executor(None, load_from_bytes, file_bytes, filename)
    else:
        raise ValueError("Provide source (URL), file_path, or file_bytes + filename")

    logger.info("Loaded %d raw document pages", len(raw_docs))

    # Step 2: Chunk (run in executor — CPU-bound)
    chunks = await loop.run_in_executor(None, chunk_documents, raw_docs, chunker_strategy)
    logger.info("Created %d chunks", len(chunks))

    # Step 3: Enrich with metadata
    enriched = enrich_chunks(chunks, metadata)

    # Step 4: Store in vector store (may call embedding API — run in executor)
    store = get_vector_store()
    await loop.run_in_executor(None, store.add_documents, enriched)
    logger.info("Stored %d chunks in vector store", len(enriched))

    # Invalidate stats cache so new data shows immediately
    try:
        from app.api.stats import invalidate_stats_cache
        invalidate_stats_cache()
    except Exception:
        pass

    return IngestResult(
        record_id=metadata.record_id,
        chunks_created=len(enriched),
        source=source or file_path or filename or "bytes",
    )


async def ingest_batch(
    items: list[dict],
    chunker_strategy: str | None = None,
) -> list[IngestResult]:
    """Ingest multiple documents with bounded concurrency."""
    semaphore = asyncio.Semaphore(3)  # Max 3 concurrent ingestions

    async def _ingest_one(item: dict) -> IngestResult:
        async with semaphore:
            meta = PolicyMetadata(**item["metadata"])
            return await ingest_document(
                metadata=meta,
                source=item.get("source"),
                file_path=item.get("file_path"),
                chunker_strategy=chunker_strategy,
            )

    results = await asyncio.gather(
        *[_ingest_one(item) for item in items],
        return_exceptions=True,
    )
    # Filter out exceptions and log them
    final: list[IngestResult] = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.exception("Batch item %d failed: %s", i, r)
        else:
            final.append(r)
    return final


async def clear_collection() -> int:
    """Remove all documents from the current vector store collection."""
    engine = _get_pg_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT uuid FROM langchain_pg_collection WHERE name = :name"),
            {"name": settings.collection_name},
        ).fetchone()
        if row:
            result = conn.execute(
                text(
                    "DELETE FROM langchain_pg_embedding WHERE collection_id = :coll_id"
                ),
                {"coll_id": row[0]},
            )
            conn.commit()
            deleted = result.rowcount
            logger.info(
                "Cleared %d chunks from collection '%s'",
                deleted,
                settings.collection_name,
            )
            # Invalidate stats cache
            try:
                from app.api.stats import invalidate_stats_cache
                invalidate_stats_cache()
            except Exception:
                pass
            return deleted
    logger.warning("Collection '%s' not found — nothing to clear", settings.collection_name)
    return 0


async def delete_document_chunks(record_id: str) -> int:
    """Remove all chunks for a given record from the vector store."""
    store = get_vector_store()
    if hasattr(store, "delete"):
        store.delete(filter={"record_id": record_id})
        logger.info("Deleted chunks for record %s", record_id)
        # Invalidate stats cache
        try:
            from app.api.stats import invalidate_stats_cache
            invalidate_stats_cache()
        except Exception:
            pass
        return 1
    logger.warning("Vector store does not support delete by filter")
    return 0
