"""Task management endpoints."""

import uuid
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import TaskRepository
from app.db.session import get_db

logger = structlog.get_logger()

router = APIRouter()


class TaskCreate(BaseModel):
    """Request model for creating a task."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(None, max_length=5000)
    due_date: datetime | None = None
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")


class TaskUpdate(BaseModel):
    """Request model for updating a task."""

    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = Field(None, max_length=5000)
    status: str | None = Field(None, pattern="^(pending|in_progress|completed|cancelled)$")
    priority: str | None = Field(None, pattern="^(low|medium|high)$")
    due_date: datetime | None = None


class TaskResponse(BaseModel):
    """Response model for a task."""

    id: str
    user_id: str
    title: str
    description: str | None
    status: str
    priority: str
    due_date: str | None
    completed_at: str | None
    created_at: str
    updated_at: str


class TaskListResponse(BaseModel):
    """Response model for listing tasks."""

    tasks: list[TaskResponse]
    total: int


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> TaskListResponse:
    """List tasks for the current user."""
    # For MVP, we'll use a placeholder user ID
    user_id = uuid.uuid4()

    repo = TaskRepository(db)
    tasks = await repo.get_by_user(user_id, status=status_filter, limit=limit)

    return TaskListResponse(
        tasks=[
            TaskResponse(
                id=str(task.id),
                user_id=str(task.user_id),
                title=task.title,
                description=task.description,
                status=task.status,
                priority=task.priority,
                due_date=task.due_date.isoformat() if task.due_date else None,
                completed_at=task.completed_at.isoformat() if task.completed_at else None,
                created_at=task.created_at.isoformat(),
                updated_at=task.updated_at.isoformat(),
            )
            for task in tasks
        ],
        total=len(tasks),
    )


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    request: TaskCreate,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Create a new task."""
    # For MVP, we'll use a placeholder user ID
    user_id = uuid.uuid4()

    repo = TaskRepository(db)
    task = await repo.create(
        user_id=user_id,
        title=request.title,
        description=request.description,
        due_date=request.due_date,
        priority=request.priority,
    )

    logger.info("Task created", task_id=str(task.id))

    return TaskResponse(
        id=str(task.id),
        user_id=str(task.user_id),
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date.isoformat() if task.due_date else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Get a specific task by ID."""
    repo = TaskRepository(db)
    task = await repo.get_by_id(uuid.UUID(task_id))

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return TaskResponse(
        id=str(task.id),
        user_id=str(task.user_id),
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date.isoformat() if task.due_date else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    request: TaskUpdate,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Update a task."""
    repo = TaskRepository(db)
    task = await repo.get_by_id(uuid.UUID(task_id))

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    await db.flush()

    logger.info("Task updated", task_id=task_id)

    return TaskResponse(
        id=str(task.id),
        user_id=str(task.user_id),
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date.isoformat() if task.due_date else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a task."""
    repo = TaskRepository(db)
    deleted = await repo.delete(uuid.UUID(task_id))

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    logger.info("Task deleted", task_id=task_id)
