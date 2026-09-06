#!/usr/bin/env python3
"""Build a deterministic Session 23 GroovePlan 2.0 JSON document."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import build_groove_plan  # noqa: E402


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a read-only Premium GroovePlan 2.0")
    parser.add_argument("candidate_set", type=Path)
    parser.add_argument("arrangement_graph", type=Path)
    parser.add_argument("song_map", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seed", type=int, default=2300)
    parser.add_argument("--strength", type=int, default=65)
    parser.add_argument("--gate-strength", type=int, default=55)
    parser.add_argument("--simplification-policy", choices=("AUTO_SAFE", "MANUAL_REVIEW"),
                        default="AUTO_SAFE")
    args = parser.parse_args(argv)
    plan = build_groove_plan(
        _load(args.candidate_set), _load(args.arrangement_graph), _load(args.song_map), ROOT,
        seed=args.seed,
        controls={
            "version": "1.0", "strength": args.strength,
            "gateStrength": args.gate_strength,
            "simplificationPolicy": args.simplification_policy,
            "softwareMidiNoteCeiling": 54,
        },
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"GroovePlan: {plan['groovePlanHash']}")
    print(f"MIDI-note peak: {plan['audit']['maximumPeakAfterSimplification']}/54")
    print(f"Device voice cost: {plan['deviceVoiceCost']['status']}")
    print(f"Read-only: {plan['safety']['readOnly']}; final MIDI: {plan['safety']['finalMidiGenerated']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())