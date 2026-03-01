"""
Ingestion API — endpoints for processing documents into the vector store.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from app.api.auth import require_api_key
from app.ingestion.metadata import PolicyMetadata
from app.ingestion.pipeline import ingest_document, ingest_batch, delete_document_chunks

logger = logging.getLogger(__name__)
router = APIRouter(tags=["ingestion"], dependencies=[Depends(require_api_key)])


class IngestFromUrlRequest(BaseModel):
    """Ingest a document from a URL (e.g. Vercel Blob)."""

    source_url: str = Field(description="URL of the document to ingest")
    filename: str | None = None
    record_id: str
    country: str
    country_name: str | None = None
    name_eng: str | None = None
    name_orig: str | None = None
    year: int | None = None
    year_revised: int | None = None
    source: str | None = None
    policy_guidance_tier: int | None = None
    strategy_tier: int | None = None
    lang_type: str | None = None
    lang_code: str | None = None
    overview: str | None = None
    link: str | None = None
    pages: int | None = None
    tokens: int | None = None
    chunker_strategy: str | None = Field(
        default=None, description="Override chunking strategy for this document"
    )


class IngestResponse(BaseModel):
    record_id: str
    chunks_created: int
    source: str


class BatchIngestRequest(BaseModel):
    items: list[dict] = Field(
        description="List of {metadata: {...}, source: url} objects"
    )
    chunker_strategy: str | None = None


@router.post("/ingest/url", response_model=IngestResponse)
async def ingest_from_url(request: IngestFromUrlRequest):
    """Ingest a document from a URL into the vector store."""
    try:
        metadata = PolicyMetadata(
            record_id=request.record_id,
            country=request.country,
            country_name=request.country_name,
            name_eng=request.name_eng,
            name_orig=request.name_orig,
            year=request.year,
            year_revised=request.year_revised,
            source=request.source,
            policy_guidance_tier=request.policy_guidance_tier,
            strategy_tier=request.strategy_tier,
            lang_type=request.lang_type,
            lang_code=request.lang_code,
            overview=request.overview,
            link=request.link,
            pages=request.pages,
            tokens=request.tokens,
        )

        result = await ingest_document(
            metadata=metadata,
            source=request.source_url,
            filename=request.filename,
            chunker_strategy=request.chunker_strategy,
        )
        return IngestResponse(
            record_id=result.record_id,
            chunks_created=result.chunks_created,
            source=result.source,
        )
    except Exception as e:
        logger.exception("Ingestion error")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during document processing. Please check the logs.",
        )


@router.post("/ingest/file", response_model=IngestResponse)
async def ingest_from_file(
    file: UploadFile = File(...),
    record_id: str = Form(...),
    country: str = Form(...),
    country_name: str | None = Form(None),
    name_eng: str | None = Form(None),
    year: int | None = Form(None),
    source: str | None = Form(None),
    policy_guidance_tier: int | None = Form(None),
    strategy_tier: int | None = Form(None),
    lang_type: str | None = Form(None),
    chunker_strategy: str | None = Form(None),
):
    """Ingest a document from a file upload."""
    try:
        content = await file.read()
        metadata = PolicyMetadata(
            record_id=record_id,
            country=country,
            country_name=country_name,
            name_eng=name_eng,
            year=year,
            source=source,
            policy_guidance_tier=policy_guidance_tier,
            strategy_tier=strategy_tier,
            lang_type=lang_type,
        )
        result = await ingest_document(
            metadata=metadata,
            file_bytes=content,
            filename=file.filename or "upload.pdf",
            chunker_strategy=chunker_strategy,
        )
        return IngestResponse(
            record_id=result.record_id,
            chunks_created=result.chunks_created,
            source=result.source,
        )
    except Exception as e:
        logger.exception("File ingestion error")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during document processing. Please check the logs.",
        )


@router.post("/ingest/batch", response_model=list[IngestResponse])
async def ingest_batch_endpoint(request: BatchIngestRequest):
    """Ingest multiple documents in a batch."""
    try:
        results = await ingest_batch(
            items=request.items,
            chunker_strategy=request.chunker_strategy,
        )
        return [
            IngestResponse(
                record_id=r.record_id,
                chunks_created=r.chunks_created,
                source=r.source,
            )
            for r in results
        ]
    except Exception as e:
        logger.exception("Batch ingestion error")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during document processing. Please check the logs.",
        )


@router.delete("/ingest/{record_id}")
async def delete_chunks(record_id: str):
    """Delete all chunks for a record from the vector store."""
    try:
        deleted = await delete_document_chunks(record_id)
        return {"record_id": record_id, "deleted": deleted}
    except Exception as e:
        logger.exception("Delete error")
        raise HTTPException(
            status_code=500,
            detail="An error occurred during document processing. Please check the logs.",
        )
