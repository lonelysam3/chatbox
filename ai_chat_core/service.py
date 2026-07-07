from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

from .config import provider_config
from .core import ai_chat_core
from .router import model_route, model_router
from .settings import runtime_settings, load_settings, mask_api_key, resolve_settings_path, save_settings, update_settings


class ai_chat_service:
    def __init__(self, settings_path: str | None = None):
        self.settings_path = resolve_settings_path(settings_path)
        self.settings = load_settings(self.settings_path)

    def _build_core(self) -> ai_chat_core:
        providers = {
            self.settings.provider_id: provider_config(
                provider_id=self.settings.provider_id,
                api_key=self.settings.api_key,
                base_url=self.settings.base_url,
            )
        }
        router = model_router(
            providers=providers,
            routes=[
                model_route("gpt-", self.settings.provider_id),
                model_route("o", self.settings.provider_id),
                model_route("claude-", self.settings.provider_id),
            ],
        )
        return ai_chat_core(router)

    def get_public_settings(self) -> Dict[str, Any]:
        return {
            "provider_id": self.settings.provider_id,
            "base_url": self.settings.base_url,
            "default_model": self.settings.default_model,
            "api_key_masked": mask_api_key(self.settings.api_key),
            "settings_path": str(self.settings_path),
        }

    def replace_settings(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.settings = update_settings(self.settings, payload)
        save_settings(self.settings_path, self.settings)
        return self.get_public_settings()

    def chat(
        self,
        *,
        message: str,
        model: Optional[str] = None,
        provider_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        if not message.strip():
            raise ValueError("message is required")
        core = self._build_core()
        return core.chat(
            model=model or self.settings.default_model,
            user_message=message,
            provider_id=provider_id,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def detect_vulnerabilities(
        self,
        *,
        code: str,
        language: str = "unknown",
        model: Optional[str] = None,
        provider_id: Optional[str] = None,
    ) -> str:
        if not code.strip():
            raise ValueError("code is required")
        core = self._build_core()
        return core.detect_vulnerabilities(
            code=code,
            language=language,
            model=model or self.settings.default_model,
            provider_id=provider_id,
        )

    def export_settings(self) -> runtime_settings:
        return runtime_settings(**asdict(self.settings))

    @property
    def path(self) -> Path:
        return self.settings_path
