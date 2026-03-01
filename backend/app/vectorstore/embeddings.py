"""
Embedding model factory — swap embedding providers via config.

Supported providers:
  - "openai"      : OpenAI text-embedding-3-small / text-embedding-3-large
  - "cohere"      : Cohere embed-english-v3.0
  - "huggingface" : Local HuggingFace sentence-transformers
"""

from __future__ import annotations

from functools import lru_cache

from langchain_core.embeddings import Embeddings

from app.config import settings


@lru_cache(maxsize=1)
def get_embeddings(
    provider: str | None = None,
    model_name: str | None = None,
) -> Embeddings:
    """Return an embeddings instance based on config."""
    provider = provider or settings.embedding_model
    model_name = model_name or settings.embedding_model_name

    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=model_name,
            openai_api_key=settings.openai_api_key,
        )

    if provider == "cohere":
        from langchain_cohere import CohereEmbeddings

        return CohereEmbeddings(
            model=model_name or "embed-english-v3.0",
            cohere_api_key=settings.cohere_api_key,
        )

    if provider == "huggingface":
        from langchain_huggingface import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(
            model_name=model_name or "sentence-transformers/all-MiniLM-L6-v2",
        )

    raise ValueError(
        f"Unknown embedding provider '{provider}'. "
        "Available: 'openai', 'cohere', 'huggingface'"
    )
