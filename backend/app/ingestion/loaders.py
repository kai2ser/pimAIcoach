"""
Document loaders — load PDF, DOCX, and TXT files into LangChain Documents.

Supports loading from local paths, URLs (Vercel Blob), or raw bytes.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import httpx
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}


def load_from_path(file_path: str | Path) -> list[Document]:
    """Load a document from a local file path."""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        loader = PyPDFLoader(str(path))
    elif ext in (".docx", ".doc"):
        loader = Docx2txtLoader(str(path))
    elif ext == ".txt":
        loader = TextLoader(str(path), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    return loader.load()


async def load_from_url(url: str, filename: str | None = None) -> list[Document]:
    """Download a document from a URL (e.g. Vercel Blob) and load it."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()

    ext = _guess_extension(url, filename)
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name

    docs = load_from_path(tmp_path)
    Path(tmp_path).unlink(missing_ok=True)
    return docs


def load_from_bytes(content: bytes, filename: str) -> list[Document]:
    """Load a document from raw bytes."""
    ext = Path(filename).suffix.lower()
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    docs = load_from_path(tmp_path)
    Path(tmp_path).unlink(missing_ok=True)
    return docs


def _guess_extension(url: str, filename: str | None) -> str:
    if filename:
        ext = Path(filename).suffix.lower()
        if ext in SUPPORTED_EXTENSIONS:
            return ext

    for ext in SUPPORTED_EXTENSIONS:
        if ext in url.lower():
            return ext

    return ".pdf"
