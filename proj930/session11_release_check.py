#!/usr/bin/env python3
"""Run Session 11 independent verifier tests and emit machine evidence."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import AuthorizedNoteAddition, VerificationPolicy, execute_pipeline, verify_candidate  # noqa: E402
from dna_midi_studio.session7_fixture import build_session7_case  # noqa: E402


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session11.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    midi, *_ = build_session7_case(ROOT)
    source = midi.to_bytes()
    raw = json.loads((ROOT / "data" / "session9-demo-config.json").read_text(encoding="utf-8"))
    pipeline = execute_pipeline(source, raw, ROOT)
    policy = VerificationPolicy((AuthorizedNoteAddition(10, 12, 1800, 5760, 12, 35,
                                                          "confirmed DNC key-switch map"),))
    journal = json.loads((ROOT / "artifacts" / "session10-after_OPT.mid.journal.json").read_text(encoding="utf-8"))
    report = verify_candidate(source, pipeline.midi, pipeline.manifest, policy,
                              rerun=lambda: execute_pipeline(source, raw, ROOT).midi,
                              worker_runs={workers: execute_pipeline(source, raw, ROOT).midi for workers in (1, 2, 4)},
                              journal=journal)
    if not report.passed:
        raise RuntimeError("Independent fixture verification failed: " + "; ".join(report.issues))
    artifact_path = ROOT / "artifacts" / "session11-independent-report.json"
    artifact_path.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    output = {
        "schema": "dna-session11-test-report", "version": "1.0", "date": date.today().isoformat(),
        "result": "pass", "scope": "independent-verifier-and-reproducibility",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures), "errors": len(result.errors)},
        "fixture": {"source": "artifacts/session10-before.mid", "candidate": "artifacts/session10-after_OPT.mid",
                    "pipelineManifest": "artifacts/session9-manifest.json",
                    "atomicJournal": "artifacts/session10-after_OPT.mid.journal.json",
                    "verification": "artifacts/session11-independent-report.json",
                    "sourceHash": report.source_hash, "candidateHash": report.candidate_hash},
        "invariants": {"optimizerVerdictReused": False, "independentByteParser": True,
                       "protectedNoteDiff": True, "protectedEventDiff": True,
                       "authorizedExceptionsOnly": True, "manifestToMidi": True,
                       "atomicJournalVerified": True, "idempotency": report.checks["idempotent"],
                       "workerCountsOneTwoFourEqual": report.checks["workerDeterminism"],
                       "pa800ContractImplemented": True, "invalidCandidateBlocked": True},
        "status": {"session11IndependentVerifier": "SOFTWARE_VALIDATED",
                   "physicalPa800": "WAITING_FOR_DEVICE"},
    }
    report_path = ROOT / "data" / "session11-test-report.json"
    report_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Session 11 verifier PASS: {result.testsRun} tests; {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())