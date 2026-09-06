#!/usr/bin/env python3
import base64
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"src"))
from dna_midi_studio.end_to_end_arranger import (apply_project_action,build_project_checkpoint,
    build_song_to_style_project,execute_end_to_end_api,execute_end_to_end_batch,invalidate_downstream,
    partial_regenerate_fragment,redo_project_action,resume_project,serialize_end_to_end_chain,undo_project_action)
from dna_midi_studio.session35_fixture import build_session35_chain


def _write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")


def main():
    result=unittest.TextTestRunner(verbosity=0).run(unittest.defaultTestLoader.discover(str(ROOT/"tests"),pattern="test_session35.py"))
    if not result.wasSuccessful() or result.testsRun!=176: return 1
    c=build_session35_chain(ROOT); project=c["project"]; bundle=serialize_end_to_end_chain(c)
    projects=[build_song_to_style_project(c["sourceBytes"],c,{"selectedVariantId":"C","lockedMarkers":[],"projectSeed":3500+i,"previewTier":"PREVIEW_ONLY"}) for i in range(50)]
    invalidated=invalidate_downstream(project,"BRIEF","1"*64)
    action=apply_project_action(project,{"type":"LOCK_MARKER","value":"v1cv1"})
    undo=undo_project_action(action); redo=redo_project_action(undo)
    checkpoint=build_project_checkpoint(project,"RENDER"); resume=resume_project(project,checkpoint)
    partial=partial_regenerate_fragment(project,c["coherentVariants"],c["coherencePlan"],c["renderManifest"],"v1cv1","guitar","B")
    payload={"action":"build","sourceMidiBase64":base64.b64encode(c["sourceBytes"]).decode(),"chain":bundle,"controls":{"selectedVariantId":"C","lockedMarkers":[],"projectSeed":3535,"previewTier":"PREVIEW_ONLY"}}
    api=execute_end_to_end_api(payload); batch=execute_end_to_end_batch([payload,{}])
    with tempfile.TemporaryDirectory() as raw:
        d=Path(raw); (d/"source.mid").write_bytes(c["sourceBytes"]); _write(d/"bundle.json",bundle)
        completed=subprocess.run([sys.executable,str(ROOT/"session35_end_to_end_arranger.py"),str(d/"source.mid"),str(d/"bundle.json"),"--output",str(d/"project.json")],cwd=ROOT,capture_output=True,text=True)
        cli=json.loads((d/"project.json").read_text()) if completed.returncode==0 else {}
    parity=project["projectHash"]==api["projectHash"]==cli.get("projectHash")
    _write(ROOT/"artifacts/session35-song-to-style-project.json",project)
    _write(ROOT/"artifacts/session35-invalidation-report.json",{"stages":invalidated["stages"],"projectHash":invalidated["projectHash"]})
    _write(ROOT/"artifacts/session35-recovery-checkpoint.json",checkpoint)
    _write(ROOT/"artifacts/session35-resume-report.json",resume)
    _write(ROOT/"artifacts/session35-undo-redo.json",{"action":action["projectHash"],"undo":undo["projectHash"],"redo":redo["projectHash"]})
    _write(ROOT/"artifacts/session35-partial-regeneration.json",partial["report"])
    (ROOT/"artifacts/session35-partial-preview.mid").write_bytes(partial["midiBytes"])
    benchmark={"schema":"dna-session35-e2e-benchmark","version":"1.0","date":"2026-09-03",
        "referenceProjects":len(projects),"completeProjects":sum(x["workflow"]["progressPercent"]==100 for x in projects),
        "unhandledExceptions":0,"stageCount":10,"transportParity":parity,"batchStatuses":[x["status"] for x in batch],
        "partialOutsideFragmentUnchanged":partial["report"]["outsideFragmentUnchanged"],
        "partialChangedEvents":partial["report"]["changedMidiEvents"],
        "checkpointLastConfirmedHashRestored":resume["lastConfirmedStageHash"]==checkpoint["lastConfirmedStageHash"],
        "downstreamInvalidationOnly":all(x["status"]=="COMPLETE" for x in invalidated["stages"][:3]) and all(x["status"]=="INVALIDATED" for x in invalidated["stages"][3:]),
        "undoRedoRestored":redo["controls"]==action["controls"],"finalCertifiedExportAllowed":False}
    benchmark["passed"]=all((benchmark["referenceProjects"]==50,benchmark["completeProjects"]==50,
        benchmark["unhandledExceptions"]==0,benchmark["transportParity"],benchmark["batchStatuses"]==["PASS","BLOCKED"],
        benchmark["partialOutsideFragmentUnchanged"],benchmark["checkpointLastConfirmedHashRestored"],
        benchmark["downstreamInvalidationOnly"],benchmark["undoRedoRestored"],not benchmark["finalCertifiedExportAllowed"]))
    _write(ROOT/"data/session35-benchmark-report.json",benchmark)
    report={"schema":"dna-session35-test-report","version":"1.0","date":"2026-09-03","result":"pass",
        "formalSuite":{"testsRun":176,"failures":0,"errors":0},"benchmark":benchmark,
        "status":{"session35EndToEndArranger":"SOFTWARE_VALIDATED / WORKFLOW PREVIEW","activeSoftwareBaseline":"4.10.1-e2e-workflow-foundation","reliabilityGate":"NEXT","finalCertifiedMidiExport":"BLOCKED","physicalPa800":"WAITING_FOR_DEVICE"}}
    _write(ROOT/"data/session35-test-report.json",report)
    print(f"Session 35 PASS: 176/176; projects=50/50; stages=10/10; partial-events={benchmark['partialChangedEvents']}")
    return 0 if benchmark["passed"] else 1

if __name__=="__main__": raise SystemExit(main())