# AI Chat Core (Python)

This repository contains a Python AI-chat core with:

- Provider/API connection setup: `/home/runner/work/chatbox/chatbox/ai_chat_core/providers.py`
- Model selection/router: `/home/runner/work/chatbox/chatbox/ai_chat_core/router.py`
- Core chat call logic + vulnerability detection: `/home/runner/work/chatbox/chatbox/ai_chat_core/core.py`
- App trigger (CLI): `/home/runner/work/chatbox/chatbox/ai_chat_core/app.py`
- HTTP API + website for key management: `/home/runner/work/chatbox/chatbox/ai_chat_core/web.py`

## Configure credentials

Settings are persisted in `~/.ai_chat_core/settings.json` by default.

Initial bootstrap can come from env vars:

- `AI_API_KEY` (required on first run)
- `AI_BASE_URL` (optional, default: `https://api.openai.com/v1`)
- `AI_PROVIDER_ID` (optional, default: `openai`)
- `AI_MODEL` (optional, default: `gpt-4o-mini`)
- `AI_CHAT_CORE_SETTINGS_PATH` (optional custom settings file path)

## CLI usage

```bash
python -m ai_chat_core.app "Hello"
```

## Start API server + website

```bash
python -m ai_chat_core.web --host 127.0.0.1 --port 8080
```

Then open:

- `http://127.0.0.1:8080/`

## API endpoints

- `GET /api/settings` -> returns provider settings (API key masked)
- `POST /api/settings` -> updates provider settings and API key
- `POST /api/chat` -> chat completion API
- `POST /api/vulnerability-detect` -> AI-based code vulnerability detection

### Example: chat

```bash
curl -X POST http://127.0.0.1:8080/api/chat \\
  -H 'Content-Type: application/json' \\
  -d '{\"message\":\"Explain SQL injection in 2 lines\",\"model\":\"gpt-4o-mini\"}'
```

### Example: vulnerability scan

```bash
curl -X POST http://127.0.0.1:8080/api/vulnerability-detect \\
  -H 'Content-Type: application/json' \\
  -d '{\"language\":\"python\",\"code\":\"query = \\\"SELECT * FROM users WHERE id = \\\" + user_id\"}'
```
