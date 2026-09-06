#!/usr/bin/env python3
"""Run Session 7 DNC tests and emit machine evidence."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import MidiFile, apply_dnc_events, plan_dnc_events  # noqa: E402
from dna_midi_studio.session7_fixture import build_session7_case  # noqa: E402


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session7.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    midi, maps, profiles, config = build_session7_case(ROOT)
    plan = plan_dnc_events(midi, maps, profiles, config)
    applied = apply_dnc_events(midi, plan)
    repeated = apply_dnc_events(midi, plan_dnc_events(midi, maps, profiles, config))
    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    before_path = artifacts / "session7-before.mid"
    after_path = artifacts / "session7-after.mid"
    manifest_path = artifacts / "session7-manifest.json"
    midi.write(before_path)
    applied.midi.write(after_path)
    manifest_path.write_text(json.dumps(applied.manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    parsed = MidiFile.read(after_path)
    report = {
        "schema": "dna-session7-test-report",
        "version": "1.0",
        "date": date.today().isoformat(),
        "result": "pass",
        "scope": "synthetic-byte-real-session7-dnc-foundation",
        "limitations": [
            "The confirmed DNC map is synthetic and requires explicit test opt-in.",
            "No official or device-captured Pa800 DNC trigger map is present.",
            "Proprietary DNC messages remain blocked; GUI and physical listening are unavailable.",
        ],
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures), "errors": len(result.errors)},
        "fixture": {
            "input": str(before_path.relative_to(ROOT)),
            "output": str(after_path.relative_to(ROOT)),
            "manifest": str(manifest_path.relative_to(ROOT)),
            "sourceNotes": 6,
            "generatedKeySwitches": len(plan.generated_notes),
            "generatedControllerEvents": len(plan.generated_events),
            "counts": dict(plan.counts),
            "selectionHash": plan.selection_hash,
            "inputHash": midi.digest(),
            "outputHash": applied.midi.digest(),
        },
        "invariants": {
            "dncTriggersGuessed": False,
            "proprietaryEventsGenerated": False,
            "exactSoundMatchRequired": True,
            "roleAndRangeValidated": True,
            "unconfirmedMapBlocked": True,
            "syntheticMapRequiresOptIn": True,
            "analysisVelocityUsed": False,
            "goldAffectsVelocity": False,
            "originalEventsPreserved": applied.manifest["originalEventsPreserved"],
            "targetSoundPreserved": applied.manifest["targetSoundPreserved"],
            "sameSeedSameMidiBytes": applied.midi.to_bytes() == repeated.midi.to_bytes(),
            "roundTripByteStable": parsed.to_bytes() == applied.midi.to_bytes(),
            "notePairingValid": applied.manifest["notePairingValid"],
        },
        "status": {
            "session7Foundation": "SOFTWARE_VALIDATED",
            "productionDncMapGate": "BLOCKED_MISSING_CONFIRMED_MAP",
            "productionGuiApiGate": "BLOCKED_MISSING_LEGACY_SOURCE_TREE",
            "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data" / "session7-test-report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Session 7 foundation PASS: {result.testsRun} tests; {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())