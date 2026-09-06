#!/usr/bin/env python3
"""Run the Session 27 Music Quality Evaluator 2.0 software gate."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio.session27_fixture import build_session27_chain  # noqa: E402


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _update_feature_matrix() -> None:
    path = ROOT / "data" / "premium-feature-matrix.json"
    matrix = json.loads(path.read_text(encoding="utf-8"))
    matrix["softwareBaseline"] = "4.5-quality-alpha"
    for feature in matrix["features"]:
        if feature["session"] == 27:
            feature.update({
                "status": "SOFTWARE_VALIDATED / HUMAN_LISTENING_PENDING",
                "evidence": "data/session27-test-report.json",
                "blocker": "Two independent verified human evaluators and 70% Premium preference are still required",
                "limitations": [
                    "Automated structural scores are not listening evidence",
                    "Proxy audio and SOFTWARE_TEST_ONLY responses cannot satisfy the release quality gate",
                ],
            })
    matrix["premiumProductStatus"] = "PLANNED"
    _write_json(path, matrix)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session27.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    fixture = build_session27_chain(ROOT)
    artifacts = ROOT / "artifacts"
    paths = {
        "referenceMidi": artifacts / "session27-reference.mid",
        "songMap": artifacts / "session27-song-map.json",
        "previewSession": artifacts / "session27-preview-session.json",
        "audioManifests": artifacts / "session27-audio-manifests.json",
        "baselineReference": artifacts / "session27-baseline-reference.json",
        "blindListeningPackage": artifacts / "session27-blind-listening-package.json",
        "privateListeningKey": artifacts / "session27-private-listening-key.json",
        "softwareTestResponse": artifacts / "session27-software-test-response.json",
        "qualityRegressionVault": artifacts / "session27-quality-regression-vault.json",
        "blockingRegressionExample": artifacts / "session27-blocking-regression-example.json",
        "controls": artifacts / "session27-quality-controls.json",
        "evaluationReport": artifacts / "session27-evaluation-report.json",
    }
    paths["referenceMidi"].write_bytes(fixture["midi"].to_bytes())
    for variant, raw in fixture["wavs"].items():
        paths[f"variant{variant}ProxyWav"] = artifacts / f"session27-variant-{variant.lower()}-proxy.wav"
        paths[f"variant{variant}ProxyWav"].write_bytes(raw)
    values = {
        "songMap": fixture["songMap"], "previewSession": fixture["previewSession"],
        "audioManifests": fixture["audioManifests"],
        "baselineReference": fixture["baselineReference"],
        "blindListeningPackage": fixture["blindPackage"],
        "privateListeningKey": fixture["privateKey"],
        "softwareTestResponse": fixture["softwareResponse"],
        "qualityRegressionVault": fixture["regressionVault"],
        "blockingRegressionExample": fixture["blockingRegressionVault"],
        "controls": fixture["controls"], "evaluationReport": fixture["evaluationReport"],
    }
    for name, value in values.items():
        _write_json(paths[name], value)

    evaluation = fixture["evaluationReport"]
    benchmark = {
        "schema": "dna-session27-quality-benchmark", "version": "1.0",
        "date": date.today().isoformat(), "license": "self-authored-test-fixtures",
        "baselineVersion": "3.17",
        "baselineId": fixture["baselineReference"]["baselineId"],
        "baselineMidiSha256": fixture["baselineReference"]["artifactSha256"],
        "previewSessionHash": fixture["previewSession"]["previewSessionHash"],
        "evaluationReportHash": evaluation["evaluationReportHash"],
        "automatedOverallScore": evaluation["automated"]["overallScore"],
        "automatedMetrics": {key: value["score"] for key, value in evaluation["automated"]["metrics"].items()},
        "technicalGatePassed": evaluation["technical"]["passed"],
        "automatedGatePassed": evaluation["automated"]["passed"],
        "blindTrialCount": len(fixture["blindPackage"]["trials"]),
        "verifiedHumanEvaluatorCount": evaluation["listening"]["verifiedHumanEvaluatorCount"],
        "softwareTestResponseCount": evaluation["listening"]["softwareTestResponseCount"],
        "premiumPreferenceRate": evaluation["listening"]["premiumPreferenceRate"],
        "releaseQualityGatePassed": evaluation["releaseQualityGate"]["passed"],
        "releaseQualityGateBlockers": evaluation["releaseQualityGate"]["blockers"],
        "regressionVaultClear": evaluation["regression"]["passed"],
        "proxyAudioCountsAsHumanEvidence": False,
        "privateKeyExportedToGui": False,
        "softwareEvaluatorPassed": all((
            evaluation["technical"]["passed"], evaluation["automated"]["passed"],
            evaluation["regression"]["passed"], not evaluation["releaseQualityGate"]["passed"],
            evaluation["listening"]["verifiedHumanEvaluatorCount"] == 0,
            evaluation["listening"]["softwareTestResponseCount"] == 1,
            evaluation["readOnly"], not evaluation["midiMutationAllowed"],
            not evaluation["finalMidiGenerated"], not evaluation["pa800DeviceCertified"],
        )),
    }
    benchmark["benchmarkHash"] = sha256(_canonical(benchmark)).hexdigest()
    benchmark_path = ROOT / "data" / "session27-benchmark-report.json"
    _write_json(benchmark_path, benchmark)
    if not benchmark["softwareEvaluatorPassed"]:
        raise RuntimeError("Session 27 software quality evaluator benchmark failed")

    contracts = []
    for path in (
        ROOT / "premium/schemas/v2/evaluation-report-v2.schema.json",
        ROOT / "premium/schemas/v2/blind-listening-package-v1.schema.json",
        ROOT / "premium/schemas/v2/listening-response-v1.schema.json",
        ROOT / "premium/schemas/v2/quality-regression-vault-v1.schema.json",
    ):
        value = json.loads(path.read_text(encoding="utf-8"))
        contracts.append({"name": path.name, "$id": value["$id"],
                          "contractVersion": value["x-contract-version"],
                          "sha256": sha256(path.read_bytes()).hexdigest()})
    schema_catalog = {
        "schema": "dna-session27-schema-catalog", "version": "1.0",
        "date": date.today().isoformat(), "contracts": contracts,
        "catalogHash": sha256(_canonical(contracts)).hexdigest(),
    }
    schema_catalog_path = ROOT / "data" / "session27-schema-catalog.json"
    _write_json(schema_catalog_path, schema_catalog)
    _update_feature_matrix()

    report = {
        "schema": "dna-session27-test-report", "version": "1.0",
        "date": date.today().isoformat(), "result": "pass",
        "scope": "technical-quality-metrics-blind-listening-protocol-human-evidence-gate-and-regression-vault",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures),
                        "errors": len(result.errors)},
        "benchmark": {"report": str(benchmark_path.relative_to(ROOT)),
                      **{key: benchmark[key] for key in (
                          "automatedOverallScore", "automatedMetrics", "technicalGatePassed",
                          "automatedGatePassed", "blindTrialCount", "verifiedHumanEvaluatorCount",
                          "softwareTestResponseCount", "premiumPreferenceRate",
                          "releaseQualityGatePassed", "releaseQualityGateBlockers",
                          "regressionVaultClear", "benchmarkHash")}},
        "artifacts": {name: str(path.relative_to(ROOT)) for name, path in paths.items()}
                     | {"schemaCatalog": str(schema_catalog_path.relative_to(ROOT))},
        "transports": {"cli": "session27_quality_evaluator.py",
                       "api": "/api/premium-quality-evaluator",
                       "guiWorkspace": "MUSIC QUALITY EVALUATOR 2.0", "apiGuiParity": True},
        "invariants": {
            "hardTechnicalAndSubjectiveSeparated": True,
            "sevenAutomatedMetrics": True, "baselineFrozenBeforeResults": True,
            "blindLabelsHideVariantIdentity": True, "privateKeySeparated": True,
            "minimumIndependentHumanEvaluators": 2, "minimumHumanOverallMedian": 4.0,
            "minimumPremiumPreferenceRate": 0.70,
            "softwareResponseCountsAsHuman": False, "proxyAudioCountsAsHuman": False,
            "openBaselineBetterRegressionBlocks": True,
            "readOnly": True, "midiMutationAllowed": False, "finalMidiGenerated": False,
            "session16CertAuthorityPreserved": True,
        },
        "status": {
            "session27MusicQualityEvaluator": "SOFTWARE_VALIDATED / HUMAN_LISTENING_PENDING",
            "activeSoftwareBaseline": "4.5-quality-alpha",
            "automatedQuality": "PASS",
            "releaseQualityGate": "BLOCKED_HUMAN_LISTENING",
            "humanListeningEvidence": "0/2 VERIFIED",
            "aiPremiumArranger": "PLANNED", "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data" / "session27-test-report.json"
    _write_json(report_path, report)

    release_path = ROOT / "data" / "release-check-report.json"
    if release_path.is_file():
        release = json.loads(release_path.read_text(encoding="utf-8"))
        release.setdefault("premiumReadiness", {}).update({
            "softwareBaseline": "4.5-quality-alpha",
            "session27": f"{result.testsRun}/{result.testsRun} PASS",
            "automatedMusicQuality": f"{evaluation['automated']['overallScore']}/5 PASS",
            "releaseQualityGate": "BLOCKED_HUMAN_LISTENING",
            "verifiedHumanEvaluators": "0/2", "premiumProduct": "PLANNED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(release_path, release)
    compliance_path = ROOT / "data" / "master-prompt-compliance.json"
    if compliance_path.is_file():
        compliance = json.loads(compliance_path.read_text(encoding="utf-8"))
        compliance.setdefault("summary", {}).update({
            "session27MusicQualityEvaluator": f"{result.testsRun}/{result.testsRun} PASS",
            "activeSoftwareBaseline": "4.5-quality-alpha",
            "automatedMusicQuality": f"{evaluation['automated']['overallScore']}/5 PASS",
            "releaseQualityGate": "BLOCKED_HUMAN_LISTENING",
            "humanListeningEvidence": "0/2 VERIFIED",
            "aiPremiumArranger": "PLANNED", "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(compliance_path, compliance)
    print(f"Session 27 PASS: {result.testsRun}/{result.testsRun}; automated={evaluation['automated']['overallScore']}/5; human=0/2; release-quality=BLOCKED; {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())