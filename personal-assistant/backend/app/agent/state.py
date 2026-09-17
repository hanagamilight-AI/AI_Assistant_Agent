"""Agent state management and type definitions."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    """
    Explicit state object for the agent execution flow.

    This prevents arbitrary state mutation and ensures all state changes
    are tracked and intentional.
    """

    # Identity & Context
    user_id: str | None = None
    conversation_id: str | None = None
    request_id: str | None = None

    # Messages
    messages: list[dict[str, Any]] = field(default_factory=list)
    user_request: str = ""

    # Retrieved Information
    retrieved_context: list[dict[str, Any]] = field(default_factory=list)
    memories: list[dict[str, Any]] = field(default_factory=list)

    # Planning
    plan: list[dict[str, Any]] = field(default_factory=list)
    current_step: int = 0

    # Tool Execution
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)

    # Confirmation
    requires_confirmation: bool = False
    confirmation_reason: str | None = None
    confirmation_details: dict[str, Any] | None = None

    # Response
    final_response: str | None = None

    # Error Handling
    errors: list[str] = field(default_factory=list)

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str, **kwargs: Any) -> None:
        """Add a message to the conversation history."""
        message = {"role": role, "content": content}
        if kwargs:
            message["metadata"] = kwargs
        self.messages.append(message)

    def add_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> None:
        """Record a tool call."""
        self.tool_calls.append({
            "tool_name": tool_name,
            "arguments": arguments,
        })

    def add_tool_result(
        self,
        tool_name: str,
        success: bool,
        data: Any | None = None,
        error: str | None = None,
    ) -> None:
        """Record a tool execution result."""
        self.tool_results.append({
            "tool_name": tool_name,
            "success": success,
            "data": data,
            "error": error,
        })

    def add_error(self, error: str) -> None:
        """Add an error to the error list."""
        self.errors.append(error)

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    def get_last_user_message(self) -> str | None:
        """Get the last user message."""
        for message in reversed(self.messages):
            if message.get("role") == "user":
                return message.get("content")
        return None

    def get_conversation_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent conversation history."""
        return self.messages[-limit:] if self.messages else []

    def clear_plan(self) -> None:
        """Clear the current plan."""
        self.plan = []
        self.current_step = 0

    def next_step(self) -> int:
        """Move to the next step in the plan."""
        self.current_step += 1
        return self.current_step

    def is_complete(self) -> bool:
        """Check if the agent has completed its task."""
        return self.final_response is not None or self.has_errors()

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "request_id": self.request_id,
            "messages": self.messages,
            "user_request": self.user_request,
            "retrieved_context": self.retrieved_context,
            "memories": self.memories,
            "plan": self.plan,
            "current_step": self.current_step,
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results,
            "requires_confirmation": self.requires_confirmation,
            "confirmation_reason": self.confirmation_reason,
            "confirmation_details": self.confirmation_details,
            "final_response": self.final_response,
            "errors": self.errors,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentState":
        """Create state from dictionary."""
        return cls(**data)
