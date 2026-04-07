"""
Country PIM Transparency API.

Endpoints:
  POST /api/country-transparency        — generate a PIM transparency briefing (SSE)
  POST /api/country-transparency/export  — export generated content as DOCX or PDF
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.export.docx_export import export_docx, TRANSPARENCY_THEME as DOCX_TRANSPARENCY_THEME
from app.export.pdf_export import export_pdf, TRANSPARENCY_THEME as PDF_TRANSPARENCY_THEME
from app.generation.transparency_prompt import (
    format_transparency_records_context,
    get_country_transparency_prompt,
)
from app.generation.prompts import format_documents
from app.ingestion.repo_source import fetch_records_with_docs, resolve_country_name
from app.retrieval.retriever import get_retriever

logger = logging.getLogger(__name__)
router = APIRouter(tags=["country-transparency"])

# Max tokens for long-form briefing generation (higher than the chat default)
_TRANSPARENCY_MAX_TOKENS = 8192


# ── Models ────────────────────────────────────────────────────

class TransparencyRequest(BaseModel):
    country_iso3: str = Field(description="ISO3 country code")


class TransparencyExportRequest(BaseModel):
    content: str = Field(description="The generated markdown content")
    country_name: str = Field(description="Country name for the document title")
    format: str = Field(description="'docx' or 'pdf'")


# ── Helpers ───────────────────────────────────────────────────

def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def _get_transparency_llm():
    """Return a ChatAnthropic instance with higher max_tokens for briefing generation."""
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        max_tokens=_TRANSPARENCY_MAX_TOKENS,
        anthropic_api_key=settings.anthropic_api_key,
    )


# ── POST /api/country-transparency ───────────────────────────

@router.post("/country-transparency")
async def generate_country_transparency(request: TransparencyRequest):
    """Generate a PIM transparency briefing and stream via SSE."""
    return StreamingResponse(
        _transparency_stream(request.country_iso3),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _transparency_stream(country_iso3: str):
    """Generator that builds context, calls the LLM, and yields SSE events."""
    try:
        # 1. Resolve country name
        country_name = resolve_country_name(country_iso3) or country_iso3
        yield _sse({"type": "status", "data": f"Preparing transparency briefing for {country_name}..."})

        # 2. Fetch structured policy records
        records = fetch_records_with_docs(country=country_iso3)
        policy_context = format_transparency_records_context(records)

        yield _sse({
            "type": "status",
            "data": f"Found {len(records)} policy records. Retrieving document context...",
        })

        # 3. Retrieve RAG document chunks for this country
        try:
            retriever = get_retriever(filters={"country": country_iso3}, k=20)
            docs = retriever.invoke(
                f"Public investment management institutional framework policy transparency for {country_name}"
            )
            rag_context = format_documents(docs) if docs else "No indexed documents found for this country."
            yield _sse({
                "type": "status",
                "data": f"Retrieved {len(docs)} document excerpts. Generating transparency briefing...",
            })
        except Exception as e:
            logger.warning("RAG retrieval failed for %s: %s", country_iso3, e)
            rag_context = "No indexed documents available."
            yield _sse({
                "type": "status",
                "data": "No indexed documents available. Generating from general knowledge...",
            })

        # 4. Build the prompt and stream the LLM response
        prompt = get_country_transparency_prompt()
        llm = _get_transparency_llm()
        chain = prompt | llm

        async for chunk in chain.astream({
            "country_name": country_name,
            "policy_records_context": policy_context,
            "rag_context": rag_context,
        }):
            if chunk.content:
                yield _sse({"type": "token", "data": chunk.content})

        yield _sse({"type": "done"})

    except Exception as e:
        logger.exception("Transparency briefing generation failed for %s", country_iso3)
        yield _sse({"type": "error", "data": str(e)})


# ── POST /api/country-transparency/export ─────────────────────

@router.post("/country-transparency/export")
async def export_country_transparency(request: TransparencyExportRequest):
    """Export a generated transparency briefing as DOCX or PDF."""
    if request.format == "docx":
        return export_docx(request.content, request.country_name, theme=DOCX_TRANSPARENCY_THEME)
    elif request.format == "pdf":
        return export_pdf(request.content, request.country_name, theme=PDF_TRANSPARENCY_THEME)
    else:
        raise HTTPException(status_code=400, detail="Format must be 'docx' or 'pdf'")
