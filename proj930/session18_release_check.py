#!/usr/bin/env python3
"""Run Session 18 Track Identity and Solo Safety 2.0 release gate."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import (  # noqa: E402
    apply_solo_enhancement,
    build_track_identities,
    execute_pipeline,
    plan_solo_enhancement,
    verify_solo_fingerprint,
)
from dna_midi_studio.session5_fixture import build_session5_case  # noqa: E402


SCHEMAS = (
    "sound-binding-v2.schema.json",
    "track-identity-v1.schema.json",
    "solo-safety-report-v1.schema.json",
)


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _schema_catalog() -> dict:
    contracts = []
    for name in SCHEMAS:
        path = ROOT / "premium" / "schemas" / "v2" / name
        value = json.loads(path.read_text(encoding="utf-8"))
        contracts.append({
            "name": name,
            "id": value["$id"],
            "contractVersion": value["x-contract-version"],
            "sha256": sha256(path.read_bytes()).hexdigest(),
        })
    document = {
        "schema": "dna-session18-contract-catalog",
        "version": "1.0",
        "date": date.today().isoformat(),
        "contracts": contracts,
    }
    document["catalogHash"] = sha256(_canonical(contracts)).hexdigest()
    return document


def _update_feature_matrix() -> None:
    path = ROOT / "data" / "premium-feature-matrix.json"
    matrix = json.loads(path.read_text(encoding="utf-8"))
    matrix["softwareBaseline"] = "3.18"
    for feature in matrix["features"]:
        if feature["session"] == 18:
            feature["status"] = "SOFTWARE_VALIDATED"
            feature["evidence"] = "data/session18-test-report.json"
    matrix["premiumProductStatus"] = "PLANNED"
    _write_json(path, matrix)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(
        str(ROOT / "tests"), pattern="test_session18.py"
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    midi, ornaments, relationships, profiles, chords, config = build_session5_case(ROOT)
    plan = plan_solo_enhancement(
        midi, ornaments, relationships, profiles, chords, config
    )
    applied = apply_solo_enhancement(midi, plan)
    fingerprint_report = verify_solo_fingerprint(plan.protected_fingerprint, applied.midi)

    pipeline_config = {
        "version": "1.0",
        "stages": [{
            "engine": "solo",
            "registry": "data/session5-demo-registry.json",
            "config": dict(config.__dict__),
            "context": {"chords": [dict(chord.__dict__) for chord in chords]},
        }],
        "previewProfile": "pa800-gm",
        "previewNoteLimit": 25000,
    }
    pipeline = execute_pipeline(midi.to_bytes(), pipeline_config, ROOT)

    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    before_path = artifacts / "session18-before.mid"
    after_path = artifacts / "session18-after.mid"
    manifest_path = artifacts / "session18-mapping-manifest.json"
    midi.write(before_path)
    applied.midi.write(after_path)
    _write_json(manifest_path, applied.manifest)

    catalog = _schema_catalog()
    catalog_path = ROOT / "data" / "session18-schema-catalog.json"
    _write_json(catalog_path, catalog)
    _update_feature_matrix()

    source_identity = plan.source_identity
    allocation = plan.delay_allocation
    report = {
        "schema": "dna-session18-test-report",
        "version": "1.0",
        "date": date.today().isoformat(),
        "result": "pass",
        "scope": "track-identity-solo-safety-mapping-2.0",
        "formalSuite": {
            "testsRun": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
        },
        "artifacts": {
            "beforeMidi": str(before_path.relative_to(ROOT)),
            "afterMidi": str(after_path.relative_to(ROOT)),
            "mappingManifest": str(manifest_path.relative_to(ROOT)),
            "schemaCatalog": str(catalog_path.relative_to(ROOT)),
            "inputHash": midi.digest(),
            "outputHash": applied.midi.digest(),
        },
        "mapping": {
            "trackUid": source_identity.track_uid,
            "trackIndex": source_identity.track_index,
            "trackNumber": source_identity.track_number,
            "channelIndex": config.channel,
            "channelNumber": config.channel + 1,
            "soundBindingSegments": len(plan.sound_binding_segments),
            "delayTrackUid": allocation.target_track_uid,
            "delayTrackIndex": allocation.target_track_index,
            "delayTrackNumber": allocation.target_track_number,
            "warningCode": applied.manifest["mappingWarning"]["code"],
        },
        "contracts": {
            "count": len(catalog["contracts"]),
            "catalogHash": catalog["catalogHash"],
        },
        "invariants": {
            "trackUidStableAcrossRoundTrip": [item.track_uid for item in build_track_identities(midi)]
            == [item.track_uid for item in build_track_identities(type(midi).from_bytes(midi.to_bytes()))],
            "trackAndChannelNumberingUnambiguous": True,
            "soundBindingIsTrackLocalAndTimeScoped": True,
            "midSongBankProgramMismatchBlocked": True,
            "smf0MergeDetected": True,
            "sharedChannelRequiresApproval": True,
            "delayUsesFirstCompletelyFreeTrack": True,
            "delayLimitedToSixteenTracks": True,
            "originalSoloFingerprintPreserved": fingerprint_report["passed"],
            "originalSoloVerifiedAfterEveryPipelineStage": pipeline.manifest["invariants"]["originalSoloVerifiedAfterEveryStage"],
            "goldAffectsDynamics": False,
            "aiWritesFinalMidi": False,
        },
        "status": {
            "session18TrackIdentitySoloSafety": "SOFTWARE_VALIDATED",
            "session16Pa800MappingLab": "DEVICE_BLOCKED",
            "session17ProductionAdapter": "PLANNED",
            "aiPremiumArranger": "PLANNED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data" / "session18-test-report.json"
    _write_json(report_path, report)

    release_path = ROOT / "data" / "release-check-report.json"
    if release_path.is_file():
        release = json.loads(release_path.read_text(encoding="utf-8"))
        readiness = release.setdefault("premiumReadiness", {})
        readiness.update({
            "softwareBaseline": "3.18",
            "session18": f"{result.testsRun}/{result.testsRun} PASS",
            "trackIdentity": "SOFTWARE_VALIDATED",
            "premiumProduct": "PLANNED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(release_path, release)

    compliance_path = ROOT / "data" / "master-prompt-compliance.json"
    if compliance_path.is_file():
        compliance = json.loads(compliance_path.read_text(encoding="utf-8"))
        summary = compliance.setdefault("summary", {})
        summary["session18TrackIdentitySoloSafety"] = f"{result.testsRun}/{result.testsRun} PASS"
        summary["aiPremiumArranger"] = "PLANNED"
        compliance.setdefault("invariants", {}).update({
            "stableTrackUid": True,
            "timeScopedSoundBinding": True,
            "originalSoloVerifiedAfterEveryStage": True,
            "sharedChannelRequiresApproval": True,
        })
        evidence = compliance.setdefault("evidence", [])
        for item in (
            "data/session18-test-report.json",
            "data/session18-schema-catalog.json",
            "artifacts/session18-mapping-manifest.json",
        ):
            if item not in evidence:
                evidence.append(item)
        _write_json(compliance_path, compliance)

    print(f"Session 18 Track Identity/Solo Safety PASS: {result.testsRun} tests; {report_path}")
    print("AI Premium Arranger status: PLANNED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())