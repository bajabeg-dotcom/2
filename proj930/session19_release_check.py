#!/usr/bin/env python3
"""Run Session 19 Song Understanding 2.0 and its locked benchmark."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import sys
import time
import unittest


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import analyze_song_map, boundary_f1, weighted_f1  # noqa: E402
from dna_midi_studio.session19_fixture import (  # noqa: E402
    build_labeled_benchmark,
    build_variable_meter_case,
)


SCHEMAS = ("song-map-v2.schema.json", "song-map-corrections-v1.schema.json")


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _update_feature_matrix() -> None:
    path = ROOT / "data" / "premium-feature-matrix.json"
    matrix = json.loads(path.read_text(encoding="utf-8"))
    matrix["softwareBaseline"] = "3.20"
    for feature in matrix["features"]:
        if feature["session"] == 19:
            feature.update({
                "status": "FOUNDATION_VALIDATED / PRODUCTION_CALIBRATION_PENDING",
                "evidence": "data/session19-test-report.json",
                "limitations": [
                    "quality thresholds are proven on a locked self-authored labeled MIDI corpus",
                    "broader human-labeled production calibration and listening review remain required",
                ],
            })
    matrix["premiumProductStatus"] = "PLANNED"
    _write_json(path, matrix)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session19.py")
    started = time.perf_counter()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    suite_seconds = time.perf_counter() - started
    if not result.wasSuccessful():
        return 1

    artifact_dir = ROOT / "artifacts" / "session19-benchmark"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    cases = build_labeled_benchmark()
    labels = []
    chord_scores = []
    boundary_scores = []
    for case in cases:
        midi_path = artifact_dir / f"{case.case_id}.mid"
        midi_path.write_bytes(case.midi)
        song_map = analyze_song_map(case.midi, midi_path.name)
        predicted_chords = [
            f"{item['root']}:{item['quality']}:{item['bass']}"
            for item in song_map["chordCells"]
        ]
        predicted_boundaries = [item["startTick"] for item in song_map["sections"]]
        chord_score = weighted_f1(case.chord_labels, predicted_chords)
        section_score = boundary_f1(case.section_boundaries, predicted_boundaries)
        chord_scores.append(chord_score)
        boundary_scores.append(section_score)
        labels.append({
            "caseId": case.case_id,
            "midi": str(midi_path.relative_to(ROOT)),
            "sha256": case.sha256,
            "expectedChordLabels": list(case.chord_labels),
            "expectedSectionBoundaries": list(case.section_boundaries),
            "expectedSectionLabels": list(case.section_labels),
            "predictedChordLabels": predicted_chords,
            "predictedSectionBoundaries": predicted_boundaries,
            "chordWeightedF1": round(chord_score, 6),
            "sectionBoundaryF1": round(section_score, 6),
            "songMapHash": song_map["mapHash"],
        })

    corpus_hash = sha256(_canonical([
        {"caseId": item["caseId"], "sha256": item["sha256"],
         "expectedChordLabels": item["expectedChordLabels"],
         "expectedSectionBoundaries": item["expectedSectionBoundaries"]}
        for item in labels
    ])).hexdigest()
    benchmark = {
        "schema": "dna-session19-labeled-benchmark",
        "version": "1.0",
        "date": date.today().isoformat(),
        "license": "self-authored-test-fixtures",
        "immutableCorpusHash": corpus_hash,
        "songCount": len(labels),
        "cases": labels,
    }
    benchmark_path = ROOT / "data" / "session19-labeled-benchmark.json"
    _write_json(benchmark_path, benchmark)

    chord_mean = sum(chord_scores) / len(chord_scores)
    boundary_mean = sum(boundary_scores) / len(boundary_scores)
    benchmark_report = {
        "schema": "dna-session19-benchmark-report",
        "version": "1.0",
        "date": date.today().isoformat(),
        "corpusHash": corpus_hash,
        "songCount": len(cases),
        "halfBarCells": sum(len(case.chord_labels) for case in cases),
        "chordWeightedF1": round(chord_mean, 6),
        "chordGate": 0.85,
        "sectionBoundaryF1": round(boundary_mean, 6),
        "sectionGate": 0.80,
        "passed": chord_mean >= 0.85 and boundary_mean >= 0.80,
    }
    benchmark_report_path = ROOT / "data" / "session19-benchmark-report.json"
    _write_json(benchmark_report_path, benchmark_report)
    if not benchmark_report["passed"]:
        raise RuntimeError("Session 19 labeled benchmark did not reach its quality gates")

    reference_map = analyze_song_map(cases[0].midi, "song19-01.mid")
    reference_path = ROOT / "artifacts" / "session19-song-map.json"
    _write_json(reference_path, reference_map)
    variable_map = analyze_song_map(build_variable_meter_case(), "session19-variable-meter.mid")
    variable_path = ROOT / "artifacts" / "session19-variable-meter-song-map.json"
    _write_json(variable_path, variable_map)

    schema_entries = []
    for name in SCHEMAS:
        path = ROOT / "premium" / "schemas" / "v2" / name
        value = json.loads(path.read_text(encoding="utf-8"))
        schema_entries.append({
            "name": name, "$id": value["$id"],
            "contractVersion": value["x-contract-version"],
            "sha256": sha256(path.read_bytes()).hexdigest(),
        })
    schema_catalog = {
        "schema": "dna-session19-schema-catalog", "version": "1.0",
        "date": date.today().isoformat(), "contracts": schema_entries,
        "catalogHash": sha256(_canonical(schema_entries)).hexdigest(),
    }
    schema_path = ROOT / "data" / "session19-schema-catalog.json"
    _write_json(schema_path, schema_catalog)
    _update_feature_matrix()

    report = {
        "schema": "dna-session19-test-report",
        "version": "1.0",
        "date": date.today().isoformat(),
        "result": "pass",
        "scope": "song-understanding-2.0-read-only-analysis-and-correction-overlay",
        "formalSuite": {
            "testsRun": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "durationSeconds": round(suite_seconds, 3),
        },
        "benchmark": {
            "labels": str(benchmark_path.relative_to(ROOT)),
            "report": str(benchmark_report_path.relative_to(ROOT)),
            "corpusHash": corpus_hash,
            "songCount": len(cases),
            "halfBarCells": benchmark_report["halfBarCells"],
            "chordWeightedF1": benchmark_report["chordWeightedF1"],
            "sectionBoundaryF1": benchmark_report["sectionBoundaryF1"],
        },
        "artifacts": {
            "referenceSongMap": str(reference_path.relative_to(ROOT)),
            "referenceMapHash": reference_map["mapHash"],
            "variableMeterSongMap": str(variable_path.relative_to(ROOT)),
            "schemaCatalog": str(schema_path.relative_to(ROOT)),
        },
        "invariants": {
            "analysisVelocityUsed": False,
            "sourceMidiMutated": False,
            "halfBarHarmony": True,
            "variableTempoAndMeter": True,
            "trackRolesAreTimeScoped": True,
            "lowConfidenceRequiresManualReview": True,
            "correctionsAreReadOnlyOverlay": True,
            "sameInputProducesSameMapHash": True,
            "goldAffectsDynamics": False,
            "aiWritesFinalMidi": False,
        },
        "status": {
            "session19SongUnderstanding": "FOUNDATION_VALIDATED / PRODUCTION_CALIBRATION_PENDING",
            "session16Pa800MappingLab": "DEVICE_BLOCKED",
            "session20AiProducerBrief": "PLANNED",
            "aiPremiumArranger": "PLANNED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data" / "session19-test-report.json"
    _write_json(report_path, report)

    release_path = ROOT / "data" / "release-check-report.json"
    if release_path.is_file():
        release = json.loads(release_path.read_text(encoding="utf-8"))
        release.setdefault("premiumReadiness", {}).update({
            "softwareBaseline": "3.20",
            "session19": f"{result.testsRun}/{result.testsRun} PASS",
            "songUnderstanding2": "FOUNDATION_VALIDATED / PRODUCTION_CALIBRATION_PENDING",
            "premiumProduct": "PLANNED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(release_path, release)

    compliance_path = ROOT / "data" / "master-prompt-compliance.json"
    if compliance_path.is_file():
        compliance = json.loads(compliance_path.read_text(encoding="utf-8"))
        compliance.setdefault("summary", {}).update({
            "session19SongUnderstanding": f"{result.testsRun}/{result.testsRun} PASS",
            "activeSoftwareBaseline": "3.20",
            "aiPremiumArranger": "PLANNED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(compliance_path, compliance)

    print(
        f"Session 19 PASS: {result.testsRun}/{result.testsRun}; "
        f"chord weighted-F1={chord_mean:.3f}; section boundary F1={boundary_mean:.3f}; {report_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())