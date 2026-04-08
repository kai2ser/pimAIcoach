"""
Country PIM Institutional Profile API.

Endpoints:
  GET  /api/countries              — list all countries
  POST /api/country-profile        — generate a PIM institutional profile (SSE)
  POST /api/country-profile/export — export generated content as DOCX or PDF
"""

from __future__ import annotations

import json
import logging
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.export.docx_export import export_docx, PROFILE_THEME as DOCX_PROFILE_THEME
from app.export.pdf_export import export_pdf, PROFILE_THEME as PDF_PROFILE_THEME
from app.generation.profile_prompt import (
    format_policy_records_context,
    get_country_profile_prompt,
)
from app.generation.prompts import format_documents
from app.ingestion.repo_source import fetch_records_with_docs, resolve_country_name
from app.retrieval.retriever import get_retriever

logger = logging.getLogger(__name__)
router = APIRouter(tags=["country-profile"])

# Max tokens for long-form profile generation (higher than the chat default)
_PROFILE_MAX_TOKENS = 8192


# ── Models ────────────────────────────────────────────────────

class CountryProfileRequest(BaseModel):
    country_iso3: str = Field(description="ISO3 country code")


class ExportRequest(BaseModel):
    content: str = Field(description="The generated markdown content")
    country_name: str = Field(description="Country name for the document title")
    format: str = Field(description="'docx' or 'pdf'")


# ── Helpers ───────────────────────────────────────────────────

from app.api import sse_event as _sse


_profile_llm_cache = None

def _get_profile_llm():
    """Return a cached ChatAnthropic instance with higher max_tokens for profile generation."""
    global _profile_llm_cache
    if _profile_llm_cache is None:
        from langchain_anthropic import ChatAnthropic
        _profile_llm_cache = ChatAnthropic(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=_PROFILE_MAX_TOKENS,
            anthropic_api_key=settings.anthropic_api_key,
        )
    return _profile_llm_cache


# ── GET /api/countries ────────────────────────────────────────

_countries_cache: dict = {"data": None, "expires_at": 0.0}
_COUNTRIES_CACHE_TTL = 300  # 5 minutes


@router.get("/countries")
async def list_countries():
    """Return all countries derived from the policy repository API (cached 5m)."""
    now = time.monotonic()
    if _countries_cache["data"] is not None and now < _countries_cache["expires_at"]:
        return _countries_cache["data"]

    try:
        records = await fetch_records_with_docs(lang=None)
        seen: dict[str, str] = {}
        for r in records:
            iso3 = r.get("country")
            name = r.get("country_name") or iso3
            if iso3 and iso3 not in seen:
                seen[iso3] = name
        result = sorted(
            [{"iso3": k, "name": v} for k, v in seen.items()],
            key=lambda c: c["name"],
        )
        _countries_cache["data"] = result
        _countries_cache["expires_at"] = now + _COUNTRIES_CACHE_TTL
        return result
    except Exception:
        logger.exception("Failed to fetch countries")
        raise HTTPException(status_code=500, detail="Could not load countries")


# ── POST /api/country-profile ─────────────────────────────────

@router.post("/country-profile")
async def generate_country_profile(request: CountryProfileRequest):
    """Generate a PIM institutional profile and stream via SSE."""
    return StreamingResponse(
        _profile_stream(request.country_iso3),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _profile_stream(country_iso3: str):
    """Generator that builds context, calls the LLM, and yields SSE events."""
    try:
        # 1. Resolve country name
        country_name = await resolve_country_name(country_iso3) or country_iso3
        yield _sse({"type": "status", "data": f"Preparing profile for {country_name}..."})

        # 2. Fetch structured policy records
        records = await fetch_records_with_docs(country=country_iso3)
        policy_context = format_policy_records_context(records)

        yield _sse({
            "type": "status",
            "data": f"Found {len(records)} policy records. Retrieving document context...",
        })

        # 3. Retrieve RAG document chunks for this country
        try:
            retriever = get_retriever(filters={"country": country_iso3}, k=20)
            docs = retriever.invoke(
                f"Public investment management institutional framework for {country_name}"
            )
            rag_context = format_documents(docs) if docs else "No indexed documents found for this country."
            yield _sse({
                "type": "status",
                "data": f"Retrieved {len(docs)} document excerpts. Generating profile...",
            })
        except Exception as e:
            logger.warning("RAG retrieval failed for %s: %s", country_iso3, e)
            rag_context = "No indexed documents available."
            yield _sse({
                "type": "status",
                "data": "No indexed documents available. Generating from general knowledge...",
            })

        # 4. Build the prompt and stream the LLM response
        prompt = get_country_profile_prompt()
        llm = _get_profile_llm()
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
        logger.exception("Profile generation failed for %s", country_iso3)
        yield _sse({"type": "error", "data": str(e)})


# ── POST /api/country-profile/export ──────────────────────────

@router.post("/country-profile/export")
async def export_country_profile(request: ExportRequest):
    """Export a generated profile as DOCX or PDF."""
    if request.format == "docx":
        return export_docx(request.content, request.country_name, theme=DOCX_PROFILE_THEME)
    elif request.format == "pdf":
        return export_pdf(request.content, request.country_name, theme=PDF_PROFILE_THEME)
    else:
        raise HTTPException(status_code=400, detail="Format must be 'docx' or 'pdf'")
