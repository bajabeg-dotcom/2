#!/usr/bin/env python3
"""Session 38 Pa800 Device Lab intake, sealing and verification CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio.device_profile_certification import (  # noqa: E402
    build_reference_device_lab,
    seal_device_capture,
    validate_device_capture,
    verify_device_capture_file,
)


def _write_or_print(value: object, output: Path | None) -> None:
    encoded = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    reference = subparsers.add_parser("reference")
    reference.add_argument("--output", type=Path)
    seal = subparsers.add_parser("seal")
    seal.add_argument("--capture", type=Path, required=True)
    seal.add_argument("--output", type=Path)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--capture", type=Path, required=True)
    verify.add_argument("--report", type=Path)
    verify.add_argument("--profile", type=Path)
    args = parser.parse_args(argv)

    if args.command == "reference":
        _write_or_print(build_reference_device_lab(ROOT), args.output)
        return 0
    if args.command == "seal":
        capture = json.loads(args.capture.read_text(encoding="utf-8"))
        validate_device_capture(capture, require_seal=False)
        _write_or_print(seal_device_capture(capture), args.output)
        return 0

    result = verify_device_capture_file(args.capture, ROOT)
    _write_or_print(result["report"], args.report)
    if args.profile:
        _write_or_print(result["profile"], args.profile)
    return 0 if result["report"]["certified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())