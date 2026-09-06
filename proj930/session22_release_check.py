#!/usr/bin/env python3
"""Run Session 22 production Candidate Search and variation release gate."""

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
    build_arrangement_graph,
    build_candidate_set,
    build_producer_brief,
)
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
    matrix["softwareBaseline"] = "4.0-alpha"
    for feature in matrix["features"]:
        if feature["session"] == 22:
            feature.update({
                "status": "SOFTWARE_VALIDATED",
                "evidence": "data/session22-test-report.json",
                "limitations": [
                    "CandidateSet 2.0 selects pattern identities but does not render final MIDI",
                    "physical Pa800 voice cost and articulation maps remain device-blocked",
                ],
            })
    matrix["premiumProductStatus"] = "PLANNED"
    _write_json(path, matrix)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session22.py")
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
    readiness = deterministic = diverse = audited = factory_guitar = gold_safe = lock_safe = 0
    eligible = blocked_expected = blocked_correct = 0
    total_requests = total_selections = total_rejections = total_relationships = 0
    for index, case in enumerate(build_labeled_benchmark()):
        song_map = analyze_song_map(case.midi, case.case_id + ".mid")
        text = intents[index % len(intents)]
        if index % 5 == 0:
            text += " Lock v2cv1."
        brief = build_producer_brief(text)
        graph = build_arrangement_graph(song_map, brief, seed=2100 + index, variant_count=2)
        if not graph["readyForCandidateSearch"]:
            blocked_expected += 1
            try:
                build_candidate_set(
                    graph, song_map, ROOT, "plan-01", seed=2200 + index, variant_count=3
                )
            except ValueError:
                blocked_correct += 1
            cases.append({
                "caseId": case.case_id, "graphHash": graph["graphHash"],
                "candidateSetHash": None, "ready": False,
                "expectedSafetyBlock": True, "safetyBlockPassed": blocked_correct == blocked_expected,
                "manualReviewCodes": [item["code"] for item in graph["manualReview"]],
            })
            continue
        eligible += 1
        candidate_set = build_candidate_set(
            graph, song_map, ROOT, "plan-01", seed=2200 + index, variant_count=3
        )
        repeated = build_candidate_set(
            graph, song_map, ROOT, "plan-01", seed=2200 + index, variant_count=3
        )
        is_diverse = all(item["diversityDistanceFromA"] >= 0.5
                         for item in candidate_set["variants"][1:])
        guitar_safe = all(
            candidate["sourceKind"] == "FACTORY_STRUMMING"
            for request in candidate_set["requests"] if request["role"] == "guitar"
            for candidate in request["rankedCandidates"]
        )
        safety = candidate_set["safety"]
        is_gold_safe = not any((safety["goldDynamicsAuthority"],
                                safety["goldBankProgramAuthority"], safety["goldGuitarAuthority"]))
        locked_markers = {node["marker"] for node in graph["nodes"] if node["locked"]}
        locks_preserved = all(
            selection["patternId"] is None and selection["locked"]
            for variant in candidate_set["variants"] for selection in variant["selections"]
            if selection["marker"] in locked_markers
        )
        readiness += candidate_set["readyForVariantRendering"]
        deterministic += candidate_set["candidateSetHash"] == repeated["candidateSetHash"]
        diverse += is_diverse
        audited += candidate_set["audit"]["allDetailedRejectionsAudited"]
        factory_guitar += guitar_safe
        gold_safe += is_gold_safe
        lock_safe += locks_preserved
        total_requests += len(candidate_set["requests"])
        total_selections += sum(len(item["selections"]) for item in candidate_set["variants"])
        total_rejections += candidate_set["audit"]["hardRejectedCount"]
        relationships = sum(
            selection["relationshipId"] is not None
            for variant in candidate_set["variants"] for selection in variant["selections"]
        )
        total_relationships += relationships
        cases.append({
            "caseId": case.case_id, "graphHash": graph["graphHash"],
            "candidateSetHash": candidate_set["candidateSetHash"],
            "ready": candidate_set["readyForVariantRendering"],
            "requestCount": len(candidate_set["requests"]),
            "variantHashes": [item["variantHash"] for item in candidate_set["variants"]],
            "diversityDistances": [item["diversityDistanceFromA"]
                                   for item in candidate_set["variants"]],
            "hardRejectedCount": candidate_set["audit"]["hardRejectedCount"],
            "relationshipSelections": relationships,
            "lockedMarkers": sorted(locked_markers),
            "lockedSelectionsPreserved": locks_preserved,
            "factoryOnlyGuitar": guitar_safe, "goldAuthoritySafe": is_gold_safe,
        })
    count = len(cases)
    rates = {
        "eligibleReadyRate": round(readiness / max(1, eligible), 6),
        "deterministicRate": round(deterministic / max(1, eligible), 6),
        "diversityRate": round(diverse / max(1, eligible), 6),
        "rejectionAuditRate": round(audited / max(1, eligible), 6),
        "factoryOnlyGuitarRate": round(factory_guitar / max(1, eligible), 6),
        "goldAuthoritySafetyRate": round(gold_safe / max(1, eligible), 6),
        "lockPreservationRate": round(lock_safe / max(1, eligible), 6),
        "manualReviewSafetyBlockRate": round(blocked_correct / max(1, blocked_expected), 6),
    }
    passed = eligible > 0 and blocked_expected > 0 and all(value == 1.0 for value in rates.values()) and total_relationships > 0
    corpus_hash = sha256(_canonical(cases)).hexdigest()
    benchmark = {
        "schema": "dna-session22-candidate-benchmark", "version": "1.0",
        "date": date.today().isoformat(), "license": "self-authored-test-fixtures",
        "corpusHash": corpus_hash, "songCount": count,
        "eligibleSongCount": eligible, "manualReviewSongCount": blocked_expected,
        "requestCount": total_requests, "selectionCount": total_selections,
        "hardRejectedCount": total_rejections,
        "relationshipSelectionCount": total_relationships,
        **rates, "passed": passed, "cases": cases,
    }
    benchmark_path = ROOT / "data" / "session22-benchmark-report.json"
    _write_json(benchmark_path, benchmark)
    if not passed:
        raise RuntimeError("Session 22 candidate benchmark failed")

    reference_case = build_labeled_benchmark()[0]
    reference_map = analyze_song_map(reference_case.midi, "session22-reference.mid")
    reference_brief = build_producer_brief(
        "Napravi življi pop-folk Style sa gitarom i podlogom, suptilnim prijelazima i punim refrenom."
    )
    reference_graph = build_arrangement_graph(reference_map, reference_brief, 2122, 2)
    reference_set = build_candidate_set(reference_graph, reference_map, ROOT, seed=2222, variant_count=3)
    reference_path = ROOT / "artifacts" / "session22-candidate-set.json"
    _write_json(reference_path, reference_set)
    partial = build_candidate_set(
        reference_graph, reference_map, ROOT, seed=2222, variant_count=3,
        controls={"version": "1.0", "regenerateMarkers": ["v3cv1"],
                  "nextCandidateOffsets": [{"requestId": "v3cv1:drums", "offset": 1}]},
        previous_candidate_set=reference_set,
    )
    partial_path = ROOT / "artifacts" / "session22-partial-regeneration.json"
    _write_json(partial_path, partial)

    schema_file = ROOT / "premium" / "schemas" / "v2" / "candidate-set-v2.schema.json"
    schema_value = json.loads(schema_file.read_text(encoding="utf-8"))
    schema_catalog = {
        "schema": "dna-session22-schema-catalog", "version": "1.0",
        "date": date.today().isoformat(),
        "contracts": [{"name": schema_file.name, "$id": schema_value["$id"],
                       "contractVersion": schema_value["x-contract-version"],
                       "sha256": sha256(schema_file.read_bytes()).hexdigest()}],
    }
    schema_catalog["catalogHash"] = sha256(_canonical(schema_catalog["contracts"])).hexdigest()
    schema_path = ROOT / "data" / "session22-schema-catalog.json"
    _write_json(schema_path, schema_catalog)
    _update_feature_matrix()

    report = {
        "schema": "dna-session22-test-report", "version": "1.0",
        "date": date.today().isoformat(), "result": "pass",
        "scope": "production-candidate-search-and-read-only-abc-variation-engine",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures),
                        "errors": len(result.errors)},
        "benchmark": {"report": str(benchmark_path.relative_to(ROOT)),
                      "corpusHash": corpus_hash, "songCount": count,
                      "eligibleSongCount": eligible, "manualReviewSongCount": blocked_expected,
                      "requestCount": total_requests, "selectionCount": total_selections,
                      "hardRejectedCount": total_rejections,
                      "relationshipSelectionCount": total_relationships, **rates},
        "artifacts": {"referenceCandidateSet": str(reference_path.relative_to(ROOT)),
                      "referenceCandidateSetHash": reference_set["candidateSetHash"],
                      "partialRegeneration": str(partial_path.relative_to(ROOT)),
                      "schemaCatalog": str(schema_path.relative_to(ROOT))},
        "transports": {"cli": "session22_candidate_search.py",
                       "api": "/api/premium-candidate-search",
                       "guiCard": "PREMIUM CANDIDATE SEARCH 2.0", "apiGuiParity": True},
        "invariants": {
            "productionPatternCount": 15837, "criteriaPerCandidate": 14,
            "hardConstraintsBeforeScoring": True, "allDetailedRejectionsAudited": True,
            "relationshipAwareDrumBass": True, "factoryOnlyGuitar": True,
            "stableAbcVariants": True, "lockedSelectionsImmutable": True,
            "partialRegenerationPreservesOtherFragments": True,
            "readOnly": True, "midiMutationAllowed": False, "finalMidiGenerated": False,
            "factoryDynamicsAuthority": True, "goldAffectsDynamics": False,
            "goldBankProgramAuthority": False, "originalSoloMutationAllowed": False,
        },
        "status": {"session22CandidateVariationEngine": "SOFTWARE_VALIDATED",
                   "aiArrangerAlpha": "SOFTWARE_VALIDATED / ALPHA",
                   "session16Pa800MappingLab": "DEVICE_BLOCKED",
                   "aiPremiumArranger": "PLANNED",
                   "physicalPa800": "WAITING_FOR_DEVICE"},
    }
    report_path = ROOT / "data" / "session22-test-report.json"
    _write_json(report_path, report)

    release_path = ROOT / "data" / "release-check-report.json"
    if release_path.is_file():
        release = json.loads(release_path.read_text(encoding="utf-8"))
        release.setdefault("premiumReadiness", {}).update({
            "softwareBaseline": "4.0-alpha", "session22": f"{result.testsRun}/{result.testsRun} PASS",
            "candidateSet2": "SOFTWARE_VALIDATED", "aiArranger": "ALPHA",
            "premiumProduct": "PLANNED", "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(release_path, release)
    compliance_path = ROOT / "data" / "master-prompt-compliance.json"
    if compliance_path.is_file():
        compliance = json.loads(compliance_path.read_text(encoding="utf-8"))
        compliance.setdefault("summary", {}).update({
            "session22CandidateVariationEngine": f"{result.testsRun}/{result.testsRun} PASS",
            "activeSoftwareBaseline": "4.0-alpha", "aiArranger": "ALPHA",
            "aiPremiumArranger": "PLANNED", "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(compliance_path, compliance)
    print(
        f"Session 22 PASS: {result.testsRun}/{result.testsRun}; "
        f"candidate benchmark={count}/{count}; {report_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())