from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from .config import ProviderConfig
from .providers import OpenAICompatibleProvider


@dataclass
class ModelRoute:
    model_prefix: str
    provider_id: str


class ModelRouter:
    """Model selection/router."""

    def __init__(self, providers: Dict[str, ProviderConfig], routes: Optional[list[ModelRoute]] = None):
        self.providers = providers
        self.routes = routes or []

    def resolve_provider(self, model: str, provider_id: Optional[str] = None) -> OpenAICompatibleProvider:
        resolved = provider_id
        if not resolved:
            for route in self.routes:
                if model.startswith(route.model_prefix):
                    resolved = route.provider_id
                    break

        if not resolved:
            raise ValueError("No provider_id given and no matching model route found")
        config = self.providers.get(resolved)
        if not config:
            raise ValueError(f"Unknown provider_id: {resolved}")
        return OpenAICompatibleProvider(config)
