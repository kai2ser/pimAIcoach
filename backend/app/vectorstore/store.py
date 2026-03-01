"""
Vector store factory — swap backends via config.

Supported backends:
  - "pgvector" : PostgreSQL + pgvector (Neon) — recommended, shared DB
  - "chroma"   : ChromaDB (local or server)
  - "faiss"    : FAISS (local, in-memory / file-backed)
"""

from __future__ import annotations

from functools import lru_cache

from langchain_core.vectorstores import VectorStore

from app.config import settings
from app.vectorstore.embeddings import get_embeddings


@lru_cache(maxsize=1)
def get_vector_store(
    backend: str | None = None,
    collection_name: str | None = None,
) -> VectorStore:
    """Return a vector store instance based on config."""
    backend = backend or settings.vector_store
    collection_name = collection_name or settings.collection_name
    embeddings = get_embeddings()

    if backend == "pgvector":
        return _create_pgvector(embeddings, collection_name)

    if backend == "chroma":
        return _create_chroma(embeddings, collection_name)

    if backend == "faiss":
        return _create_faiss(embeddings)

    raise ValueError(
        f"Unknown vector store '{backend}'. "
        "Available: 'pgvector', 'chroma', 'faiss'"
    )


def _create_pgvector(embeddings, collection_name: str) -> VectorStore:
    from langchain_postgres import PGVector

    return PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=settings.database_url,
        use_jsonb=True,
    )


def _create_chroma(embeddings, collection_name: str) -> VectorStore:
    from langchain_chroma import Chroma

    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory="./chroma_db",
    )


def _create_faiss(embeddings) -> VectorStore:
    from langchain_community.vectorstores import FAISS

    # FAISS requires initialization with at least one document
    # Return an empty store that can be added to
    return FAISS.from_texts(
        texts=["initialization"],
        embedding=embeddings,
        metadatas=[{"_init": True}],
    )
