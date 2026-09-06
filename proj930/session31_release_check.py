#!/usr/bin/env python3
"""Run the Session 31 automatic analysis and track-instrument gate."""

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

from dna_midi_studio import analyze_track_instruments, load_factory_catalog  # noqa: E402
from dna_midi_studio.session31_fixture import build_session31_chain  # noqa: E402


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _update_feature_matrix() -> None:
    path = ROOT / "data/premium-feature-matrix.json"
    matrix = json.loads(path.read_text(encoding="utf-8"))
    matrix["softwareBaseline"] = "4.9-automatic-analysis-foundation"
    feature = {
        "session": 31,
        "id": "automatic-track-instrument-analysis",
        "priority": "P0",
        "status": "SOFTWARE_VALIDATED / EVIDENCE_FIRST_FOUNDATION",
        "evidence": "data/session31-test-report.json",
        "blocker": "Full EvidenceLedger and mutating TrackPlan remain scheduled after this read-only phase",
        "limitations": [
            "GM family, register and track-name evidence are hints only",
            "Shared channels, incomplete SoundBinding and missing Factory profiles require manual review",
            "The detector has no MIDI mutation, dynamics, validator or device authority",
        ],
    }
    matrix["features"] = [item for item in matrix["features"] if item.get("session") != 31]
    matrix["features"].append(feature)
    matrix["premiumProductStatus"] = "PREVIEW_AUTOMATIC_ANALYSIS_FOUNDATION"
    _write_json(path, matrix)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session31.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    if result.testsRun != 136:
        raise RuntimeError(f"Session 31 expected 136 tests, got {result.testsRun}")

    fixture = build_session31_chain(ROOT)
    production_catalog = load_factory_catalog(ROOT)
    if not production_catalog:
        raise RuntimeError("Production Factory registry is required for the Session 31 evidence gate")
    start = perf_counter()
    production_analysis = analyze_track_instruments(
        fixture["midi"].to_bytes(), "session31-production-evidence.mid",
        factory_catalog=production_catalog,
    )
    elapsed = perf_counter() - start

    paths = {
        "referenceMidi": ROOT / "artifacts/session31-reference.mid",
        "automaticAnalysis": ROOT / "artifacts/session31-track-instrument-analysis.json",
        "exactFixtureAnalysis": ROOT / "artifacts/session31-exact-fixture-analysis.json",
        "sharedChannelAnalysis": ROOT / "artifacts/session31-shared-channel-analysis.json",
        "optimizationBaseline": ROOT / "artifacts/session31-application-optimization-baseline.json",
    }
    paths["referenceMidi"].write_bytes(fixture["midi"].to_bytes())
    _write_json(paths["automaticAnalysis"], production_analysis)
    _write_json(paths["exactFixtureAnalysis"], fixture["analysis"])
    _write_json(paths["sharedChannelAnalysis"], fixture["sharedAnalysis"])
    _write_json(paths["optimizationBaseline"], {
        "schema": "dna-application-optimization-baseline", "version": "1.0",
        "date": date.today().isoformat(),
        "sourceAnalysisHash": production_analysis["analysisHash"],
        "automaticTrackPolicy": production_analysis["applicationOptimizationBaseline"],
        "workstreams": [
            {"id": "analysis-fusion", "status": "FOUNDATION_VALIDATED"},
            {"id": "evidence-authority-resolver", "status": "NEXT"},
            {"id": "track-plan-full-optimizer", "status": "PLANNED"},
            {"id": "deterministic-renderer", "status": "PLANNED"},
            {"id": "performance-memory-io", "status": "PLANNED"},
            {"id": "zero-silent-failure", "status": "PLANNED"},
        ],
        "invariants": {
            "readOnly": True, "finalMidiExportAllowed": False,
            "factoryDynamicsAuthorityChanged": False, "physicalPa800Claimed": False,
        },
    })

    benchmark = {
        "schema": "dna-session31-automatic-analysis-benchmark", "version": "1.0",
        "date": date.today().isoformat(), "license": "self-authored-test-fixtures",
        "sourceMidiSha256": fixture["midi"].digest(),
        "productionFactoryDatabaseVersion": production_catalog["databaseVersion"],
        "productionFactoryProfileCount": len(production_catalog["profiles"]),
        "analysisSeconds": round(elapsed, 6),
        "physicalTrackCount": production_analysis["summary"]["physicalTrackCount"],
        "segmentCount": production_analysis["summary"]["segmentCount"],
        "exactFactorySegmentCount": production_analysis["summary"]["exactFactorySegmentCount"],
        "acceptedTrackCount": production_analysis["summary"]["acceptedTrackCount"],
        "manualReviewTrackCount": production_analysis["summary"]["manualReviewTrackCount"],
        "midSongProgramSegments": len(next(
            track for track in production_analysis["tracks"] if track["trackName"] == "Rhythm Guitar"
        )["segments"]),
        "velocityBlindDecisionHashStable": fixture["analysis"]["decisionHash"] == fixture["velocityAnalysis"]["decisionHash"],
        "sharedChannelFailClosed": fixture["sharedAnalysis"]["summary"]["manualReviewTrackCount"] == 2,
        "approximateSoundBindingAllowed": False,
        "midiMutationAuthority": False,
        "passed": all((
            elapsed < 2.0,
            len(production_catalog["profiles"]) >= 1900,
            production_analysis["summary"]["segmentCount"] == 6,
            fixture["analysis"]["summary"]["acceptedTrackCount"] == 5,
            fixture["analysis"]["decisionHash"] == fixture["velocityAnalysis"]["decisionHash"],
            fixture["sharedAnalysis"]["summary"]["manualReviewTrackCount"] == 2,
            not production_analysis["invariants"]["midiMutationAuthority"],
        )),
    }
    benchmark["benchmarkHash"] = sha256(_canonical(benchmark)).hexdigest()
    benchmark_path = ROOT / "data/session31-benchmark-report.json"
    _write_json(benchmark_path, benchmark)
    if not benchmark["passed"]:
        raise RuntimeError("Session 31 automatic analysis benchmark failed")

    schema_path = ROOT / "premium/schemas/v2/track-instrument-analysis-v3.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema_catalog = {
        "schema": "dna-session31-schema-catalog", "version": "1.0",
        "date": date.today().isoformat(),
        "contracts": [{"name": schema_path.name, "$id": schema["$id"],
                       "contractVersion": schema["x-contract-version"],
                       "sha256": sha256(schema_path.read_bytes()).hexdigest()}],
    }
    schema_catalog["catalogHash"] = sha256(_canonical(schema_catalog["contracts"])).hexdigest()
    schema_catalog_path = ROOT / "data/session31-schema-catalog.json"
    _write_json(schema_catalog_path, schema_catalog)
    _update_feature_matrix()

    report = {
        "schema": "dna-session31-test-report", "version": "1.0",
        "date": date.today().isoformat(), "result": "pass",
        "scope": "automatic-song-track-instrument-analysis-exact-soundbinding-velocity-blind-and-full-optimization-baseline",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures),
                        "errors": len(result.errors)},
        "benchmark": {"report": str(benchmark_path.relative_to(ROOT)), **{
            key: benchmark[key] for key in (
                "productionFactoryDatabaseVersion", "productionFactoryProfileCount",
                "analysisSeconds", "physicalTrackCount", "segmentCount",
                "exactFactorySegmentCount", "acceptedTrackCount", "manualReviewTrackCount",
                "midSongProgramSegments", "velocityBlindDecisionHashStable",
                "sharedChannelFailClosed", "benchmarkHash",
            )}},
        "artifacts": {name: str(path.relative_to(ROOT)) for name, path in paths.items()} | {
            "schemaCatalog": str(schema_catalog_path.relative_to(ROOT)),
        },
        "transports": {
            "cli": "session31_track_analysis.py", "api": "/api/automatic-track-analysis",
            "guiWorkspace": "AUTOMATIC SONG & TRACK ANALYSIS 3.0", "apiGuiParity": True,
        },
        "invariants": {
            "analysisVelocityUsed": False, "goldUsed": False,
            "approximateSoundBindingAllowed": False, "trackLocalSoundState": True,
            "midSongProgramChangesSegmented": True, "sharedChannelAutoAcceptAllowed": False,
            "originalMidiChanged": False, "midiMutationAuthority": False,
            "validatorAuthority": False, "physicalCertificationClaimed": False,
            "finalMidiExportAllowed": False,
        },
        "status": {
            "session31AutomaticAnalysis": "SOFTWARE_VALIDATED / EVIDENCE_FIRST_FOUNDATION",
            "activeSoftwareBaseline": "4.9-automatic-analysis-foundation",
            "fullApplicationOptimization": "ROADMAP_ACTIVE",
            "evidenceAuthorityResolver": "NEXT",
            "trackPlanRenderer": "PLANNED",
            "finalMidiExport": "BLOCKED",
            "humanListeningEvidence": "0/2 VERIFIED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data/session31-test-report.json"
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
            "softwareBaseline": "4.9-automatic-analysis-foundation",
            "session31A": f"{result.testsRun}/{result.testsRun} PASS",
            "automaticTrackInstrumentAnalysis": "SOFTWARE_VALIDATED_READ_ONLY",
            "fullApplicationOptimization": "ROADMAP_ACTIVE",
            "evidenceAuthorityResolver": "NEXT",
            "finalMidiExport": "BLOCKED",
            "premiumProduct": "PREVIEW_ONLY",
            "physicalPa800": "WAITING_FOR_DEVICE",
            **({"recoveryPremiumAnalysis": f"{recovery_total}/{recovery_total} PASS"}
               if recovery_total else {}),
        })
        _write_json(release_path, release)
    compliance_path = ROOT / "data/master-prompt-compliance.json"
    if compliance_path.is_file():
        compliance = json.loads(compliance_path.read_text(encoding="utf-8"))
        compliance.setdefault("summary", {}).update({
            "session31AutomaticTrackAnalysis": f"{result.testsRun}/{result.testsRun} PASS",
            "activeSoftwareBaseline": "4.9-automatic-analysis-foundation",
            "automaticTrackInstrumentAnalysis": "SOFTWARE_VALIDATED_READ_ONLY",
            "fullApplicationOptimization": "ROADMAP_ACTIVE",
            "evidenceAuthorityResolver": "NEXT",
            **({"recoveryPremiumAnalysis": f"{recovery_total}/{recovery_total} PASS"}
               if recovery_total else {}),
        })
        evidence = compliance.setdefault("evidence", [])
        for relative in (
            "data/session31-test-report.json", "data/session31-benchmark-report.json",
            "data/session31-schema-catalog.json",
            "artifacts/session31-track-instrument-analysis.json",
            "artifacts/session31-application-optimization-baseline.json",
        ):
            if relative not in evidence:
                evidence.append(relative)
        _write_json(compliance_path, compliance)
    print(
        f"Session 31 PASS: {result.testsRun}/{result.testsRun}; "
        f"profiles={benchmark['productionFactoryProfileCount']}; "
        f"segments={benchmark['segmentCount']}; analysis={elapsed:.4f}s; {report_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())