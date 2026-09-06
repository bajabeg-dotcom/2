#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio.reliability_gate import run_reliability_gate  # noqa: E402
from dna_midi_studio.session35_fixture import build_session35_chain  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="DNA Session 36 zero-silent-failure gate")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/session36-reliability-report.json")
    parser.add_argument("--quick", action="store_true", help="Use small stress fixtures for a quick diagnostic")
    args = parser.parse_args()
    chain = build_session35_chain(ROOT)
    counts = (250, 1000) if args.quick else (25_000, 100_000)
    result = run_reliability_gate(chain, ROOT, counts, 32 if args.quick else 200)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result["report"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Session 36 reliability: {result['report']['result'].upper()}; {args.output}")
    return 0 if result["report"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())