#!/usr/bin/env python3
"""Run Session 6 RX tests and emit machine evidence."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import MidiFile, apply_rx_events, plan_rx_events  # noqa: E402
from dna_midi_studio.session6_fixture import build_session6_case  # noqa: E402


def main() -> int:
    suite = unittest.defaultTestLoader.discover(
        str(ROOT / "tests"), pattern="test_session6.py"
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    midi, rx_maps, profiles, config = build_session6_case(ROOT)
    plan = plan_rx_events(midi, rx_maps, profiles, config)
    applied = apply_rx_events(midi, plan)
    repeated = apply_rx_events(
        midi, plan_rx_events(midi, rx_maps, profiles, config)
    )

    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    before_path = artifacts / "session6-before.mid"
    after_path = artifacts / "session6-after.mid"
    manifest_path = artifacts / "session6-manifest.json"
    midi.write(before_path)
    applied.midi.write(after_path)
    manifest_path.write_text(
        json.dumps(applied.manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    parsed = MidiFile.read(after_path)
    report = {
        "schema": "dna-session6-test-report",
        "version": "1.0",
        "date": date.today().isoformat(),
        "result": "pass",
        "scope": "synthetic-byte-real-session6-rx-foundation",
        "limitations": [
            "The confirmed RX map is synthetic and requires explicit test opt-in.",
            "No official or device-captured Pa800 RX map is present in this snapshot.",
            "Historical GUI/API integration and physical Pa800 listening are unavailable.",
        ],
        "formalSuite": {
            "testsRun": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
        },
        "fixture": {
            "input": str(before_path.relative_to(ROOT)),
            "output": str(after_path.relative_to(ROOT)),
            "manifest": str(manifest_path.relative_to(ROOT)),
            "sourceNotes": 6,
            "generatedRxEvents": len(plan.generated_notes),
            "counts": dict(plan.counts),
            "selectionHash": plan.selection_hash,
            "inputHash": midi.digest(),
            "outputHash": applied.midi.digest(),
        },
        "invariants": {
            "rxTriggersGuessed": False,
            "exactSoundMatchRequired": True,
            "unconfirmedMapBlocked": True,
            "syntheticMapRequiresOptIn": True,
            "analysisVelocityUsed": False,
            "goldAffectsVelocity": False,
            "factoryVelocityOnly": all(
                note.factory_profile_id == config.profile_id
                for note in plan.generated_notes
            ),
            "originalEventsPreserved": applied.manifest["originalEventsPreserved"],
            "targetSoundPreserved": applied.manifest["targetSoundPreserved"],
            "sameSeedSameMidiBytes": applied.midi.to_bytes() == repeated.midi.to_bytes(),
            "roundTripByteStable": parsed.to_bytes() == applied.midi.to_bytes(),
            "notePairingValid": applied.manifest["notePairingValid"],
        },
        "status": {
            "session6Foundation": "SOFTWARE_VALIDATED",
            "productionRxMapGate": "BLOCKED_MISSING_CONFIRMED_MAP",
            "productionGuiApiGate": "BLOCKED_MISSING_LEGACY_SOURCE_TREE",
            "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data" / "session6-test-report.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Session 6 foundation PASS: {result.testsRun} tests; {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())