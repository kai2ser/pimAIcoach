"""
Metadata enrichment — attach PIM-domain metadata to document chunks.

Each chunk inherits metadata from its parent policy record (country, tier,
year, source, language) so that retrieval can filter on these fields.
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.documents import Document


@dataclass
class PolicyMetadata:
    """Metadata from a pimrepository policy_record row."""

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
    lang_type: str | None = None  # "ENG" or "ORI"
    lang_code: str | None = None
    overview: str | None = None
    link: str | None = None
    pages: int | None = None
    tokens: int | None = None


def enrich_chunks(
    chunks: list[Document],
    metadata: PolicyMetadata,
) -> list[Document]:
    """Attach policy-level metadata to every chunk."""
    meta_dict = _metadata_to_dict(metadata)
    total_chunks = len(chunks)

    for chunk in chunks:
        chunk.metadata.update(meta_dict)
        chunk.metadata["total_chunks"] = total_chunks

    return chunks


def _metadata_to_dict(meta: PolicyMetadata) -> dict:
    """Convert PolicyMetadata to a flat dict, dropping None values."""
    return {k: v for k, v in meta.__dict__.items() if v is not None}


# Metadata field descriptions for the SelfQueryRetriever
METADATA_FIELD_INFO = [
    {
        "name": "country",
        "description": "ISO Alpha-3 country code (e.g. 'COL', 'KEN', 'ZAF')",
        "type": "string",
    },
    {
        "name": "country_name",
        "description": "Full country name (e.g. 'Colombia', 'Kenya')",
        "type": "string",
    },
    {
        "name": "policy_guidance_tier",
        "description": (
            "Policy tier: 1=Primary Legislation, 2=Secondary Regulations, "
            "3=Procedural Guidelines, 4=Strategies for Project Prioritization"
        ),
        "type": "integer",
    },
    {
        "name": "strategy_tier",
        "description": (
            "Strategy classification (only when policy_guidance_tier=4): "
            "1=National Long Term, 2=Medium Term, 3=Sectoral, "
            "4=Cross-Cutting Climate, 5=Cross-Cutting Other, 6=Sub-National"
        ),
        "type": "integer",
    },
    {
        "name": "year",
        "description": "Publication year of the policy document",
        "type": "integer",
    },
    {
        "name": "source",
        "description": "Issuing body or agency (e.g. 'National Treasury')",
        "type": "string",
    },
    {
        "name": "lang_type",
        "description": "Language version: 'ENG' for English, 'ORI' for original language",
        "type": "string",
    },
    {
        "name": "name_eng",
        "description": "English title of the policy document",
        "type": "string",
    },
]
