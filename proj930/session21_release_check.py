#!/usr/bin/env python3
"""Run Session 21 ArrangementGraph 2.0 release gate and benchmark."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import build_arrangement_graph, build_producer_brief  # noqa: E402
from dna_midi_studio.session19_fixture import build_labeled_benchmark  # noqa: E402
from dna_midi_studio.song_understanding import analyze_song_map  # noqa: E402


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _update_feature_matrix() -> None:
    path = ROOT / "data" / "premium-feature-matrix.json"
    matrix = json.loads(path.read_text(encoding="utf-8"))
    matrix["softwareBaseline"] = "3.22"
    for feature in matrix["features"]:
        if feature["session"] == 21:
            feature.update({
                "status": "SOFTWARE_VALIDATED",
                "evidence": "data/session21-test-report.json",
                "limitations": [
                    "graph is read-only and does not select Factory or GOLD runtime patterns",
                    "device voice cost remains an unconfirmed software estimate until physical Pa800 testing",
                ],
            })
    matrix["premiumProductStatus"] = "PLANNED"
    _write_json(path, matrix)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session21.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    intents = (
        "Make a balanced pop style with guitar, subtle transitions and a full chorus.",
        "Napravi življi pop-folk Style sa gitarom i podlogom, sa punim refrenom.",
        "Create a sparse acoustic style with bass and subtle transitions.",
        "Napravi puni dance Style sa bubnjevima, basom i dramaticnim prijelazima.",
    )
    cases = []
    total_nodes = total_edges = total_variants = 0
    controlled_rise = transition_targets = deterministic = lock_safe = 0
    benchmark_cases = build_labeled_benchmark()
    for index, case in enumerate(benchmark_cases):
        song_map = analyze_song_map(case.midi, case.case_id + ".mid")
        text = intents[index % len(intents)]
        if index % 5 == 0:
            text += " Lock v2cv1."
        brief = build_producer_brief(text)
        graph = build_arrangement_graph(song_map, brief, seed=2100 + index, variant_count=2)
        repeated = build_arrangement_graph(song_map, brief, seed=2100 + index, variant_count=2)
        by_marker = {node["marker"]: node for node in graph["nodes"]}
        energies = [by_marker[f"v{number}cv1"]["targetEnergy"] for number in range(1, 5)]
        rise = energies == sorted(energies)
        targets = by_marker["f1cv1"]["transitionTarget"] == "v2cv1" and \
                  by_marker["f2cv1"]["transitionTarget"] == "v4cv1"
        locked_markers = {node["marker"] for node in graph["nodes"] if node["locked"]}
        locks_preserved = all(
            next(target for target in variant["elementTargets"] if target["marker"] == marker)["targetEnergy"]
            == by_marker[marker]["targetEnergy"]
            for marker in locked_markers for variant in graph["planVariants"]
        )
        controlled_rise += rise
        transition_targets += targets
        deterministic += graph["graphHash"] == repeated["graphHash"]
        lock_safe += locks_preserved
        total_nodes += len(graph["nodes"])
        total_edges += len(graph["edges"])
        total_variants += len(graph["planVariants"])
        cases.append({
            "caseId": case.case_id, "songMapHash": song_map["mapHash"],
            "briefHash": brief["briefHash"], "graphHash": graph["graphHash"],
            "readyForCandidateSearch": graph["readyForCandidateSearch"],
            "variationEnergy": energies, "controlledRise": rise,
            "fillTargetsDeclared": targets, "lockedMarkers": sorted(locked_markers),
            "lockedTargetsPreserved": locks_preserved,
        })
    count = len(cases)
    rates = {
        "controlledRiseRate": round(controlled_rise / count, 6),
        "transitionTargetRate": round(transition_targets / count, 6),
        "deterministicRate": round(deterministic / count, 6),
        "lockPreservationRate": round(lock_safe / count, 6),
    }
    passed = all(value == 1.0 for value in rates.values())
    corpus_hash = sha256(_canonical(cases)).hexdigest()
    benchmark = {
        "schema": "dna-session21-global-plan-benchmark", "version": "1.0",
        "date": date.today().isoformat(), "license": "self-authored-test-fixtures",
        "corpusHash": corpus_hash, "songCount": count,
        "nodeCount": total_nodes, "edgeCount": total_edges,
        "planVariantCount": total_variants, **rates, "passed": passed,
        "cases": cases,
    }
    benchmark_path = ROOT / "data" / "session21-benchmark-report.json"
    _write_json(benchmark_path, benchmark)
    if not passed:
        raise RuntimeError("Session 21 global plan benchmark failed")

    reference_map = analyze_song_map(benchmark_cases[0].midi, "session21-reference.mid")
    reference_brief = build_producer_brief(
        "Napravi življi pop-folk Style sa gitarom, suptilnim prijelazima i punim refrenom."
    )
    reference_graph = build_arrangement_graph(reference_map, reference_brief, 2100, 2)
    reference_path = ROOT / "artifacts" / "session21-arrangement-graph.json"
    _write_json(reference_path, reference_graph)
    locked_brief = build_producer_brief(
        "Make a full pop style with dramatic transitions. Lock v2cv1 and f1cv1."
    )
    locked_graph = build_arrangement_graph(reference_map, locked_brief, 2121, 4)
    locked_path = ROOT / "artifacts" / "session21-locked-four-plan-graph.json"
    _write_json(locked_path, locked_graph)

    schema_file = ROOT / "premium" / "schemas" / "v2" / "arrangement-graph-v2.schema.json"
    schema_value = json.loads(schema_file.read_text(encoding="utf-8"))
    schema_catalog = {
        "schema": "dna-session21-schema-catalog", "version": "1.0",
        "date": date.today().isoformat(),
        "contracts": [{"name": schema_file.name, "$id": schema_value["$id"],
                       "contractVersion": schema_value["x-contract-version"],
                       "sha256": sha256(schema_file.read_bytes()).hexdigest()}],
    }
    schema_catalog["catalogHash"] = sha256(_canonical(schema_catalog["contracts"])).hexdigest()
    schema_path = ROOT / "data" / "session21-schema-catalog.json"
    _write_json(schema_path, schema_catalog)
    _update_feature_matrix()

    report = {
        "schema": "dna-session21-test-report", "version": "1.0",
        "date": date.today().isoformat(), "result": "pass",
        "scope": "global-read-only-arrangement-graph-before-candidate-search",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures),
                        "errors": len(result.errors)},
        "benchmark": {"report": str(benchmark_path.relative_to(ROOT)),
                      "corpusHash": corpus_hash, "songCount": count,
                      "nodeCount": total_nodes, "edgeCount": total_edges,
                      "planVariantCount": total_variants, **rates},
        "artifacts": {"referenceGraph": str(reference_path.relative_to(ROOT)),
                      "referenceGraphHash": reference_graph["graphHash"],
                      "lockedFourPlanGraph": str(locked_path.relative_to(ROOT)),
                      "schemaCatalog": str(schema_path.relative_to(ROOT))},
        "transports": {"cli": "session21_arrangement_graph.py",
                       "songMapApi": "/api/premium-song-map",
                       "graphApi": "/api/premium-arrangement-graph",
                       "guiCard": "ARRANGEMENT GRAPH 2.0", "apiGuiParity": True},
        "invariants": {
            "readOnly": True, "midiMutationAllowed": False,
            "candidatePatternSelectionAllowed": False,
            "allPa800ElementsPlanned": True, "fillTransitionTargetsRequired": True,
            "variationEnergyIsNondecreasing": True, "lockedElementsImmutable": True,
            "fullDurationPolyphonyRequired": True, "maximumConcurrentMidiNotes": 54,
            "deviceVoiceCostConfirmed": False, "lowConfidenceRequiresManualReview": True,
            "factoryDynamicsAuthority": True, "goldAffectsDynamics": False,
            "originalSoloMutationAllowed": False,
        },
        "status": {"session21ArrangementGraph": "SOFTWARE_VALIDATED",
                   "session16Pa800MappingLab": "DEVICE_BLOCKED",
                   "session22CandidateVariationEngine": "PLANNED",
                   "aiPremiumArranger": "PLANNED",
                   "physicalPa800": "WAITING_FOR_DEVICE"},
    }
    report_path = ROOT / "data" / "session21-test-report.json"
    _write_json(report_path, report)

    release_path = ROOT / "data" / "release-check-report.json"
    if release_path.is_file():
        release = json.loads(release_path.read_text(encoding="utf-8"))
        release.setdefault("premiumReadiness", {}).update({
            "softwareBaseline": "3.22", "session21": f"{result.testsRun}/{result.testsRun} PASS",
            "arrangementGraph2": "SOFTWARE_VALIDATED", "premiumProduct": "PLANNED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(release_path, release)
    compliance_path = ROOT / "data" / "master-prompt-compliance.json"
    if compliance_path.is_file():
        compliance = json.loads(compliance_path.read_text(encoding="utf-8"))
        compliance.setdefault("summary", {}).update({
            "session21ArrangementGraph": f"{result.testsRun}/{result.testsRun} PASS",
            "activeSoftwareBaseline": "3.22", "aiPremiumArranger": "PLANNED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(compliance_path, compliance)
    print(
        f"Session 21 PASS: {result.testsRun}/{result.testsRun}; "
        f"global plan benchmark={count}/{count}; {report_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())