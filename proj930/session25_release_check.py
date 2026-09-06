#!/usr/bin/env python3
"""Run the Session 25 ArticulationMap 2.0 software release gate."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import (  # noqa: E402
    articulation_production_readiness,
    build_articulation_plan,
)
from dna_midi_studio.session25_fixture import build_session25_chain  # noqa: E402


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _update_feature_matrix() -> None:
    path = ROOT / "data" / "premium-feature-matrix.json"
    matrix = json.loads(path.read_text(encoding="utf-8"))
    matrix["softwareBaseline"] = "4.3-alpha"
    for feature in matrix["features"]:
        if feature["session"] == 25:
            feature.update({
                "status": "SOFTWARE_VALIDATED / DEVICE_CAPTURE_BLOCKED",
                "evidence": "data/session25-test-report.json",
                "blocker": "operator-approved physical Pa800 capture required",
                "limitations": [
                    "Reference Guitar/RX/DNC maps are SOFTWARE_TEST_ONLY and cannot authorize production",
                    "Final MIDI rendering remains disabled; Session 25 emits a read-only trigger plan",
                ],
            })
    matrix["premiumProductStatus"] = "PLANNED"
    _write_json(path, matrix)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session25.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    midi, capture, catalog, groove, expression, controls = build_session25_chain()
    plans = {
        engine: build_articulation_plan(midi, catalog, groove, expression, config)
        for engine, config in controls.items()
    }
    repeated = {
        engine: build_articulation_plan(midi, catalog, groove, expression, config)
        for engine, config in controls.items()
    }
    artifacts = ROOT / "artifacts"
    paths = {
        "referenceMidi": artifacts / "session25-reference.mid",
        "capture": artifacts / "session25-reference-capture.json",
        "catalog": artifacts / "session25-articulation-map.json",
        "groovePlan": artifacts / "session25-groove-plan.json",
        "expressionPlan": artifacts / "session25-expression-plan.json",
    }
    paths["referenceMidi"].write_bytes(midi.to_bytes())
    for name, value in (("capture", capture), ("catalog", catalog), ("groovePlan", groove),
                        ("expressionPlan", expression)):
        _write_json(paths[name], value)
    for engine, plan in plans.items():
        path = artifacts / f"session25-{engine.lower()}-articulation-plan.json"
        paths[f"{engine.lower()}Plan"] = path
        _write_json(path, plan)
        control_path = artifacts / f"session25-{engine.lower()}-controls.json"
        paths[f"{engine.lower()}Controls"] = control_path
        _write_json(control_path, controls[engine])

    event_counts = {engine: plan["audit"]["generatedEventCount"] for engine, plan in plans.items()}
    standard_types = sorted({event["eventType"] for plan in plans.values() for event in plan["events"]})
    readiness = {
        item["engine"]: articulation_production_readiness(
            catalog, item["engine"],
            (item["exactSound"]["bankMsb"], item["exactSound"]["bankLsb"], item["exactSound"]["program"]),
        )
        for item in catalog["maps"]
    }
    benchmark = {
        "schema": "dna-session25-articulation-benchmark", "version": "1.0",
        "date": date.today().isoformat(), "license": "self-authored-test-fixtures",
        "sourceMidiSha256": midi.digest(), "captureHash": capture["captureHash"],
        "catalogHash": catalog["catalogHash"],
        "mapCount": catalog["audit"]["mapCount"],
        "entryCount": catalog["audit"]["entryCount"],
        "confirmedEntryCount": catalog["audit"]["confirmedEntryCount"],
        "eventCounts": event_counts, "standardEventTypes": standard_types,
        "keyswitchNoteOffCount": sum(plan["audit"]["keyswitchNoteOffCount"] for plan in plans.values()),
        "maximumEstimatedPeak": max(plan["audit"]["estimatedPeak"] for plan in plans.values()),
        "softwareMidiNoteCeiling": 54,
        "deterministic": plans == repeated,
        "previewReady": all(plan["readyForPreview"] for plan in plans.values()),
        "productionRenderReady": any(plan["readyForProductionRender"] for plan in plans.values()),
        "productionEligibleMapCount": catalog["audit"]["productionEligibleMapCount"],
        "deviceReadiness": readiness,
        "passed": all((
            plans == repeated, catalog["audit"]["mapCount"] == 3,
            set(standard_types) == {"KEYSWITCH", "CC", "CHANNEL_PRESSURE"},
            all(plan["readyForPreview"] for plan in plans.values()),
            not any(plan["readyForProductionRender"] for plan in plans.values()),
            catalog["audit"]["productionEligibleMapCount"] == 0,
            all(not item["allowed"] for item in readiness.values()),
            max(plan["audit"]["estimatedPeak"] for plan in plans.values()) <= 54,
        )),
    }
    benchmark["benchmarkHash"] = sha256(_canonical({key: value for key, value in benchmark.items()
                                                     if key != "benchmarkHash"})).hexdigest()
    benchmark_path = ROOT / "data" / "session25-benchmark-report.json"
    _write_json(benchmark_path, benchmark)
    if not benchmark["passed"]:
        raise RuntimeError("Session 25 articulation benchmark failed")

    schema_paths = [
        ROOT / "premium/schemas/v2/articulation-capture-v1.schema.json",
        ROOT / "premium/schemas/v2/articulation-map-v2.schema.json",
        ROOT / "premium/schemas/v2/articulation-plan-v2.schema.json",
    ]
    contracts = []
    for path in schema_paths:
        value = json.loads(path.read_text(encoding="utf-8"))
        contracts.append({"name": path.name, "$id": value["$id"],
                          "contractVersion": value["x-contract-version"],
                          "sha256": sha256(path.read_bytes()).hexdigest()})
    schema_catalog = {
        "schema": "dna-session25-schema-catalog", "version": "1.0",
        "date": date.today().isoformat(), "contracts": contracts,
        "catalogHash": sha256(_canonical(contracts)).hexdigest(),
    }
    schema_catalog_path = ROOT / "data" / "session25-schema-catalog.json"
    _write_json(schema_catalog_path, schema_catalog)
    _update_feature_matrix()

    report = {
        "schema": "dna-session25-test-report", "version": "1.0",
        "date": date.today().isoformat(), "result": "pass",
        "scope": "exact-sound-guitar-rx-dnc-articulation-capture-trust-collision-noteoff-and-polyphony-safety",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures),
                        "errors": len(result.errors)},
        "benchmark": {"report": str(benchmark_path.relative_to(ROOT)),
                      **{key: benchmark[key] for key in (
                          "mapCount", "entryCount", "confirmedEntryCount", "eventCounts",
                          "standardEventTypes", "keyswitchNoteOffCount", "maximumEstimatedPeak",
                          "deterministic", "previewReady", "productionRenderReady",
                          "productionEligibleMapCount", "benchmarkHash")}},
        "artifacts": {name: str(path.relative_to(ROOT)) for name, path in paths.items()}
                     | {"schemaCatalog": str(schema_catalog_path.relative_to(ROOT))},
        "transports": {"cli": "session25_articulation_map.py",
                       "api": "/api/premium-articulation-map",
                       "guiCard": "ARTICULATION MAPS 2.0", "apiGuiParity": True},
        "invariants": {
            "exactSoundBindingOnly": True, "approximateNameMatching": False,
            "nearestProgramFallback": False, "confirmedUnknownBlockedExplicit": True,
            "keyswitchCcPressureOnly": True, "proprietarySysExBlocked": True,
            "keyswitchNoteOffRequired": True, "triggerPlayableCollisionBlocked": True,
            "duplicateTriggerBlocked": True, "grooveExpressionPeakUsed": True,
            "softwareMidiNoteCeiling": 54, "softwareFixtureCannotAuthorizeProduction": True,
            "operatorApprovedDeviceHashRequired": True, "readOnly": True,
            "midiMutationAllowed": False, "finalMidiGenerated": False,
        },
        "status": {
            "session25ArticulationMaps": "SOFTWARE_VALIDATED / DEVICE_CAPTURE_BLOCKED",
            "activeSoftwareBaseline": "4.3-alpha", "aiArrangerAlpha": "SOFTWARE_VALIDATED / ALPHA",
            "productionGuitarMap": "MISSING_DEVICE_CAPTURE",
            "productionRxMap": "MISSING_DEVICE_CAPTURE",
            "productionDncMap": "MISSING_DEVICE_CAPTURE",
            "aiPremiumArranger": "PLANNED", "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data/session25-test-report.json"
    _write_json(report_path, report)

    release_path = ROOT / "data/release-check-report.json"
    if release_path.is_file():
        release = json.loads(release_path.read_text(encoding="utf-8"))
        release.setdefault("premiumReadiness", {}).update({
            "softwareBaseline": "4.3-alpha", "session25": f"{result.testsRun}/{result.testsRun} PASS",
            "articulationMap2": "SOFTWARE_VALIDATED / DEVICE_CAPTURE_BLOCKED",
            "aiArranger": "ALPHA", "premiumProduct": "PLANNED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(release_path, release)
    compliance_path = ROOT / "data/master-prompt-compliance.json"
    if compliance_path.is_file():
        compliance = json.loads(compliance_path.read_text(encoding="utf-8"))
        compliance.setdefault("summary", {}).update({
            "session25ArticulationMaps": f"{result.testsRun}/{result.testsRun} PASS",
            "activeSoftwareBaseline": "4.3-alpha",
            "productionArticulationCapture": "MISSING", "aiArranger": "ALPHA",
            "aiPremiumArranger": "PLANNED", "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(compliance_path, compliance)
    print(f"Session 25 PASS: {result.testsRun}/{result.testsRun}; maps={benchmark['mapCount']}; events={sum(event_counts.values())}; peak={benchmark['maximumEstimatedPeak']}/54; {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
