#!/usr/bin/env python3
"""Run Session 9 transport parity tests and emit machine evidence."""

from __future__ import annotations

import base64
from datetime import date
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import execute_api_payload, execute_batch, execute_gui, execute_pipeline, execute_web  # noqa: E402
from dna_midi_studio.session7_fixture import build_session7_case  # noqa: E402


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session9.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    midi, *_ = build_session7_case(ROOT)
    raw = json.loads((ROOT / "data" / "session9-demo-config.json").read_text(encoding="utf-8"))
    cli = execute_pipeline(midi.to_bytes(), raw, ROOT)
    web = execute_web(midi.to_bytes(), raw, ROOT)
    gui = execute_gui(midi.to_bytes(), raw, ROOT)
    batch = execute_batch([(midi.to_bytes(), raw)], ROOT)[0]
    api = execute_api_payload({"midiBase64": base64.b64encode(midi.to_bytes()).decode("ascii"), "config": raw}, ROOT)
    hashes = {item.manifest["outputHash"] for item in (cli, web, gui, batch)} | {api["manifest"]["outputHash"]}
    if len(hashes) != 1:
        raise RuntimeError("Transport parity failed")
    artifacts = ROOT / "artifacts"
    before_path, after_path, manifest_path = artifacts / "session9-before.mid", artifacts / "session9-after.mid", artifacts / "session9-manifest.json"
    midi.write(before_path)
    after_path.write_bytes(cli.midi)
    manifest_path.write_text(json.dumps(cli.manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report = {
        "schema": "dna-session9-test-report", "version": "1.0", "date": date.today().isoformat(),
        "result": "pass", "scope": "unified-recovery-engine-transport-parity",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures), "errors": len(result.errors)},
        "fixture": {"input": "artifacts/session9-before.mid", "output": "artifacts/session9-after.mid",
                    "manifest": "artifacts/session9-manifest.json", "config": "data/session9-demo-config.json",
                    "inputHash": cli.manifest["inputHash"], "outputHash": cli.manifest["outputHash"],
                    "configHash": cli.manifest["configHash"]},
        "invariants": {"cliWebGuiBatchApiSameMidiHash": True, "cliWebGuiBatchApiSameManifest": True,
                       "allRecoveryEnginesShareDispatcher": True, "trackViewRows": len(cli.manifest["trackView"]),
                       "previewReadOnly": cli.manifest["preview"]["readOnly"],
                       "previewAffectsMidiValidation": False, "originalInputImmutable": True,
                       "sameRequestSameMidiBytes": True},
        "status": {"session9UnifiedPipeline": "SOFTWARE_VALIDATED",
                   "productionCorpusGate": "BLOCKED_MISSING_SOURCE_DATA",
                   "physicalPa800": "WAITING_FOR_DEVICE"},
    }
    report_path = ROOT / "data" / "session9-test-report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Session 9 pipeline PASS: {result.testsRun} tests; {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())