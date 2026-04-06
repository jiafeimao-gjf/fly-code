"""MiniMax model client."""

import os
import httpx
from typing import Optional

from core.models.base import AIModel, AIResponse


class MiniMaxModel(AIModel):
    """MiniMax AI API client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "abab6.5s-chat",
        base_url: str = "https://api.minimax.chat/v1",
    ):
        self.api_key = api_key or os.environ.get("MINIMAX_API_KEY", "")
        self.model = model
        self.base_url = base_url

    @property
    def name(self) -> str:
        return f"minimax:{self.model}"

    def set_api_key(self, api_key: str) -> None:
        """Set MiniMax API key."""
        self.api_key = api_key

    def complete(
        self,
        prompt: str,
        system: str = "",
        tools: list[dict] | None = None,
        **kwargs,
    ) -> AIResponse:
        """Generate completion using MiniMax."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        return self.chat(messages, system=system, tools=tools, **kwargs)

    def chat(
        self,
        messages: list[dict],
        system: str = "",
        tools: list[dict] | None = None,
        **kwargs,
    ) -> AIResponse:
        """Generate chat response using MiniMax."""
        if not self.api_key:
            raise ValueError("MiniMax API key not set")

        all_messages = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": all_messages,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools

        try:
            response = httpx.post(
                f"{self.base_url}/text/chatcompletion_v2",
                headers=headers,
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()

            return AIResponse(
                content=data["choices"][0]["message"]["content"],
                model=self.name,
                usage=data.get("usage", {}),
                finish_reason=data["choices"][0].get("finish_reason"),
            )
        except httpx.HTTPError as e:
            raise RuntimeError(f"MiniMax request failed: {e}")
