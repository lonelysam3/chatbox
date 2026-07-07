from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class provider_config:
    provider_id: str
    api_key: str
    base_url: str
    default_headers: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class chat_request:
    model: str
    user_message: str
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: bool = True
