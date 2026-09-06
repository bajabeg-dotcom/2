#!/usr/bin/env python3
"""Run the Session 31B Evidence Authority Resolver 3.0 gate."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import sys
from time import perf_counter
import unittest


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import build_evidence_ledger, evidence_cache_stats  # noqa: E402
from dna_midi_studio.session31b_fixture import build_session31b_chain  # noqa: E402


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _update_feature_matrix() -> None:
    path = ROOT / "data/premium-feature-matrix.json"
    matrix = json.loads(path.read_text(encoding="utf-8"))
    matrix["softwareBaseline"] = "4.9.1-evidence-authority-foundation"
    matrix["features"] = [item for item in matrix["features"] if item.get("id") != "evidence-authority-resolver"]
    matrix["features"].append({
        "session": "31B", "id": "evidence-authority-resolver", "priority": "P0",
        "status": "SOFTWARE_VALIDATED / READ_ONLY AUTHORITY FOUNDATION",
        "evidence": "data/session31b-test-report.json",
        "blocker": "Mutating TrackPlan and evidence-driven MIDI renderer remain Session 32/33 work",
        "limitations": [
            "SOFTWARE_TEST_ONLY expression and articulation evidence is skipped",
            "Manual-review Track Instrument evidence cannot authorize automatic mutation",
            "The resolver cannot write MIDI, override the verifier or certify Pa800 hardware",
        ],
    })
    matrix["premiumProductStatus"] = "PREVIEW_EVIDENCE_AUTHORITY_FOUNDATION"
    _write_json(path, matrix)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session31b.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    if result.testsRun != 144:
        raise RuntimeError(f"Session 31B expected 144 tests, got {result.testsRun}")

    start = perf_counter()
    fixture = build_session31b_chain(ROOT)
    ledger = fixture["ledger"]
    first_elapsed = perf_counter() - start
    repeat_start = perf_counter()
    repeated = build_evidence_ledger(fixture["documents"], ROOT, selected_variant_id="C")
    repeat_elapsed = perf_counter() - repeat_start
    if repeated != ledger:
        raise RuntimeError("EvidenceLedger is not deterministic")

    paths = {
        "referenceMidi": ROOT / "artifacts/session31b-reference.mid",
        "trackAnalysis": ROOT / "artifacts/session31b-track-analysis.json",
        "evidenceLedger": ROOT / "artifacts/session31b-evidence-ledger.json",
        "coverageReport": ROOT / "artifacts/session31b-evidence-coverage-report.json",
        "authorityDecisions": ROOT / "artifacts/session31b-authority-decisions.json",
    }
    paths["referenceMidi"].write_bytes(fixture["midi"].to_bytes())
    _write_json(paths["trackAnalysis"], fixture["trackAnalysis"])
    _write_json(paths["evidenceLedger"], ledger)
    _write_json(paths["coverageReport"], ledger["coverage"])
    _write_json(paths["authorityDecisions"], {
        "schema": "dna-session31b-authority-decision-set", "version": "1.0",
        "sourceLedgerHash": ledger["ledgerHash"], "decisions": ledger["decisions"],
    })

    coverage = ledger["coverage"]
    benchmark = {
        "schema": "dna-session31b-evidence-authority-benchmark", "version": "1.0",
        "date": date.today().isoformat(), "license": "self-authored-test-fixtures",
        "sourceMidiSha256": fixture["midi"].digest(),
        "ledgerHash": ledger["ledgerHash"], "totalSubjects": coverage["totalSubjects"],
        "explicitAuthoritySubjects": coverage["explicitAuthoritySubjects"],
        "coverageRate": coverage["coverageRate"], "decisionCounts": coverage["decisionCounts"],
        "subjectCounts": coverage["subjectCounts"], "evidenceCount": len(ledger["evidence"]),
        "verifiedRegistryCount": sum(item["status"] == "VERIFIED" for item in ledger["registries"].values()),
        "firstBuildSeconds": round(first_elapsed, 6), "cachedBuildSeconds": round(repeat_elapsed, 6),
        "cache": evidence_cache_stats(), "deterministic": repeated == ledger,
        "softwareTestExpressionSkipped": all(
            item["disposition"] == "SKIP" for item in ledger["decisions"]
            if item["subjectType"] == "EXPRESSION_EVENT"
        ),
        "deviceArticulationSkipped": all(
            item["disposition"] == "SKIP" for item in ledger["decisions"]
            if item["subjectType"] == "ARTICULATION_EVENT"
        ),
        "goldDynamicsAuthority": False, "midiMutationAuthority": False,
        "finalMidiExportAllowed": False,
    }
    benchmark["passed"] = all((
        benchmark["deterministic"], benchmark["totalSubjects"] == 1657,
        benchmark["coverageRate"] >= 0.99, benchmark["evidenceCount"] == 111,
        benchmark["verifiedRegistryCount"] == 3,
        benchmark["softwareTestExpressionSkipped"], benchmark["deviceArticulationSkipped"],
        repeat_elapsed < 10.0, not benchmark["goldDynamicsAuthority"],
        not benchmark["midiMutationAuthority"], not benchmark["finalMidiExportAllowed"],
    ))
    benchmark["benchmarkHash"] = sha256(_canonical(benchmark)).hexdigest()
    benchmark_path = ROOT / "data/session31b-benchmark-report.json"
    _write_json(benchmark_path, benchmark)
    if not benchmark["passed"]:
        raise RuntimeError("Session 31B benchmark failed")

    schema_paths = [
        ROOT / "premium/schemas/v2/evidence-ledger-v3.schema.json",
        ROOT / "premium/schemas/v2/authority-decision-v1.schema.json",
        ROOT / "premium/schemas/v2/evidence-coverage-report-v1.schema.json",
    ]
    contracts = []
    for path in schema_paths:
        value = json.loads(path.read_text(encoding="utf-8"))
        contracts.append({"name": path.name, "$id": value["$id"],
                          "contractVersion": value["x-contract-version"],
                          "sha256": sha256(path.read_bytes()).hexdigest()})
    schema_catalog = {
        "schema": "dna-session31b-schema-catalog", "version": "1.0",
        "date": date.today().isoformat(), "contracts": contracts,
        "catalogHash": sha256(_canonical(contracts)).hexdigest(),
    }
    schema_catalog_path = ROOT / "data/session31b-schema-catalog.json"
    _write_json(schema_catalog_path, schema_catalog)
    _update_feature_matrix()

    report = {
        "schema": "dna-session31b-test-report", "version": "1.0",
        "date": date.today().isoformat(), "result": "pass",
        "scope": "content-addressed-factory-gold-analysis-expression-articulation-authority-resolution",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures),
                        "errors": len(result.errors)},
        "benchmark": {"report": str(benchmark_path.relative_to(ROOT)), **{
            key: benchmark[key] for key in (
                "ledgerHash", "totalSubjects", "explicitAuthoritySubjects", "coverageRate",
                "decisionCounts", "subjectCounts", "evidenceCount", "verifiedRegistryCount",
                "firstBuildSeconds", "cachedBuildSeconds", "benchmarkHash",
            )}},
        "artifacts": {name: str(path.relative_to(ROOT)) for name, path in paths.items()} | {
            "schemaCatalog": str(schema_catalog_path.relative_to(ROOT)),
        },
        "transports": {"cli": "session31b_evidence_resolver.py",
                       "api": "/api/evidence-authority-resolver",
                       "guiWorkspace": "EVIDENCE AUTHORITY LEDGER 3.0", "apiGuiParity": True},
        "invariants": ledger["safety"],
        "status": {
            "session31BEvidenceAuthority": "SOFTWARE_VALIDATED / READ_ONLY FOUNDATION",
            "activeSoftwareBaseline": "4.9.1-evidence-authority-foundation",
            "trackPlanFullOptimizer": "NEXT", "evidenceDrivenRenderer": "PLANNED",
            "finalMidiExport": "BLOCKED", "humanListeningEvidence": "0/2 VERIFIED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data/session31b-test-report.json"
    _write_json(report_path, report)
    recovery_path = ROOT / "data/recovery-release-report.json"
    recovery_total = None
    if recovery_path.is_file():
        recovery = json.loads(recovery_path.read_text(encoding="utf-8"))
        if recovery.get("result") == "pass":
            recovery_total = recovery.get("tests", {}).get("run")
    release_path = ROOT / "data/release-check-report.json"
    if release_path.is_file():
        release = json.loads(release_path.read_text(encoding="utf-8"))
        release.setdefault("premiumReadiness", {}).update({
            "softwareBaseline": "4.9.1-evidence-authority-foundation",
            "session31B": f"{result.testsRun}/{result.testsRun} PASS",
            "evidenceAuthorityResolver": "SOFTWARE_VALIDATED_READ_ONLY",
            "trackPlanFullOptimizer": "NEXT",
            "finalMidiExport": "BLOCKED", "premiumProduct": "PREVIEW_ONLY",
            "physicalPa800": "WAITING_FOR_DEVICE",
            **({"recoveryPremiumAnalysisEvidence": f"{recovery_total}/{recovery_total} PASS"}
               if recovery_total else {}),
        })
        _write_json(release_path, release)
    compliance_path = ROOT / "data/master-prompt-compliance.json"
    if compliance_path.is_file():
        compliance = json.loads(compliance_path.read_text(encoding="utf-8"))
        compliance.setdefault("summary", {}).update({
            "session31BEvidenceAuthority": f"{result.testsRun}/{result.testsRun} PASS",
            "activeSoftwareBaseline": "4.9.1-evidence-authority-foundation",
            "evidenceAuthorityResolver": "SOFTWARE_VALIDATED_READ_ONLY",
            "trackPlanFullOptimizer": "NEXT",
            **({"recoveryPremiumAnalysisEvidence": f"{recovery_total}/{recovery_total} PASS"}
               if recovery_total else {}),
        })
        evidence_items = compliance.setdefault("evidence", [])
        for relative in (
            "data/session31b-test-report.json", "data/session31b-benchmark-report.json",
            "data/session31b-schema-catalog.json", "artifacts/session31b-evidence-ledger.json",
            "artifacts/session31b-evidence-coverage-report.json",
        ):
            if relative not in evidence_items:
                evidence_items.append(relative)
        _write_json(compliance_path, compliance)
    print(
        f"Session 31B PASS: {result.testsRun}/{result.testsRun}; "
        f"subjects={coverage['totalSubjects']}; coverage={coverage['coverageRate']:.4f}; "
        f"{report_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())