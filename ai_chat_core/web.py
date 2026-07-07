from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict
from urllib.parse import urlparse

from .service import AIChatService
from .settings import SettingsError


WEB_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AI Chat Core</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 2rem; max-width: 960px; }
    textarea, input { width: 100%; margin-top: .35rem; margin-bottom: .8rem; }
    textarea { min-height: 140px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
    .panel { border: 1px solid #ddd; border-radius: 8px; padding: 1rem; }
    button { padding: .5rem .9rem; cursor: pointer; }
    pre { background: #f7f7f7; padding: 1rem; overflow: auto; white-space: pre-wrap; }
    .small { color: #666; font-size: .9rem; }
  </style>
</head>
<body>
  <h1>AI Chat Core API Console</h1>
  <p class="small">Use this page to update API keys/settings, chat, and run vulnerability detection.</p>

  <div class="grid">
    <div class="panel">
      <h2>Provider Settings</h2>
      <label>Provider ID<input id="provider_id" /></label>
      <label>Base URL<input id="base_url" /></label>
      <label>Default model<input id="default_model" /></label>
      <label>New API key (leave blank to keep existing)<input id="api_key" type="password" /></label>
      <div class="small">Current key: <span id="api_key_masked"></span></div>
      <button onclick="saveSettings()">Save Settings</button>
      <pre id="settings_result"></pre>
    </div>

    <div class="panel">
      <h2>Chat</h2>
      <label>Model<input id="chat_model" /></label>
      <label>Message<textarea id="chat_message"></textarea></label>
      <button onclick="sendChat()">Send Chat</button>
      <pre id="chat_result"></pre>
    </div>
  </div>

  <div class="panel" style="margin-top:1.5rem;">
    <h2>Vulnerability Detection</h2>
    <label>Model<input id="scan_model" /></label>
    <label>Language<input id="scan_language" value="python" /></label>
    <label>Code<textarea id="scan_code"></textarea></label>
    <button onclick="scanCode()">Analyze Vulnerabilities</button>
    <pre id="scan_result"></pre>
  </div>

  <script>
    async function request(url, method='GET', body=null) {
      const res = await fetch(url, {
        method,
        headers: {'Content-Type': 'application/json'},
        body: body ? JSON.stringify(body) : null,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Request failed');
      return data;
    }

    async function loadSettings() {
      const data = await request('/api/settings');
      provider_id.value = data.provider_id;
      base_url.value = data.base_url;
      default_model.value = data.default_model;
      chat_model.value = data.default_model;
      scan_model.value = data.default_model;
      api_key_masked.textContent = data.api_key_masked || '(not set)';
      settings_result.textContent = JSON.stringify(data, null, 2);
    }

    async function saveSettings() {
      try {
        const payload = {
          provider_id: provider_id.value,
          base_url: base_url.value,
          default_model: default_model.value,
          api_key: api_key.value,
        };
        const data = await request('/api/settings', 'POST', payload);
        api_key.value = '';
        api_key_masked.textContent = data.api_key_masked;
        settings_result.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        settings_result.textContent = String(err);
      }
    }

    async function sendChat() {
      try {
        const data = await request('/api/chat', 'POST', {
          model: chat_model.value,
          message: chat_message.value,
        });
        chat_result.textContent = data.reply;
      } catch (err) {
        chat_result.textContent = String(err);
      }
    }

    async function scanCode() {
      try {
        const data = await request('/api/vulnerability-detect', 'POST', {
          model: scan_model.value,
          language: scan_language.value,
          code: scan_code.value,
        });
        scan_result.textContent = data.report;
      } catch (err) {
        scan_result.textContent = String(err);
      }
    }

    loadSettings().catch((err) => {
      settings_result.textContent = String(err);
    });
  </script>
</body>
</html>
"""


class APIHandler(BaseHTTPRequestHandler):
    server: "AIHTTPServer"

    def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/":
            body = WEB_PAGE.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/api/settings":
            self._send_json(HTTPStatus.OK, self.server.service.get_public_settings())
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            payload = self._read_json()
            if path == "/api/settings":
                updated = self.server.service.replace_settings(payload)
                self._send_json(HTTPStatus.OK, updated)
                return

            if path == "/api/chat":
                reply = self.server.service.chat(
                    message=str(payload.get("message") or ""),
                    model=payload.get("model"),
                    provider_id=payload.get("provider_id"),
                    system_prompt=payload.get("system_prompt"),
                    temperature=payload.get("temperature"),
                    max_tokens=payload.get("max_tokens"),
                )
                self._send_json(HTTPStatus.OK, {"reply": reply})
                return

            if path == "/api/vulnerability-detect":
                report = self.server.service.detect_vulnerabilities(
                    code=str(payload.get("code") or ""),
                    language=str(payload.get("language") or "unknown"),
                    model=payload.get("model"),
                    provider_id=payload.get("provider_id"),
                )
                self._send_json(HTTPStatus.OK, {"report": report})
                return

            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
        except json.JSONDecodeError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON payload"})
        except (ValueError, SettingsError) as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})


class AIHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], handler_cls: type[BaseHTTPRequestHandler], service: AIChatService):
        super().__init__(server_address, handler_cls)
        self.service = service


def run_server(host: str, port: int, settings_path: str | None = None) -> None:
    service = AIChatService(settings_path=settings_path)
    server = AIHTTPServer((host, port), APIHandler, service)
    print(f"AI Chat Core server running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Chat Core HTTP API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--settings-path", default=None)
    args = parser.parse_args()
    run_server(args.host, args.port, args.settings_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
