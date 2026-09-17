"""Task management tool for creating and managing user tasks."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.db.repositories import TaskRepository
from app.tools.registry import (
    BaseTool,
    RiskLevel,
    ToolContext,
    ToolMetadata,
    ToolResult,
)


class CreateTaskInput(BaseModel):
    """Input schema for create_task tool."""

    title: str = Field(..., description="Task title", min_length=1, max_length=500)
    description: str | None = Field(None, description="Task description", max_length=5000)
    due_date: datetime | None = Field(None, description="Due date for the task")
    priority: str = Field(
        default="medium",
        description="Task priority: low, medium, high",
    )


class TaskTool(BaseTool):
    """Tool for task management operations."""

    def __init__(self, task_repository: TaskRepository):
        super().__init__()
        self._task_repository = task_repository

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="create_task",
            description="Create a new task for the user. Use this when the user wants to remember something to do later or plans an action.",
            requires_confirmation=False,
            risk_level=RiskLevel.LOW,
            reversible=True,
            timeout_seconds=10,
            max_retries=2,
        )

    @property
    def input_schema(self) -> type[BaseModel]:
        return CreateTaskInput

    async def _execute(
        self,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        """Create a new task."""
        try:
            # Parse and validate input
            task_input = CreateTaskInput(**arguments)

            # Create task in database
            task = await self._task_repository.create(
                user_id=context.user_id,
                title=task_input.title,
                description=task_input.description,
                due_date=task_input.due_date,
                priority=task_input.priority,
            )

            return ToolResult.ok(
                data={
                    "task_id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "priority": task.priority,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "created_at": task.created_at.isoformat(),
                },
                metadata={
                    "operation": "create_task",
                    "task_id": str(task.id),
                },
            )

        except Exception as e:
            return ToolResult.fail(
                error=f"Failed to create task: {str(e)}",
                metadata={"operation": "create_task"},
            )


class GetTasksTool(BaseTool):
    """Tool for retrieving user tasks."""

    def __init__(self, task_repository: TaskRepository):
        super().__init__()
        self._task_repository = task_repository

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_tasks",
            description="Retrieve tasks for the user. Can filter by status.",
            requires_confirmation=False,
            risk_level=RiskLevel.LOW,
            reversible=True,
            timeout_seconds=10,
            max_retries=2,
        )

    async def _execute(
        self,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        """Get user tasks."""
        try:
            status = arguments.get("status")
            limit = arguments.get("limit", 50)

            tasks = await self._task_repository.get_by_user(
                user_id=context.user_id,
                status=status,
                limit=limit,
            )

            return ToolResult.ok(
                data={
                    "tasks": [
                        {
                            "id": str(task.id),
                            "title": task.title,
                            "description": task.description,
                            "status": task.status,
                            "priority": task.priority,
                            "due_date": task.due_date.isoformat() if task.due_date else None,
                            "created_at": task.created_at.isoformat(),
                        }
                        for task in tasks
                    ],
                    "count": len(tasks),
                },
                metadata={"operation": "get_tasks"},
            )

        except Exception as e:
            return ToolResult.fail(
                error=f"Failed to retrieve tasks: {str(e)}",
                metadata={"operation": "get_tasks"},
            )


def create_task_tools(task_repository: TaskRepository) -> list[BaseTool]:
    """Create and return all task-related tools."""
    return [
        TaskTool(task_repository),
        GetTasksTool(task_repository),
    ]
