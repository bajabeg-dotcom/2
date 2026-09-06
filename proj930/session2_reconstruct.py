#!/usr/bin/env python3
"""Command-line entry point for Session 2 reconstruction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from dna_midi_studio import (  # noqa: E402
    MidiFile,
    ReconstructionConfig,
    apply_reconstruction,
    load_registry,
    plan_reconstruction,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic Factory-dynamic drum/percussion reconstruction"
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()

    midi = MidiFile.read(args.input)
    patterns, profiles = load_registry(args.registry)
    config = ReconstructionConfig(
        **json.loads(args.config.read_text(encoding="utf-8"))
    )
    plan = plan_reconstruction(midi, patterns, profiles, config)
    result = apply_reconstruction(midi, plan)
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
        f"{plan.decision}: {plan.pattern_id or '-'}; "
        f"generated={len(plan.generated_notes)}; output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())