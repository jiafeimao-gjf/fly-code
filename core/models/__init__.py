"""AI model clients."""

from core.models.base import AIModel, AIResponse
from core.models.ollama_model import OllamaModel
from core.models.minimax_model import MiniMaxModel

# Registry
MODEL_REGISTRY: dict[str, type[AIModel]] = {
    "ollama": OllamaModel,
    "minimax": MiniMaxModel,
}


def get_model(name: str, **kwargs) -> AIModel | None:
    """Get a model instance by name."""
    model_class = MODEL_REGISTRY.get(name)
    if model_class:
        return model_class(**kwargs)
    return None
