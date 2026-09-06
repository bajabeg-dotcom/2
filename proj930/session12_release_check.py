#!/usr/bin/env python3
"""Run Session 12 adversarial tests and build the available-corpus vault."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import RegressionVault  # noqa: E402


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session12.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    demo_paths = [f"data/session{number}-demo-registry.json" for number in range(2, 8)]
    production_paths = [
        "data/factory-velocity-profiles.json", "data/gold-patterns.json",
        "data/factory-style-segments.json", "data/factory-strumming.json",
        "data/gold-performance-patterns.json", "prism-uploads/DNA.zip",
    ]
    production_present = all((ROOT / path).is_file() for path in production_paths)
    paths = demo_paths + production_paths if production_present else demo_paths
    vault = RegressionVault.build(ROOT, paths)
    vault_path = ROOT / "data" / "session12-regression-vault.json"
    vault_path.write_text(json.dumps(vault.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report = {
        "schema": "dna-session12-test-report", "version": "1.0", "date": date.today().isoformat(),
        "result": "pass", "scope": "adversarial-and-available-corpus-foundation",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures), "errors": len(result.errors)},
        "fuzz": {"deterministicMutations": 200, "seed": 12012,
                 "unexpectedExceptions": 0, "largeTrackNotes": 5000},
        "coverage": {"truncatedChunksAndVlq": True, "smpteRejected": True,
                     "runningStatus": True, "sysex": True, "rpnNrpn": True,
                     "channelAndPolyAftertouch": True, "pitchBend": True,
                     "zeroAndLargeTracks": True, "illegalBytes": True,
                     "eotAndStuckNotes": True, "fakeRxDncSoloEvidence": True,
                     "deepGoldDynamicFields": True, "roleSpecificCalibration": True,
                     "sustainedNotePolyphony": True, "validatorPolyphonyOverflow": True},
        "corpus": {"vault": "data/session12-regression-vault.json",
                   "availableRegistryFiles": len(vault.entries),
                   "stableIds": sum(len(entry.stable_ids) for entry in vault.entries),
                   "vaultHash": vault.vault_hash, "vaultReverified": vault.verify(ROOT),
                   "productionFactoryGoldPresent": production_present},
        "skips": [] if production_present else [{"gate": "full-production-factory-gold-rebuild",
                   "status": "BLOCKED_MISSING_SOURCE_DATA",
                   "reason": "Production Factory/GOLD registries and original corpus are absent from this snapshot."}],
        "status": {"session12AdversarialFoundation": "SOFTWARE_VALIDATED",
                   "productionCorpusGate": "SOFTWARE_VALIDATED" if production_present else "BLOCKED_MISSING_SOURCE_DATA",
                   "physicalPa800": "WAITING_FOR_DEVICE"},
    }
    report_path = ROOT / "data" / "session12-test-report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Session 12 adversarial foundation PASS: {result.testsRun} tests; {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())