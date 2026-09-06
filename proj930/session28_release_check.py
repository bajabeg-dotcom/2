#!/usr/bin/env python3
"""Run the Session 28 Premium Producer workflow software gate."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import build_recovery_checkpoint, resume_workflow  # noqa: E402
from dna_midi_studio.session28_fixture import build_session28_chain  # noqa: E402


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _update_feature_matrix() -> None:
    path = ROOT / "data" / "premium-feature-matrix.json"
    matrix = json.loads(path.read_text(encoding="utf-8"))
    matrix["softwareBaseline"] = "4.6-workflow-alpha"
    for feature in matrix["features"]:
        if feature["session"] == 28:
            feature.update({
                "status": "SOFTWARE_VALIDATED / EXPORT_GATES_PENDING",
                "evidence": "data/session28-test-report.json",
                "blocker": "Human listening, production expression evidence and physical Pa800 certification are required for final export",
                "limitations": [
                    "The guided producer workflow is read-only and does not render final MIDI",
                    "Preview/project downloads remain available while final export is blocked",
                ],
            })
    matrix["premiumProductStatus"] = "PLANNED"
    _write_json(path, matrix)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session28.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    if result.testsRun != 112:
        raise RuntimeError(f"Session 28 expected 112 tests, got {result.testsRun}")

    fixture = build_session28_chain(ROOT)
    workflow = fixture["workflow"]
    documents = fixture["documents"]
    checkpoint = build_recovery_checkpoint(workflow, "VERIFY")
    resumed = resume_workflow(workflow, checkpoint)

    artifacts = ROOT / "artifacts"
    paths = {
        "referenceMidi": artifacts / "session28-reference.mid",
        "songMap": artifacts / "session28-song-map.json",
        "producerBrief": artifacts / "session28-producer-brief.json",
        "arrangementGraph": artifacts / "session28-arrangement-graph.json",
        "candidateSet": artifacts / "session28-candidate-set.json",
        "groovePlan": artifacts / "session28-groove-plan.json",
        "expressionPlan": artifacts / "session28-expression-plan.json",
        "previewSession": artifacts / "session28-preview-session.json",
        "evaluationReport": artifacts / "session28-evaluation-report.json",
        "workflowControls": artifacts / "session28-workflow-controls.json",
        "premiumWorkflow": artifacts / "session28-premium-workflow.json",
        "workflowDiff": artifacts / "session28-workflow-diff.json",
        "recoveryCheckpoint": artifacts / "session28-recovery-checkpoint.json",
        "resumeReport": artifacts / "session28-resume-report.json",
        "blindListeningPackage": artifacts / "session28-blind-listening-package.json",
        "audioManifests": artifacts / "session28-audio-manifests.json",
        "baselineReference": artifacts / "session28-baseline-reference.json",
        "validatorVerdict": artifacts / "session28-validator-verdict.json",
    }
    paths["referenceMidi"].write_bytes(fixture["midi"].to_bytes())
    values = {
        "songMap": documents["songMap"],
        "producerBrief": documents["producerBrief"],
        "arrangementGraph": documents["arrangementGraph"],
        "candidateSet": documents["candidateSet"],
        "groovePlan": documents["groovePlan"],
        "expressionPlan": documents["expressionPlan"],
        "previewSession": documents["previewSession"],
        "evaluationReport": documents["evaluationReport"],
        "workflowControls": fixture["workflowControls"],
        "premiumWorkflow": workflow,
        "workflowDiff": workflow["diff"],
        "recoveryCheckpoint": checkpoint,
        "resumeReport": resumed,
        "blindListeningPackage": fixture["blindPackage"],
        "audioManifests": fixture["audioManifests"],
        "baselineReference": fixture["baselineReference"],
        "validatorVerdict": fixture["validatorVerdict"],
    }
    for name, value in values.items():
        _write_json(paths[name], value)

    evaluation = documents["evaluationReport"]
    diff = workflow["diff"]
    completed = sum(item["status"] == "COMPLETE" for item in workflow["stages"])
    blocked = sum(item["status"] == "BLOCKED" for item in workflow["stages"])
    benchmark = {
        "schema": "dna-session28-workflow-benchmark", "version": "1.0",
        "date": date.today().isoformat(), "license": "self-authored-test-fixtures",
        "sourceMidiSha256": fixture["midi"].digest(),
        "workflowId": workflow["workflowId"], "workflowHash": workflow["workflowHash"],
        "selectedVariantId": workflow["controls"]["selectedVariantId"],
        "stageCount": len(workflow["stages"]), "completedStageCount": completed,
        "blockedStageCount": blocked, "blockedStageIds": [
            item["stageId"] for item in workflow["stages"] if item["status"] == "BLOCKED"
        ],
        "timelineItemCount": len(workflow["timeline"]),
        "trackMatrixRowCount": len(workflow["trackMatrix"]),
        "explainDecisionCount": len(workflow["explain"]),
        "backgroundJobCount": len(workflow["jobs"]),
        "commandPaletteCount": len(workflow["commandPalette"]),
        "baselineNoteCount": diff["notes"]["baseline"],
        "premiumPreviewNoteCount": diff["notes"]["premium"],
        "addedPreviewNoteCount": diff["notes"]["added"],
        "originalNotesChanged": diff["notes"]["originalNotesChanged"],
        "cc11PointCount": diff["controllers"]["cc11Added"],
        "soundBindingChanges": diff["soundSetup"]["soundBindingChanges"],
        "automatedQualityScore": evaluation["automated"]["overallScore"],
        "verifiedHumanEvaluatorCount": evaluation["listening"]["verifiedHumanEvaluatorCount"],
        "guidedWithoutTerminal": workflow["producerTask"]["guidedWithoutTerminal"],
        "referencePreviewTaskComplete": workflow["producerTask"]["referencePreviewTaskComplete"],
        "advancedWorkflowReproducible": workflow["producerTask"]["advancedReproducibleFromSeedAndProject"],
        "checkpointReadyToResume": resumed["status"] == "READY_TO_RESUME",
        "finalExportAllowed": workflow["exportGate"]["canExportFinalMidi"],
        "exportBlockers": workflow["exportGate"]["blockers"],
        "softwareWorkflowPassed": all((
            completed == 7, blocked == 1,
            workflow["stages"][-1]["stageId"] == "EXPORT",
            len(workflow["timeline"]) == 10, len(workflow["trackMatrix"]) == 4,
            len(workflow["explain"]) == 52, len(workflow["jobs"]) == 8,
            len(workflow["commandPalette"]) == 10,
            diff["notes"]["added"] == 61, diff["notes"]["originalNotesChanged"] == 0,
            diff["controllers"]["cc11Added"] == 16,
            diff["soundSetup"]["soundBindingChanges"] == 0,
            workflow["verification"]["independentValidatorPassed"],
            workflow["verification"]["technicalQualityPassed"],
            not workflow["verification"]["humanQualityPassed"],
            not workflow["verification"]["deviceCertified"],
            resumed["sourceVerified"], workflow["safety"]["readOnly"],
            not workflow["safety"]["midiMutationAllowed"],
            not workflow["exportGate"]["canExportFinalMidi"],
        )),
    }
    benchmark["benchmarkHash"] = sha256(_canonical(benchmark)).hexdigest()
    benchmark_path = ROOT / "data" / "session28-benchmark-report.json"
    _write_json(benchmark_path, benchmark)
    if not benchmark["softwareWorkflowPassed"]:
        raise RuntimeError("Session 28 Premium Producer workflow benchmark failed")

    contracts = []
    for path in (
        ROOT / "premium/schemas/v2/premium-workflow-v2.schema.json",
        ROOT / "premium/schemas/v2/workflow-recovery-v1.schema.json",
    ):
        value = json.loads(path.read_text(encoding="utf-8"))
        contracts.append({"name": path.name, "$id": value["$id"],
                          "contractVersion": value["x-contract-version"],
                          "sha256": sha256(path.read_bytes()).hexdigest()})
    schema_catalog = {
        "schema": "dna-session28-schema-catalog", "version": "1.0",
        "date": date.today().isoformat(), "contracts": contracts,
        "catalogHash": sha256(_canonical(contracts)).hexdigest(),
    }
    schema_catalog_path = ROOT / "data" / "session28-schema-catalog.json"
    _write_json(schema_catalog_path, schema_catalog)
    _update_feature_matrix()

    report = {
        "schema": "dna-session28-test-report", "version": "1.0",
        "date": date.today().isoformat(), "result": "pass",
        "scope": "guided-premium-producer-workflow-track-matrix-explain-diff-locks-accessibility-jobs-cancel-resume-and-export-gates",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures),
                        "errors": len(result.errors)},
        "benchmark": {"report": str(benchmark_path.relative_to(ROOT)),
                      **{key: benchmark[key] for key in (
                          "workflowId", "workflowHash", "stageCount", "completedStageCount",
                          "blockedStageCount", "blockedStageIds", "timelineItemCount",
                          "trackMatrixRowCount", "explainDecisionCount", "backgroundJobCount",
                          "commandPaletteCount", "baselineNoteCount", "premiumPreviewNoteCount",
                          "addedPreviewNoteCount", "originalNotesChanged", "cc11PointCount",
                          "soundBindingChanges", "automatedQualityScore",
                          "verifiedHumanEvaluatorCount", "checkpointReadyToResume",
                          "finalExportAllowed", "exportBlockers", "benchmarkHash")}},
        "artifacts": {name: str(path.relative_to(ROOT)) for name, path in paths.items()}
                     | {"schemaCatalog": str(schema_catalog_path.relative_to(ROOT))},
        "transports": {"cli": "session28_premium_workflow.py",
                       "api": "/api/premium-producer-workflow",
                       "guiWorkspace": "PREMIUM PRODUCER WORKFLOW 2.0", "apiGuiParity": True},
        "invariants": {
            "oneGuidedWorkflow": True, "eightOrderedStages": True,
            "allTenPa800ElementsVisible": True, "trackMatrixVisible": True,
            "explainAndDiffVisible": True, "globalAndElementLocks": True,
            "partialRegenerationControl": True, "commandPaletteAndShortcuts": True,
            "keyboardReachableHighContrast": True, "backgroundJobs": True,
            "safeCancelResumeRecovery": True, "originalNotesChanged": 0,
            "soundBindingChanges": 0, "goldAffectsDynamics": False,
            "readOnly": True, "midiMutationAllowed": False, "finalMidiGenerated": False,
            "qualityGateBypassAllowed": False, "deviceGateBypassAllowed": False,
        },
        "status": {
            "session28PremiumProducerWorkflow": "SOFTWARE_VALIDATED / EXPORT_GATES_PENDING",
            "activeSoftwareBaseline": "4.6-workflow-alpha",
            "guidedProducerWorkflow": "REFERENCE_TASK_COMPLETE",
            "finalMidiExport": "BLOCKED_QUALITY_DEVICE_AND_EVIDENCE",
            "humanListeningEvidence": "0/2 VERIFIED",
            "aiPremiumArranger": "PLANNED", "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data" / "session28-test-report.json"
    _write_json(report_path, report)

    release_path = ROOT / "data" / "release-check-report.json"
    if release_path.is_file():
        release = json.loads(release_path.read_text(encoding="utf-8"))
        release.setdefault("premiumReadiness", {}).update({
            "softwareBaseline": "4.6-workflow-alpha",
            "session28": f"{result.testsRun}/{result.testsRun} PASS",
            "premiumProducerWorkflow": "SOFTWARE_VALIDATED / EXPORT_GATES_PENDING",
            "guidedReferenceTask": "COMPLETE", "finalMidiExport": "BLOCKED",
            "verifiedHumanEvaluators": "0/2", "premiumProduct": "PLANNED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(release_path, release)
    compliance_path = ROOT / "data" / "master-prompt-compliance.json"
    if compliance_path.is_file():
        compliance = json.loads(compliance_path.read_text(encoding="utf-8"))
        compliance.setdefault("summary", {}).update({
            "session28PremiumProducerWorkflow": f"{result.testsRun}/{result.testsRun} PASS",
            "activeSoftwareBaseline": "4.6-workflow-alpha",
            "guidedReferenceTask": "COMPLETE", "finalMidiExport": "BLOCKED",
            "humanListeningEvidence": "0/2 VERIFIED",
            "aiPremiumArranger": "PLANNED", "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(compliance_path, compliance)
    print(
        f"Session 28 PASS: {result.testsRun}/{result.testsRun}; stages={completed}/8 complete; "
        f"timeline={len(workflow['timeline'])}; tracks={len(workflow['trackMatrix'])}; "
        f"explain={len(workflow['explain'])}; export=BLOCKED; {report_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())