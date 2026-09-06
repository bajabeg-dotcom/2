#!/usr/bin/env python3
"""Run the Session 32 TrackPlan 3.0 / Full Optimizer dry-run gate."""

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

from dna_midi_studio import build_track_plan  # noqa: E402
from dna_midi_studio.session32_fixture import build_session32_chain  # noqa: E402


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _update_feature_matrix() -> None:
    path = ROOT / "data/premium-feature-matrix.json"
    matrix = json.loads(path.read_text(encoding="utf-8"))
    matrix["softwareBaseline"] = "4.9.2-track-plan-foundation"
    matrix["features"] = [item for item in matrix["features"] if item.get("id") != "track-plan-full-optimizer"]
    matrix["features"].append({
        "session": "32", "id": "track-plan-full-optimizer", "priority": "P0",
        "status": "SOFTWARE_VALIDATED / READ_ONLY MUTATION CONTRACT",
        "evidence": "data/session32-test-report.json",
        "blocker": "Deterministic evidence-driven MIDI renderer remains Session 33 work",
        "limitations": [
            "TrackPlan predicts and authorizes operations but writes zero MIDI bytes",
            "One reference drum source remains MANUAL_REVIEW because exact Factory coverage is incomplete",
            "Final export, human listening and physical Pa800 certification remain blocked",
        ],
    })
    matrix["premiumProductStatus"] = "PREVIEW_TRACK_PLAN_FOUNDATION"
    _write_json(path, matrix)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session32.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    if result.testsRun != 152:
        raise RuntimeError(f"Session 32 expected 152 tests, got {result.testsRun}")

    fixture = build_session32_chain(ROOT)
    plan = fixture["trackPlan"]
    start = perf_counter()
    repeated = build_track_plan(
        fixture["midi"].to_bytes(), fixture["documents"], fixture["ledger"],
        fixture["targetBindings"], fixture["controls"], ROOT,
    )
    build_seconds = perf_counter() - start
    if repeated != plan:
        raise RuntimeError("TrackPlan is not deterministic")

    paths = {
        "referenceMidi": ROOT / "artifacts/session32-reference.mid",
        "trackAnalysis": ROOT / "artifacts/session32-track-analysis.json",
        "evidenceLedger": ROOT / "artifacts/session32-evidence-ledger.json",
        "targetBindings": ROOT / "artifacts/session32-target-bindings.json",
        "trackPlan": ROOT / "artifacts/session32-track-plan.json",
        "dryRun": ROOT / "artifacts/session32-optimizer-dry-run.json",
    }
    paths["referenceMidi"].write_bytes(fixture["midi"].to_bytes())
    _write_json(paths["trackAnalysis"], fixture["documents"]["trackAnalysis"])
    _write_json(paths["evidenceLedger"], fixture["ledger"])
    _write_json(paths["targetBindings"], {"targetBindings": fixture["targetBindings"]})
    _write_json(paths["trackPlan"], plan)
    _write_json(paths["dryRun"], plan["dryRun"])

    benchmark = {
        "schema": "dna-session32-track-plan-benchmark", "version": "1.0",
        "date": date.today().isoformat(), "license": "self-authored-test-fixtures",
        "sourceMidiSha256": fixture["midi"].digest(), "trackPlanHash": plan["trackPlanHash"],
        "sourceTrackPlans": len(plan["sourceTrackPlans"]), "arrangerFragments": len(plan["fragments"]),
        "exactTargetBindings": len(plan["targetBindings"]),
        "replaceFragments": plan["dryRun"]["fragmentDecisionCounts"].get("REPLACE", 0),
        "manualReviewScopes": len(plan["manualReview"]),
        "plannedOperations": sum(plan["dryRun"]["operationCounts"].values()),
        "operationCounts": plan["dryRun"]["operationCounts"],
        "factoryRegistryVerified": fixture["ledger"]["registries"]["factoryProfiles"]["status"] == "VERIFIED",
        "evidenceCoverageRate": fixture["ledger"]["coverage"]["coverageRate"],
        "arrangerFragmentsReady": plan["readiness"]["arrangerFragmentsReady"],
        "deterministic": repeated == plan, "trackPlanBuildSeconds": round(build_seconds, 6),
        "midiBytesWritten": plan["dryRun"]["midiBytesWritten"],
        "protectedOriginalNoteChanges": plan["dryRun"]["protectedOriginalNoteChanges"],
        "goldVelocityChanges": plan["dryRun"]["goldVelocityChanges"],
        "finalMidiExportAllowed": plan["readiness"]["finalMidiExportAllowed"],
    }
    benchmark["passed"] = all((
        benchmark["sourceTrackPlans"] == 5, benchmark["arrangerFragments"] == 52,
        benchmark["exactTargetBindings"] == 52, benchmark["replaceFragments"] == 52,
        benchmark["manualReviewScopes"] == 1, benchmark["plannedOperations"] == 249,
        benchmark["factoryRegistryVerified"], benchmark["evidenceCoverageRate"] == 1.0,
        benchmark["arrangerFragmentsReady"], benchmark["deterministic"], build_seconds < 2.0,
        benchmark["midiBytesWritten"] == 0, benchmark["protectedOriginalNoteChanges"] == 0,
        benchmark["goldVelocityChanges"] == 0, not benchmark["finalMidiExportAllowed"],
    ))
    benchmark["benchmarkHash"] = sha256(_canonical(benchmark)).hexdigest()
    benchmark_path = ROOT / "data/session32-benchmark-report.json"
    _write_json(benchmark_path, benchmark)
    if not benchmark["passed"]:
        raise RuntimeError("Session 32 benchmark failed")

    schema_paths = [
        ROOT / "premium/schemas/v2/track-plan-v3.schema.json",
        ROOT / "premium/schemas/v2/optimizer-operation-v1.schema.json",
        ROOT / "premium/schemas/v2/optimizer-dry-run-v1.schema.json",
    ]
    contracts = []
    for path in schema_paths:
        value = json.loads(path.read_text(encoding="utf-8"))
        contracts.append({"name": path.name, "$id": value["$id"],
                          "contractVersion": value["x-contract-version"],
                          "sha256": sha256(path.read_bytes()).hexdigest()})
    schema_catalog = {
        "schema": "dna-session32-schema-catalog", "version": "1.0",
        "date": date.today().isoformat(), "contracts": contracts,
        "catalogHash": sha256(_canonical(contracts)).hexdigest(),
    }
    schema_catalog_path = ROOT / "data/session32-schema-catalog.json"
    _write_json(schema_catalog_path, schema_catalog)
    _update_feature_matrix()

    report = {
        "schema": "dna-session32-test-report", "version": "1.0",
        "date": date.today().isoformat(), "result": "pass",
        "scope": "evidence-driven-track-plan-and-full-optimizer-dry-run-contract",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures),
                        "errors": len(result.errors)},
        "benchmark": {"report": str(benchmark_path.relative_to(ROOT)), **{
            key: benchmark[key] for key in (
                "trackPlanHash", "sourceTrackPlans", "arrangerFragments", "exactTargetBindings",
                "replaceFragments", "manualReviewScopes", "plannedOperations", "operationCounts",
                "evidenceCoverageRate", "trackPlanBuildSeconds", "benchmarkHash",
            )}},
        "artifacts": {name: str(path.relative_to(ROOT)) for name, path in paths.items()} | {
            "schemaCatalog": str(schema_catalog_path.relative_to(ROOT)),
        },
        "transports": {"cli": "session32_track_plan.py", "api": "/api/track-plan",
                       "guiWorkspace": "TRACK PLAN / FULL OPTIMIZER DRY RUN 3.0",
                       "apiGuiParity": True},
        "invariants": plan["safety"],
        "status": {
            "session32TrackPlanFullOptimizer": "SOFTWARE_VALIDATED / READ_ONLY MUTATION CONTRACT",
            "activeSoftwareBaseline": "4.9.2-track-plan-foundation",
            "evidenceDrivenRenderer": "NEXT", "finalMidiExport": "BLOCKED",
            "humanListeningEvidence": "0/2 VERIFIED", "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data/session32-test-report.json"
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
            "softwareBaseline": "4.9.2-track-plan-foundation",
            "session32": f"{result.testsRun}/{result.testsRun} PASS",
            "trackPlanFullOptimizer": "SOFTWARE_VALIDATED_READ_ONLY",
            "evidenceDrivenRenderer": "NEXT", "finalMidiExport": "BLOCKED",
            "premiumProduct": "PREVIEW_ONLY", "physicalPa800": "WAITING_FOR_DEVICE",
            **({"recoveryPremiumTrackPlan": f"{recovery_total}/{recovery_total} PASS"}
               if recovery_total else {}),
        })
        _write_json(release_path, release)
    compliance_path = ROOT / "data/master-prompt-compliance.json"
    if compliance_path.is_file():
        compliance = json.loads(compliance_path.read_text(encoding="utf-8"))
        compliance.setdefault("summary", {}).update({
            "session32TrackPlanFullOptimizer": f"{result.testsRun}/{result.testsRun} PASS",
            "activeSoftwareBaseline": "4.9.2-track-plan-foundation",
            "trackPlanFullOptimizer": "SOFTWARE_VALIDATED_READ_ONLY",
            "evidenceDrivenRenderer": "NEXT",
            **({"recoveryPremiumTrackPlan": f"{recovery_total}/{recovery_total} PASS"}
               if recovery_total else {}),
        })
        evidence = compliance.setdefault("evidence", [])
        for relative in (
            "data/session32-test-report.json", "data/session32-benchmark-report.json",
            "data/session32-schema-catalog.json", "artifacts/session32-track-plan.json",
            "artifacts/session32-optimizer-dry-run.json",
        ):
            if relative not in evidence:
                evidence.append(relative)
        _write_json(compliance_path, compliance)
    print(
        f"Session 32 PASS: {result.testsRun}/{result.testsRun}; "
        f"fragments={len(plan['fragments'])}; operations={benchmark['plannedOperations']}; "
        f"MIDI bytes written=0; {report_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())