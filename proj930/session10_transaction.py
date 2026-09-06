#!/usr/bin/env python3
"""Run the unified pipeline and atomically publish its validated MIDI."""

from __future__ import annotations

from hashlib import sha256
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from dna_midi_studio import AtomicMidiPublisher, MidiFile, TransactionIdentity, execute_pipeline  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Atomic DNA MIDI pipeline export")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    source = args.input.read_bytes()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = execute_pipeline(source, config, root)
    registry_hashes = [sha256((root / stage["registry"]).read_bytes()).hexdigest() for stage in config["stages"]]
    database_hash = sha256(":".join(registry_hashes).encode()).hexdigest()
    identity = TransactionIdentity(sha256(source).hexdigest(), result.manifest["configHash"], database_hash)
    verifier = lambda data: {"passed": MidiFile.from_bytes(data).to_bytes() == data, "kind": "midi-round-trip"}
    committed = AtomicMidiPublisher(args.output_dir).publish(result.midi, args.input.name, identity, verifier)
    print(f"{committed.status}: {committed.output_path}; resumed={committed.resumed}")
    return 0 if committed.status == "COMMITTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())