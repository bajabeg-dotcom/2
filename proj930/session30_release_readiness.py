#!/usr/bin/env python3
"""CLI for Session 30 software release-readiness and project migration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import execute_release_readiness_api  # noqa: E402
from dna_midi_studio.session30_fixture import build_session30_chain  # noqa: E402


def _read(path: str) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Input JSON must be an object")
    return value


def _write(path: str, value: object) -> None:
    Path(path).write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build Preview RC readiness or migrate a legacy DNA project"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    reference = commands.add_parser("reference", help="Build the reference readiness report")
    reference.add_argument("--output", required=True)
    migrate = commands.add_parser("migrate", help="Migrate a legacy project without overwriting it")
    migrate.add_argument("input")
    migrate.add_argument("--date", default="2026-09-03")
    migrate.add_argument("--output", required=True)
    request = commands.add_parser("request", help="Execute a strict JSON readiness API request")
    request.add_argument("payload")
    request.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.command == "reference":
        fixture = build_session30_chain(ROOT)
        result = {
            "readiness": fixture["releaseReadiness"],
            "statusMatrix": fixture["statusMatrix"],
            "hardening": fixture["hardeningReport"],
            "migration": fixture["projectMigration"],
        }
    elif args.command == "migrate":
        result = execute_release_readiness_api(
            {"action": "migrate", "releaseDate": args.date, "legacyProject": _read(args.input)},
            ROOT,
        )
    else:
        result = execute_release_readiness_api(_read(args.payload), ROOT)
    _write(args.output, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())