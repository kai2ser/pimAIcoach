"""
Retriever factory — swap retrieval strategies via config.

Strategies:
  - "similarity"  : Standard similarity search
  - "mmr"         : Maximal Marginal Relevance (diversity + relevance)
  - "self_query"  : LLM-powered metadata filter extraction from natural language
"""

from __future__ import annotations

from langchain_core.retrievers import BaseRetriever

from app.config import settings
from app.vectorstore.store import get_vector_store
from app.retrieval.filters import build_metadata_filter


def get_retriever(
    strategy: str | None = None,
    filters: dict | None = None,
    k: int | None = None,
) -> BaseRetriever:
    """
    Build a retriever with the given strategy and optional metadata filters.

    Args:
        strategy: Override config retriever_type
        filters: Explicit metadata filters (e.g. {"country": "COL"})
        k: Number of documents to retrieve
    """
    strategy = strategy or settings.retriever_type
    k = k or settings.retriever_k
    store = get_vector_store()

    if strategy == "similarity":
        return _similarity_retriever(store, filters, k)

    if strategy == "mmr":
        return _mmr_retriever(store, filters, k)

    if strategy == "self_query":
        return _self_query_retriever(store, k)

    raise ValueError(
        f"Unknown retriever '{strategy}'. "
        "Available: 'similarity', 'mmr', 'self_query'"
    )


def _similarity_retriever(
    store, filters: dict | None, k: int
) -> BaseRetriever:
    search_kwargs = {"k": k}
    if filters:
        search_kwargs["filter"] = build_metadata_filter(filters)
    if settings.retriever_score_threshold is not None:
        search_kwargs["score_threshold"] = settings.retriever_score_threshold
        return store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs=search_kwargs,
        )
    return store.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs,
    )


def _mmr_retriever(store, filters: dict | None, k: int) -> BaseRetriever:
    search_kwargs = {"k": k, "fetch_k": k * 3, "lambda_mult": 0.7}
    if filters:
        search_kwargs["filter"] = build_metadata_filter(filters)
    return store.as_retriever(
        search_type="mmr",
        search_kwargs=search_kwargs,
    )


def _self_query_retriever(store, k: int) -> BaseRetriever:
    """Use an LLM to extract metadata filters from the user's query."""
    from langchain.retrievers.self_query.base import SelfQueryRetriever
    from langchain.chains.query_constructor.schema import AttributeInfo

    from app.generation.llm import get_llm
    from app.ingestion.metadata import METADATA_FIELD_INFO

    llm = get_llm()
    attribute_info = [
        AttributeInfo(**field) for field in METADATA_FIELD_INFO
    ]

    return SelfQueryRetriever.from_llm(
        llm=llm,
        vectorstore=store,
        document_contents=(
            "Public Investment Management policy documents including "
            "legislation, regulations, guidelines, and strategies from "
            "various countries."
        ),
        metadata_field_info=attribute_info,
        search_kwargs={"k": k},
    )
