#!/usr/bin/env python3
"""Run Session 20 AI Producer Brief 2.0 release gate."""

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
    BriefAiPolicy,
    approve_producer_brief,
    build_producer_brief,
    execute_producer_brief_api,
    execute_producer_brief_gui,
)
from dna_midi_studio.session20_fixture import CASES, corpus_hash, intent_value  # noqa: E402


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _update_feature_matrix() -> None:
    path = ROOT / "data" / "premium-feature-matrix.json"
    matrix = json.loads(path.read_text(encoding="utf-8"))
    matrix["softwareBaseline"] = "3.21"
    for feature in matrix["features"]:
        if feature["session"] == 20:
            feature.update({
                "status": "SOFTWARE_VALIDATED",
                "evidence": "data/session20-test-report.json",
                "limitations": [
                    "optional AI enrichment is adapter-only and disabled without explicit consent",
                    "ProducerBrief is read-only and cannot authorize MIDI generation or device mappings",
                ],
            })
    matrix["premiumProductStatus"] = "PLANNED"
    _write_json(path, matrix)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session20.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    cases = []
    expected_fields = correct_fields = conflict_hits = 0
    for case in CASES:
        brief = build_producer_brief(case.text)
        field_results = []
        for key, expected in case.expected.items():
            actual = intent_value(brief, key)
            passed = actual == expected
            expected_fields += 1
            correct_fields += passed
            field_results.append({"field": key, "expected": expected, "actual": actual,
                                  "passed": passed})
        conflict_passed = bool(brief["conflicts"]) == case.conflict
        conflict_hits += conflict_passed
        cases.append({
            "caseId": case.case_id, "text": case.text,
            "expected": case.expected, "expectedConflict": case.conflict,
            "fieldResults": field_results, "conflictPassed": conflict_passed,
            "briefHash": brief["briefHash"], "language": brief["language"],
        })
    field_accuracy = correct_fields / expected_fields
    conflict_accuracy = conflict_hits / len(CASES)
    corpus = {
        "schema": "dna-session20-intent-corpus", "version": "1.0",
        "date": date.today().isoformat(), "license": "self-authored-test-fixtures",
        "immutableCorpusHash": corpus_hash(), "caseCount": len(CASES), "cases": cases,
    }
    corpus_path = ROOT / "data" / "session20-intent-corpus.json"
    _write_json(corpus_path, corpus)
    benchmark = {
        "schema": "dna-session20-intent-benchmark", "version": "1.0",
        "date": date.today().isoformat(), "corpusHash": corpus_hash(),
        "caseCount": len(CASES), "expectedFieldCount": expected_fields,
        "fieldAccuracy": round(field_accuracy, 6), "fieldGate": 0.95,
        "conflictAccuracy": round(conflict_accuracy, 6), "conflictGate": 0.95,
        "passed": field_accuracy >= 0.95 and conflict_accuracy >= 0.95,
    }
    benchmark_path = ROOT / "data" / "session20-benchmark-report.json"
    _write_json(benchmark_path, benchmark)
    if not benchmark["passed"]:
        raise RuntimeError("Session 20 bilingual intent benchmark failed")

    reference = build_producer_brief(
        "Napravi življi pop-folk Style, sa suzdržanom strofom i punim refrenom, "
        "sa gitarom i bez dodatnog sola."
    )
    reference_path = ROOT / "artifacts" / "session20-producer-brief.json"
    _write_json(reference_path, reference)
    conflict = build_producer_brief("Use drums but make it without drums.")
    approved = approve_producer_brief(conflict, "local-user", {"role-drums": "require:drums"})
    approval_path = ROOT / "artifacts" / "session20-approved-conflict-brief.json"
    _write_json(approval_path, approved)
    fallback = build_producer_brief(
        "Make a rock style with guitar.", BriefAiPolicy(True, True),
        lambda _: (_ for _ in ()).throw(ConnectionError()),
    )
    fallback_path = ROOT / "artifacts" / "session20-offline-fallback-brief.json"
    _write_json(fallback_path, fallback)
    parity = execute_producer_brief_api({"text": reference["sourceText"]}) == execute_producer_brief_gui(
        {"text": reference["sourceText"]}
    )

    schema_file = ROOT / "premium" / "schemas" / "v2" / "producer-brief-v2.schema.json"
    schema_value = json.loads(schema_file.read_text(encoding="utf-8"))
    schema_catalog = {
        "schema": "dna-session20-schema-catalog", "version": "1.0",
        "date": date.today().isoformat(),
        "contracts": [{"name": schema_file.name, "$id": schema_value["$id"],
                       "contractVersion": schema_value["x-contract-version"],
                       "sha256": sha256(schema_file.read_bytes()).hexdigest()}],
    }
    schema_catalog["catalogHash"] = sha256(_canonical(schema_catalog["contracts"])).hexdigest()
    schema_path = ROOT / "data" / "session20-schema-catalog.json"
    _write_json(schema_path, schema_catalog)
    _update_feature_matrix()

    report = {
        "schema": "dna-session20-test-report", "version": "1.0",
        "date": date.today().isoformat(), "result": "pass",
        "scope": "bilingual-ai-producer-brief-2.0-and-safe-optional-enrichment",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures),
                        "errors": len(result.errors)},
        "benchmark": {"corpus": str(corpus_path.relative_to(ROOT)),
                      "report": str(benchmark_path.relative_to(ROOT)),
                      "corpusHash": corpus_hash(), "caseCount": len(CASES),
                      "fieldAccuracy": benchmark["fieldAccuracy"],
                      "conflictAccuracy": benchmark["conflictAccuracy"]},
        "artifacts": {"referenceBrief": str(reference_path.relative_to(ROOT)),
                      "approvedConflictBrief": str(approval_path.relative_to(ROOT)),
                      "offlineFallbackBrief": str(fallback_path.relative_to(ROOT)),
                      "schemaCatalog": str(schema_path.relative_to(ROOT))},
        "transports": {"cli": "session20_producer_brief.py",
                       "localApi": "/api/premium-producer-brief",
                       "guiCard": "AI je razumio", "apiGuiParity": parity},
        "invariants": {
            "readOnly": True, "midiBytesAccepted": False, "midiWriterAvailable": False,
            "pathWriteAllowed": False, "bankProgramAuthority": False,
            "validatorBypassAllowed": False, "goldAffectsDynamics": False,
            "originalSoloMutationAllowed": False, "cloudEnabledByDefault": False,
            "cloudRequiresExplicitConsent": True, "cloudMetadataOnly": True,
            "invalidCloudResponseFallsBackLocally": True,
            "conflictsRequireExplicitUserResolution": True,
            "offlineCoreEquivalent": True,
        },
        "status": {"session20AiProducerBrief": "SOFTWARE_VALIDATED",
                   "session16Pa800MappingLab": "DEVICE_BLOCKED",
                   "session21ArrangementGraph": "PLANNED",
                   "aiPremiumArranger": "PLANNED",
                   "physicalPa800": "WAITING_FOR_DEVICE"},
    }
    report_path = ROOT / "data" / "session20-test-report.json"
    _write_json(report_path, report)

    release_path = ROOT / "data" / "release-check-report.json"
    if release_path.is_file():
        release = json.loads(release_path.read_text(encoding="utf-8"))
        release.setdefault("premiumReadiness", {}).update({
            "softwareBaseline": "3.21", "session20": f"{result.testsRun}/{result.testsRun} PASS",
            "producerBrief2": "SOFTWARE_VALIDATED", "premiumProduct": "PLANNED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(release_path, release)
    compliance_path = ROOT / "data" / "master-prompt-compliance.json"
    if compliance_path.is_file():
        compliance = json.loads(compliance_path.read_text(encoding="utf-8"))
        compliance.setdefault("summary", {}).update({
            "session20AiProducerBrief": f"{result.testsRun}/{result.testsRun} PASS",
            "activeSoftwareBaseline": "3.21", "aiPremiumArranger": "PLANNED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(compliance_path, compliance)
    print(
        f"Session 20 PASS: {result.testsRun}/{result.testsRun}; "
        f"intent accuracy={field_accuracy:.3f}; conflict accuracy={conflict_accuracy:.3f}; {report_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())