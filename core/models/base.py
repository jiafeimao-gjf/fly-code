"""Base AI model interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Callable, Iterator


@dataclass
class AIResponse:
    """Response from AI model."""
    content: str
    model: str
    usage: Optional[dict] = None
    finish_reason: Optional[str] = None


class AIModel(ABC):
    """Abstract base class for AI models."""

    @abstractmethod
    def complete(
        self,
        prompt: str,
        system: str = "",
        tools: list[dict] | None = None,
        **kwargs,
    ) -> AIResponse:
        """Generate completion from prompt.

        Args:
            prompt: The user prompt
            system: System prompt
            tools: Optional list of tool schemas for tool use

        Returns:
            AIResponse with generated content
        """
        ...

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        system: str = "",
        tools: list[dict] | None = None,
        **kwargs,
    ) -> AIResponse:
        """Generate chat response.

        Args:
            messages: List of message dicts with role and content
            system: System prompt
            tools: Optional list of tool schemas for tool use

        Returns:
            AIResponse with generated content
        """
        ...

    def chat_stream(
        self,
        messages: list[dict],
        system: str = "",
        tools: list[dict] | None = None,
        **kwargs,
    ) -> Iterator[str]:
        """Generate streaming chat response.

        Args:
            messages: List of message dicts with role and content
            system: System prompt
            tools: Optional list of tool schemas for tool use

        Yields:
            Str chunks of the response
        """
        # Default: collect and yield at end
        response = self.chat(messages, system, tools, **kwargs)
        yield response.content

    @abstractmethod
    def set_api_key(self, api_key: str) -> None:
        """Set API key for the model."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Model name."""
        ...
