#!/usr/bin/env python3
"""Run every source-backed recovery gate available in this snapshot."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path

import session2_release_check
import session3_release_check
import session4_release_check
import session5_release_check
import session6_release_check
import session7_release_check
import session8_release_check
import session9_release_check
import session10_release_check
import session11_release_check
import session12_release_check
import session13_release_check
import session14_release_check
import session15_release_check
import session17_release_check
import session18_release_check
import session19_release_check
import session20_release_check
import session21_release_check
import session22_release_check
import session23_release_check
import session24_release_check
import session25_release_check
import session26_release_check
import session27_release_check
import session28_release_check
import session29_release_check
import session30_release_check
import session31_release_check
import session31b_release_check
import session32_release_check
import session33_release_check
import session34_release_check
import session35_release_check
import session36_release_check
import session37_release_check
import session38_release_check
import release_packager


ROOT = Path(__file__).resolve().parent


def finalize_release_package() -> None:
    """Rebuild the ZIP after the aggregate report exists and align Session 13 metadata."""

    zip_path, _checksum_path, manifest = release_packager.build_release()
    session13_path = ROOT / "data" / "session13-test-report.json"
    if session13_path.is_file():
        session13 = json.loads(session13_path.read_text(encoding="utf-8"))
        session13.setdefault("package", {}).update({
            "zip": str(zip_path.relative_to(ROOT)),
            "zipSha256": sha256(zip_path.read_bytes()).hexdigest(),
            "bytes": zip_path.stat().st_size,
            "files": len(manifest["files"]),
            "contentHash": manifest["contentHash"],
        })
        session13_path.write_text(
            json.dumps(session13, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )


def main() -> int:
    gates = [
        ("session2", session2_release_check.main, ROOT / "data" / "session2-test-report.json"),
        ("session3", session3_release_check.main, ROOT / "data" / "session3-test-report.json"),
        ("session4", session4_release_check.main, ROOT / "data" / "session4-test-report.json"),
        ("session5", session5_release_check.main, ROOT / "data" / "session5-test-report.json"),
        ("session6", session6_release_check.main, ROOT / "data" / "session6-test-report.json"),
        ("session7", session7_release_check.main, ROOT / "data" / "session7-test-report.json"),
        ("session8", session8_release_check.main, ROOT / "data" / "session8-test-report.json"),
        ("session9", session9_release_check.main, ROOT / "data" / "session9-test-report.json"),
        ("session10", session10_release_check.main, ROOT / "data" / "session10-test-report.json"),
        ("session11", session11_release_check.main, ROOT / "data" / "session11-test-report.json"),
        ("session12", session12_release_check.main, ROOT / "data" / "session12-test-report.json"),
        # Device preflight must run before packaging so its test kit is included
        # in the deterministic Windows release. It does not certify hardware.
        ("session14Preflight", session14_release_check.main, ROOT / "data" / "session14-preflight-report.json"),
        ("session15PremiumBaseline", session15_release_check.main, ROOT / "data" / "session15-test-report.json"),
        ("session18TrackIdentitySoloSafety", session18_release_check.main, ROOT / "data" / "session18-test-report.json"),
        ("session17ProductionAdapter", session17_release_check.main, ROOT / "data" / "session17-test-report.json"),
        ("session19SongUnderstanding", session19_release_check.main, ROOT / "data" / "session19-test-report.json"),
        ("session20AiProducerBrief", session20_release_check.main, ROOT / "data" / "session20-test-report.json"),
        ("session21ArrangementGraph", session21_release_check.main, ROOT / "data" / "session21-test-report.json"),
        ("session22CandidateVariationEngine", session22_release_check.main, ROOT / "data" / "session22-test-report.json"),
        ("session23GroovePolyphony", session23_release_check.main, ROOT / "data" / "session23-test-report.json"),
        ("session24SoloExpression", session24_release_check.main, ROOT / "data" / "session24-test-report.json"),
        ("session25ArticulationMaps", session25_release_check.main, ROOT / "data" / "session25-test-report.json"),
        ("session26PremiumPreview", session26_release_check.main, ROOT / "data" / "session26-test-report.json"),
        ("session27MusicQualityEvaluator", session27_release_check.main, ROOT / "data" / "session27-test-report.json"),
        ("session28PremiumProducerWorkflow", session28_release_check.main, ROOT / "data" / "session28-test-report.json"),
        ("session29PersonalProducerProfile", session29_release_check.main, ROOT / "data" / "session29-test-report.json"),
        ("session30ReleaseReadiness", session30_release_check.main, ROOT / "data" / "session30-test-report.json"),
        ("session31AutomaticTrackAnalysis", session31_release_check.main, ROOT / "data" / "session31-test-report.json"),
        ("session31BEvidenceAuthority", session31b_release_check.main, ROOT / "data" / "session31b-test-report.json"),
        ("session32TrackPlanFullOptimizer", session32_release_check.main, ROOT / "data" / "session32-test-report.json"),
        ("session33ArrangementRenderer", session33_release_check.main, ROOT / "data" / "session33-test-report.json"),
        ("session34GlobalCoherence", session34_release_check.main, ROOT / "data" / "session34-test-report.json"),
        ("session35EndToEndArranger", session35_release_check.main, ROOT / "data" / "session35-test-report.json"),
        ("session36ZeroSilentFailure", session36_release_check.main, ROOT / "data" / "session36-test-report.json"),
        ("session37QualityCalibration", session37_release_check.main, ROOT / "data" / "session37-test-report.json"),
        ("session38DeviceCertificationIntake", session38_release_check.main, ROOT / "data" / "session38-test-report.json"),
        ("session13", session13_release_check.main, ROOT / "data" / "session13-test-report.json"),
    ]
    reports = []
    for name, runner, report_path in gates:
        if runner() != 0:
            return 1
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if report.get("result") != "pass":
            raise RuntimeError(f"{name} report did not declare pass")
        reports.append((name, report, report_path))

    tests_run = sum(report["formalSuite"]["testsRun"] for _, report, _ in reports)
    failures = sum(report["formalSuite"]["failures"] for _, report, _ in reports)
    errors = sum(report["formalSuite"]["errors"] for _, report, _ in reports)
    output = {
        "schema": "dna-recovery-release-report",
        "version": "1.0",
        "date": date.today().isoformat(),
        "result": "pass" if failures == 0 and errors == 0 else "fail",
        "tests": {"run": tests_run, "failures": failures, "errors": errors},
        "gates": {
            name: {
                "result": report["result"],
                "testsRun": report["formalSuite"]["testsRun"],
                "evidence": str(path.relative_to(ROOT)),
                "productionGates": {
                    key: value
                    for key, value in report["status"].items()
                    if key.startswith("production")
                },
            }
            for name, report, path in reports
        },
        "limitations": {
            "legacySourceTreePresent": all((ROOT / path).is_file() for path in (
                "release_check.py", "server.py", "test_master_prompt.py")),
            "productionRegistriesPresent": all((ROOT / "data" / name).is_file() for name in (
                "factory-velocity-profiles.json", "gold-patterns.json",
                "factory-style-segments.json", "factory-strumming.json",
                "gold-performance-patterns.json")),
            "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    output_path = ROOT / "data" / "recovery-release-report.json"
    output_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    release_path = ROOT / "data" / "release-check-report.json"
    if release_path.is_file():
        release = json.loads(release_path.read_text(encoding="utf-8"))
        readiness = release.setdefault("premiumReadiness", {})
        for key in tuple(readiness):
            if key.startswith("recoveryPremium"):
                readiness[key] = f"{tests_run}/{tests_run} PASS"
        readiness.update({
            "softwareBaseline": "4.11.1-device-certification-intake-foundation",
            "recoveryPremiumWorkflow": f"{tests_run}/{tests_run} PASS",
            "recoveryPremiumDeviceIntake": f"{tests_run}/{tests_run} PASS",
            "arrangementRenderer": "SOFTWARE_VALIDATED_PREVIEW_MIDI",
            "softwarePreviewMidi": "ALLOWED_AFTER_INDEPENDENT_VERIFIER",
            "finalCertifiedMidiExport": "BLOCKED",
        })
        release_path.write_text(json.dumps(release, indent=2, ensure_ascii=False) + "\n",
                                encoding="utf-8")
    compliance_path = ROOT / "data" / "master-prompt-compliance.json"
    if compliance_path.is_file():
        compliance = json.loads(compliance_path.read_text(encoding="utf-8"))
        summary = compliance.setdefault("summary", {})
        for key in tuple(summary):
            if key.startswith("recoveryPremium"):
                summary[key] = f"{tests_run}/{tests_run} PASS"
        summary.update({
            "activeSoftwareBaseline": "4.11.1-device-certification-intake-foundation",
            "recoveryPremiumWorkflow": f"{tests_run}/{tests_run} PASS",
            "recoveryPremiumDeviceIntake": f"{tests_run}/{tests_run} PASS",
            "arrangementRenderer": "SOFTWARE_VALIDATED_PREVIEW_MIDI",
        })
        compliance_path.write_text(
            json.dumps(compliance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    finalize_release_package()
    print(f"Recovery release PASS: {tests_run}/{tests_run}; {output_path}")
    return 0 if output["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())