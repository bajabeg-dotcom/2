#!/usr/bin/env python3
"""CLI for the Session 28 Premium Producer workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import (  # noqa: E402
    build_premium_workflow,
    build_recovery_checkpoint,
    resume_workflow,
)
from dna_midi_studio.session28_fixture import build_session28_chain  # noqa: E402


def _read(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: str, value: object) -> None:
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build, cancel or resume a read-only Premium Producer workflow")
    sub = parser.add_subparsers(dest="command", required=True)
    reference = sub.add_parser("reference", help="Build the self-authored reference workflow")
    reference.add_argument("--output", required=True)
    build = sub.add_parser("build", help="Build a workflow from a JSON payload")
    build.add_argument("payload")
    build.add_argument("--output", required=True)
    cancel = sub.add_parser("cancel", help="Create a recovery checkpoint")
    cancel.add_argument("workflow")
    cancel.add_argument("stage")
    cancel.add_argument("--output", required=True)
    resume = sub.add_parser("resume", help="Verify and resume a recovery checkpoint")
    resume.add_argument("workflow")
    resume.add_argument("checkpoint")
    resume.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.command == "reference":
        result = build_session28_chain(ROOT)["workflow"]
    elif args.command == "build":
        payload = _read(args.payload)
        result = build_premium_workflow(payload["documents"], payload.get("controls"))
    elif args.command == "cancel":
        result = build_recovery_checkpoint(_read(args.workflow), args.stage)
    else:
        result = resume_workflow(_read(args.workflow), _read(args.checkpoint))
    _write(args.output, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())