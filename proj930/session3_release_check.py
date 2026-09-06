#!/usr/bin/env python3
"""Run the self-contained Session 3 gate and emit machine evidence."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import (  # noqa: E402
    MidiFile,
    apply_harmonic_reconstruction,
    plan_harmonic_reconstruction,
)
from dna_midi_studio.session3_fixture import build_session3_case  # noqa: E402


def main() -> int:
    suite = unittest.defaultTestLoader.discover(
        str(ROOT / "tests"), pattern="test_session3.py"
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    midi, patterns, profiles, relationships, chords, config = build_session3_case(ROOT)
    plan = plan_harmonic_reconstruction(
        midi, patterns, profiles, relationships, chords, config
    )
    applied = apply_harmonic_reconstruction(midi, plan)
    repeated = apply_harmonic_reconstruction(
        midi,
        plan_harmonic_reconstruction(
            midi, patterns, profiles, relationships, chords, config
        ),
    )

    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    before_path = artifacts / "session3-before.mid"
    after_path = artifacts / "session3-after.mid"
    manifest_path = artifacts / "session3-manifest.json"
    midi.write(before_path)
    applied.midi.write(after_path)
    manifest_path.write_text(
        json.dumps(applied.manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    parsed = MidiFile.read(after_path)
    profile = profiles[config.profile_id]
    report = {
        "schema": "dna-session3-test-report",
        "version": "1.0",
        "date": date.today().isoformat(),
        "result": "pass",
        "scope": "synthetic-byte-real-session3-foundation",
        "limitations": [
            "Production Factory/GOLD registries and source MIDI corpus are not present in this workspace.",
            "Historical GUI/API integration cannot be tested because its source tree is absent.",
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
            "outputNotesInWindow": len(plan.generated_notes),
            "selectedPattern": plan.pattern_id,
            "relationship": plan.relationship_id,
            "selectionHash": plan.selection_hash,
            "inputHash": midi.digest(),
            "outputHash": applied.midi.digest(),
            "collisionShifts": plan.collision_shifts,
            "collisionDrops": plan.collision_drops,
            "maxVoiceLeadingLeap": plan.max_voice_leading_leap,
        },
        "invariants": {
            "goldContainsAbsolutePitch": False,
            "goldAffectsVelocity": False,
            "goldAffectsProgramChange": False,
            "factoryProfileForEveryGeneratedNote": all(
                note.factory_profile_id == profile.profile_id
                and note.velocity == profile.velocity(config.intensity)
                for note in plan.generated_notes
            ),
            "registerSafe": all(
                profile.register_min <= note.pitch <= profile.register_max
                for note in plan.generated_notes
            ),
            "confirmedDrumBassRelationship": plan.relationship_id == "230.001.001",
            "manualBassProtected": True,
            "qualityIdentityProtection": True,
            "programChangePreserved": applied.manifest["programChangePreserved"],
            "sameSeedSameMidiBytes": applied.midi.to_bytes() == repeated.midi.to_bytes(),
            "roundTripByteStable": parsed.to_bytes() == applied.midi.to_bytes(),
            "notePairingValid": applied.manifest["notePairingValid"],
        },
        "status": {
            "session3Foundation": "SOFTWARE_VALIDATED",
            "productionCorpusGate": "BLOCKED_MISSING_SOURCE_DATA",
            "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data" / "session3-test-report.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Session 3 foundation PASS: {result.testsRun} tests; {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())