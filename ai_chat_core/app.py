from __future__ import annotations

import argparse
import os
import sys

from .config import ProviderConfig
from .core import AIChatCore
from .router import ModelRoute, ModelRouter


def build_core_from_env() -> AIChatCore:
    api_key = os.getenv("AI_API_KEY", "")
    base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
    provider_id = os.getenv("AI_PROVIDER_ID", "openai")

    if not api_key:
        raise RuntimeError("AI_API_KEY is required")

    providers = {
        provider_id: ProviderConfig(
            provider_id=provider_id,
            api_key=api_key,
            base_url=base_url,
        )
    }
    router = ModelRouter(
        providers=providers,
        routes=[
            ModelRoute("gpt-", provider_id),
            ModelRoute("o", provider_id),
        ],
    )
    return AIChatCore(router)


def main() -> int:
    parser = argparse.ArgumentParser(description="AI chat core CLI")
    parser.add_argument("message", help="User message")
    parser.add_argument("--model", default=os.getenv("AI_MODEL", "gpt-4o-mini"))
    parser.add_argument("--provider-id", default=os.getenv("AI_PROVIDER_ID"))
    parser.add_argument("--system-prompt", default=None)
    parser.add_argument("--no-stream", action="store_true")
    args = parser.parse_args()

    core = build_core_from_env()
    if args.no_stream:
        result = core.chat(
            model=args.model,
            provider_id=args.provider_id,
            user_message=args.message,
            system_prompt=args.system_prompt,
        )
        print(result)
        return 0

    for token in core.chat_stream(
        model=args.model,
        provider_id=args.provider_id,
        user_message=args.message,
        system_prompt=args.system_prompt,
    ):
        sys.stdout.write(token)
        sys.stdout.flush()
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
