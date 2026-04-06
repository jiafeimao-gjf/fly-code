"""Ollama model client."""

import httpx
import json
from typing import Optional, Iterator

from core.models.base import AIModel, AIResponse


class OllamaModel(AIModel):
    """Ollama local LLM client."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "",
        timeout: int = 300,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._model: str = ""

        # Auto-select first available model if not specified
        if not model:
            model = self._select_first_available()

        self._model = model

    @property
    def model(self) -> str:
        """Current model name."""
        return self._model

    def switch_model(self, model_name: str) -> tuple[bool, str]:
        """Switch to a different model.

        Returns:
            (success, message)
        """
        # Verify the model exists
        available = self.list_models()
        if model_name not in available:
            return False, f"Model '{model_name}' not found. Available: {available}"

        self._model = model_name
        return True, f"Switched to model: {model_name}"

    def _select_first_available(self) -> str:
        """Select the first available model."""
        try:
            available = self.list_models()
            if available:
                return available[0]
        except Exception:
            pass
        return "llama3.2"  # Fallback

    @property
    def name(self) -> str:
        return f"ollama:{self._model}"

    def set_api_key(self, api_key: str) -> None:
        """Ollama doesn't need API key, no-op."""
        pass

    def complete(
        self,
        prompt: str,
        system: str = "",
        tools: list[dict] | None = None,
        **kwargs,
    ) -> AIResponse:
        """Generate completion using Ollama."""
        payload = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system
        if tools:
            payload["tools"] = tools

        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            return AIResponse(
                content=data.get("response", ""),
                model=self.name,
                usage={"done_reason": data.get("done_reason")},
            )
        except httpx.ConnectError:
            raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}")
        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama request failed: {e}")

    def chat(
        self,
        messages: list[dict],
        system: str = "",
        tools: list[dict] | None = None,
        **kwargs,
    ) -> AIResponse:
        """Generate chat response using Ollama.

        Note: The tools parameter is accepted for compatibility but not sent to Ollama
        because it causes issues with many models. Instead, the system prompt should
        instruct the model to output tool calls in JSON format.
        """
        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)

        payload = {
            "model": self._model,
            "messages": all_messages,
            "stream": False,
        }
        # Note: Not sending tools parameter as it causes issues with Ollama
        # The system prompt instructs the model to output JSON tool calls

        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            return AIResponse(
                content=data.get("message", {}).get("content", ""),
                model=self.name,
            )
        except httpx.ConnectError:
            raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}")
        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama request failed: {e}")

    def chat_stream(
        self,
        messages: list[dict],
        system: str = "",
        tools: list[dict] | None = None,
        **kwargs,
    ) -> Iterator[str]:
        """Generate streaming chat response using Ollama.

        Args:
            messages: List of message dicts with role and content
            system: System prompt
            tools: Not used for streaming

        Yields:
            Str chunks of the response
        """
        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)

        payload = {
            "model": self._model,
            "messages": all_messages,
            "stream": True,
        }

        try:
            with httpx.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
        except httpx.ConnectError:
            raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}")
        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama request failed: {e}")

    def list_models(self) -> list[str]:
        """List available Ollama models."""
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except httpx.ConnectError:
            raise ConnectionError(f"Cannot connect to Ollama at {self.base_url}")
