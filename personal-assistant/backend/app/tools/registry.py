"""Tool system for the AI Personal Assistant."""

import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from pydantic import BaseModel


class RiskLevel(str, Enum):
    """Risk levels for tool operations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ToolMetadata:
    """Metadata describing a tool's capabilities and requirements."""

    name: str
    description: str
    requires_confirmation: bool = False
    risk_level: RiskLevel = RiskLevel.LOW
    reversible: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3


@dataclass
class ToolContext:
    """Context passed to tools during execution."""

    user_id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    """Result from a tool execution."""

    success: bool
    data: Any | None = None
    error: str | None = None
    requires_confirmation: bool = False
    confirmation_details: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, data: Any | None = None, **kwargs: Any) -> "ToolResult":
        """Create a successful result."""
        return cls(success=True, data=data, **kwargs)

    @classmethod
    def fail(cls, error: str, **kwargs: Any) -> "ToolResult":
        """Create a failed result."""
        return cls(success=False, error=error, **kwargs)


class Tool(Protocol):
    """Protocol defining the tool interface."""

    metadata: ToolMetadata

    async def execute(
        self,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        """Execute the tool with given arguments."""
        ...


class BaseTool(ABC):
    """Base class for tools with common functionality."""

    def __init__(self):
        self._metadata: ToolMetadata | None = None

    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """Return tool metadata."""
        pass

    @abstractmethod
    async def _execute(
        self,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        """Implement tool-specific execution logic."""
        pass

    async def execute(
        self,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        """
        Execute the tool with validation and error handling.

        Args:
            arguments: Tool arguments
            context: Execution context

        Returns:
            ToolResult with success/failure status
        """
        start_time = time.time()

        try:
            # Validate arguments if schema is defined
            if hasattr(self, "input_schema") and self.input_schema:
                arguments = self._validate_arguments(arguments)

            # Execute tool-specific logic
            result = await self._execute(arguments, context)

            # Add execution time to metadata
            result.metadata["execution_time_ms"] = int((time.time() - start_time) * 1000)

            return result

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            return ToolResult.fail(
                error=str(e),
                metadata={"execution_time_ms": execution_time},
            )

    def _validate_arguments(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Validate arguments against input schema."""
        if hasattr(self, "input_schema") and self.input_schema:
            # Use Pydantic model if available
            if isinstance(self.input_schema, type) and issubclass(self.input_schema, BaseModel):
                return self.input_schema(**arguments).model_dump()
        return arguments

    def __str__(self) -> str:
        return f"Tool({self.metadata.name})"


class ToolRegistry:
    """Registry for managing available tools."""

    _instance: "ToolRegistry | None" = None
    _tools: dict[str, Tool]

    def __new__(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
        return cls._instance

    def register(self, tool: Tool) -> None:
        """Register a tool in the registry."""
        self._tools[tool.metadata.name] = tool

    def unregister(self, tool_name: str) -> bool:
        """Unregister a tool by name."""
        if tool_name in self._tools:
            del self._tools[tool_name]
            return True
        return False

    def get(self, tool_name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(tool_name)

    def list_tools(self) -> list[dict[str, Any]]:
        """List all registered tools with their metadata."""
        return [
            {
                "name": tool.metadata.name,
                "description": tool.metadata.description,
                "requires_confirmation": tool.metadata.requires_confirmation,
                "risk_level": tool.metadata.risk_level.value,
                "reversible": tool.metadata.reversible,
            }
            for tool in self._tools.values()
        ]

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()


# Global registry instance
tool_registry = ToolRegistry()
