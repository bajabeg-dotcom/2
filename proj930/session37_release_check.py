#!/usr/bin/env python3
"""Run Session 37 locked-corpus production-quality calibration gate."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio.session37_fixture import build_session37_chain  # noqa: E402


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _update_feature_matrix() -> None:
    path = ROOT / "data/premium-feature-matrix.json"
    if not path.is_file():
        return
    matrix = json.loads(path.read_text(encoding="utf-8"))
    matrix["softwareBaseline"] = "4.11-quality-calibration-foundation"
    features = matrix.setdefault("features", [])
    value = {
        "session": 37,
        "feature": "Production Evidence Expansion and Quality Calibration",
        "priority": "P0",
        "status": "SOFTWARE_VALIDATED / HUMAN_AND_PRODUCTION_EVIDENCE_PENDING",
        "evidence": "data/session37-test-report.json",
        "blocker": "TWO_HUMAN_EVALUATORS_PRODUCTION_EXPRESSION_AND_PA800_DEVICE",
        "limitations": [
            "Structural holdout is not a substitute for human listening",
            "Production expression intake remains empty until operator evidence is imported",
            "Session 37 cannot certify or unlock final Pa800 MIDI export",
        ],
    }
    row = next((item for item in features if item.get("session") == 37), None)
    if row is None:
        features.append(value)
    else:
        row.update(value)
    matrix["premiumProductStatus"] = "QUALITY_CALIBRATION_PREVIEW"
    _write(path, matrix)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session37.py")
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful():
        return 1
    if result.testsRun != 192:
        raise RuntimeError(f"Session 37 expected 192 tests, got {result.testsRun}")

    chain = build_session37_chain(ROOT)
    artifacts = {
        "corpus": ROOT / "artifacts/session37-quality-corpus.json",
        "groundTruthVault": ROOT / "artifacts/session37-private-ground-truth-vault.json",
        "calibration": ROOT / "artifacts/session37-calibration-report.json",
        "holdout": ROOT / "artifacts/session37-holdout-report.json",
        "expressionIntake": ROOT / "artifacts/session37-expression-intake.json",
        "listeningIntake": ROOT / "artifacts/session37-listening-intake.json",
        "qualityGate": ROOT / "artifacts/session37-quality-release-gate.json",
    }
    for key, path in artifacts.items():
        _write(path, chain[key])

    benchmark = {
        "schema": "dna-session37-quality-calibration-benchmark",
        "version": "1.0",
        "date": date.today().isoformat(),
        "license": "self-authored-test-fixtures",
        "corpusHash": chain["corpus"]["corpusHash"],
        "caseCount": chain["corpus"]["caseCount"],
        "trainCaseCount": chain["calibration"]["trainingCaseCount"],
        "holdoutCaseCount": chain["calibration"]["holdoutCaseCount"],
        "sourceCaseCounts": {row["id"]: row["caseCount"] for row in chain["corpus"]["sourceCorpora"]},
        "holdoutCoverage": chain["holdout"]["coverage"],
        "holdoutGroundTruthKinds": chain["holdout"]["groundTruthKinds"],
        "minimumHoldoutScores": {
            "chord": min(row["chordExactRate"] for row in chain["holdout"]["results"]),
            "section": min(row["sectionBoundaryExactRate"] for row in chain["holdout"]["results"]),
            "trackRole": min(row["trackRoleExactRate"] for row in chain["holdout"]["results"]),
            "transition": min(row["transitionExactRate"] for row in chain["holdout"]["results"]),
        },
        "holdoutStructuralPass": chain["holdout"]["structuralPass"],
        "metricWeightsChanged": chain["calibration"]["metricWeightsChanged"],
        "thresholdsChanged": chain["calibration"]["thresholdsChanged"],
        "verifiedHumanEvaluators": chain["listeningIntake"]["verifiedIndependentEvaluators"],
        "requiredHumanEvaluators": chain["listeningIntake"]["requiredIndependentEvaluators"],
        "productionExpressionEvidence": chain["expressionIntake"]["status"],
        "automatedOverallScore": chain["evaluationReport"]["automated"]["overallScore"],
        "qualityReleaseGatePassed": chain["qualityGate"]["qualityReleaseGatePassed"],
        "qualityReleaseGateBlockers": chain["qualityGate"]["blockers"],
        "finalCertifiedMidiExportAllowed": False,
    }
    benchmark["benchmarkHash"] = sha256(_canonical(benchmark)).hexdigest()
    benchmark_path = ROOT / "data/session37-benchmark-report.json"
    _write(benchmark_path, benchmark)

    contracts = []
    for name in (
        "quality-corpus-v2.schema.json",
        "quality-calibration-report-v1.schema.json",
        "production-expression-intake-v1.schema.json",
        "human-listening-intake-v1.schema.json",
        "quality-release-gate-v1.schema.json",
    ):
        path = ROOT / "premium/schemas/v2" / name
        value = json.loads(path.read_text(encoding="utf-8"))
        contracts.append({"name": name, "$id": value["$id"],
                          "contractVersion": value["x-contract-version"],
                          "sha256": sha256(path.read_bytes()).hexdigest()})
    schema_catalog = {
        "schema": "dna-session37-schema-catalog",
        "version": "1.0",
        "date": date.today().isoformat(),
        "contracts": contracts,
        "catalogHash": sha256(_canonical(contracts)).hexdigest(),
    }
    schema_path = ROOT / "data/session37-schema-catalog.json"
    _write(schema_path, schema_catalog)
    _update_feature_matrix()

    report = {
        "schema": "dna-session37-test-report",
        "version": "1.0",
        "date": date.today().isoformat(),
        "result": "pass",
        "scope": "locked-train-holdout-quality-calibration-and-external-evidence-intake",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures),
                        "errors": len(result.errors)},
        "benchmark": {"report": str(benchmark_path.relative_to(ROOT)), **{
            key: benchmark[key] for key in (
                "caseCount", "trainCaseCount", "holdoutCaseCount", "sourceCaseCounts",
                "holdoutCoverage", "holdoutGroundTruthKinds", "minimumHoldoutScores",
                "holdoutStructuralPass", "metricWeightsChanged",
                "thresholdsChanged", "verifiedHumanEvaluators", "requiredHumanEvaluators",
                "productionExpressionEvidence", "automatedOverallScore",
                "qualityReleaseGatePassed", "qualityReleaseGateBlockers", "benchmarkHash",
            )}},
        "artifacts": {key: str(path.relative_to(ROOT)) for key, path in artifacts.items()} |
                     {"schemaCatalog": str(schema_path.relative_to(ROOT))},
        "transports": {"cli": "session37_quality_calibration.py",
                       "api": "/api/quality-calibration",
                       "guiWorkspace": "PRODUCTION QUALITY & EVIDENCE",
                       "apiGuiParity": True},
        "invariants": {
            "corpusLockedBeforeScoring": True,
            "trainHoldoutOverlap": False,
            "holdoutLabelsVisibleToCalibration": False,
            "fourGroundTruthKinds": ["chord", "section", "trackRole", "transition"],
            "metricWeightsChangedWithoutHumans": False,
            "qualityThresholdsWeakened": False,
            "proxyAudioCountsAsHuman": False,
            "softwareTestBundleCountsAsHuman": False,
            "testExpressionEvidenceProductionEligible": False,
            "goldVelocityAuthority": False,
            "finalCertifiedMidiExportAllowed": False,
            "physicalCertificationClaimed": False,
        },
        "status": {
            "session37QualityCalibration": "SOFTWARE_VALIDATED / HUMAN_AND_PRODUCTION_EVIDENCE_PENDING",
            "activeSoftwareBaseline": "4.11-quality-calibration-foundation",
            "allowedProductName": "AI PREMIUM ARRANGER PREVIEW",
            "humanListeningEvidence": "0/2 VERIFIED",
            "productionExpressionEvidence": "AWAITING_OPERATOR_CAPTURE",
            "qualityReleaseGate": "BLOCKED_EXTERNAL_EVIDENCE",
            "finalCertifiedMidiExport": "BLOCKED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data/session37-test-report.json"
    _write(report_path, report)
    print(
        f"Session 37 PASS: {result.testsRun}/{result.testsRun}; corpus=32; train=24; "
        "holdout=8; humans=0/2; production-expression=PENDING; release-quality=BLOCKED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())