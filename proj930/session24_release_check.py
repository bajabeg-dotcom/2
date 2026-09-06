#!/usr/bin/env python3
"""Run the Session 24 Premium Solo/Expression software release gate."""

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
    build_expression_plan,
    remove_ai_expression_layer,
)
from dna_midi_studio.session24_fixture import build_session24_chain  # noqa: E402


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _update_feature_matrix() -> None:
    path = ROOT / "data" / "premium-feature-matrix.json"
    matrix = json.loads(path.read_text(encoding="utf-8"))
    matrix["softwareBaseline"] = "4.2-alpha"
    for feature in matrix["features"]:
        if feature["session"] == 24:
            feature.update({
                "status": "SOFTWARE_VALIDATED / PRODUCTION_EVIDENCE_BLOCKED",
                "evidence": "data/session24-test-report.json",
                "limitations": [
                    "ExpressionPlan is a removable read-only preview layer and does not render final MIDI",
                    "Built-in ornament/relationship evidence is SOFTWARE_TEST_ONLY; production evidence and listening/device gates remain required",
                ],
            })
    matrix["premiumProductStatus"] = "PLANNED"
    _write_json(path, matrix)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session24.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    midi, song_map, brief, graph, candidate, groove, controls, evidence = build_session24_chain(ROOT)
    plan = build_expression_plan(midi, groove, song_map, ROOT, controls, evidence)
    repeated = build_expression_plan(midi, groove, song_map, ROOT, controls, evidence)
    removal = remove_ai_expression_layer(plan)

    artifacts = ROOT / "artifacts"
    paths = {
        "referenceMidi": artifacts / "session24-reference.mid",
        "songMap": artifacts / "session24-song-map.json",
        "groovePlan": artifacts / "session24-groove-plan.json",
        "controls": artifacts / "session24-expression-controls.json",
        "evidence": artifacts / "session24-reference-evidence.json",
        "expressionPlan": artifacts / "session24-expression-plan.json",
        "removal": artifacts / "session24-remove-ai-layer.json",
    }
    paths["referenceMidi"].write_bytes(midi.to_bytes())
    for name, value in (("songMap", song_map), ("groovePlan", groove),
                        ("controls", controls), ("evidence", evidence),
                        ("expressionPlan", plan), ("removal", removal)):
        _write_json(paths[name], value)

    layer_counts = {item["subtype"]: len(item["events"]) for item in plan["layers"]}
    production_eligible_notes = sum(item["productionEligible"] for layer in plan["layers"] for item in layer["events"])
    benchmark = {
        "schema": "dna-session24-expression-benchmark", "version": "1.0",
        "date": date.today().isoformat(), "license": "self-authored-test-fixtures",
        "sourceMidiSha256": midi.digest(), "songMapHash": song_map["mapHash"],
        "groovePlanHash": groove["groovePlanHash"],
        "expressionPlanHash": plan["expressionPlanHash"],
        "deterministic": plan["expressionPlanHash"] == repeated["expressionPlanHash"],
        "originalNoteCount": plan["audit"]["originalNoteCount"],
        "originalFingerprintSha256": plan["source"]["originalSoloFingerprint"]["sha256"],
        "layerCounts": layer_counts, "generatedNoteCount": plan["audit"]["generatedNoteCount"],
        "cc11PointCount": plan["audit"]["cc11PointCount"],
        "maximumEstimatedPeak": plan["audit"]["maximumEstimatedPeak"],
        "softwareMidiNoteCeiling": 54,
        "aBPreviewCount": len(plan["previews"]),
        "removalEventCount": len(removal["removedEventIds"]),
        "productionEligibleGeneratedNotes": production_eligible_notes,
        "referenceEvidenceAuthority": plan["evidence"]["authority"],
        "previewReady": plan["readyForPreview"],
        "productionRenderReady": plan["readyForProductionRender"],
        "passed": all((
            plan["readyForPreview"], not plan["readyForProductionRender"],
            plan["audit"]["allVariantsWithinMidiNoteCeiling"],
            plan["audit"]["sourceNoteUidCoverage"], plan["audit"]["evidenceCoverage"],
            plan["audit"]["reasonCodeCoverage"], removal["originalNotesPreserved"],
            removal["soundBindingPreserved"], production_eligible_notes == 0,
        )),
    }
    benchmark["benchmarkHash"] = sha256(_canonical({key: value for key, value in benchmark.items()
                                                     if key != "benchmarkHash"})).hexdigest()
    benchmark_path = ROOT / "data" / "session24-benchmark-report.json"
    _write_json(benchmark_path, benchmark)
    if not benchmark["passed"]:
        raise RuntimeError("Session 24 solo/expression benchmark failed")

    schema_file = ROOT / "premium" / "schemas" / "v2" / "expression-plan-v2.schema.json"
    schema_value = json.loads(schema_file.read_text(encoding="utf-8"))
    catalog = {
        "schema": "dna-session24-schema-catalog", "version": "1.0",
        "date": date.today().isoformat(),
        "contracts": [{"name": schema_file.name, "$id": schema_value["$id"],
                       "contractVersion": schema_value["x-contract-version"],
                       "sha256": sha256(schema_file.read_bytes()).hexdigest()}],
    }
    catalog["catalogHash"] = sha256(_canonical(catalog["contracts"])).hexdigest()
    catalog_path = ROOT / "data" / "session24-schema-catalog.json"
    _write_json(catalog_path, catalog)
    _update_feature_matrix()

    report = {
        "schema": "dna-session24-test-report", "version": "1.0",
        "date": date.today().isoformat(), "result": "pass",
        "scope": "phrase-aware-solo-expression-preview-fingerprint-soundbinding-and-polyphony-safety",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures),
                        "errors": len(result.errors)},
        "benchmark": {"report": str(benchmark_path.relative_to(ROOT)),
                      **{key: benchmark[key] for key in (
                          "originalNoteCount", "layerCounts", "generatedNoteCount",
                          "cc11PointCount", "maximumEstimatedPeak", "aBPreviewCount",
                          "removalEventCount", "referenceEvidenceAuthority",
                          "previewReady", "productionRenderReady", "benchmarkHash")}},
        "artifacts": {name: str(path.relative_to(ROOT)) for name, path in paths.items()}
                     | {"schemaCatalog": str(catalog_path.relative_to(ROOT))},
        "transports": {"cli": "session24_expression_plan.py",
                       "api": "/api/premium-expression-plan",
                       "guiCard": "PREMIUM SOLO & EXPRESSION 2.0", "apiGuiParity": True},
        "invariants": {
            "originalSoloFingerprintUnchanged": True, "soundBindingUnchanged": True,
            "everyGeneratedEventHasSourceNoteUid": True,
            "everyGeneratedEventHasEvidenceId": True,
            "everyGeneratedEventHasReasonCode": True,
            "factoryVelocityAndCc11Only": True, "goldAffectsDynamics": False,
            "phraseAwareOrnaments": True, "diatonicThird": True,
            "nonRecursiveSeparateEcho": True, "groovePlanBudgetBeforeAddition": True,
            "softwareMidiNoteCeiling": 54, "oneClickAiLayerRemoval": True,
            "readOnly": True, "midiMutationAllowed": False, "finalMidiGenerated": False,
            "referenceEvidenceProductionEligible": False,
        },
        "status": {
            "session24SoloExpression": "SOFTWARE_VALIDATED / PRODUCTION_EVIDENCE_BLOCKED",
            "activeSoftwareBaseline": "4.2-alpha", "aiArrangerAlpha": "SOFTWARE_VALIDATED / ALPHA",
            "productionOrnamentEvidence": "MISSING", "listeningGate": "PENDING",
            "aiPremiumArranger": "PLANNED", "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data" / "session24-test-report.json"
    _write_json(report_path, report)

    release_path = ROOT / "data" / "release-check-report.json"
    if release_path.is_file():
        release = json.loads(release_path.read_text(encoding="utf-8"))
        release.setdefault("premiumReadiness", {}).update({
            "softwareBaseline": "4.2-alpha", "session24": f"{result.testsRun}/{result.testsRun} PASS",
            "expressionPlan2": "SOFTWARE_VALIDATED / PRODUCTION_EVIDENCE_BLOCKED",
            "aiArranger": "ALPHA", "premiumProduct": "PLANNED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(release_path, release)
    compliance_path = ROOT / "data" / "master-prompt-compliance.json"
    if compliance_path.is_file():
        compliance = json.loads(compliance_path.read_text(encoding="utf-8"))
        compliance.setdefault("summary", {}).update({
            "session24SoloExpression": f"{result.testsRun}/{result.testsRun} PASS",
            "activeSoftwareBaseline": "4.2-alpha",
            "productionOrnamentEvidence": "MISSING", "aiArranger": "ALPHA",
            "aiPremiumArranger": "PLANNED", "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(compliance_path, compliance)
    print(f"Session 24 PASS: {result.testsRun}/{result.testsRun}; generated={benchmark['generatedNoteCount']}; peak={benchmark['maximumEstimatedPeak']}/54; {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())