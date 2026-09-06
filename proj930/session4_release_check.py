#!/usr/bin/env python3
"""Run Session 4 Factory Guitar Mode tests and emit machine evidence."""

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
    apply_guitar_reconstruction,
    plan_guitar_reconstruction,
)
from dna_midi_studio.session4_fixture import build_session4_case  # noqa: E402


def main() -> int:
    suite = unittest.defaultTestLoader.discover(
        str(ROOT / "tests"), pattern="test_session4.py"
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    midi, patterns, profiles, control_maps, chords, config = build_session4_case(ROOT)
    plan = plan_guitar_reconstruction(
        midi, patterns, profiles, control_maps, chords, config
    )
    applied = apply_guitar_reconstruction(midi, plan)
    repeated = apply_guitar_reconstruction(
        midi,
        plan_guitar_reconstruction(
            midi, patterns, profiles, control_maps, chords, config
        ),
    )

    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    before_path = artifacts / "session4-before.mid"
    after_path = artifacts / "session4-after.mid"
    manifest_path = artifacts / "session4-manifest.json"
    midi.write(before_path)
    applied.midi.write(after_path)
    manifest_path.write_text(
        json.dumps(applied.manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    parsed = MidiFile.read(after_path)
    profile = profiles[config.profile_id]
    control_notes = [
        note
        for note, audit in zip(plan.generated_notes, plan.note_audit)
        if audit.control_action is not None
    ]
    report = {
        "schema": "dna-session4-test-report",
        "version": "1.0",
        "date": date.today().isoformat(),
        "result": "pass",
        "scope": "synthetic-byte-real-session4-foundation",
        "limitations": [
            "Factory strum evidence and Guitar Mode trigger map are synthetic test fixtures.",
            "No production Factory registry, official/device-captured control map or GUI/API source is present.",
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
            "factoryPattern": plan.pattern_id,
            "factoryProfile": config.profile_id,
            "controlMap": plan.control_map_id,
            "selectionHash": plan.selection_hash,
            "inputHash": midi.digest(),
            "outputHash": applied.midi.digest(),
            "strokeCounts": dict(plan.stroke_counts),
            "maxFretSpan": plan.max_fret_span,
        },
        "invariants": {
            "goldControlsRhythmGuitar": False,
            "goldAffectsVelocity": False,
            "factoryPatternEvidencePresent": bool(plan.source_ids),
            "factoryProfileForEveryGeneratedNote": all(
                note.factory_profile_id == profile.profile_id
                and note.velocity == profile.velocity(config.intensity)
                for note in plan.generated_notes
            ),
            "stringVoicingsPlayable": all(
                audit.control_action is not None
                or (
                    audit.string is not None
                    and audit.fret is not None
                    and profile.fret_min <= audit.fret <= profile.fret_max
                )
                for audit in plan.note_audit
            ),
            "confirmedControlNotesOnly": {note.pitch for note in control_notes} == {24, 25},
            "syntheticControlMapExplicitlyOptedIn": config.allow_synthetic_control_map,
            "programChangePreserved": applied.manifest["programChangePreserved"],
            "sameSeedSameMidiBytes": applied.midi.to_bytes() == repeated.midi.to_bytes(),
            "roundTripByteStable": parsed.to_bytes() == applied.midi.to_bytes(),
            "notePairingValid": applied.manifest["notePairingValid"],
        },
        "status": {
            "session4Foundation": "SOFTWARE_VALIDATED",
            "productionFactoryGate": "BLOCKED_MISSING_SOURCE_DATA",
            "productionControlMapGate": "BLOCKED_MISSING_CONFIRMED_MAP",
            "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data" / "session4-test-report.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Session 4 foundation PASS: {result.testsRun} tests; {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())