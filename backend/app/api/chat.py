"""
Chat API — main Q&A endpoint for the PIM AI Coach.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.generation.chains import rag_query, rag_query_stream

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
async def chat(request: ChatRequest):
    """Ask a question to the PIM AI Coach."""
    try:
        if request.stream:
            return StreamingResponse(
                _stream_response(request),
                media_type="text/event-stream",
            )

        result = await rag_query(
            question=request.question,
            chat_history=[msg.model_dump() for msg in request.chat_history],
            filters=request.filters,
            retriever_strategy=request.retriever_strategy,
        )
        return ChatResponse(**result)

    except Exception as e:
        logger.exception("Chat error")
        raise HTTPException(status_code=500, detail=str(e))


async def _stream_response(request: ChatRequest):
    """Server-Sent Events stream for chat responses."""
    async for chunk in rag_query_stream(
        question=request.question,
        chat_history=[msg.model_dump() for msg in request.chat_history],
        filters=request.filters,
        retriever_strategy=request.retriever_strategy,
    ):
        yield f"data: {json.dumps(chunk)}\n\n"
