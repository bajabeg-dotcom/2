#!/usr/bin/env python3
"""CLI for the Session 33 deterministic evidence-driven renderer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import publish_rendered_arrangement, render_arrangement  # noqa: E402


def _read(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a software-validated Pa800 Style-import SMF0 from TrackPlan 3.0"
    )
    parser.add_argument("midi", help="Original source .mid/.midi")
    parser.add_argument("documents", help="Analysis/Brief/Graph/Candidate/Groove/Expression JSON object")
    parser.add_argument("ledger", help="EvidenceLedger 3.0 JSON")
    parser.add_argument("track_plan", help="TrackPlan 3.0 JSON")
    parser.add_argument("--output-dir", required=True, help="Authorized atomic output directory")
    parser.add_argument("--source-name", help="Output stem; defaults to source MIDI filename")
    args = parser.parse_args()
    source_path = Path(args.midi)
    if source_path.suffix.lower() not in {".mid", ".midi"}:
        raise ValueError("Renderer input must be a .mid or .midi file")
    documents_payload = _read(args.documents)
    documents = documents_payload.get("documents", documents_payload)
    source = source_path.read_bytes()
    midi, manifest = render_arrangement(
        source, _read(args.track_plan), documents, _read(args.ledger), ROOT
    )
    result = publish_rendered_arrangement(
        source, midi, manifest, args.output_dir, args.source_name or source_path.name
    )
    if result["status"] != "COMMITTED":
        raise RuntimeError(f"Renderer publication was {result['status']}")
    print(
        f"Renderer PASS: {manifest['audit']['renderedFragments']} fragments; "
        f"{manifest['midi']['noteCount']} notes; {manifest['midi']['outputSha256']}; "
        f"{result['output_path']}"
    )
    print("Certification: SOFTWARE_VALIDATED_ARRANGER_PREVIEW; physical Pa800 WAITING_FOR_DEVICE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())