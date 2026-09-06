#!/usr/bin/env python3
"""Unified CLI/batch entry point for the recovery pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from dna_midi_studio import execute_batch, execute_pipeline  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="DNA unified pipeline")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--batch", type=Path, help="JSON array with input/config/output/manifest paths")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    if args.batch:
        jobs = json.loads(args.batch.read_text(encoding="utf-8"))
        inputs = [(Path(job["input"]).read_bytes(), json.loads(Path(job["config"]).read_text(encoding="utf-8"))) for job in jobs]
        results = execute_batch(inputs, root)
        for job, result in zip(jobs, results):
            Path(job["output"]).write_bytes(result.midi)
            Path(job["manifest"]).write_text(json.dumps(result.manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"BATCH PASS: {len(results)} files")
        return 0
    if not all((args.input, args.config, args.output, args.manifest)):
        parser.error("single mode requires --input --config --output --manifest")
    result = execute_pipeline(args.input.read_bytes(), json.loads(args.config.read_text(encoding="utf-8")), root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result.midi)
    args.manifest.write_text(json.dumps(result.manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"PIPELINE PASS: {result.manifest['outputHash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())