#!/usr/bin/env python3
"""Prepare or evaluate the Session 14 physical Korg Pa800 test."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio.device_certification import (  # noqa: E402
    evaluate_device_result,
    prepare_device_kit,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--output", default="artifacts/session14-device-kit")
    verify = subparsers.add_parser("verify")
    verify.add_argument("--result", required=True)
    verify.add_argument("--kit-manifest", default="artifacts/session14-device-kit/kit-manifest.json")
    verify.add_argument("--output", default="data/session14-device-report.json")
    args = parser.parse_args(argv)

    if args.command == "prepare":
        prepared = prepare_device_kit(ROOT, ROOT / args.output)
        print(f"Session 14 kit prepared: {prepared['manifestPath']}")
        print("Physical Pa800 status: WAITING_FOR_DEVICE")
        return 0

    report = evaluate_device_result(ROOT / args.result, ROOT / args.kit_manifest)
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Session 14 device result: {report['status']}; {output}")
    return 0 if report["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
