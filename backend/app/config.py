"""
Central configuration for the PIM AI Coach RAG pipeline.

All component choices (chunker, embeddings, vector store, retriever, LLM, etc.)
are configured here. Swap implementations by changing these values — no other
code changes required.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field


class RAGConfig(BaseSettings):
    """RAG pipeline configuration — each field maps to a swappable component."""

    # -- Ingestion / Chunking --------------------------------------------------
    chunker: str = Field(
        default="recursive",
        description="Chunking strategy: 'recursive' | 'semantic' | 'by_section'",
    )
    chunk_size: int = Field(default=1000, description="Target chunk size in characters")
    chunk_overlap: int = Field(default=200, description="Overlap between chunks")

    # -- Embeddings ------------------------------------------------------------
    embedding_model: str = Field(
        default="openai",
        description="Embedding provider: 'openai' | 'cohere' | 'huggingface'",
    )
    embedding_model_name: str = Field(
        default="text-embedding-3-small",
        description="Specific model name for the embedding provider",
    )

    # -- Vector Store ----------------------------------------------------------
    vector_store: str = Field(
        default="pgvector",
        description="Vector store backend: 'pgvector' | 'chroma' | 'faiss'",
    )
    collection_name: str = Field(
        default="pim_documents",
        description="Collection / table name in the vector store",
    )

    # -- Retrieval -------------------------------------------------------------
    retriever_type: str = Field(
        default="similarity",
        description="Retrieval strategy: 'similarity' | 'mmr' | 'self_query'",
    )
    retriever_k: int = Field(default=6, description="Number of documents to retrieve")
    retriever_score_threshold: float | None = Field(
        default=None,
        description="Minimum similarity score (0-1). None = no threshold.",
    )

    # -- Reranker (optional) ---------------------------------------------------
    reranker: str | None = Field(
        default=None,
        description="Reranking strategy: None | 'cohere' | 'cross_encoder'",
    )
    reranker_top_k: int = Field(
        default=4,
        description="Number of documents to keep after reranking",
    )

    # -- LLM / Generation ------------------------------------------------------
    llm_provider: str = Field(
        default="anthropic",
        description="LLM provider: 'anthropic' | 'openai' | 'ollama'",
    )
    llm_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Model identifier for the LLM provider",
    )
    llm_temperature: float = Field(default=0.2, description="LLM temperature")
    llm_max_tokens: int = Field(default=2048, description="Max tokens for LLM response")

    chain_type: str = Field(
        default="stuff",
        description="RAG chain type: 'stuff' | 'map_reduce' | 'refine'",
    )

    # -- Database (Neon / PostgreSQL) ------------------------------------------
    database_url: str = Field(
        default="",
        description="PostgreSQL connection string (Neon)",
    )

    # -- API Keys --------------------------------------------------------------
    openai_api_key: str = Field(default="", description="OpenAI API key")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    cohere_api_key: str = Field(default="", description="Cohere API key (optional)")

    # -- Vercel Blob (document source) -----------------------------------------
    blob_read_write_token: str = Field(
        default="",
        description="Vercel Blob token to access stored documents",
    )

    model_config = {
        "env_prefix": "PIM_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton instance — import this throughout the app
settings = RAGConfig()
