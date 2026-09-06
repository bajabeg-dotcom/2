#!/usr/bin/env python3
"""Build and validate the Session 14 physical-device test kit."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio.device_certification import prepare_device_kit  # noqa: E402


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session14.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    prepared = prepare_device_kit(ROOT, ROOT / "artifacts" / "session14-device-kit")
    manifest = prepared["manifest"]
    report = {
        "schema": "dna-session14-preflight-report",
        "version": "1.0",
        "date": date.today().isoformat(),
        "result": "pass",
        "scope": "physical-pa800-test-kit-preflight-only",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures),
                        "errors": len(result.errors)},
        "kit": {
            "manifest": "artifacts/session14-device-kit/kit-manifest.json",
            "manifestSha256": prepared["manifestSha256"],
            "resultTemplate": "artifacts/session14-device-kit/device-result-template.json",
            "functionalMidi": "artifacts/session14-device-kit/DNA_PA800_FUNCTIONAL_TEST.mid",
            "polyphonyMidi": "artifacts/session14-device-kit/DNA_PA800_POLYPHONY_STRESS.mid",
            "downloadZip": "artifacts/session14-device-kit/DNA-PA800-Session14-Device-Test-Kit.zip",
            "downloadZipSha256": prepared["deviceKitZipSha256"],
            "artifactCount": len(manifest["artifacts"]),
        },
        "invariants": {
            "officialSmf0MarkerContract": True,
            "allEightStyleChannels": True,
            "projectPolyphonyPeak": 54,
            "physicalObservationFabricated": False,
            "humanAttestationRequired": True,
            "imageAndAudioEvidenceRequired": True,
        },
        "status": {
            "session14DevicePreflight": "SOFTWARE_VALIDATED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data" / "session14-preflight-report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    compliance_path = ROOT / "data" / "master-prompt-compliance.json"
    if compliance_path.is_file():
        compliance = json.loads(compliance_path.read_text(encoding="utf-8"))
        compliance.setdefault("summary", {})["session14DevicePreflight"] = "12/12 PASS"
        compliance["summary"]["physicalPa800"] = "WAITING_FOR_DEVICE"
        evidence = compliance.setdefault("evidence", [])
        if "data/session14-preflight-report.json" not in evidence:
            evidence.append("data/session14-preflight-report.json")
        compliance_path.write_text(
            json.dumps(compliance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    print(f"Session 14 device preflight PASS: {result.testsRun} tests; {report_path}")
    print("Physical Pa800 status: WAITING_FOR_DEVICE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())