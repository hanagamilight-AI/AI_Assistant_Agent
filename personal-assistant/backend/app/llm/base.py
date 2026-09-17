"""LLM provider abstraction layer."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class LLMMessage:
    """Represents a message in a conversation."""

    role: str  # system, user, assistant
    content: str


@dataclass
class LLMResponse:
    """Response from an LLM provider."""

    content: str
    model: str
    usage: dict[str, int] | None = None
    finish_reason: str | None = None
    raw_response: Any = None


@dataclass
class StructuredResponse:
    """Structured response from an LLM with parsed data."""

    data: dict[str, Any]
    raw_content: str
    model: str
    usage: dict[str, int] | None = None


class LLMProvider(Protocol):
    """Protocol for LLM providers."""

    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        ...

    async def generate_structured(
        self,
        messages: list[LLMMessage],
        response_schema: dict[str, Any],
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> StructuredResponse:
        """Generate a structured response following a schema."""
        ...


class BaseLLMProvider(ABC):
    """Base class for LLM providers with common functionality."""

    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        self.api_key = api_key
        self.model = model
        self.default_temperature = temperature
        self.default_max_tokens = max_tokens

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        messages: list[LLMMessage],
        response_schema: dict[str, Any],
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> StructuredResponse:
        """Generate a structured response following a schema."""
        pass

    def _prepare_messages(
        self,
        messages: list[LLMMessage],
        system_prompt: str | None = None,
    ) -> list[dict[str, str]]:
        """Prepare messages for API call."""
        formatted_messages = []

        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})

        for msg in messages:
            formatted_messages.append({"role": msg.role, "content": msg.content})

        return formatted_messages
