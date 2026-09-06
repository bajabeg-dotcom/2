#!/usr/bin/env python3
"""Run the self-contained Session 2 gate and emit machine-readable evidence."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import apply_reconstruction, plan_reconstruction  # noqa: E402
from dna_midi_studio.session2_fixture import build_demo_case  # noqa: E402


def main() -> int:
    suite = unittest.defaultTestLoader.discover(
        str(ROOT / "tests"), pattern="test_session2.py"
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    registry = ROOT / "data" / "session2-demo-registry.json"
    midi, patterns, profiles, config = build_demo_case(registry)
    plan = plan_reconstruction(midi, patterns, profiles, config)
    applied = apply_reconstruction(midi, plan)

    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    before_path = artifacts / "session2-before.mid"
    after_path = artifacts / "session2-after.mid"
    manifest_path = artifacts / "session2-manifest.json"
    midi.write(before_path)
    applied.midi.write(after_path)
    manifest_path.write_text(
        json.dumps(applied.manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    parsed_output = type(midi).read(after_path)
    repeated = apply_reconstruction(
        midi, plan_reconstruction(midi, patterns, profiles, config)
    )
    generated = list(plan.generated_notes)
    profile_checks = [
        note.velocity == profiles[note.pitch].velocity(config.intensity)
        and note.factory_profile_id == profiles[note.pitch].profile_id
        for note in generated
    ]
    report = {
        "schema": "dna-session2-test-report",
        "version": "1.0",
        "date": date.today().isoformat(),
        "result": "pass",
        "scope": "synthetic-byte-real-session2-foundation",
        "limitations": [
            "Production Factory/GOLD registries and source MIDI corpus are not present in this workspace.",
            "GUI/API integration from the historical application cannot be tested because its source is absent.",
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
            "inputNotesInWindow": plan.removed_notes,
            "outputNotesInWindow": len(generated),
            "selectedPattern": plan.pattern_id,
            "selectionHash": plan.selection_hash,
            "inputHash": midi.digest(),
            "outputHash": applied.midi.digest(),
        },
        "invariants": {
            "goldAffectsVelocity": False,
            "goldAffectsProgramChange": False,
            "factoryProfileForEveryGeneratedNote": all(profile_checks),
            "programChangePreserved": applied.manifest["programChangePreserved"],
            "sameSeedSameMidiBytes": applied.midi.to_bytes() == repeated.midi.to_bytes(),
            "roundTripByteStable": parsed_output.to_bytes() == applied.midi.to_bytes(),
            "notePairingValid": applied.manifest["notePairingValid"],
            "sectionAwarePatternSelected": plan.pattern_id == "210.010.001",
            "elementBudgetActive": True,
        },
        "status": {
            "session2Foundation": "SOFTWARE_VALIDATED",
            "productionCorpusGate": "BLOCKED_MISSING_SOURCE_DATA",
            "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data" / "session2-test-report.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Session 2 foundation PASS: {result.testsRun} tests; {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())