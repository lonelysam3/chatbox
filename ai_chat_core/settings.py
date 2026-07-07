from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict


DEFAULT_SETTINGS_PATH = Path.home() / ".ai_chat_core" / "settings.json"


@dataclass
class RuntimeSettings:
    provider_id: str
    api_key: str
    base_url: str
    default_model: str


class SettingsError(RuntimeError):
    pass


def resolve_settings_path(custom_path: str | None = None) -> Path:
    if custom_path:
        return Path(custom_path).expanduser().resolve()
    env_path = os.getenv("AI_CHAT_CORE_SETTINGS_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()
    return DEFAULT_SETTINGS_PATH


def default_settings_from_env() -> RuntimeSettings:
    return RuntimeSettings(
        provider_id=os.getenv("AI_PROVIDER_ID", "openai"),
        api_key=os.getenv("AI_API_KEY", ""),
        base_url=os.getenv("AI_BASE_URL", "https://api.openai.com/v1"),
        default_model=os.getenv("AI_MODEL", "gpt-4o-mini"),
    )


def load_settings(path: Path) -> RuntimeSettings:
    defaults = default_settings_from_env()
    if not path.exists():
        if not defaults.api_key:
            raise SettingsError("API key is missing. Set AI_API_KEY or configure it in the web UI.")
        save_settings(path, defaults)
        return defaults

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SettingsError(f"Failed to read settings: {exc}") from exc

    merged = {
        "provider_id": payload.get("provider_id", defaults.provider_id),
        "api_key": payload.get("api_key", defaults.api_key),
        "base_url": payload.get("base_url", defaults.base_url),
        "default_model": payload.get("default_model", defaults.default_model),
    }

    if not merged["api_key"]:
        raise SettingsError("API key is missing. Update settings with a valid API key.")

    return RuntimeSettings(**merged)


def save_settings(path: Path, settings: RuntimeSettings) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
    except OSError as exc:
        raise SettingsError(f"Failed to save settings: {exc}") from exc


def update_settings(current: RuntimeSettings, payload: Dict[str, Any]) -> RuntimeSettings:
    provider_id = str(payload.get("provider_id") or current.provider_id).strip()
    base_url = str(payload.get("base_url") or current.base_url).strip()
    default_model = str(payload.get("default_model") or current.default_model).strip()

    submitted_api_key = payload.get("api_key")
    if submitted_api_key is None:
        api_key = current.api_key
    else:
        api_key = str(submitted_api_key).strip() or current.api_key

    updated = RuntimeSettings(
        provider_id=provider_id,
        api_key=api_key,
        base_url=base_url,
        default_model=default_model,
    )

    if not updated.api_key:
        raise SettingsError("api_key cannot be empty")
    if not updated.base_url:
        raise SettingsError("base_url cannot be empty")
    if not updated.provider_id:
        raise SettingsError("provider_id cannot be empty")
    if not updated.default_model:
        raise SettingsError("default_model cannot be empty")

    return updated


def mask_api_key(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"
