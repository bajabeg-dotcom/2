#!/usr/bin/env python3
"""Run the Session 29 local Personal Producer Profile software gate."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio.session29_fixture import build_session29_chain  # noqa: E402


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _orders(overlay: dict) -> list[list[str]]:
    return [item["adjustedOrder"] for item in overlay["requests"]]


def _update_feature_matrix() -> None:
    path = ROOT / "data" / "premium-feature-matrix.json"
    matrix = json.loads(path.read_text(encoding="utf-8"))
    matrix["softwareBaseline"] = "4.7-profile-alpha"
    for feature in matrix["features"]:
        if feature["session"] == 29:
            feature.update({
                "status": "SOFTWARE_VALIDATED / LOCAL_EXPLICIT_ONLY",
                "evidence": "data/session29-test-report.json",
                "blocker": None,
                "limitations": [
                    "The profile affects only soft ranking of candidates that already passed hard constraints",
                    "Learning requires explicit accepted variants or explicit manual locks",
                    "The profile stores no MIDI, project, audio or cloud telemetry content",
                ],
            })
    matrix["premiumProductStatus"] = "PLANNED"
    _write_json(path, matrix)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session29.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    if result.testsRun != 120:
        raise RuntimeError(f"Session 29 expected 120 tests, got {result.testsRun}")

    fixture = build_session29_chain(ROOT)
    profile = fixture["personalProfile"]
    overlay = fixture["rankingOverlay"]
    cold = fixture["coldStartOverlay"]
    disabled = fixture["disabledOverlay"]
    deleted = fixture["deletedOverlay"]
    artifacts = ROOT / "artifacts"
    paths = {
        "referenceMidi": artifacts / "session29-reference.mid",
        "learningEvents": artifacts / "session29-learning-events.json",
        "sourceManifest": artifacts / "session29-source-manifest.json",
        "personalProfile": artifacts / "session29-personal-profile.json",
        "rankingOverlay": artifacts / "session29-ranking-overlay.json",
        "coldStartProfile": artifacts / "session29-cold-start-profile.json",
        "coldStartOverlay": artifacts / "session29-cold-start-overlay.json",
        "editedProfile": artifacts / "session29-edited-profile.json",
        "editedOverlay": artifacts / "session29-edited-overlay.json",
        "disabledProfile": artifacts / "session29-disabled-profile.json",
        "disabledOverlay": artifacts / "session29-disabled-overlay.json",
        "profileExport": artifacts / "session29-profile-export.json",
        "profileDeletion": artifacts / "session29-profile-deletion.json",
        "deletedOverlay": artifacts / "session29-deleted-overlay.json",
    }
    paths["referenceMidi"].write_bytes(fixture["midi"].to_bytes())
    documents = fixture["documents"]
    values = {
        "learningEvents": fixture["learningEvents"],
        "sourceManifest": {
            "schema": "dna-session29-profile-source-manifest", "version": "1.0",
            "date": date.today().isoformat(),
            "workflowHash": fixture["workflow"]["workflowHash"],
            "producerBriefHash": documents["producerBrief"]["briefHash"],
            "arrangementGraphHash": documents["arrangementGraph"]["graphHash"],
            "candidateSetHash": documents["candidateSet"]["candidateSetHash"],
            "midiSha256": fixture["midi"].digest(),
        },
        "personalProfile": profile, "rankingOverlay": overlay,
        "coldStartProfile": fixture["coldStartProfile"], "coldStartOverlay": cold,
        "editedProfile": fixture["editedProfile"], "editedOverlay": fixture["editedOverlay"],
        "disabledProfile": fixture["disabledProfile"], "disabledOverlay": disabled,
        "profileExport": fixture["profileExport"],
        "profileDeletion": fixture["profileDeletion"], "deletedOverlay": deleted,
    }
    for name, value in values.items():
        _write_json(paths[name], value)

    audit = overlay["audit"]
    cold_orders = _orders(cold)
    benchmark = {
        "schema": "dna-session29-personal-profile-benchmark", "version": "1.0",
        "date": date.today().isoformat(), "license": "self-authored-test-fixtures",
        "sourceMidiSha256": fixture["midi"].digest(),
        "workflowHash": fixture["workflow"]["workflowHash"],
        "candidateSetHash": documents["candidateSet"]["candidateSetHash"],
        "profileHash": profile["profileHash"], "overlayHash": overlay["overlayHash"],
        "explicitLearningEventCount": profile["learning"]["eventCount"],
        "acceptedVariantCount": profile["learning"]["acceptedVariantCount"],
        "manualLockCount": profile["learning"]["manualLockCount"],
        "implicitLearningCount": profile["audit"]["implicitLearningCount"],
        "genrePreferenceCount": len(profile["preferences"]["genres"]),
        "rolePreferenceCount": len(profile["preferences"]["roles"]),
        "markerPreferenceCount": len(profile["preferences"]["markers"]),
        "patternPreferenceCount": len(profile["preferences"]["patterns"]),
        "registerPreferenceCount": len(profile["preferences"]["registerBands"]),
        "requestCount": audit["requestCount"],
        "eligibleCandidateCount": audit["eligibleCandidateCount"],
        "rerankedRequestCount": audit["rerankedRequestCount"],
        "rejectedCandidateCountUntouched": audit["rejectedCandidateCountUntouched"],
        "maximumAbsoluteBonus": audit["maximumAbsoluteBonus"],
        "coldStartRerankedRequestCount": cold["audit"]["rerankedRequestCount"],
        "disabledRerankedRequestCount": disabled["audit"]["rerankedRequestCount"],
        "deletedRerankedRequestCount": deleted["audit"]["rerankedRequestCount"],
        "deletedOrderEqualsColdStart": _orders(deleted) == cold_orders,
        "disabledOrderEqualsColdStart": _orders(disabled) == cold_orders,
        "exportContainsMidi": fixture["profileExport"]["containsMidi"],
        "exportContainsProject": fixture["profileExport"]["containsProject"],
        "exportContainsAudio": fixture["profileExport"]["containsAudio"],
        "deletionDataRetained": fixture["profileDeletion"]["dataRetained"],
        "deletionProfileUsable": fixture["profileDeletion"]["profileUsable"],
        "softwareProfilePassed": all((
            profile["learning"]["eventCount"] == 2,
            profile["learning"]["acceptedVariantCount"] == 1,
            profile["learning"]["manualLockCount"] == 1,
            profile["audit"]["implicitLearningCount"] == 0,
            len(profile["preferences"]["patterns"]) == 52,
            audit["requestCount"] == 52,
            audit["eligibleCandidateCount"] == 624,
            audit["rerankedRequestCount"] == 52,
            audit["rejectedCandidateCountUntouched"] == 829,
            0 < audit["maximumAbsoluteBonus"] <= 0.08,
            not audit["hardConstraintsReevaluated"],
            cold["audit"]["rerankedRequestCount"] == 0,
            disabled["audit"]["rerankedRequestCount"] == 0,
            deleted["audit"]["rerankedRequestCount"] == 0,
            _orders(deleted) == cold_orders, _orders(disabled) == cold_orders,
            not fixture["profileExport"]["containsMidi"],
            not fixture["profileExport"]["containsProject"],
            not fixture["profileExport"]["containsAudio"],
            not fixture["profileDeletion"]["dataRetained"],
            not fixture["profileDeletion"]["profileUsable"],
            profile["audit"]["profileAffectsSoftRankingOnly"],
            not profile["safety"]["hardConstraintAuthority"],
            not profile["safety"]["factoryDynamicsAuthority"],
            not profile["safety"]["soundBindingAuthority"],
            not profile["safety"]["validatorAuthority"],
            not profile["safety"]["midiMutationAllowed"],
        )),
    }
    benchmark["benchmarkHash"] = sha256(_canonical(benchmark)).hexdigest()
    benchmark_path = ROOT / "data" / "session29-benchmark-report.json"
    _write_json(benchmark_path, benchmark)
    if not benchmark["softwareProfilePassed"]:
        raise RuntimeError("Session 29 Personal Producer Profile benchmark failed")

    contracts = []
    for path in (
        ROOT / "premium/schemas/v2/personal-producer-profile-v2.schema.json",
        ROOT / "premium/schemas/v2/personal-ranking-overlay-v1.schema.json",
        ROOT / "premium/schemas/v2/personal-profile-deletion-v1.schema.json",
    ):
        value = json.loads(path.read_text(encoding="utf-8"))
        contracts.append({"name": path.name, "$id": value["$id"],
                          "contractVersion": value["x-contract-version"],
                          "sha256": sha256(path.read_bytes()).hexdigest()})
    schema_catalog = {
        "schema": "dna-session29-schema-catalog", "version": "1.0",
        "date": date.today().isoformat(), "contracts": contracts,
        "catalogHash": sha256(_canonical(contracts)).hexdigest(),
    }
    schema_catalog_path = ROOT / "data" / "session29-schema-catalog.json"
    _write_json(schema_catalog_path, schema_catalog)
    _update_feature_matrix()

    report = {
        "schema": "dna-session29-test-report", "version": "1.0",
        "date": date.today().isoformat(), "result": "pass",
        "scope": "local-explicit-only-personal-producer-profile-soft-ranking-edit-export-delete-and-neutral-reset",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures),
                        "errors": len(result.errors)},
        "benchmark": {"report": str(benchmark_path.relative_to(ROOT)),
                      **{key: benchmark[key] for key in (
                          "profileHash", "overlayHash", "explicitLearningEventCount",
                          "acceptedVariantCount", "manualLockCount", "implicitLearningCount",
                          "patternPreferenceCount", "requestCount", "eligibleCandidateCount",
                          "rerankedRequestCount", "rejectedCandidateCountUntouched",
                          "maximumAbsoluteBonus", "coldStartRerankedRequestCount",
                          "disabledRerankedRequestCount", "deletedRerankedRequestCount",
                          "deletedOrderEqualsColdStart", "disabledOrderEqualsColdStart",
                          "benchmarkHash")}},
        "artifacts": {name: str(path.relative_to(ROOT)) for name, path in paths.items()}
                     | {"schemaCatalog": str(schema_catalog_path.relative_to(ROOT))},
        "transports": {"cli": "session29_personal_profile.py",
                       "api": "/api/personal-producer-profile",
                       "guiWorkspace": "PERSONAL PRODUCER PROFILE 2.0", "apiGuiParity": True},
        "invariants": {
            "explicitAcceptedActionsOnly": True, "implicitLearning": False,
            "playbackLearning": False, "rejectionLearning": False,
            "cloudTelemetryLearning": False, "localOnly": True,
            "containsMidi": False, "containsProject": False, "containsAudio": False,
            "softRankingOnly": True, "hardConstraintAuthority": False,
            "factoryDynamicsAuthority": False, "soundBindingAuthority": False,
            "validatorAuthority": False, "bankProgramAuthority": False,
            "midiMutationAllowed": False, "completeDeletion": True,
            "coldStartNeutral": True, "deletionRestoresNeutralDeterminism": True,
        },
        "status": {
            "session29PersonalProducerProfile": "SOFTWARE_VALIDATED / LOCAL_EXPLICIT_ONLY",
            "activeSoftwareBaseline": "4.7-profile-alpha",
            "personalRanking": "SOFT_ONLY", "profileStorage": "LOCAL_ONLY",
            "finalMidiExport": "BLOCKED_QUALITY_DEVICE_AND_EVIDENCE",
            "humanListeningEvidence": "0/2 VERIFIED",
            "aiPremiumArranger": "PLANNED", "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data" / "session29-test-report.json"
    _write_json(report_path, report)

    release_path = ROOT / "data" / "release-check-report.json"
    if release_path.is_file():
        release = json.loads(release_path.read_text(encoding="utf-8"))
        release.setdefault("premiumReadiness", {}).update({
            "softwareBaseline": "4.7-profile-alpha",
            "session29": f"{result.testsRun}/{result.testsRun} PASS",
            "personalProducerProfile": "SOFTWARE_VALIDATED / LOCAL_EXPLICIT_ONLY",
            "personalRanking": "SOFT_ONLY", "profileStorage": "LOCAL_ONLY",
            "finalMidiExport": "BLOCKED", "verifiedHumanEvaluators": "0/2",
            "premiumProduct": "PLANNED", "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(release_path, release)
    compliance_path = ROOT / "data" / "master-prompt-compliance.json"
    if compliance_path.is_file():
        compliance = json.loads(compliance_path.read_text(encoding="utf-8"))
        compliance.setdefault("summary", {}).update({
            "session29PersonalProducerProfile": f"{result.testsRun}/{result.testsRun} PASS",
            "activeSoftwareBaseline": "4.7-profile-alpha",
            "personalRanking": "SOFT_ONLY", "profileStorage": "LOCAL_ONLY",
            "finalMidiExport": "BLOCKED", "humanListeningEvidence": "0/2 VERIFIED",
            "aiPremiumArranger": "PLANNED", "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(compliance_path, compliance)
    print(
        f"Session 29 PASS: {result.testsRun}/{result.testsRun}; events=2; "
        f"patterns={len(profile['preferences']['patterns'])}; requests={audit['requestCount']}; "
        f"rejected-untouched={audit['rejectedCandidateCountUntouched']}; {report_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())