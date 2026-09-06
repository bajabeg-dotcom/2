#!/usr/bin/env python3
"""Session 37 quality corpus, calibration and external-evidence CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio.quality_calibration import (  # noqa: E402
    execute_quality_calibration_api,
)
from dna_midi_studio.session37_fixture import build_session37_chain  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Session 37 production quality calibration")
    parser.add_argument("--request", type=Path, help="Optional JSON API-style request")
    parser.add_argument("--output", type=Path, help="Write JSON result")
    args = parser.parse_args()
    if args.request:
        payload = json.loads(args.request.read_text(encoding="utf-8"))
        result = execute_quality_calibration_api(payload, ROOT)
    else:
        chain = build_session37_chain(ROOT)
        result = {
            "corpusHash": chain["corpus"]["corpusHash"],
            "calibrationHash": chain["calibration"]["calibrationHash"],
            "holdoutHash": chain["holdout"]["holdoutHash"],
            "gate": chain["qualityGate"],
        }
    encoded = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())