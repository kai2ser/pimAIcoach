"""
Re-index API — trigger a full or language-filtered re-index from the
PIM Policy Repository export API.  Streams progress via Server-Sent Events.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.auth import require_api_key
from app.ingestion.metadata import PolicyMetadata
from app.ingestion.pipeline import clear_collection, ingest_document
from app.api import sse_event as _sse
from app.ingestion.repo_source import fetch_records_with_docs

logger = logging.getLogger(__name__)
router = APIRouter(tags=["reindex"], dependencies=[Depends(require_api_key)])


class ReindexRequest(BaseModel):
    lang_filter: str = Field(
        default="eng",
        description="'all' for every language version, 'eng' for English only, 'ori' for original language only",
    )
    clear_existing: bool = Field(
        default=True,
        description="Clear the collection before re-indexing",
    )


@router.post("/reindex")
async def reindex(request: ReindexRequest):
    """Trigger a re-index and stream progress as SSE events."""
    return StreamingResponse(
        _reindex_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


async def _reindex_stream(request: ReindexRequest):
    """Generator that performs the re-index and yields SSE events."""
    try:
        # --- Fetch records from policy repository API ---
        yield _sse({"type": "status", "message": "Fetching records from repository API..."})

        # Map lang_filter to API parameter
        lang_param = {"eng": "ENG", "ori": "ORI", "all": None}.get(
            request.lang_filter.lower(), "ENG"
        )
        records = await fetch_records_with_docs(lang=lang_param)

        # --- Flatten to a list of (record, doc) pairs ---
        work_items: list[tuple[dict, dict]] = []
        for record in records:
            for doc in record.get("documents", []):
                work_items.append((record, doc))

        total = len(work_items)

        if total == 0:
            yield _sse(
                {
                    "type": "complete",
                    "succeeded": 0,
                    "failed": 0,
                    "total_chunks": 0,
                    "message": "No documents matched the filter.",
                }
            )
            return

        yield _sse(
            {"type": "status", "message": f"Found {total} documents to index."}
        )

        # --- Optionally clear the existing collection ---
        # Safety: we defer clearing until AFTER at least one document succeeds
        # to avoid leaving the collection empty on total failure.
        _clear_pending = request.clear_existing
        _cleared = False

        # --- Ingest documents in batches with bounded concurrency ---
        _BATCH_SIZE = 4
        succeeded = 0
        failed = 0
        total_chunks = 0

        async def _ingest_one(record, doc):
            """Ingest a single document, returning (label, result_or_error)."""
            label = f"{record['country']} — {record['name_eng']} ({doc['lang_type']})"
            country_name = record.get("country_name") or record["country"]
            metadata = PolicyMetadata(
                record_id=str(record["id"]),
                country=record["country"],
                country_name=country_name,
                name_eng=record["name_eng"],
                name_orig=record.get("name_orig"),
                year=record.get("year"),
                year_revised=record.get("year_revised"),
                source=record.get("source"),
                policy_guidance_tier=record.get("policy_guidance_tier"),
                strategy_tier=record.get("strategy_tier"),
                lang_type=doc["lang_type"],
                lang_code=doc.get("lang_code"),
                overview=record.get("overview"),
                link=record.get("link"),
                pages=record.get("pages"),
                tokens=record.get("tokens"),
            )
            try:
                result = await ingest_document(
                    metadata=metadata,
                    source=doc["blob_url"],
                    filename=doc.get("file_name"),
                )
                return label, result
            except Exception as exc:
                logger.exception("Failed to ingest %s", label)
                return label, exc

        for batch_start in range(0, total, _BATCH_SIZE):
            batch = work_items[batch_start:batch_start + _BATCH_SIZE]

            # Clear collection just before the first batch
            if _clear_pending and not _cleared:
                yield _sse({"type": "status", "message": "Clearing existing collection..."})
                deleted = await clear_collection()
                _cleared = True
                yield _sse({"type": "status", "message": f"Cleared {deleted} existing chunks."})

            # Ingest batch concurrently
            results = await asyncio.gather(
                *[_ingest_one(record, doc) for record, doc in batch],
                return_exceptions=False,
            )

            # Yield progress for each item in the batch
            for i, (label, result) in enumerate(results):
                idx = batch_start + i + 1
                if isinstance(result, Exception):
                    failed += 1
                    yield _sse({
                        "type": "progress",
                        "current": idx,
                        "total": total,
                        "document": label,
                        "status": "error",
                        "error": str(result),
                    })
                else:
                    succeeded += 1
                    total_chunks += result.chunks_created
                    yield _sse({
                        "type": "progress",
                        "current": idx,
                        "total": total,
                        "document": label,
                        "status": "done",
                        "chunks": result.chunks_created,
                    })

        # --- Final summary ---
        yield _sse(
            {
                "type": "complete",
                "succeeded": succeeded,
                "failed": failed,
                "total_chunks": total_chunks,
            }
        )

    except Exception as exc:
        logger.exception("Re-index failed")
        yield _sse({"type": "error", "message": str(exc)})
