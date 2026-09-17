"""Chat endpoints for conversational AI."""

import uuid
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message request model."""

    content: str = Field(..., min_length=1, max_length=10000)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    """Chat response model."""

    conversation_id: str
    message_id: str
    content: str
    sources: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatMessage,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    Process a chat message and return a response.

    This is the main entry point for user interactions with the AI assistant.
    """
    # For MVP, return a simple echo response
    # Full agent integration will be added in subsequent phases

    logger.info(
        "Chat request received",
        conversation_id=request.conversation_id,
        content_length=len(request.content),
    )

    # Generate response (placeholder - will be replaced with actual agent logic)
    response_content = f"I received your message: {request.content[:100]}..."

    return ChatResponse(
        conversation_id=request.conversation_id or str(uuid.uuid4()),
        message_id=str(uuid.uuid4()),
        content=response_content,
        sources=[],
    )


class StreamChatRequest(BaseModel):
    """Streaming chat request model."""

    content: str = Field(..., min_length=1, max_length=10000)
    conversation_id: str | None = None


@router.post("/chat/stream")
async def chat_stream(
    request: StreamChatRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Process a chat message with streaming response.

    Uses Server-Sent Events (SSE) to stream the response.
    """
    # Placeholder for streaming implementation
    # Will be implemented with proper agent integration
    raise HTTPException(
        status_code=501,
        detail="Streaming not yet implemented",
    )
