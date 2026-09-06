#!/usr/bin/env python3
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"src"))
from dna_midi_studio.session34_fixture import build_session34_chain


def _write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")


def main():
    result=unittest.TextTestRunner(verbosity=0).run(unittest.defaultTestLoader.discover(str(ROOT/"tests"),pattern="test_session34.py"))
    if not result.wasSuccessful() or result.testsRun!=168: return 1
    c=build_session34_chain(ROOT); plan=c["coherencePlan"]
    _write(ROOT/"artifacts/session34-coherence-plan.json",plan)
    _write(ROOT/"artifacts/session34-coherence-verification.json",c["coherenceVerification"])
    for key in "ABC": (ROOT/f"artifacts/session34-variant-{key.lower()}.mid").write_bytes(c["coherentVariants"][key])
    benchmark={"schema":"dna-session34-coherence-benchmark","version":"1.0","date":"2026-09-03",
        "variantMidiSha256":{x["variantId"]:x["metrics"]["midiSha256"] for x in plan["variants"]},
        "operationCounts":{x["variantId"]:len(x["operations"]) for x in plan["variants"]},
        "noteCounts":{x["variantId"]:x["metrics"]["noteCount"] for x in plan["variants"]},
        "peaks":{x["variantId"]:x["metrics"]["globalPeakConcurrentMidiNotes"] for x in plan["variants"]},"passed":True}
    _write(ROOT/"data/session34-benchmark-report.json",benchmark)
    report={"schema":"dna-session34-test-report","version":"1.0","date":"2026-09-03","result":"pass",
        "formalSuite":{"testsRun":168,"failures":0,"errors":0},"benchmark":benchmark,
        "status":{"session34GlobalCoherence":"SOFTWARE_VALIDATED / COHERENCE PREVIEW","physicalPa800":"WAITING_FOR_DEVICE"}}
    _write(ROOT/"data/session34-test-report.json",report)
    print("Session 34 PASS: 168/168")
    return 0

if __name__=="__main__": raise SystemExit(main())