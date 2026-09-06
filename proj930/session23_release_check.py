#!/usr/bin/env python3
"""Run the Session 23 GroovePlan and polyphony safety release gate."""

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
    ROLE_POLICIES,
    analyze_full_duration_polyphony,
    build_arrangement_graph,
    build_candidate_set,
    build_groove_plan,
    build_producer_brief,
    simplify_event_plan,
)
from dna_midi_studio.session19_fixture import build_labeled_benchmark  # noqa: E402
from dna_midi_studio.song_understanding import analyze_song_map  # noqa: E402


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _event(index: int, role: str, tier: str, priority: int, *, request: str,
           start: int = 0, duration: int = 480, channel: int = 12,
           locked: bool = False) -> dict:
    return {
        "eventId": f"stress-{index:03d}", "requestId": request,
        "marker": "f2cv1", "role": role, "channelNumber": channel,
        "onsetTick": start, "durationTick": duration, "enabled": True,
        "priorityTier": tier, "preservePriority": priority,
        "pitchToken": 36 + index, "locked": locked,
    }


def _update_feature_matrix() -> None:
    path = ROOT / "data" / "premium-feature-matrix.json"
    matrix = json.loads(path.read_text(encoding="utf-8"))
    matrix["softwareBaseline"] = "4.1-alpha"
    for feature in matrix["features"]:
        if feature["session"] == 23:
            feature.update({
                "status": "SOFTWARE_VALIDATED",
                "evidence": "data/session23-test-report.json",
                "limitations": [
                    "GroovePlan is an event-level read-only timing plan and does not render final MIDI",
                    "Pa800 oscillator/voice cost remains UNCONFIRMED until physical Session 16 evidence exists",
                ],
            })
    matrix["premiumProductStatus"] = "PLANNED"
    _write_json(path, matrix)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session23.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    case = build_labeled_benchmark()[0]
    song_map = analyze_song_map(case.midi, "session23-reference.mid")
    brief = build_producer_brief(
        "Napravi zivlji pop-folk Style sa gitarom i podlogom, "
        "suptilnim prijelazima i punim refrenom."
    )
    graph = build_arrangement_graph(song_map, brief, 2122, 2)
    candidate_set = build_candidate_set(graph, song_map, ROOT, seed=2222, variant_count=3)
    groove_plan = build_groove_plan(candidate_set, graph, song_map, ROOT, seed=2300)
    repeated = build_groove_plan(candidate_set, graph, song_map, ROOT, seed=2300)

    artifacts = ROOT / "artifacts"
    source_paths = {
        "songMap": artifacts / "session23-song-map.json",
        "arrangementGraph": artifacts / "session23-arrangement-graph.json",
        "candidateSet": artifacts / "session23-candidate-set.json",
        "groovePlan": artifacts / "session23-groove-plan.json",
    }
    for name, value in (("songMap", song_map), ("arrangementGraph", graph),
                        ("candidateSet", candidate_set), ("groovePlan", groove_plan)):
        _write_json(source_paths[name], value)

    decorative_case = [_event(i, "drums", "CORE", 100, request="f2cv1:drums", channel=10)
                       for i in range(40)] + [
        _event(100 + i, "percussion", "DECORATIVE", 20,
               request="f2cv1:percussion", channel=11) for i in range(20)
    ]
    support_case = [_event(i, "drums", "CORE", 100, request="f2cv1:drums", channel=10)
                    for i in range(50)] + [
        _event(100 + i, "guitar", "SUPPORT", 75, request="f2cv1:guitar", channel=12)
        for i in range(10)
    ]
    core_case = [_event(i, "drums", "CORE", 100, request="f2cv1:drums", channel=10)
                 for i in range(60)]
    sustain_events = [
        _event(1, "pad", "DECORATIVE", 30, request="f2cv1:pad", start=0, duration=120),
        _event(2, "pad", "DECORATIVE", 30, request="f2cv1:pad", start=300, duration=60),
    ]
    sustain_windows = [{"marker": "f2cv1", "channelNumber": 12,
                        "startTick": 0, "endTick": 480}]
    decorative_result = simplify_event_plan(decorative_case)
    support_result = simplify_event_plan(support_case)
    core_result = simplify_event_plan(core_case)
    sustain_result = analyze_full_duration_polyphony(sustain_events, sustain_windows)
    stress = {
        "schema": "dna-session23-polyphony-stress", "version": "1.0",
        "date": date.today().isoformat(),
        "cases": [
            {"id": "dense-fill-decorative-first", "beforePeak": decorative_result["before"]["peak"],
             "afterPeak": decorative_result["after"]["peak"],
             "blocked": decorative_result["blocked"],
             "operations": decorative_result["operations"]},
            {"id": "support-thinning", "beforePeak": support_result["before"]["peak"],
             "afterPeak": support_result["after"]["peak"],
             "blocked": support_result["blocked"],
             "operations": support_result["operations"]},
            {"id": "core-overflow-manual-review", "beforePeak": core_result["before"]["peak"],
             "afterPeak": core_result["after"]["peak"], "blocked": core_result["blocked"],
             "operations": core_result["operations"]},
            {"id": "sustain-window", "peak": sustain_result["peak"],
             "longestDurationTick": sustain_result["longestDurationTick"],
             "sustainWindowCount": sustain_result["sustainWindowCount"]},
        ],
    }
    stress["stressHash"] = sha256(_canonical(stress["cases"])).hexdigest()
    stress_path = ROOT / "artifacts" / "session23-polyphony-stress.json"
    _write_json(stress_path, stress)

    template_count = groove_plan["audit"]["templateCount"]
    event_count = groove_plan["audit"]["eventCount"]
    fragment_count = groove_plan["audit"]["fragmentCount"]
    variant_peaks = [item["polyphonyAfter"]["globalPeak"] for item in groove_plan["variants"]]
    offset_count = sum(event["timingOffsetTick"] != 0 for variant in groove_plan["variants"]
                       for fragment in variant["fragments"] for event in fragment["events"])
    gate_count = sum(event["gateDeltaTick"] != 0 for variant in groove_plan["variants"]
                     for fragment in variant["fragments"] for event in fragment["events"])
    stress_passed = (
        decorative_result["after"]["peak"] <= 54
        and decorative_result["operations"][0]["operation"] == "DROP_DECORATIVE_LAYER"
        and support_result["after"]["peak"] == 54
        and all(item["operation"] == "THIN_SUPPORT_VOICE"
                for item in support_result["operations"])
        and core_result["blocked"] and not core_result["operations"]
        and sustain_result["peak"] == 2
    )
    benchmark = {
        "schema": "dna-session23-groove-benchmark", "version": "1.0",
        "date": date.today().isoformat(), "license": "self-authored-test-fixtures",
        "sourceCandidateSetHash": candidate_set["candidateSetHash"],
        "groovePlanHash": groove_plan["groovePlanHash"],
        "deterministic": groove_plan["groovePlanHash"] == repeated["groovePlanHash"],
        "variantCount": len(groove_plan["variants"]), "templateCount": template_count,
        "fragmentCount": fragment_count, "eventCount": event_count,
        "microtimingAdjustedEventCount": offset_count,
        "gateAdjustedEventCount": gate_count, "variantPeaks": variant_peaks,
        "maximumPeak": max(variant_peaks), "softwareMidiNoteCeiling": 54,
        "allProductionVariantsSafe": all(item <= 54 for item in variant_peaks),
        "goldTimingOnly": groove_plan["audit"]["goldTimingOnly"],
        "lockedFragmentsPreserved": groove_plan["audit"]["lockedFragmentsPreserved"],
        "deviceVoiceCostStatus": groove_plan["deviceVoiceCost"]["status"],
        "stressSuitePassed": stress_passed,
        "passed": all((groove_plan["readyForRenderPlanning"], stress_passed,
                       groove_plan["audit"]["allVariantsWithinMidiNoteCeiling"],
                       groove_plan["audit"]["goldTimingOnly"],
                       groove_plan["audit"]["lockedFragmentsPreserved"]))
                  and groove_plan["deviceVoiceCost"]["status"] == "UNCONFIRMED",
    }
    benchmark["benchmarkHash"] = sha256(_canonical({key: value for key, value in benchmark.items()
                                                     if key != "benchmarkHash"})).hexdigest()
    benchmark_path = ROOT / "data" / "session23-benchmark-report.json"
    _write_json(benchmark_path, benchmark)
    if not benchmark["passed"]:
        raise RuntimeError("Session 23 groove/polyphony benchmark failed")

    schema_file = ROOT / "premium" / "schemas" / "v2" / "groove-plan-v2.schema.json"
    schema_value = json.loads(schema_file.read_text(encoding="utf-8"))
    schema_catalog = {
        "schema": "dna-session23-schema-catalog", "version": "1.0",
        "date": date.today().isoformat(),
        "contracts": [{"name": schema_file.name, "$id": schema_value["$id"],
                       "contractVersion": schema_value["x-contract-version"],
                       "sha256": sha256(schema_file.read_bytes()).hexdigest()}],
    }
    schema_catalog["catalogHash"] = sha256(_canonical(schema_catalog["contracts"])).hexdigest()
    schema_path = ROOT / "data" / "session23-schema-catalog.json"
    _write_json(schema_path, schema_catalog)
    _update_feature_matrix()

    report = {
        "schema": "dna-session23-test-report", "version": "1.0",
        "date": date.today().isoformat(), "result": "pass",
        "scope": "groove-humanization-full-duration-polyphony-and-device-voice-cost-boundary",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures),
                        "errors": len(result.errors)},
        "benchmark": {"report": str(benchmark_path.relative_to(ROOT)),
                      **{key: benchmark[key] for key in (
                          "variantCount", "templateCount", "fragmentCount", "eventCount",
                          "microtimingAdjustedEventCount", "gateAdjustedEventCount",
                          "variantPeaks", "maximumPeak", "softwareMidiNoteCeiling",
                          "allProductionVariantsSafe", "stressSuitePassed", "benchmarkHash")}},
        "artifacts": {name: str(path.relative_to(ROOT)) for name, path in source_paths.items()}
                     | {"polyphonyStress": str(stress_path.relative_to(ROOT)),
                        "schemaCatalog": str(schema_path.relative_to(ROOT))},
        "transports": {"cli": "session23_groove_plan.py",
                       "api": "/api/premium-groove-plan",
                       "guiCard": "GROOVE & POLYPHONY 2.0", "apiGuiParity": True},
        "invariants": {
            "goldTimingGateOnly": True, "goldAffectsDynamics": False,
            "factoryDynamicsUnchanged": True, "soundBindingUnchanged": True,
            "originalSoloUnchanged": True, "lockedFragmentsUnchanged": True,
            "roleSpecificMicrotiming": True, "fullDurationPolyphony": True,
            "sustainAwareStress": True, "softwareMidiNoteCeiling": 54,
            "decorativeLayersSimplifiedBeforeCore": True,
            "coreOverflowRequiresManualReview": True,
            "deviceVoiceCostRequiresCertifiedProfile": True,
            "readOnly": True, "midiMutationAllowed": False, "finalMidiGenerated": False,
        },
        "status": {"session23GroovePolyphony": "SOFTWARE_VALIDATED",
                   "activeSoftwareBaseline": "4.1-alpha",
                   "aiArrangerAlpha": "SOFTWARE_VALIDATED / ALPHA",
                   "deviceVoiceCost": "UNCONFIRMED / SESSION16_DEVICE_BLOCKED",
                   "aiPremiumArranger": "PLANNED", "physicalPa800": "WAITING_FOR_DEVICE"},
    }
    report_path = ROOT / "data" / "session23-test-report.json"
    _write_json(report_path, report)

    release_path = ROOT / "data" / "release-check-report.json"
    if release_path.is_file():
        release = json.loads(release_path.read_text(encoding="utf-8"))
        release.setdefault("premiumReadiness", {}).update({
            "softwareBaseline": "4.1-alpha", "session23": f"{result.testsRun}/{result.testsRun} PASS",
            "groovePlan2": "SOFTWARE_VALIDATED", "deviceVoiceCost": "UNCONFIRMED",
            "aiArranger": "ALPHA", "premiumProduct": "PLANNED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(release_path, release)
    compliance_path = ROOT / "data" / "master-prompt-compliance.json"
    if compliance_path.is_file():
        compliance = json.loads(compliance_path.read_text(encoding="utf-8"))
        compliance.setdefault("summary", {}).update({
            "session23GroovePolyphony": f"{result.testsRun}/{result.testsRun} PASS",
            "activeSoftwareBaseline": "4.1-alpha", "deviceVoiceCost": "UNCONFIRMED",
            "aiArranger": "ALPHA", "aiPremiumArranger": "PLANNED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(compliance_path, compliance)
    print(
        f"Session 23 PASS: {result.testsRun}/{result.testsRun}; "
        f"events={event_count}; peak={max(variant_peaks)}/54; {report_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())