#!/usr/bin/env python3
"""Create/import ArticulationMap 2.0 or build a read-only trigger plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import (  # noqa: E402
    build_articulation_plan,
    build_reference_articulation_capture,
    import_articulation_capture,
)
from dna_midi_studio.midi import MidiFile  # noqa: E402


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Session 25 exact-sound articulation mapping")
    commands = parser.add_subparsers(dest="command", required=True)

    reference = commands.add_parser("reference", help="write the SOFTWARE_TEST_ONLY capture/catalog")
    reference.add_argument("midi", type=Path)
    reference.add_argument("capture_output", type=Path)
    reference.add_argument("catalog_output", type=Path)

    importer = commands.add_parser("import", help="validate a capture and build a normalized catalog")
    importer.add_argument("capture", type=Path)
    importer.add_argument("output", type=Path)
    importer.add_argument("--approved-hashes", type=Path)

    planner = commands.add_parser("plan", help="build a read-only articulation trigger plan")
    planner.add_argument("midi", type=Path)
    planner.add_argument("catalog", type=Path)
    planner.add_argument("groove_plan", type=Path)
    planner.add_argument("controls", type=Path)
    planner.add_argument("output", type=Path)
    planner.add_argument("--expression-plan", type=Path)

    args = parser.parse_args(argv)
    if args.command == "reference":
        midi = MidiFile.read(args.midi)
        capture = build_reference_articulation_capture(midi.digest())
        catalog = import_articulation_capture(capture)
        _write(args.capture_output, capture)
        _write(args.catalog_output, catalog)
        print(f"Capture: {capture['captureHash']}")
        print(f"Catalog: {catalog['catalogHash']} · {catalog['productionStatus']}")
        return 0
    if args.command == "import":
        hashes: list[str] = []
        if args.approved_hashes:
            document = _load(args.approved_hashes)
            hashes = document.get("approvedCaptureHashes", [])
        catalog = import_articulation_capture(_load(args.capture), hashes)
        _write(args.output, catalog)
        print(f"Catalog: {catalog['catalogHash']} · {catalog['productionStatus']}")
        return 0
    plan = build_articulation_plan(
        MidiFile.read(args.midi), _load(args.catalog), _load(args.groove_plan),
        _load(args.expression_plan) if args.expression_plan else None, _load(args.controls),
    )
    _write(args.output, plan)
    print(f"ArticulationPlan: {plan['articulationPlanHash']}")
    print(f"Events: {plan['audit']['generatedEventCount']}; peak {plan['audit']['estimatedPeak']}/54")
    print(f"Preview: {plan['readyForPreview']}; production render: {plan['readyForProductionRender']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
