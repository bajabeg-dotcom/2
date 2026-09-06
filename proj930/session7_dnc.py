#!/usr/bin/env python3
"""CLI for exact-sound, map-driven DNC articulations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from dna_midi_studio import (  # noqa: E402
    DncConfig,
    MidiFile,
    apply_dnc_events,
    load_dnc_registry,
    plan_dnc_events,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Confirmed DNC articulation engine")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    config = DncConfig(**json.loads(args.config.read_text(encoding="utf-8")))
    midi = MidiFile.read(args.input)
    maps, profiles = load_dnc_registry(args.registry)
    plan = plan_dnc_events(midi, maps, profiles, config)
    result = apply_dnc_events(midi, plan)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(result.manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if plan.decision == "MANUAL_REVIEW":
        print(plan.reason, file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.midi.write(args.output)
    print(f"{plan.decision}: generated={len(plan.generated_notes) + len(plan.generated_events)}; output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())