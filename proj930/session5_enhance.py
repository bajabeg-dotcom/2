#!/usr/bin/env python3
"""CLI for evidence-gated protected solo enhancement."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from dna_midi_studio import (  # noqa: E402
    ChordCell,
    MidiFile,
    SoloConfig,
    apply_solo_enhancement,
    load_solo_registry,
    plan_solo_enhancement,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Protected solo, ornaments, third, echo and CC11")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()

    raw_config = json.loads(args.config.read_text(encoding="utf-8"))
    chords = [ChordCell(**item) for item in raw_config.pop("chords")]
    config = SoloConfig.from_mapping(raw_config)
    midi = MidiFile.read(args.input)
    ornaments, relationships, profiles = load_solo_registry(args.registry)
    plan = plan_solo_enhancement(
        midi, ornaments, relationships, profiles, chords, config
    )
    result = apply_solo_enhancement(midi, plan)
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
        f"{plan.decision}: generated={len(plan.generated_notes)}; "
        f"cc11={len(plan.expression_events)}; output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())