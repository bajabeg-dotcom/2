#!/usr/bin/env python3
"""CLI for Session 27 automated metrics and blind listening evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import (  # noqa: E402
    build_blind_listening_package,
    build_quality_regression_vault,
    evaluate_music_quality,
    load_baseline_reference,
)


def _json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: str, value) -> None:
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Premium MIDI structure and prepare blind listening gates")
    sub = parser.add_subparsers(dest="action", required=True)

    blind = sub.add_parser("blind-package", help="Create public blind package and separate private key")
    blind.add_argument("preview_session")
    blind.add_argument("audio_manifests", help="JSON object keyed by A, B and C")
    blind.add_argument("public_output")
    blind.add_argument("private_key_output")
    blind.add_argument("--seed", type=int, default=2700)

    evaluate = sub.add_parser("evaluate", help="Create EvaluationReport 2.0")
    evaluate.add_argument("preview_session")
    evaluate.add_argument("song_map")
    evaluate.add_argument("blind_package")
    evaluate.add_argument("private_key")
    evaluate.add_argument("regression_vault")
    evaluate.add_argument("output")
    evaluate.add_argument("--response", action="append", default=[])
    evaluate.add_argument("--controls")

    vault = sub.add_parser("regression-vault", help="Build locked quality regression vault")
    vault.add_argument("entries")
    vault.add_argument("output")
    args = parser.parse_args()

    if args.action == "blind-package":
        package, key = build_blind_listening_package(
            _json(args.preview_session), _json(args.audio_manifests),
            load_baseline_reference(ROOT), args.seed,
        )
        _write(args.public_output, package)
        _write(args.private_key_output, key)
        print(f"Blind package {package['packageHash']} -> {args.public_output}")
    elif args.action == "evaluate":
        report = evaluate_music_quality(
            _json(args.preview_session), _json(args.song_map), load_baseline_reference(ROOT),
            _json(args.blind_package), _json(args.private_key),
            [_json(path) for path in args.response], _json(args.regression_vault),
            _json(args.controls) if args.controls else None,
        )
        _write(args.output, report)
        print(f"Evaluation {report['status']} {report['evaluationReportHash']} -> {args.output}")
    else:
        entries = _json(args.entries)
        if not isinstance(entries, list):
            raise ValueError("Regression entries file must contain a JSON array")
        result = build_quality_regression_vault(entries)
        _write(args.output, result)
        print(f"Regression vault {result['vaultHash']} -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())