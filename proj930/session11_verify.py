#!/usr/bin/env python3
"""Independently verify source, candidate, pipeline manifest and atomic journal."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from dna_midi_studio import AuthorizedNoteAddition, VerificationPolicy, verify_candidate  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Independent DNA MIDI verifier")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--journal", type=Path)
    parser.add_argument("--authorization", action="append", default=[],
                        help="track,channel,start,end,pitchMin,pitchMax,reason")
    parser.add_argument("--pa800-style", action="store_true")
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    rules = []
    for value in args.authorization:
        fields = value.split(",", 6)
        if len(fields) != 7:
            parser.error("authorization requires seven comma-separated fields")
        rules.append(AuthorizedNoteAddition(*(int(item) for item in fields[:6]), fields[6]))
    candidate = args.candidate.read_bytes()
    report = verify_candidate(
        args.source.read_bytes(), candidate,
        json.loads(args.manifest.read_text(encoding="utf-8")),
        VerificationPolicy(tuple(rules), args.pa800_style, require_idempotency=False),
        journal=json.loads(args.journal.read_text(encoding="utf-8")) if args.journal else None,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{'PASS' if report.passed else 'BLOCKED'}: {len(report.issues)} issue(s)")
    return 0 if report.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())