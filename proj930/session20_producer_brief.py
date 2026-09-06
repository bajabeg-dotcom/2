#!/usr/bin/env python3
"""Create a local, read-only ProducerBrief 2.0 JSON document."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import build_producer_brief  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Local AI Producer Brief 2.0 parser")
    parser.add_argument("--text", required=True, help="Croatian or English arrangement intent")
    parser.add_argument("--output", required=True, type=Path, help="Output JSON path")
    args = parser.parse_args()
    brief = build_producer_brief(args.text)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(brief, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"ProducerBrief 2.0: {brief['approval']['status']}; {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())