"""Conversation management endpoints."""

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import ConversationRepository
from app.db.session import get_db

logger = structlog.get_logger()

router = APIRouter()


class ConversationCreate(BaseModel):
    """Request model for creating a conversation."""

    title: str | None = None


class ConversationResponse(BaseModel):
    """Response model for a conversation."""

    id: str
    user_id: str
    title: str | None
    created_at: str
    updated_at: str
    message_count: int = 0


class ConversationListResponse(BaseModel):
    """Response model for listing conversations."""

    conversations: list[ConversationResponse]
    total: int


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> ConversationListResponse:
    """List all conversations for the current user."""
    # For MVP, we'll use a placeholder user ID
    # In production, this should come from authentication
    user_id = uuid.uuid4()

    repo = ConversationRepository(db)
    conversations = await repo.get_by_user(user_id, limit=limit, offset=offset)

    return ConversationListResponse(
        conversations=[
            ConversationResponse(
                id=str(conv.id),
                user_id=str(conv.user_id),
                title=conv.title,
                created_at=conv.created_at.isoformat(),
                updated_at=conv.updated_at.isoformat(),
                message_count=len(conv.messages),
            )
            for conv in conversations
        ],
        total=len(conversations),
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """Get a specific conversation by ID."""
    repo = ConversationRepository(db)
    conversation = await repo.get_by_id(uuid.UUID(conversation_id))

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return ConversationResponse(
        id=str(conversation.id),
        user_id=str(conversation.user_id),
        title=conversation.title,
        created_at=conversation.created_at.isoformat(),
        updated_at=conversation.updated_at.isoformat(),
        message_count=len(conversation.messages),
    )


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: ConversationCreate,
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """Create a new conversation."""
    # For MVP, we'll use a placeholder user ID
    user_id = uuid.uuid4()

    repo = ConversationRepository(db)
    conversation = await repo.create(user_id=user_id, title=request.title)

    logger.info("Conversation created", conversation_id=str(conversation.id))

    return ConversationResponse(
        id=str(conversation.id),
        user_id=str(conversation.user_id),
        title=conversation.title,
        created_at=conversation.created_at.isoformat(),
        updated_at=conversation.updated_at.isoformat(),
        message_count=0,
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a conversation."""
    repo = ConversationRepository(db)
    deleted = await repo.delete(uuid.UUID(conversation_id))

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    logger.info("Conversation deleted", conversation_id=conversation_id)
