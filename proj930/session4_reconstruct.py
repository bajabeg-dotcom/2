#!/usr/bin/env python3
"""CLI for Factory-only Guitar Mode and strumming reconstruction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from dna_midi_studio import (  # noqa: E402
    ChordCell,
    GuitarConfig,
    MidiFile,
    apply_guitar_reconstruction,
    load_guitar_registry,
    plan_guitar_reconstruction,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Factory-only Guitar Mode reconstruction")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()

    raw_config = json.loads(args.config.read_text(encoding="utf-8"))
    chords = [ChordCell(**item) for item in raw_config.pop("chords")]
    config = GuitarConfig(**raw_config)
    midi = MidiFile.read(args.input)
    patterns, profiles, control_maps = load_guitar_registry(args.registry)
    plan = plan_guitar_reconstruction(
        midi, patterns, profiles, control_maps, chords, config
    )
    result = apply_guitar_reconstruction(midi, plan)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(result.manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if plan.decision == "MANUAL_REVIEW":
        print(plan.reason, file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.midi.write(args.output)
    print(
        f"{plan.decision}: Factory pattern={plan.pattern_id or '-'}; "
        f"controlMap={plan.control_map_id or '-'}; "
        f"generated={len(plan.generated_notes)}; output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())