"""AI client integration - wraps the new models module for backwards compatibility."""

from core.models import get_model, MODEL_REGISTRY, AIModel, AIResponse as BaseAIResponse
from core.models.ollama_model import OllamaClient
from core.models.minimax_model import MiniMaxModel
from utils.logger import logger


# Backwards compatibility alias
class AIResponse(BaseAIResponse):
    """Response from AI client (backwards compatibility)."""
    pass


class AIClientManager:
    """Manages AI client connections - backwards compatibility wrapper."""

    def __init__(self):
        self.clients: dict[str, AIModel] = {}
        self.active_provider: str | None = None

    def add_client(self, name: str, client: AIModel) -> None:
        """Add an AI client."""
        self.clients[name] = client
        if self.active_provider is None:
            self.active_provider = name
        logger.info(f"Added AI provider: {name}")

    def set_active(self, name: str) -> bool:
        """Set active AI provider."""
        if name not in self.clients:
            logger.error(f"Unknown provider: {name}")
            return False
        self.active_provider = name
        logger.info(f"Switched to AI provider: {name}")
        return True

    def get_active(self) -> AIModel | None:
        """Get active AI client."""
        if self.active_provider:
            return self.clients.get(self.active_provider)
        return None

    def complete(self, prompt: str, system: str | None = None) -> AIResponse:
        """Generate completion using active client."""
        client = self.get_active()
        if client is None:
            raise RuntimeError("No AI provider configured.")
        return client.complete(prompt, system or "")

    def chat(self, messages: list[dict], system: str | None = None) -> AIResponse:
        """Generate chat using active client."""
        client = self.get_active()
        if client is None:
            raise RuntimeError("No AI provider configured.")
        return client.chat(messages, system or "")

    def list_providers(self) -> list[str]:
        """List available providers."""
        return list(self.clients.keys())


# Global AI manager instance
ai_manager = AIClientManager()


def setup_default_providers() -> None:
    """Set up default AI providers."""
    # Ollama (local)
    try:
        ollama = OllamaClient()
        models = ollama.list_models()
        if models:
            ollama.model = models[0]
            ai_manager.add_client("ollama", ollama)
            logger.info(f"Ollama connected. Models: {models}")
        else:
            logger.warning("Ollama running but no models found")
    except ConnectionError as e:
        logger.warning(f"Ollama not available: {e}")

    # MiniMax (cloud)
    import os
    api_key = os.environ.get("MINIMAX_API_KEY", "")
    if api_key:
        minimax = MiniMaxModel(api_key=api_key)
        ai_manager.add_client("minimax", minimax)
        logger.info("MiniMax API configured")
    else:
        logger.warning("MINIMAX_API_KEY not set. MiniMax not available.")


setup_default_providers()
