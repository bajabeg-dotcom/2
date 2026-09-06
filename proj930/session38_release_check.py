#!/usr/bin/env python3
"""Run Session 38 Pa800 Device Lab software-foundation gate."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio.session38_fixture import build_session38_chain  # noqa: E402


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
    matrix["softwareBaseline"] = "4.11.1-device-certification-intake-foundation"
    matrix["premiumProductStatus"] = "DEVICE_LAB_PREVIEW"
    value = {
        "session": 38,
        "feature": "Pa800 Mapping Lab and DeviceProfile Certification Intake",
        "priority": "P0",
        "status": "SOFTWARE_VALIDATED / WAITING_FOR_DEVICE",
        "evidence": "data/session38-test-report.json",
        "blocker": "PHYSICAL_PA800_OPERATOR_CAPTURE_REQUIRED",
        "limitations": [
            "The built-in reference is a blank intake template and cannot certify hardware",
            "Only exact hashed external image/audio evidence can activate device-specific maps",
            "A DeviceProfile alone never unlocks final certified MIDI export",
        ],
    }
    features = matrix.setdefault("features", [])
    row = next((item for item in features if item.get("session") == 38), None)
    if row is None:
        features.append(value)
    else:
        row.update(value)
    _write(path, matrix)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session38.py")
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful():
        return 1
    if result.testsRun != 200:
        raise RuntimeError(f"Session 38 expected 200 tests, got {result.testsRun}")

    chain = build_session38_chain(ROOT)
    artifacts = {
        "captureTemplate": ROOT / "artifacts/session38-device-capture-template.json",
        "report": ROOT / "artifacts/session38-device-certification-report.json",
        "profile": ROOT / "artifacts/session38-device-profile.json",
    }
    for key, path in artifacts.items():
        _write(path, chain[key])

    contracts = []
    for name in ("pa800-device-capture-v2.schema.json", "device-profile-v2.schema.json",
                 "device-certification-report-v2.schema.json"):
        path = ROOT / "premium/schemas/v2" / name
        schema = json.loads(path.read_text(encoding="utf-8"))
        contracts.append({"name": name, "$id": schema["$id"],
                          "contractVersion": schema["x-contract-version"],
                          "sha256": sha256(path.read_bytes()).hexdigest()})
    schema_catalog = {
        "schema": "dna-session38-schema-catalog", "version": "1.0",
        "date": date.today().isoformat(), "contracts": contracts,
        "catalogHash": sha256(_canonical(contracts)).hexdigest(),
    }
    schema_path = ROOT / "data/session38-schema-catalog.json"
    _write(schema_path, schema_catalog)

    benchmark = {
        "schema": "dna-session38-device-lab-benchmark", "version": "1.0",
        "date": date.today().isoformat(),
        "requiredPhysicalChecks": len(chain["captureTemplate"]["checks"]),
        "requiredMarkers": len(chain["captureTemplate"]["markerResults"]),
        "requiredStyleBindings": len(chain["captureTemplate"]["styleBindings"]),
        "requiredArticulationEngines": len(chain["captureTemplate"]["articulationCaptures"]),
        "requiredVoiceCostRows": len(chain["captureTemplate"]["voiceMeasurements"]["roleVoiceCosts"]),
        "captureAuthority": chain["captureTemplate"]["captureAuthority"],
        "deviceStatus": chain["report"]["status"],
        "machineObservedPhysicalDevice": chain["report"]["machineObservedPhysicalDevice"],
        "deviceSpecificMapsAllowed": chain["profile"]["activation"]["deviceSpecificMapsAllowed"],
        "voiceCostModelAllowed": chain["profile"]["activation"]["voiceCostModelAllowed"],
        "pa800CertifiedLabelAllowed": chain["profile"]["activation"]["pa800CertifiedLabelAllowed"],
        "finalCertifiedMidiExportAllowed": chain["profile"]["activation"]["finalCertifiedMidiExportAllowed"],
        "requiredExternalEvidence": ["HASHED_DEVICE_IMAGE", "HASHED_DEVICE_AUDIO",
                                     "OPERATOR_APPROVED_HASH", "INDEPENDENT_REVIEW"],
    }
    benchmark["benchmarkHash"] = sha256(_canonical(benchmark)).hexdigest()
    benchmark_path = ROOT / "data/session38-benchmark-report.json"
    _write(benchmark_path, benchmark)

    _update_feature_matrix()
    report = {
        "schema": "dna-session38-test-report", "version": "1.0",
        "date": date.today().isoformat(), "result": "pass",
        "scope": "pa800-device-lab-intake-and-device-profile-certification-foundation",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures),
                        "errors": len(result.errors)},
        "benchmark": {"report": str(benchmark_path.relative_to(ROOT)), **benchmark},
        "artifacts": {key: str(path.relative_to(ROOT)) for key, path in artifacts.items()} |
                     {"schemaCatalog": str(schema_path.relative_to(ROOT))},
        "transports": {"cli": "session38_device_lab.py", "api": "/api/device-certification",
                       "guiWorkspace": "PA800 DEVICE LAB", "apiGuiParity": True},
        "invariants": {
            "allEightStyleChannelsRequired": True,
            "allTenMarkersRequired": True,
            "exactBankProgramOnly": True,
            "confirmedUnsupportedUnknownSeparated": True,
            "voiceCostRequiresPhysicalMeasurement": True,
            "imageAndAudioMagicHashVerified": True,
            "operatorApprovedHashRequired": True,
            "softwareReferenceCanCertify": False,
            "machinePhysicalObservationClaimed": False,
            "finalCertifiedMidiExportAllowed": False,
        },
        "status": {
            "session38DeviceLab": "SOFTWARE_VALIDATED / WAITING_FOR_DEVICE",
            "activeSoftwareBaseline": "4.11.1-device-certification-intake-foundation",
            "allowedProductName": "AI PREMIUM ARRANGER PREVIEW",
            "physicalPa800": "WAITING_FOR_DEVICE",
            "deviceProfile": "PENDING_EXTERNAL_CAPTURE",
            "deviceSpecificMaps": "BLOCKED",
            "voiceCostModel": "BLOCKED",
            "finalCertifiedMidiExport": "BLOCKED",
        },
    }
    report_path = ROOT / "data/session38-test-report.json"
    _write(report_path, report)

    for path_name, branch in (
        ("data/master-prompt-compliance.json", "summary"),
        ("data/release-check-report.json", "premiumReadiness"),
    ):
        path = ROOT / path_name
        if path.is_file():
            value = json.loads(path.read_text(encoding="utf-8"))
            value.setdefault(branch, {}).update({
                "activeSoftwareBaseline" if branch == "summary" else "softwareBaseline":
                    "4.11.1-device-certification-intake-foundation",
                "session38DeviceLab": "200/200 PASS",
                "physicalPa800": "WAITING_FOR_DEVICE",
                "deviceProfile2": "SOFTWARE_VALIDATED_INTAKE / EXTERNAL_CAPTURE_PENDING",
                "finalCertifiedMidiExport": "BLOCKED",
            })
            _write(path, value)
    print("Session 38 PASS: 200/200; Device Lab intake=READY; physical Pa800=WAITING_FOR_DEVICE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())