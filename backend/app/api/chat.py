"""
Chat API — main Q&A endpoint for the PIM AI Coach.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.generation.chains import rag_query, rag_query_stream
from app.ratelimit import chat_limiter

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


class ChatMessage(BaseModel):
    role: str = Field(description="'user' or 'assistant'")
    content: str


class ChatRequest(BaseModel):
    question: str = Field(description="The user's question")
    chat_history: list[ChatMessage] = Field(default_factory=list)
    filters: dict | None = Field(
        default=None,
        description=(
            "Optional metadata filters: "
            '{"country": "COL", "policy_guidance_tier": 3}'
        ),
    )
    stream: bool = Field(default=False, description="Enable streaming response")
    retriever_strategy: str | None = Field(
        default=None,
        description="Override retriever strategy for this request",
    )


class SourceDocument(BaseModel):
    content: str
    metadata: dict


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceDocument]


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, raw_request: Request):
    """Ask a question to the PIM AI Coach."""
    chat_limiter.check(raw_request)
    try:
        # Derive response language from lang_type filter
        response_language = None
        if request.filters and request.filters.get("lang_type") == "ORI":
            response_language = "ORI"

        if request.stream:
            return StreamingResponse(
                _stream_response(request, response_language),
                media_type="text/event-stream",
            )

        result = await rag_query(
            question=request.question,
            chat_history=[msg.model_dump() for msg in request.chat_history],
            filters=request.filters,
            retriever_strategy=request.retriever_strategy,
            response_language=response_language,
        )
        return ChatResponse(**result)

    except Exception as e:
        logger.exception("Chat error")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your question. Please try again.",
        )


async def _stream_response(request: ChatRequest, response_language: str | None = None):
    """Server-Sent Events stream for chat responses."""
    try:
        async for chunk in rag_query_stream(
            question=request.question,
            chat_history=[msg.model_dump() for msg in request.chat_history],
            filters=request.filters,
            retriever_strategy=request.retriever_strategy,
            response_language=response_language,
        ):
            yield f"data: {json.dumps(chunk)}\n\n"
    except Exception as e:
        logger.exception("Streaming error")
        error_event = {
            "type": "error",
            "data": "An error occurred while generating the answer. Please try again.",
        }
        yield f"data: {json.dumps(error_event)}\n\n"
