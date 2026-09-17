"""Database repositories for common operations."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    AuditLog,
    Conversation,
    Memory,
    Message,
    Task,
    ToolExecution,
    User,
)


class UserRepository:
    """Repository for User operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def create(self, email: str, hashed_password: str, **kwargs: Any) -> User:
        """Create a new user."""
        user = User(email=email, hashed_password=hashed_password, **kwargs)
        self.session.add(user)
        await self.session.flush()
        return user


class ConversationRepository:
    """Repository for Conversation operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, conversation_id: uuid.UUID) -> Conversation | None:
        """Get conversation by ID with messages loaded."""
        result = await self.session.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Conversation]:
        """Get conversations for a user."""
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, user_id: uuid.UUID, title: str | None = None) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(user_id=user_id, title=title)
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def update_title(self, conversation_id: uuid.UUID, title: str) -> None:
        """Update conversation title."""
        await self.session.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(title=title, updated_at=datetime.utcnow())
        )

    async def delete(self, conversation_id: uuid.UUID) -> bool:
        """Delete a conversation."""
        result = await self.session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            await self.session.delete(conversation)
            return True
        return False


class MessageRepository:
    """Repository for Message operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> Message:
        """Create a new message."""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata=metadata,
        )
        self.session.add(message)
        await self.session.flush()
        return message

    async def get_by_conversation(
        self,
        conversation_id: uuid.UUID,
        limit: int = 50,
    ) -> list[Message]:
        """Get messages for a conversation."""
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())


class TaskRepository:
    """Repository for Task operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, task_id: uuid.UUID) -> Task | None:
        """Get task by ID."""
        result = await self.session.execute(
            select(Task).where(Task.id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Task]:
        """Get tasks for a user."""
        query = select(Task).where(Task.user_id == user_id)
        if status:
            query = query.where(Task.status == status)
        query = query.order_by(Task.due_date.asc().nullslast(), Task.created_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        user_id: uuid.UUID,
        title: str,
        description: str | None = None,
        due_date: datetime | None = None,
        priority: str = "medium",
        **kwargs: Any,
    ) -> Task:
        """Create a new task."""
        task = Task(
            user_id=user_id,
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            **kwargs,
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def update_status(
        self,
        task_id: uuid.UUID,
        status: str,
        completed_at: datetime | None = None,
    ) -> None:
        """Update task status."""
        await self.session.execute(
            update(Task)
            .where(Task.id == task_id)
            .values(status=status, completed_at=completed_at, updated_at=datetime.utcnow())
        )

    async def delete(self, task_id: uuid.UUID) -> bool:
        """Delete a task."""
        result = await self.session.execute(
            select(Task).where(Task.id == task_id)
        )
        task = result.scalar_one_or_none()
        if task:
            await self.session.delete(task)
            return True
        return False


class MemoryRepository:
    """Repository for Memory operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        memory_type: str | None = None,
        limit: int = 100,
    ) -> list[Memory]:
        """Get memories for a user."""
        query = select(Memory).where(Memory.user_id == user_id)
        if memory_type:
            query = query.where(Memory.memory_type == memory_type)
        query = query.order_by(Memory.importance_score.desc(), Memory.created_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        user_id: uuid.UUID,
        content: str,
        memory_type: str,
        importance_score: float = 0.5,
        source: str | None = None,
        metadata: dict | None = None,
    ) -> Memory:
        """Create a new memory."""
        memory = Memory(
            user_id=user_id,
            content=content,
            memory_type=memory_type,
            importance_score=importance_score,
            source=source,
            metadata=metadata,
        )
        self.session.add(memory)
        await self.session.flush()
        return memory


class ToolExecutionRepository:
    """Repository for ToolExecution operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_execution(
        self,
        user_id: uuid.UUID,
        tool_name: str,
        tool_arguments: dict,
        tool_result: dict | None = None,
        status: str = "success",
        error_message: str | None = None,
        execution_time_ms: int | None = None,
        requires_confirmation: bool = False,
        confirmation_given: bool | None = None,
        conversation_id: uuid.UUID | None = None,
    ) -> ToolExecution:
        """Log a tool execution."""
        execution = ToolExecution(
            user_id=user_id,
            tool_name=tool_name,
            tool_arguments=tool_arguments,
            tool_result=tool_result,
            status=status,
            error_message=error_message,
            execution_time_ms=execution_time_ms,
            requires_confirmation=requires_confirmation,
            confirmation_given=confirmation_given,
            conversation_id=conversation_id,
        )
        self.session.add(execution)
        await self.session.flush()
        return execution


class AuditLogRepository:
    """Repository for AuditLog operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log(
        self,
        action: str,
        user_id: uuid.UUID | None = None,
        resource_type: str | None = None,
        resource_id: uuid.UUID | None = None,
        request_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict | None = None,
    ) -> AuditLog:
        """Create an audit log entry."""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
        )
        self.session.add(audit_log)
        await self.session.flush()
        return audit_log
