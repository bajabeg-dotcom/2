#!/usr/bin/env python3
"""CLI for evidence-first automatic song track/instrument analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import analyze_track_instruments, load_factory_catalog  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze physical MIDI tracks, exact SoundBinding and instrument roles"
    )
    parser.add_argument("input", help="Input .mid/.midi file")
    parser.add_argument("--output", required=True, help="Output JSON report")
    parser.add_argument(
        "--factory-catalog",
        help="Optional Factory profile JSON; defaults to data/factory-velocity-profiles.json",
    )
    args = parser.parse_args()
    input_path = Path(args.input)
    if input_path.suffix.lower() not in {".mid", ".midi"}:
        raise ValueError("Input must be a .mid or .midi file")
    if args.factory_catalog:
        catalog = json.loads(Path(args.factory_catalog).read_text(encoding="utf-8"))
    else:
        catalog = load_factory_catalog(ROOT)
    report = analyze_track_instruments(
        input_path.read_bytes(), input_path.name, factory_catalog=catalog
    )
    Path(args.output).write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"Track analysis PASS: {report['summary']['acceptedTrackCount']} accepted; "
        f"{report['summary']['manualReviewTrackCount']} manual review; {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
