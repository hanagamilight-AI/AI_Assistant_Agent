"""OpenAI-compatible LLM provider implementation."""

import json
from typing import Any

import httpx

from app.llm.base import (
    BaseLLMProvider,
    LLMMessage,
    LLMResponse,
    StructuredResponse,
)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI-compatible LLM provider."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        base_url: str = "https://api.openai.com/v1",
    ):
        super().__init__(api_key, model, temperature, max_tokens)
        self.base_url = base_url.rstrip("/")

    async def generate(
        self,
        messages: list[LLMMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response from OpenAI API."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": self._prepare_messages(messages),
            "temperature": temperature or self.default_temperature,
            "max_tokens": max_tokens or self.default_max_tokens,
            **kwargs,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]
        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", self.model),
            usage=data.get("usage"),
            finish_reason=choice.get("finish_reason"),
            raw_response=data,
        )

    async def generate_structured(
        self,
        messages: list[LLMMessage],
        response_schema: dict[str, Any],
        temperature: float = 0.0,
        **kwargs: Any,
    ) -> StructuredResponse:
        """Generate a structured response using JSON mode."""
        # Add instruction for JSON output to system message
        schema_instruction = (
            f"\n\nIMPORTANT: Respond ONLY with valid JSON matching this schema:\n"
            f"{json.dumps(response_schema, indent=2)}\n\n"
            f"Do not include any text outside the JSON object."
        )

        # Append to last user message or create new one
        augmented_messages = messages.copy()
        if augmented_messages and augmented_messages[-1].role == "user":
            augmented_messages[-1] = LLMMessage(
                role="user",
                content=augmented_messages[-1].content + schema_instruction,
            )
        else:
            augmented_messages.append(LLMMessage(role="user", content=schema_instruction))

        # Try with JSON mode first (for OpenAI)
        try:
            response = await self.generate(
                messages=augmented_messages,
                temperature=temperature,
                response_format={"type": "json_object"},
                **kwargs,
            )
        except Exception:
            # Fallback without JSON mode
            response = await self.generate(
                messages=augmented_messages,
                temperature=temperature,
                **kwargs,
            )

        # Parse JSON response
        try:
            parsed_data = json.loads(response.content)
        except json.JSONDecodeError as e:
            # Try to extract JSON from response
            content = response.content.strip()
            if content.startswith("```json"):
                content = content.removeprefix("```json").removesuffix("```").strip()
            elif content.startswith("```"):
                content = content.removeprefix("```").removesuffix("```").strip()

            try:
                parsed_data = json.loads(content)
            except json.JSONDecodeError:
                raise ValueError(f"Failed to parse JSON response: {e}") from e

        return StructuredResponse(
            data=parsed_data,
            raw_content=response.content,
            model=response.model,
            usage=response.usage,
        )


def create_llm_provider(
    provider_name: str,
    api_key: str,
    model: str,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    **kwargs: Any,
) -> BaseLLMProvider:
    """
    Factory function to create an LLM provider.

    Args:
        provider_name: Name of the provider (openai, anthropic, local)
        api_key: API key for the provider
        model: Model identifier
        temperature: Default temperature
        max_tokens: Maximum tokens
        **kwargs: Additional provider-specific arguments

    Returns:
        Configured LLM provider instance

    Raises:
        ValueError: If provider_name is not supported
    """
    providers = {
        "openai": OpenAIProvider,
        # Add more providers here as they are implemented
        # "anthropic": AnthropicProvider,
        # "local": LocalProvider,
    }

    provider_class = providers.get(provider_name.lower())
    if not provider_class:
        raise ValueError(
            f"Unsupported LLM provider: {provider_name}. "
            f"Supported providers: {list(providers.keys())}"
        )

    return provider_class(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs,
    )
