"""Small validation CLI used by installers and CI."""

from __future__ import annotations

import argparse
import json

from .manifest import load_manifest


def main() -> int:
    parser = argparse.ArgumentParser(prog="dcc-mcp-runtime")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate-manifest")
    validate.add_argument("path")
    args = parser.parse_args()
    if args.command == "validate-manifest":
        manifest = load_manifest(args.path)
        print(json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2))
        return 0
    return 2


if __name__ == "__main__":  # pragma: no cover - exercised by the CLI smoke path
    raise SystemExit(main())
