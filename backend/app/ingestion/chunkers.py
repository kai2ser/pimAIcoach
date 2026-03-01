"""
Chunking strategies — split documents into chunks for embedding.

Strategies are selected via config.chunker:
  - "recursive"   : RecursiveCharacterTextSplitter (default, general-purpose)
  - "semantic"    : SemanticChunker (groups by embedding similarity)
  - "by_section"  : Splits on headings/section markers common in policy docs
"""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)

from app.config import settings


def get_chunker(strategy: str | None = None):
    """Factory: return a chunker callable based on the strategy name."""
    strategy = strategy or settings.chunker
    chunkers = {
        "recursive": _recursive_chunker,
        "semantic": _semantic_chunker,
        "by_section": _section_chunker,
    }
    if strategy not in chunkers:
        raise ValueError(
            f"Unknown chunker '{strategy}'. Available: {list(chunkers.keys())}"
        )
    return chunkers[strategy]


def chunk_documents(
    documents: list[Document], strategy: str | None = None
) -> list[Document]:
    """Split documents into chunks using the configured strategy."""
    chunker = get_chunker(strategy)
    return chunker(documents)


def _recursive_chunker(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    chunks = splitter.split_documents(documents)
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
    return chunks


def _semantic_chunker(documents: list[Document]) -> list[Document]:
    """Semantic chunking — groups consecutive sentences by embedding similarity."""
    from langchain_experimental.text_splitter import SemanticChunker
    from app.vectorstore.embeddings import get_embeddings

    embeddings = get_embeddings()
    splitter = SemanticChunker(
        embeddings,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=75,
    )
    chunks = splitter.split_documents(documents)
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
    return chunks


def _section_chunker(documents: list[Document]) -> list[Document]:
    """Section-based chunking — splits on markdown-style headings, then
    applies recursive splitting to sections that exceed chunk_size."""
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "heading_1"),
            ("##", "heading_2"),
            ("###", "heading_3"),
        ],
        strip_headers=False,
    )

    all_chunks = []
    recursive = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    for doc in documents:
        sections = header_splitter.split_text(doc.page_content)
        for section in sections:
            section.metadata.update(doc.metadata)

        sub_chunks = recursive.split_documents(sections)
        for i, chunk in enumerate(sub_chunks):
            chunk.metadata["chunk_index"] = i
        all_chunks.extend(sub_chunks)

    return all_chunks
