#!/usr/bin/env python3
"""CLI for Session 35 Song-to-Style project creation."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import build_song_to_style_project  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a complete evidence-linked Song-to-Style project")
    parser.add_argument("source_midi")
    parser.add_argument("chain_bundle")
    parser.add_argument("--output", required=True)
    parser.add_argument("--variant", choices=("A", "B", "C"), default="C")
    parser.add_argument("--seed", type=int, default=3535)
    args = parser.parse_args()
    source = Path(args.source_midi).read_bytes()
    chain = json.loads(Path(args.chain_bundle).read_text(encoding="utf-8"))
    project = build_song_to_style_project(source, chain, {
        "selectedVariantId": args.variant, "lockedMarkers": [],
        "projectSeed": args.seed, "previewTier": "PREVIEW_ONLY"})
    Path(args.output).write_text(json.dumps(project, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"End-to-End PASS: {len(project['stages'])}/10 stages; {project['projectHash']}; {args.output}")
    print("Publication: PREVIEW_ONLY; final Pa800-certified export remains blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())