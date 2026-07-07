# AI Chat Core (Python)

This repository now contains only the AI-chat core in Python, split into four parts:

- Provider/API connection setup: `/home/runner/work/chatbox/chatbox/ai_chat_core/providers.py`
- Core chat call logic: `/home/runner/work/chatbox/chatbox/ai_chat_core/core.py`
- Where app triggers chat: `/home/runner/work/chatbox/chatbox/ai_chat_core/app.py`
- Model selection/router: `/home/runner/work/chatbox/chatbox/ai_chat_core/router.py`

## Quick start

1. Set environment variables:

- `AI_API_KEY` (required)
- `AI_BASE_URL` (optional, default: `https://api.openai.com/v1`)
- `AI_PROVIDER_ID` (optional, default: `openai`)
- `AI_MODEL` (optional, default: `gpt-4o-mini`)

2. Run:

```bash
python -m ai_chat_core.app "Hello"
```

Non-streaming:

```bash
python -m ai_chat_core.app "Hello" --no-stream
```
