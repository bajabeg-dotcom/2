#!/usr/bin/env python3
"""Create a local Session 8 advisory job manifest from a JSON task spec."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from dna_midi_studio import AgentRuntime, TaskSpec  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Local advisory-only agent runtime")
    parser.add_argument("--team", type=Path, default=Path("agents/agent-team.json"))
    parser.add_argument("--task", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    runtime = AgentRuntime.from_file(args.team)
    raw = json.loads(args.task.read_text(encoding="utf-8"))
    spec = TaskSpec(**raw)
    runtime.create(spec)
    manifest = runtime.manifest(spec.task_id)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"PLANNED: {spec.task_id}; read-only brief; agent MIDI export disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())