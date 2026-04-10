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
    lang_type: str = Field(
        default="ENG",
        description="Language version: 'ENG' for English, 'ORI' for original language",
    )


class TransparencyExportRequest(BaseModel):
    content: str = Field(description="The generated markdown content")
    country_name: str = Field(description="Country name for the document title")
    format: str = Field(description="'docx' or 'pdf'")


# ── Helpers ───────────────────────────────────────────────────

from app.api import sse_event as _sse


_transparency_llm_cache = None

def _get_transparency_llm():
    """Return a cached ChatAnthropic instance with higher max_tokens for briefing generation."""
    global _transparency_llm_cache
    if _transparency_llm_cache is None:
        from langchain_anthropic import ChatAnthropic
        _transparency_llm_cache = ChatAnthropic(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=_TRANSPARENCY_MAX_TOKENS,
            anthropic_api_key=settings.anthropic_api_key,
        )
    return _transparency_llm_cache


# ── POST /api/country-transparency ───────────────────────────

@router.post("/country-transparency")
async def generate_country_transparency(request: TransparencyRequest):
    """Generate a PIM transparency briefing and stream via SSE."""
    return StreamingResponse(
        _transparency_stream(request.country_iso3, request.lang_type),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# Language instruction injected into the prompt for ORI briefings
_ORI_LANGUAGE_INSTRUCTION = """

IMPORTANT — ORIGINAL LANGUAGE MODE:
The policy documents provided are in their original language (not English).
- You MUST write the entire transparency briefing in the same language as the source documents.
- Use original-language document titles (name_orig) for citations.
- All section headings, analysis, and recommendations should be in the original language.
- If documents span multiple languages, use the dominant language."""


async def _transparency_stream(country_iso3: str, lang_type: str = "ENG"):
    """Generator that builds context, calls the LLM, and yields SSE events."""
    use_ori = lang_type.upper() == "ORI"
    try:
        # 1. Resolve country name
        country_name = await resolve_country_name(country_iso3) or country_iso3
        lang_label = "original-language" if use_ori else "English"
        yield _sse({"type": "status", "data": f"Preparing {lang_label} transparency briefing for {country_name}..."})

        # 2. Fetch structured policy records (filtered by language)
        records = await fetch_records_with_docs(
            lang="ORI" if use_ori else "ENG",
            country=country_iso3,
        )
        policy_context = format_transparency_records_context(records)

        yield _sse({
            "type": "status",
            "data": f"Found {len(records)} {lang_label} policy records. Retrieving document context...",
        })

        # 3. Retrieve RAG document chunks for this country (filtered by language)
        try:
            filters = {"country": country_iso3}
            if use_ori:
                filters["lang_type"] = "ORI"
            retriever = get_retriever(filters=filters, k=20)
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

        # Inject language instruction for ORI briefings
        language_instruction = _ORI_LANGUAGE_INSTRUCTION if use_ori else ""

        async for chunk in chain.astream({
            "country_name": country_name,
            "policy_records_context": policy_context,
            "rag_context": rag_context + language_instruction,
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
