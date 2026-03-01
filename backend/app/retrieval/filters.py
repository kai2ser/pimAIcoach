"""
Metadata filter construction — translate user-facing filter dicts into
vector-store-compatible filter expressions.

Supports both simple equality and range filters.
"""

from __future__ import annotations

# Valid filterable fields and their types
FILTERABLE_FIELDS = {
    "country": str,
    "country_name": str,
    "policy_guidance_tier": int,
    "strategy_tier": int,
    "year": int,
    "source": str,
    "lang_type": str,
    "record_id": str,
}


def build_metadata_filter(filters: dict) -> dict:
    """
    Build a metadata filter dict compatible with LangChain vector stores.

    Accepts:
        {"country": "COL"}                          → exact match
        {"country": ["COL", "KEN"]}                  → in-list ($in)
        {"year": {"$gte": 2020}}                     → range filter
        {"year_from": 2020, "year_to": 2025}         → converted to year range
        {"country": "COL", "policy_guidance_tier": 3} → AND of conditions

    Returns a dict passable to vector store search_kwargs["filter"].
    """
    result = {}

    # Handle year_from / year_to convenience keys from the frontend
    year_from = filters.get("year_from")
    year_to = filters.get("year_to")
    if year_from is not None or year_to is not None:
        year_range = {}
        if year_from is not None:
            year_range["$gte"] = int(year_from)
        if year_to is not None:
            year_range["$lte"] = int(year_to)
        result["year"] = year_range

    for key, value in filters.items():
        if key in ("year_from", "year_to"):
            continue  # Already handled above
        if key not in FILTERABLE_FIELDS:
            continue

        if isinstance(value, list):
            result[key] = {"$in": value}
        elif isinstance(value, dict):
            # Pass through operator dicts like {"$gte": 2020}
            result[key] = value
        else:
            result[key] = value

    return result


def parse_filter_params(
    country: str | list[str] | None = None,
    tier: int | list[int] | None = None,
    strategy: int | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    lang: str | None = None,
) -> dict | None:
    """
    Convert API query parameters into a metadata filter dict.

    Returns None if no filters are specified.
    """
    filters = {}

    if country:
        filters["country"] = country if isinstance(country, list) else country

    if tier is not None:
        filters["policy_guidance_tier"] = tier if isinstance(tier, list) else tier

    if strategy is not None:
        filters["strategy_tier"] = strategy

    if year_from is not None and year_to is not None:
        filters["year"] = {"$gte": year_from, "$lte": year_to}
    elif year_from is not None:
        filters["year"] = {"$gte": year_from}
    elif year_to is not None:
        filters["year"] = {"$lte": year_to}

    if lang:
        filters["lang_type"] = lang

    return filters if filters else None
