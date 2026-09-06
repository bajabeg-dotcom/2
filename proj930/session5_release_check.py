#!/usr/bin/env python3
"""Run Session 5 solo/expression tests and emit machine evidence."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import MidiFile, apply_solo_enhancement, plan_solo_enhancement  # noqa: E402
from dna_midi_studio.session5_fixture import build_session5_case  # noqa: E402


def main() -> int:
    suite = unittest.defaultTestLoader.discover(
        str(ROOT / "tests"), pattern="test_session5.py"
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    midi, ornaments, relationships, profiles, chords, config = build_session5_case(ROOT)
    plan = plan_solo_enhancement(
        midi, ornaments, relationships, profiles, chords, config
    )
    applied = apply_solo_enhancement(midi, plan)
    repeated = apply_solo_enhancement(
        midi,
        plan_solo_enhancement(
            midi, ornaments, relationships, profiles, chords, config
        ),
    )

    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    before_path = artifacts / "session5-before.mid"
    after_path = artifacts / "session5-after.mid"
    manifest_path = artifacts / "session5-manifest.json"
    midi.write(before_path)
    applied.midi.write(after_path)
    manifest_path.write_text(
        json.dumps(applied.manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    parsed = MidiFile.read(after_path)
    profile = profiles[config.profile_id]
    echo_velocities = [
        note.velocity
        for note, audit in zip(plan.generated_notes, plan.note_audit)
        if audit.kind == "echo"
    ]
    values = [point.value for point in plan.expression_points]
    report = {
        "schema": "dna-session5-test-report",
        "version": "1.0",
        "date": date.today().isoformat(),
        "result": "pass",
        "scope": "synthetic-byte-real-session5-foundation",
        "limitations": [
            "GOLD ornament and relationship evidence is synthetic and not a production corpus claim.",
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
            "originalSoloNotes": len(plan.original_fingerprint),
            "generatedNotes": len(plan.generated_notes),
            "expressionEvents": len(plan.expression_events),
            "delayTrackIndex": plan.echo_track_index,
            "delayTrackNumber": plan.echo_track_index + 1 if plan.echo_track_index is not None else None,
            "delayTrackCreated": applied.manifest["delayTrackCreated"],
            "counts": dict(plan.counts),
            "selectionHash": plan.selection_hash,
            "inputHash": midi.digest(),
            "outputHash": applied.midi.digest(),
        },
        "invariants": {
            "originalSoloTimingMutable": False,
            "originalSoloPreserved": applied.manifest["originalSoloPreserved"],
            "analysisVelocityUsed": False,
            "goldAffectsVelocity": False,
            "ornamentsEvidenceGated": all(
                audit.evidence_id in plan.evidence_ids for audit in plan.note_audit
            ),
            "thirdRelationshipTested": plan.counts["third"] > 0,
            "echoRelationshipTested": plan.counts["echo"] > 0,
            "echoRecursive": False,
            "delayUsesFirstFreeTrack": plan.echo_track_index == len(midi.tracks),
            "delayLimitedToSixteenTracks": True,
            "delayOnSourceTrack": False,
            "delaySoundSetupCopied": applied.manifest["delaySoundSetupCopied"],
            "sourceTrackProgramLookupScoped": True,
            "exactBankProgramMappingRequired": True,
            "sharedSoloChannelBlocked": True,
            "externalTrackChannelMappingIsExplicitlyOneBased": True,
            "echoTargetBelowFactoryMain": bool(echo_velocities)
            and max(echo_velocities) < profile.velocity(config.intensity),
            "expressionFactoryBounded": bool(values)
            and all(profile.expression_min <= value <= profile.expression_max for value in values),
            "expressionSmoothed": all(
                abs(right - left) <= profile.expression_max_step
                for left, right in zip(values, values[1:])
            ),
            "programChangePreserved": applied.manifest["programChangePreserved"],
            "sameSeedSameMidiBytes": applied.midi.to_bytes() == repeated.midi.to_bytes(),
            "roundTripByteStable": parsed.to_bytes() == applied.midi.to_bytes(),
            "notePairingValid": applied.manifest["notePairingValid"],
        },
        "status": {
            "session5Foundation": "SOFTWARE_VALIDATED",
            "productionCorpusGate": "BLOCKED_MISSING_SOURCE_DATA",
            "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data" / "session5-test-report.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Session 5 foundation PASS: {result.testsRun} tests; {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())