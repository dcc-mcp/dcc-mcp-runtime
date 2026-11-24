"""Small validation CLI used by installers and CI."""

from __future__ import annotations

import argparse
import json

from .launch import prepare_launch
from .manifest import load_manifest


def main() -> int:
    parser = argparse.ArgumentParser(prog="dcc-mcp-runtime")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate-manifest")
    validate.add_argument("path")
    launch = sub.add_parser("prepare-launch", help="probe an operator-trusted staged bundle")
    launch.add_argument("root")
    launch.add_argument("lock")
    launch.add_argument("--expected-lock-sha256", required=True)
    args = parser.parse_args()
    if args.command == "validate-manifest":
        manifest = load_manifest(args.path)
        print(json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2))
        return 0
    if args.command == "prepare-launch":
        print(json.dumps(prepare_launch(args.root, args.lock, args.expected_lock_sha256), indent=2))
        return 0
    return 2


if __name__ == "__main__":  # pragma: no cover - exercised by the CLI smoke path
    raise SystemExit(main())
