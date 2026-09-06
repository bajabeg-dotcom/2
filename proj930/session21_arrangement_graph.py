#!/usr/bin/env python3
"""Build a read-only ArrangementGraph 2.0 from SongMap and ProducerBrief JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import build_arrangement_graph  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--song-map", required=True)
    parser.add_argument("--producer-brief", required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--variants", type=int, default=2)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    song_map = json.loads(Path(args.song_map).read_text(encoding="utf-8"))
    producer_brief = json.loads(Path(args.producer_brief).read_text(encoding="utf-8"))
    graph = build_arrangement_graph(song_map, producer_brief, args.seed, args.variants)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(graph, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"ArrangementGraph 2.0: {graph['graphHash']} ({len(graph['planVariants'])} plans)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())