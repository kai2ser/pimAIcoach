"""
RAG chain assembly — combines retrieval + generation into executable chains.

Chain types (selected via config.chain_type):
  - "stuff"      : Stuffs all retrieved docs into a single prompt (default)
  - "map_reduce" : Maps each doc through LLM, then reduces
  - "refine"     : Iteratively refines answer with each doc
"""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.config import settings
from app.generation.llm import get_llm
from app.generation.prompts import (
    get_rag_prompt,
    get_condense_prompt,
    format_documents,
    CONTEXT_INSTRUCTION_WITH_DOCS,
    CONTEXT_INSTRUCTION_NO_DOCS,
)
from app.retrieval.retriever import get_retriever
from app.retrieval.reranker import rerank

logger = logging.getLogger(__name__)

# ---------- Transient-error retry helpers ---------- #

# Exceptions that are worth retrying (timeouts, rate limits, connection errors)
_RETRYABLE_EXCEPTIONS = (
    TimeoutError,
    ConnectionError,
    OSError,
)

try:
    from httpx import HTTPStatusError, ConnectError, ReadTimeout

    _RETRYABLE_EXCEPTIONS += (HTTPStatusError, ConnectError, ReadTimeout)  # type: ignore[assignment]
except ImportError:
    pass

_llm_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)


async def _invoke_llm(chain, inputs: dict):
    """Invoke an LLM chain with retry logic for transient errors."""
    @_llm_retry
    async def _call():
        return await chain.ainvoke(inputs)

    return await _call()


async def _retrieve_docs(retriever, question: str):
    """Invoke the retriever in a thread to avoid blocking the event loop."""
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, retriever.invoke, question)
    except Exception as e:
        logger.exception("Retriever error for question: %s", question)
        raise RuntimeError("Failed to search the document store. Please try again.") from e


async def rag_query(
    question: str,
    chat_history: list[dict] | None = None,
    filters: dict | None = None,
    retriever_strategy: str | None = None,
) -> dict:
    """
    Execute a full RAG query: retrieve → (rerank) → generate.

    Returns:
        {
            "answer": str,
            "sources": [{"content": str, "metadata": dict}, ...],
        }
    """
    # Condense follow-up questions using chat history
    standalone_question = question
    lc_history = _convert_chat_history(chat_history)

    if lc_history:
        standalone_question = await _condense_question(question, lc_history)
        logger.info("Condensed question: %s", standalone_question)

    # Retrieve
    retriever = get_retriever(strategy=retriever_strategy, filters=filters)
    docs = await _retrieve_docs(retriever, standalone_question)
    logger.info("Retrieved %d documents", len(docs))

    # Rerank (if configured)
    if settings.reranker:
        docs = rerank(standalone_question, docs)
        logger.info("Reranked to %d documents", len(docs))

    # Generate
    context = format_documents(docs)
    context_instruction = (
        CONTEXT_INSTRUCTION_WITH_DOCS.format(context=context)
        if docs
        else CONTEXT_INSTRUCTION_NO_DOCS
    )

    prompt = get_rag_prompt()
    llm = get_llm()

    chain = prompt | llm
    response = await _invoke_llm(chain, {
        "context_instruction": context_instruction,
        "chat_history": lc_history,
        "question": question,
    })

    # Log token usage if available
    _log_token_usage(response, "rag_query")

    return {
        "answer": response.content,
        "sources": [
            {
                "content": doc.page_content[:300],
                "metadata": doc.metadata,
            }
            for doc in docs
        ],
    }


async def rag_query_stream(
    question: str,
    chat_history: list[dict] | None = None,
    filters: dict | None = None,
    retriever_strategy: str | None = None,
) -> AsyncIterator[dict]:
    """
    Streaming version of rag_query. Yields chunks as they are generated.

    Yields:
        {"type": "source", "data": {...}}  — for each retrieved source
        {"type": "token", "data": str}     — for each generated token
        {"type": "done"}                   — when generation is complete
    """
    standalone_question = question
    lc_history = _convert_chat_history(chat_history)

    if lc_history:
        standalone_question = await _condense_question(question, lc_history)

    retriever = get_retriever(strategy=retriever_strategy, filters=filters)
    docs = await _retrieve_docs(retriever, standalone_question)

    if settings.reranker:
        docs = rerank(standalone_question, docs)

    # Yield sources first
    for doc in docs:
        yield {
            "type": "source",
            "data": {
                "content": doc.page_content[:300],
                "metadata": doc.metadata,
            },
        }

    # Generate with streaming
    context = format_documents(docs)
    context_instruction = (
        CONTEXT_INSTRUCTION_WITH_DOCS.format(context=context)
        if docs
        else CONTEXT_INSTRUCTION_NO_DOCS
    )

    prompt = get_rag_prompt()
    llm = get_llm()
    chain = prompt | llm

    async for chunk in chain.astream({
        "context_instruction": context_instruction,
        "chat_history": lc_history,
        "question": question,
    }):
        if chunk.content:
            yield {"type": "token", "data": chunk.content}

    yield {"type": "done"}


async def _condense_question(
    question: str,
    chat_history: list,
) -> str:
    """Rephrase a follow-up question into a standalone question."""
    prompt = get_condense_prompt()
    llm = get_llm()
    chain = prompt | llm
    result = await _invoke_llm(chain, {
        "chat_history": chat_history,
        "question": question,
    })
    return result.content


def _log_token_usage(response, label: str = "llm_call") -> None:
    """Log token usage from LLM response metadata (if available)."""
    try:
        usage = getattr(response, "usage_metadata", None) or {}
        if not usage and hasattr(response, "response_metadata"):
            usage = response.response_metadata.get("usage", {})
        if usage:
            input_tokens = usage.get("input_tokens") or usage.get("prompt_tokens", 0)
            output_tokens = usage.get("output_tokens") or usage.get("completion_tokens", 0)
            total = input_tokens + output_tokens
            logger.info(
                "Token usage [%s]: input=%d output=%d total=%d",
                label, input_tokens, output_tokens, total,
            )
    except Exception:
        pass  # Never fail on telemetry


def _convert_chat_history(history: list[dict] | None) -> list:
    """Convert raw chat history dicts to LangChain message objects."""
    if not history:
        return []

    messages = []
    for msg in history:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    return messages
