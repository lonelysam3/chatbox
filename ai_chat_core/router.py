from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from .config import provider_config
from .providers import open_ai_compatible_provider


@dataclass
class model_route:
    model_prefix: str
    provider_id: str


class model_router:
    """Model selection/router."""

    def __init__(self, providers: Dict[str, provider_config], routes: Optional[list[model_route]] = None):
        self.providers = providers
        self.routes = routes or []

    def resolve_provider(self, model: str, provider_id: Optional[str] = None) -> open_ai_compatible_provider:
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
        return open_ai_compatible_provider(config)
