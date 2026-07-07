from __future__ import annotations

import argparse
import sys

from .service import ai_chat_service


def main() -> int:
    parser = argparse.ArgumentParser(description="AI chat core CLI")
    parser.add_argument("message", help="User message")
    parser.add_argument("--model", default=None)
    parser.add_argument("--provider-id", default=None)
    parser.add_argument("--system-prompt", default=None)
    parser.add_argument("--settings-path", default=None)
    parser.add_argument("--no-stream", action="store_true")
    args = parser.parse_args()

    service = ai_chat_service(settings_path=args.settings_path)
    if args.no_stream:
        result = service.chat(
            provider_id=args.provider_id,
            message=args.message,
            model=args.model,
            system_prompt=args.system_prompt,
        )
        print(result)
        return 0

    reply = service.chat(
        provider_id=args.provider_id,
        message=args.message,
        model=args.model,
        system_prompt=args.system_prompt,
    )
    sys.stdout.write(reply)
    print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
