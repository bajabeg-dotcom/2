#!/usr/bin/env python3
"""Run the Session 30 honest Preview release-candidate software gate."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio.session30_fixture import build_session30_chain  # noqa: E402


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _update_feature_matrix() -> None:
    path = ROOT / "data" / "premium-feature-matrix.json"
    matrix = json.loads(path.read_text(encoding="utf-8"))
    matrix["softwareBaseline"] = "4.8-release-candidate-preview"
    for feature in matrix["features"]:
        if feature["session"] == 30:
            feature.update({
                "status": "SOFTWARE_VALIDATED / PREVIEW_RC_EXTERNAL_GATES_BLOCKED",
                "evidence": "data/session30-test-report.json",
                "blocker": "HUMAN_LISTENING_AND_PA800_DEVICE_EVIDENCE",
                "limitations": [
                    "Only the AI PREMIUM ARRANGER PREVIEW product name is authorized",
                    "Final MIDI export remains blocked by human, production-evidence and device gates",
                    "The local SHA-256 content seal is not an identity or code-signing certificate",
                ],
            })
    matrix["premiumProductStatus"] = "PREVIEW_RELEASE_CANDIDATE"
    _write_json(path, matrix)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session30.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    if result.testsRun != 128:
        raise RuntimeError(f"Session 30 expected 128 tests, got {result.testsRun}")

    fixture = build_session30_chain(ROOT)
    migration = fixture["projectMigration"]
    manifest = fixture["softwareManifest"]
    hardening = fixture["hardeningReport"]
    matrix = fixture["statusMatrix"]
    readiness = fixture["releaseReadiness"]
    paths = {
        "referenceMidi": ROOT / "artifacts/session30-reference.mid",
        "legacyProject": ROOT / "artifacts/session30-legacy-project.json",
        "projectMigration": ROOT / "artifacts/session30-project-migration.json",
        "migratedProject": ROOT / "artifacts/session30-migrated-project.dnaproject.json",
        "softwareManifest": ROOT / "artifacts/session30-software-manifest.json",
        "statusMatrix": ROOT / "artifacts/session30-release-status-matrix.json",
        "releaseReadiness": ROOT / "artifacts/session30-release-readiness.json",
    }
    paths["referenceMidi"].write_bytes(fixture["midi"].to_bytes())
    values = {
        "legacyProject": fixture["legacyProject"],
        "projectMigration": migration,
        "migratedProject": migration["migratedProject"],
        "softwareManifest": manifest,
        "statusMatrix": matrix,
        "releaseReadiness": readiness,
    }
    for name, value in values.items():
        _write_json(paths[name], value)
    hardening_path = ROOT / "data/session30-hardening-report.json"
    _write_json(hardening_path, hardening)

    benchmark = {
        "schema": "dna-session30-release-readiness-benchmark",
        "version": "1.0",
        "date": date.today().isoformat(),
        "license": "self-authored-test-fixtures",
        "sourceMidiSha256": fixture["midi"].digest(),
        "migrationHash": migration["migrationHash"],
        "softwareManifestHash": manifest["manifestHash"],
        "softwareContentHash": manifest["contentHash"],
        "hardeningHash": hardening["hardeningHash"],
        "statusMatrixHash": matrix["matrixHash"],
        "releaseReadinessHash": readiness["readinessHash"],
        "manifestApplicationFiles": len(manifest["application"]),
        "manifestRegistryFiles": len(manifest["registries"]),
        "manifestContractFiles": len(manifest["contracts"]),
        "analysis25000Seconds": hardening["performance"]["analysis25000Notes"]["seconds"],
        "globalPlanSeconds": hardening["performance"]["globalPlan"]["seconds"],
        "partialRegenerationSeconds": hardening["performance"]["partialRegeneration"]["seconds"],
        "migrationPeakBytes": hardening["memory"]["peakBytes"],
        "statusEntryCount": matrix["summary"]["entryCount"],
        "openSeverity1Defects": readiness["defects"]["openSeverity1"],
        "openSeverity2Defects": readiness["defects"]["openSeverity2"],
        "verifiedHumanEvaluators": readiness["quality"]["verifiedHumanEvaluators"],
        "requiredHumanEvaluators": readiness["quality"]["requiredHumanEvaluators"],
        "softwareReleaseCandidateReady": readiness["gates"]["softwareReleaseCandidateReady"],
        "finalPremiumReleaseAllowed": readiness["gates"]["finalPremiumReleaseAllowed"],
        "finalMidiExportAllowed": readiness["gates"]["finalMidiExportAllowed"],
        "allowedProductName": readiness["gates"]["allowedProductName"],
        "physicalCertificationClaimed": readiness["safety"]["physicalCertificationClaimed"],
        "softwareReleaseReadinessPassed": all((
            hardening["passed"], matrix["summary"]["softwarePassed"],
            readiness["gates"]["softwareReleaseCandidateReady"],
            readiness["defects"]["openSeverity1"] == 0,
            readiness["defects"]["openSeverity2"] == 0,
            readiness["quality"]["verifiedHumanEvaluators"] == 0,
            not readiness["gates"]["finalPremiumReleaseAllowed"],
            not readiness["gates"]["finalMidiExportAllowed"],
            not readiness["safety"]["physicalCertificationClaimed"],
        )),
    }
    benchmark["benchmarkHash"] = sha256(_canonical(benchmark)).hexdigest()
    benchmark_path = ROOT / "data/session30-benchmark-report.json"
    _write_json(benchmark_path, benchmark)
    if not benchmark["softwareReleaseReadinessPassed"]:
        raise RuntimeError("Session 30 software release-readiness benchmark failed")

    contracts = []
    for path in (
        ROOT / "premium/schemas/v2/release-readiness-v2.schema.json",
        ROOT / "premium/schemas/v2/software-manifest-v1.schema.json",
        ROOT / "premium/schemas/v2/project-migration-report-v1.schema.json",
        ROOT / "premium/schemas/v2/release-status-matrix-v1.schema.json",
    ):
        value = json.loads(path.read_text(encoding="utf-8"))
        contracts.append({"name": path.name, "$id": value["$id"],
                          "contractVersion": value["x-contract-version"],
                          "sha256": sha256(path.read_bytes()).hexdigest()})
    schema_catalog = {
        "schema": "dna-session30-schema-catalog", "version": "1.0",
        "date": date.today().isoformat(), "contracts": contracts,
        "catalogHash": sha256(_canonical(contracts)).hexdigest(),
    }
    schema_catalog_path = ROOT / "data/session30-schema-catalog.json"
    _write_json(schema_catalog_path, schema_catalog)
    _update_feature_matrix()

    report = {
        "schema": "dna-session30-test-report", "version": "1.0",
        "date": date.today().isoformat(), "result": "pass",
        "scope": "preview-release-candidate-manifest-migration-performance-memory-path-rollback-and-honest-external-gates",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures),
                        "errors": len(result.errors)},
        "benchmark": {"report": str(benchmark_path.relative_to(ROOT)), **{
            key: benchmark[key] for key in (
                "softwareContentHash", "releaseReadinessHash", "manifestApplicationFiles",
                "manifestRegistryFiles", "manifestContractFiles", "analysis25000Seconds",
                "globalPlanSeconds", "partialRegenerationSeconds", "migrationPeakBytes",
                "statusEntryCount", "openSeverity1Defects", "openSeverity2Defects",
                "verifiedHumanEvaluators", "requiredHumanEvaluators",
                "softwareReleaseCandidateReady", "finalPremiumReleaseAllowed",
                "finalMidiExportAllowed", "allowedProductName", "benchmarkHash",
            )}},
        "artifacts": {name: str(path.relative_to(ROOT)) for name, path in paths.items()} | {
            "hardeningReport": str(hardening_path.relative_to(ROOT)),
            "schemaCatalog": str(schema_catalog_path.relative_to(ROOT)),
        },
        "transports": {"cli": "session30_release_readiness.py",
                       "api": "/api/premium-release-readiness",
                       "guiWorkspace": "AI PREMIUM RELEASE READINESS 2.0", "apiGuiParity": True},
        "invariants": {
            "sourceProjectUnchanged": True, "originalProjectOverwriteAllowed": False,
            "midiEmbeddedInProject": False, "audioEmbeddedInProject": False,
            "offlineCore": True, "thirdPartyRuntimeDependencies": 0,
            "contentSealIsIdentitySignature": False, "openSeverity1Defects": 0,
            "openSeverity2Defects": 0, "finalMidiExportAllowed": False,
            "finalPremiumProductNameAllowed": False, "previewProductNameAllowed": True,
            "physicalCertificationClaimed": False, "validatorBypassAllowed": False,
            "qualityGateBypassAllowed": False, "deviceGateBypassAllowed": False,
        },
        "status": {
            "session30ReleaseReadiness": "SOFTWARE_VALIDATED / PREVIEW_RC_EXTERNAL_GATES_BLOCKED",
            "activeSoftwareBaseline": "4.8-release-candidate-preview",
            "allowedProductName": "AI PREMIUM ARRANGER PREVIEW",
            "aiPremiumArranger": "BLOCKED_EXTERNAL_GATES",
            "finalMidiExport": "BLOCKED", "humanListeningEvidence": "0/2 VERIFIED",
            "expressionEvidence": "PRODUCTION_EVIDENCE_BLOCKED",
            "articulationEvidence": "DEVICE_CAPTURE_BLOCKED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data/session30-test-report.json"
    _write_json(report_path, report)

    release_path = ROOT / "data/release-check-report.json"
    if release_path.is_file():
        release = json.loads(release_path.read_text(encoding="utf-8"))
        release.setdefault("premiumReadiness", {}).update({
            "softwareBaseline": "4.8-release-candidate-preview",
            "session30": f"{result.testsRun}/{result.testsRun} PASS",
            "softwareReleaseCandidate": "READY_PREVIEW_ONLY",
            "allowedProductName": "AI PREMIUM ARRANGER PREVIEW",
            "finalMidiExport": "BLOCKED", "verifiedHumanEvaluators": "0/2",
            "premiumProduct": "BLOCKED_EXTERNAL_GATES", "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(release_path, release)
    compliance_path = ROOT / "data/master-prompt-compliance.json"
    if compliance_path.is_file():
        compliance = json.loads(compliance_path.read_text(encoding="utf-8"))
        compliance.setdefault("summary", {}).update({
            "session30ReleaseReadiness": f"{result.testsRun}/{result.testsRun} PASS",
            "activeSoftwareBaseline": "4.8-release-candidate-preview",
            "softwareReleaseCandidate": "READY_PREVIEW_ONLY",
            "allowedProductName": "AI PREMIUM ARRANGER PREVIEW",
            "finalMidiExport": "BLOCKED", "humanListeningEvidence": "0/2 VERIFIED",
            "aiPremiumArranger": "BLOCKED_EXTERNAL_GATES", "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(compliance_path, compliance)
    print(
        f"Session 30 PASS: {result.testsRun}/{result.testsRun}; "
        f"analysis25k={benchmark['analysis25000Seconds']:.3f}s; "
        f"partial={benchmark['partialRegenerationSeconds']:.3f}s; "
        f"name={benchmark['allowedProductName']}; final-export=BLOCKED; {report_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())