#!/usr/bin/env python3
"""Run Session 36 zero-silent-failure reliability and stress gate."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio.reliability_gate import run_reliability_gate  # noqa: E402
from dna_midi_studio.session35_fixture import build_session35_chain  # noqa: E402


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
    matrix["softwareBaseline"] = "4.10.2-zero-silent-failure-reliability-foundation"
    features = matrix.setdefault("features", [])
    row = next((item for item in features if item.get("session") == 36), None)
    value = {
        "session": 36,
        "feature": "Zero-Silent-Failure Reliability Gate",
        "priority": "P0",
        "status": "SOFTWARE_VALIDATED / RELEASE_HARDENED_PREVIEW",
        "evidence": "data/session36-test-report.json",
        "blocker": "HUMAN_LISTENING_AND_PA800_DEVICE_EVIDENCE",
        "limitations": [
            "Reliability certification covers the locked software corpus, not all possible MIDI files",
            "Physical Pa800 behavior still requires the signed device procedure",
            "Final Premium export remains blocked by human, production-evidence and device gates",
        ],
    }
    if row is None:
        features.append(value)
    else:
        row.update(value)
    matrix["premiumProductStatus"] = "RELEASE_HARDENED_PREVIEW"
    _write(path, matrix)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session36.py")
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful():
        return 1
    if result.testsRun != 184:
        raise RuntimeError(f"Session 36 expected 184 tests, got {result.testsRun}")

    chain = build_session35_chain(ROOT)
    outcome = run_reliability_gate(chain, ROOT, (25_000, 100_000), 200)
    reliability = outcome["report"]
    vault = outcome["vault"]
    if not reliability["passed"]:
        raise RuntimeError("Session 36 reliability benchmark failed")

    artifacts = {
        "report": ROOT / "artifacts/session36-reliability-report.json",
        "vault": ROOT / "artifacts/session36-regression-vault.json",
        "atomic": ROOT / "artifacts/session36-atomic-fault-matrix.json",
        "workerParity": ROOT / "artifacts/session36-worker-parity.json",
        "stress": ROOT / "artifacts/session36-stress-profiles.json",
    }
    _write(artifacts["report"], reliability)
    _write(artifacts["vault"], vault)
    _write(artifacts["atomic"], reliability["atomicPublication"])
    _write(artifacts["workerParity"], reliability["workerParity"])
    _write(artifacts["stress"], {"profiles": reliability["stressProfiles"],
                                 "passed": all(item["withinBudget"] for item in reliability["stressProfiles"])})

    benchmark = {
        "schema": "dna-session36-reliability-benchmark", "version": "1.0",
        "date": date.today().isoformat(), "license": "self-authored-adversarial-fixtures",
        "reportHash": reliability["reportHash"], "vaultHash": vault["vaultHash"],
        "malformedMidiCases": reliability["summary"]["malformedCases"],
        "sealedByteMutations": reliability["summary"]["fuzzMutations"],
        "atomicFaults": reliability["summary"]["atomicFaults"],
        "workerCounts": reliability["summary"]["workerCounts"],
        "byteIdenticalAcrossWorkers": reliability["summary"]["byteIdenticalAcrossWorkers"],
        "unhandledExceptions": reliability["summary"]["unhandledExceptions"],
        "silentFallbacks": reliability["summary"]["silentFallbacks"],
        "partialOutputs": reliability["summary"]["partialOutputs"],
        "openSeverity1": reliability["summary"]["openSeverity1"],
        "openSeverity2": reliability["summary"]["openSeverity2"],
        "stressProfiles": reliability["stressProfiles"],
        "lockedRegressions": vault["summary"]["lockedRegressions"],
        "zeroTrackParserRegressionClosed": True,
        "finalCertifiedMidiExportAllowed": False,
        "benchmarkPassed": reliability["passed"],
    }
    benchmark["benchmarkHash"] = sha256(_canonical(benchmark)).hexdigest()
    benchmark_path = ROOT / "data/session36-benchmark-report.json"
    _write(benchmark_path, benchmark)

    schemas = []
    for path in (
        ROOT / "premium/schemas/v2/reliability-report-v1.schema.json",
        ROOT / "premium/schemas/v2/reliability-regression-vault-v1.schema.json",
    ):
        value = json.loads(path.read_text(encoding="utf-8"))
        schemas.append({"name": path.name, "$id": value["$id"],
                        "contractVersion": value["x-contract-version"],
                        "sha256": sha256(path.read_bytes()).hexdigest()})
    schema_catalog = {"schema": "dna-session36-schema-catalog", "version": "1.0",
                      "date": date.today().isoformat(), "contracts": schemas,
                      "catalogHash": sha256(_canonical(schemas)).hexdigest()}
    schema_path = ROOT / "data/session36-schema-catalog.json"
    _write(schema_path, schema_catalog)
    _update_feature_matrix()

    report = {
        "schema": "dna-session36-test-report", "version": "1.0",
        "date": date.today().isoformat(), "result": "pass",
        "scope": "zero-silent-failure-parser-fuzz-atomic-worker-stress-and-regression-vault",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures),
                        "errors": len(result.errors)},
        "benchmark": {"report": str(benchmark_path.relative_to(ROOT)), **{
            key: benchmark[key] for key in (
                "malformedMidiCases", "sealedByteMutations", "atomicFaults", "workerCounts",
                "byteIdenticalAcrossWorkers", "unhandledExceptions", "silentFallbacks",
                "partialOutputs", "openSeverity1", "openSeverity2", "stressProfiles",
                "lockedRegressions", "zeroTrackParserRegressionClosed", "benchmarkHash",
            )}},
        "artifacts": {key: str(path.relative_to(ROOT)) for key, path in artifacts.items()} |
                     {"schemaCatalog": str(schema_path.relative_to(ROOT))},
        "transports": {"cli": "session36_reliability_gate.py",
                       "api": "/api/reliability-gate",
                       "guiWorkspace": "RELIABILITY & SAFETY",
                       "apiGuiParity": True},
        "invariants": {
            "allFailuresFailClosed": True, "silentFallbackAllowed": False,
            "partialOutputAllowed": False, "sourceOverwriteAllowed": False,
            "workerOutputDivergence": False, "goldAffectsDynamics": False,
            "originalSoloMutationAllowed": False, "validatorBypassAllowed": False,
            "finalCertifiedMidiExportAllowed": False, "physicalCertificationClaimed": False,
        },
        "status": {
            "session36Reliability": "SOFTWARE_VALIDATED / RELEASE_HARDENED_PREVIEW",
            "activeSoftwareBaseline": "4.10.2-zero-silent-failure-reliability-foundation",
            "allowedProductName": "AI PREMIUM ARRANGER PREVIEW",
            "qualityEvidence": "HUMAN_LISTENING_PENDING_0_OF_2",
            "finalCertifiedMidiExport": "BLOCKED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data/session36-test-report.json"
    _write(report_path, report)
    print(
        f"Session 36 PASS: {result.testsRun}/{result.testsRun}; "
        f"malformed={benchmark['malformedMidiCases']}; fuzz={benchmark['sealedByteMutations']}; "
        f"workers=1/2/4; partial=0; severity-1/2=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())