from __future__ import annotations

from typing import Iterable, Optional

from .config import ChatRequest
from .router import ModelRouter


class AIChatCore:
    """Core chat call logic."""

    def __init__(self, router: ModelRouter):
        self.router = router

    def chat(
        self,
        *,
        model: str,
        user_message: str,
        provider_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        provider = self.router.resolve_provider(model=model, provider_id=provider_id)
        request = ChatRequest(
            model=model,
            user_message=user_message,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        return provider.create_chat_completion(request)

    def chat_stream(
        self,
        *,
        model: str,
        user_message: str,
        provider_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Iterable[str]:
        provider = self.router.resolve_provider(model=model, provider_id=provider_id)
        request = ChatRequest(
            model=model,
            user_message=user_message,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        return provider.stream_chat_completion(request)
