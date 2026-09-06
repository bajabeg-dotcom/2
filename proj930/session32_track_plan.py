#!/usr/bin/env python3
"""CLI for Session 32 TrackPlan 3.0 and Full Optimizer dry-run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import build_track_plan  # noqa: E402


def _read(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a strict read-only TrackPlan; this command never writes MIDI bytes"
    )
    parser.add_argument("midi", help="Source .mid/.midi file")
    parser.add_argument("documents", help="JSON object containing Analysis/Brief/Graph/Candidate/Groove/Expression documents")
    parser.add_argument("ledger", help="EvidenceLedger 3.0 JSON")
    parser.add_argument("bindings", help="Exact target SoundBinding JSON array")
    parser.add_argument("--controls", help="Optional TrackPlan controls JSON")
    parser.add_argument("--output", required=True, help="Output TrackPlan JSON")
    args = parser.parse_args()
    midi_path = Path(args.midi)
    if midi_path.suffix.lower() not in {".mid", ".midi"}:
        raise ValueError("TrackPlan input must be a .mid or .midi file")
    documents_payload = _read(args.documents)
    documents = documents_payload.get("documents", documents_payload)
    bindings_payload = _read(args.bindings)
    bindings = bindings_payload.get("targetBindings", bindings_payload)
    plan = build_track_plan(
        midi_path.read_bytes(), documents, _read(args.ledger), bindings,
        _read(args.controls) if args.controls else None, ROOT,
    )
    Path(args.output).write_text(
        json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"TrackPlan PASS: {len(plan['fragments'])} fragments; "
        f"{len(plan['manualReview'])} manual review; MIDI bytes written=0; {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())