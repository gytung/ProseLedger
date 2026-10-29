"""Generate a proposal or validate the bundled resources."""

import argparse
import json
import sys
from .runner import execute, verify_runtime


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify", help="Validate resources and graph imports without model calls.")
    run = sub.add_parser("run", help="Generate a new proposal using the signed-in Codex CLI.")
    run.add_argument("--output", required=True)
    run.add_argument("--sources", required=True, help="JSON file containing 2–10 explicit sources.")
    run.add_argument("--topic", required=True)
    run.add_argument("--model", default="gpt-6.1-sol")
    run.add_argument("--timeout", type=int, default=240)
    run.add_argument(
        "--resume", action="store_true", help="Resume with exactly the original inputs."
    )
    args = parser.parse_args()
    try:
        if args.command == "verify":
            result = verify_runtime()
        else:
            result = execute(
                args.output,
                sources_path=args.sources,
                topic=args.topic,
                resume=args.resume,
                model=args.model,
                timeout=args.timeout,
            )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as error:
        print(
            json.dumps(
                {"status": "failed", "error": str(error), "type": type(error).__name__},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
