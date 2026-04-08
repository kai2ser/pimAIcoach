"""
Reranking strategies — optionally reorder retrieved documents for relevance.

Strategies (selected via config.reranker):
  - None             : No reranking (default)
  - "cohere"         : Cohere Rerank API
  - "cross_encoder"  : Local cross-encoder model (sentence-transformers)
"""

from __future__ import annotations

from functools import lru_cache

from langchain_core.documents import Document

from app.config import settings


def rerank(
    query: str,
    documents: list[Document],
    strategy: str | None = None,
    top_k: int | None = None,
) -> list[Document]:
    """Rerank documents using the configured strategy."""
    strategy = strategy if strategy is not None else settings.reranker
    top_k = top_k or settings.reranker_top_k

    if strategy is None:
        return documents[:top_k]

    if strategy == "cohere":
        return _cohere_rerank(query, documents, top_k)

    if strategy == "cross_encoder":
        return _cross_encoder_rerank(query, documents, top_k)

    raise ValueError(
        f"Unknown reranker '{strategy}'. Available: None, 'cohere', 'cross_encoder'"
    )


def _cohere_rerank(
    query: str, documents: list[Document], top_k: int
) -> list[Document]:
    from langchain_cohere import CohereRerank

    reranker = CohereRerank(
        cohere_api_key=settings.cohere_api_key,
        top_n=top_k,
        model="rerank-english-v3.0",
    )
    results = reranker.compress_documents(documents, query)
    return list(results)


@lru_cache(maxsize=1)
def _get_cross_encoder():
    from sentence_transformers import CrossEncoder
    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def _cross_encoder_rerank(
    query: str, documents: list[Document], top_k: int
) -> list[Document]:
    model = _get_cross_encoder()
    pairs = [(query, doc.page_content) for doc in documents]
    scores = model.predict(pairs)

    scored_docs = sorted(
        zip(scores, documents), key=lambda x: x[0], reverse=True
    )
    return [doc for _, doc in scored_docs[:top_k]]
