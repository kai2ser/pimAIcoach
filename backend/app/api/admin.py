"""
Admin API — runtime configuration inspection and updates.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.auth import require_api_key
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["admin"], dependencies=[Depends(require_api_key)])


class RAGConfigResponse(BaseModel):
    chunker: str
    chunk_size: int
    chunk_overlap: int
    embedding_model: str
    embedding_model_name: str
    vector_store: str
    collection_name: str
    retriever_type: str
    retriever_k: int
    retriever_score_threshold: float | None
    reranker: str | None
    reranker_top_k: int
    llm_provider: str
    llm_model: str
    llm_temperature: float
    llm_max_tokens: int
    chain_type: str


class RAGConfigUpdate(BaseModel):
    """Partial update — only include fields you want to change."""

    chunker: str | None = None
    chunk_size: int | None = None
    chunk_overlap: int | None = None
    embedding_model: str | None = None
    embedding_model_name: str | None = None
    vector_store: str | None = None
    retriever_type: str | None = None
    retriever_k: int | None = None
    retriever_score_threshold: float | None = None
    reranker: str | None = None
    reranker_top_k: int | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_temperature: float | None = None
    llm_max_tokens: int | None = None
    chain_type: str | None = None


@router.get("/config", response_model=RAGConfigResponse)
async def get_config():
    """Return the current RAG pipeline configuration."""
    return RAGConfigResponse(
        chunker=settings.chunker,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        embedding_model=settings.embedding_model,
        embedding_model_name=settings.embedding_model_name,
        vector_store=settings.vector_store,
        collection_name=settings.collection_name,
        retriever_type=settings.retriever_type,
        retriever_k=settings.retriever_k,
        retriever_score_threshold=settings.retriever_score_threshold,
        reranker=settings.reranker,
        reranker_top_k=settings.reranker_top_k,
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
        llm_temperature=settings.llm_temperature,
        llm_max_tokens=settings.llm_max_tokens,
        chain_type=settings.chain_type,
    )


@router.put("/config", response_model=RAGConfigResponse)
async def update_config(update: RAGConfigUpdate):
    """
    Update RAG pipeline configuration at runtime.

    Note: Changes to embedding_model or vector_store require re-ingestion
    of documents. This endpoint updates the in-memory config only.
    """
    # Clear cached instances so factories create new ones
    from app.vectorstore.embeddings import get_embeddings
    from app.vectorstore.store import get_vector_store
    from app.generation.llm import get_llm

    updated_fields = update.model_dump(exclude_none=True)

    for field, value in updated_fields.items():
        if hasattr(settings, field):
            object.__setattr__(settings, field, value)

    # Clear LRU caches if relevant fields changed
    cache_breaking_fields = {
        "embedding_model", "embedding_model_name",
        "vector_store", "collection_name",
        "llm_provider", "llm_model", "llm_temperature", "llm_max_tokens",
    }
    if cache_breaking_fields & set(updated_fields.keys()):
        get_embeddings.cache_clear()
        get_vector_store.cache_clear()
        get_llm.cache_clear()

    logger.info("Config updated: %s", list(updated_fields.keys()))
    return await get_config()
