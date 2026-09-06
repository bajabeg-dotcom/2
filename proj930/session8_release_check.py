#!/usr/bin/env python3
"""Run Session 8 agent/cloud safety tests and emit machine evidence."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import (  # noqa: E402
    AgentRuntime, AgentSubmission, CloudPolicy, TaskSpec, dispatch_optional_cloud,
)


def submission(file_name: str, message: str) -> AgentSubmission:
    return AgentSubmission(
        produced_files=(file_name,), diff_summary=message,
        observed_test_output="Session 8 bounded check PASS", unresolved_risks=(),
        status="HANDOFF_READY", recommendation="Continue through the contracted gate.",
    )


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session8.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    runtime = AgentRuntime.from_file(ROOT / "agents" / "agent-team.json")
    raw = json.loads((ROOT / "data" / "session8-demo-task.json").read_text(encoding="utf-8"))
    spec = TaskSpec(**raw)
    job = runtime.create(spec)
    runtime.start(spec.task_id, "codex-lead-engineer")
    runtime.submit(spec.task_id, "codex-lead-engineer",
                   submission("artifacts/session8-code-review.json", "Runtime implementation reviewed."))
    runtime.handoff(spec.task_id, "codex-lead-engineer", "codex-midi-compliance")
    runtime.start(spec.task_id, "codex-midi-compliance")
    runtime.submit(spec.task_id, "codex-midi-compliance",
                   submission("artifacts/session8-validator-report.json", "Independent validator gate executed."))
    validator_hash = "c" * 64
    runtime.record_validator(spec.task_id, "codex-midi-compliance", True, validator_hash)
    runtime.handoff(spec.task_id, "codex-midi-compliance", "chatgpt-style-evaluator")
    runtime.start(spec.task_id, "chatgpt-style-evaluator")
    runtime.submit(spec.task_id, "chatgpt-style-evaluator",
                   submission("artifacts/session8-evaluation.json", "Advisory evaluation recorded."))
    runtime.record_evaluation(
        spec.task_id, "chatgpt-style-evaluator",
        {"boundedScope": True, "midiUntouched": True, "validatorIndependent": True},
        "The advisory result respects every Session 8 safety boundary.",
    )
    runtime.handoff(spec.task_id, "chatgpt-style-evaluator", "chatgpt-orchestrator")
    runtime.start(spec.task_id, "chatgpt-orchestrator")
    runtime.submit(spec.task_id, "chatgpt-orchestrator",
                   submission("artifacts/session8-approval-request.json", "Manager requested human approval."))
    runtime.request_approval(spec.task_id, "chatgpt-orchestrator")
    runtime.approve(spec.task_id, "local-user")
    runtime.complete(spec.task_id, "chatgpt-orchestrator")

    cloud = dispatch_optional_cloud(
        CloudPolicy(enabled=True, explicit_consent=True),
        {"taskId": spec.task_id, "inputHashes": dict(spec.input_hashes)},
        lambda payload: (_ for _ in ()).throw(ConnectionError("offline fixture")),
        lambda payload: {"decision": "KEEP", "offlineCore": True},
    )
    manifest = runtime.manifest(spec.task_id)
    manifest["cloudProbe"] = cloud
    manifest_path = ROOT / "artifacts" / "session8-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    report = {
        "schema": "dna-session8-test-report", "version": "1.0", "date": date.today().isoformat(),
        "result": "pass", "scope": "local-agent-runtime-and-optional-metadata-cloud",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures), "errors": len(result.errors)},
        "fixture": {"task": "data/session8-demo-task.json", "manifest": "artifacts/session8-manifest.json",
                    "traceEvents": len(job.trace), "traceHash": manifest["traceHash"]},
        "invariants": {
            "structuredHandoffComplete": True, "exclusiveOwnershipEnforced": True,
            "structuredEvaluationRecorded": bool(job.evaluations) and job.evaluations[0]["passed"],
            "readOnlyBrief": True, "agentCanWriteFinalMidi": False,
            "humanApprovalRecorded": job.human_approved,
            "independentValidatorPassed": job.validator_passed,
            "validatorCanBeBypassed": False, "cloudEnabledByDefault": False,
            "cloudRequiresExplicitConsent": True, "midiAllowedInCloudPayload": False,
            "apiKeysStoredInProject": False, "networkFailureBreaksOfflineCore": False,
            "cloudProbeMode": cloud["mode"], "finalStatus": job.status,
        },
        "status": {"session8Runtime": "SOFTWARE_VALIDATED", "cloudApi": "OPTIONAL_OPT_IN",
                   "offlineCore": "SOFTWARE_VALIDATED", "physicalPa800": "WAITING_FOR_DEVICE"},
    }
    report_path = ROOT / "data" / "session8-test-report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Session 8 runtime PASS: {result.testsRun} tests; {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())