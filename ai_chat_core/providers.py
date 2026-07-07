from __future__ import annotations

import json
from typing import Dict, Iterable, List
from urllib import error, request

from .config import ChatRequest, ProviderConfig


class ProviderAPIError(RuntimeError):
    pass


class OpenAICompatibleProvider:
    """Provider/API connection setup for OpenAI-compatible chat endpoints."""

    def __init__(self, config: ProviderConfig):
        self.config = config

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Authorization": "Bearer " + self.config.api_key,
            "Content-Type": "application/json",
        }
        headers.update(self.config.default_headers)
        return headers

    def _build_payload(self, chat_request: ChatRequest) -> Dict[str, object]:
        messages: List[Dict[str, str]] = []
        if chat_request.system_prompt:
            messages.append({"role": "system", "content": chat_request.system_prompt})
        messages.append({"role": "user", "content": chat_request.user_message})

        payload: Dict[str, object] = {
            "model": chat_request.model,
            "messages": messages,
            "stream": chat_request.stream,
        }
        if chat_request.temperature is not None:
            payload["temperature"] = chat_request.temperature
        if chat_request.max_tokens is not None:
            payload["max_tokens"] = chat_request.max_tokens
        return payload

    def create_chat_completion(self, chat_request: ChatRequest) -> str:
        """Non-streaming completion call."""
        payload = self._build_payload(ChatRequest(**{**chat_request.__dict__, "stream": False}))
        endpoint = f"{self.config.base_url.rstrip('/')}/chat/completions"
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=120) as res:
                body = json.loads(res.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise ProviderAPIError(f"HTTP {exc.code}: {exc.read().decode('utf-8', errors='ignore')}") from exc
        except error.URLError as exc:
            raise ProviderAPIError(f"Connection failed: {exc.reason}") from exc

        try:
            return body["choices"][0]["message"]["content"]
        except Exception as exc:  # noqa: BLE001
            raise ProviderAPIError(f"Unexpected response: {body}") from exc

    def stream_chat_completion(self, chat_request: ChatRequest) -> Iterable[str]:
        """Streaming completion call (SSE chunks)."""
        payload = self._build_payload(ChatRequest(**{**chat_request.__dict__, "stream": True}))
        endpoint = f"{self.config.base_url.rstrip('/')}/chat/completions"
        req = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=300) as res:
                for raw_line in res:
                    line = raw_line.decode("utf-8", errors="ignore").strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0]["delta"].get("content")
                        if delta:
                            yield delta
                    except Exception:
                        continue
        except error.HTTPError as exc:
            raise ProviderAPIError(f"HTTP {exc.code}: {exc.read().decode('utf-8', errors='ignore')}") from exc
        except error.URLError as exc:
            raise ProviderAPIError(f"Connection failed: {exc.reason}") from exc
