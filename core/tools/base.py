"""Base tool class and schemas."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    content: str
    error: str | None = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for AI consumption."""
        return {
            "success": self.success,
            "content": self.content,
            "error": self.error,
            "metadata": self.metadata,
        }


class BaseTool(ABC):
    """Abstract base class for all tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for AI."""
        ...

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """JSON schema for tool parameters."""
        ...

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        ...

    def get_schema(self) -> dict:
        """Get the full schema for AI tool calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
