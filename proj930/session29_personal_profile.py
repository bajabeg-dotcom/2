#!/usr/bin/env python3
"""CLI for the Session 29 local Personal Producer Profile."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import execute_personal_profile_api  # noqa: E402
from dna_midi_studio.session29_fixture import build_session29_chain  # noqa: E402


def _read(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: str, value: object) -> None:
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build, inspect, export or delete a local Personal Producer Profile"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    reference = sub.add_parser("reference", help="Build the self-authored reference profile")
    reference.add_argument("--output", required=True)
    request = sub.add_parser("request", help="Execute a strict JSON profile API request")
    request.add_argument("payload")
    request.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.command == "reference":
        result = build_session29_chain(ROOT)["personalProfile"]
    else:
        result = execute_personal_profile_api(_read(args.payload))
    _write(args.output, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())