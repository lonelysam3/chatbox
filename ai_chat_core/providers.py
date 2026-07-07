from __future__ import annotations

import json
from typing import Dict, Iterable, List
from urllib import error, request

from .config import chat_request, provider_config


class provider_api_error(RuntimeError):
    pass


class open_ai_compatible_provider:
    """Provider/API connection setup for OpenAI-compatible chat endpoints."""

    def __init__(self, config: provider_config):
        self.config = config

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Authorization": "Bearer " + self.config.api_key,
            "Content-Type": "application/json",
        }
        headers.update(self.config.default_headers)
        return headers

    def _build_payload(self, request_data: chat_request) -> Dict[str, object]:
        messages: List[Dict[str, str]] = []
        if request_data.system_prompt:
            messages.append({"role": "system", "content": request_data.system_prompt})
        messages.append({"role": "user", "content": request_data.user_message})

        payload: Dict[str, object] = {
            "model": request_data.model,
            "messages": messages,
            "stream": request_data.stream,
        }
        if request_data.temperature is not None:
            payload["temperature"] = request_data.temperature
        if request_data.max_tokens is not None:
            payload["max_tokens"] = request_data.max_tokens
        return payload

    def create_chat_completion(self, request_data: chat_request) -> str:
        """Non-streaming completion call."""
        payload = self._build_payload(chat_request(**{**request_data.__dict__, "stream": False}))
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
            raise provider_api_error(f"HTTP {exc.code}: {exc.read().decode('utf-8', errors='ignore')}") from exc
        except error.URLError as exc:
            raise provider_api_error(f"Connection failed: {exc.reason}") from exc

        try:
            return body["choices"][0]["message"]["content"]
        except Exception as exc:  # noqa: BLE001
            raise provider_api_error(f"Unexpected response: {body}") from exc

    def stream_chat_completion(self, request_data: chat_request) -> Iterable[str]:
        """Streaming completion call (SSE chunks)."""
        payload = self._build_payload(chat_request(**{**request_data.__dict__, "stream": True}))
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
            raise provider_api_error(f"HTTP {exc.code}: {exc.read().decode('utf-8', errors='ignore')}") from exc
        except error.URLError as exc:
            raise provider_api_error(f"Connection failed: {exc.reason}") from exc
