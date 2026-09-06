#!/usr/bin/env python3
"""Build a deterministic read-only Session 24 ExpressionPlan 2.0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import build_expression_plan  # noqa: E402
from dna_midi_studio.midi import MidiFile  # noqa: E402


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a read-only Premium ExpressionPlan 2.0")
    parser.add_argument("midi", type=Path)
    parser.add_argument("groove_plan", type=Path)
    parser.add_argument("song_map", type=Path)
    parser.add_argument("controls", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args(argv)
    plan = build_expression_plan(
        MidiFile.read(args.midi), _load(args.groove_plan), _load(args.song_map), ROOT,
        _load(args.controls), _load(args.evidence) if args.evidence else None,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"ExpressionPlan: {plan['expressionPlanHash']}")
    print(f"Original solo notes: {plan['audit']['originalNoteCount']}; generated preview notes: {plan['audit']['generatedNoteCount']}")
    print(f"Maximum estimated peak: {plan['audit']['maximumEstimatedPeak']}/54")
    print(f"Preview: {plan['readyForPreview']}; production render: {plan['readyForProductionRender']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())