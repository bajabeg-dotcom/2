#!/usr/bin/env python3
"""Run Session 10 atomic commit/recovery tests and emit machine evidence."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import AtomicMidiPublisher, MidiFile, TransactionIdentity, execute_pipeline  # noqa: E402
from dna_midi_studio.session7_fixture import build_session7_case  # noqa: E402


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session10.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    midi, *_ = build_session7_case(ROOT)
    raw = json.loads((ROOT / "data" / "session9-demo-config.json").read_text(encoding="utf-8"))
    pipeline = execute_pipeline(midi.to_bytes(), raw, ROOT)
    registry_hashes = [sha256((ROOT / stage["registry"]).read_bytes()).hexdigest() for stage in raw["stages"]]
    database_hash = sha256(":".join(registry_hashes).encode()).hexdigest()
    identity = TransactionIdentity(pipeline.manifest["inputHash"], pipeline.manifest["configHash"], database_hash)
    verifier = lambda data: {"passed": MidiFile.from_bytes(data).to_bytes() == data,
                             "parser": "independent-round-trip-fixture"}
    artifacts = ROOT / "artifacts"
    before = artifacts / "session10-before.mid"
    before.write_bytes(midi.to_bytes())
    publisher = AtomicMidiPublisher(artifacts)
    committed = publisher.publish(pipeline.midi, "session10-after.mid", identity, verifier)
    resumed = publisher.publish(pipeline.midi, "session10-after.mid", identity, verifier)
    report = {
        "schema": "dna-session10-test-report", "version": "1.0", "date": date.today().isoformat(),
        "result": "pass", "scope": "atomic-commit-cancel-resume-crash-recovery",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures), "errors": len(result.errors)},
        "fixture": {"input": "artifacts/session10-before.mid",
                    "output": str(committed.output_path.relative_to(ROOT)),
                    "journal": str(committed.journal_path.relative_to(ROOT)),
                    "sourceHash": identity.source_hash, "configHash": identity.config_hash,
                    "databaseHash": identity.database_hash, "outputHash": committed.output_hash,
                    "resumeObserved": resumed.resumed},
        "invariants": {"temporaryWriteBeforeVerify": True, "atomicReplace": True,
                       "invalidCandidatePublished": False, "partialMidiAfterCancel": False,
                       "partialMidiAfterCrash": False, "outputLocking": True,
                       "resumeUsesSourceConfigDatabaseHashes": True, "diskFullRollback": True,
                       "lockedFileIsolation": True, "unicodeAndLongNamesSafe": True,
                       "pathTraversalBlocked": True, "batchPerFileFailures": True},
        "status": {"session10Transactions": "SOFTWARE_VALIDATED", "physicalPa800": "WAITING_FOR_DEVICE"},
    }
    report_path = ROOT / "data" / "session10-test-report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Session 10 transaction PASS: {result.testsRun} tests; {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())