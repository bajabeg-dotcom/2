#!/usr/bin/env python3
"""Build a deterministic read-only CandidateSet 2.0 from graph and SongMap."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import build_candidate_set  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", required=True, type=Path)
    parser.add_argument("--song-map", required=True, type=Path)
    parser.add_argument("--plan-variant", default="plan-01")
    parser.add_argument("--seed", type=int, default=2200)
    parser.add_argument("--variants", type=int, default=3)
    parser.add_argument("--controls", type=Path)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    graph = json.loads(args.graph.read_text(encoding="utf-8"))
    song_map = json.loads(args.song_map.read_text(encoding="utf-8"))
    controls = json.loads(args.controls.read_text(encoding="utf-8")) if args.controls else None
    previous = json.loads(args.previous.read_text(encoding="utf-8")) if args.previous else None
    result = build_candidate_set(
        graph, song_map, ROOT, args.plan_variant, args.seed, args.variants, controls, previous
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"CandidateSet {result['candidateSetHash']} | "
        f"{len(result['requests'])} requests | {len(result['variants'])} variants | "
        f"ready={result['readyForVariantRendering']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())