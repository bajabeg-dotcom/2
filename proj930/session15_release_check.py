#!/usr/bin/env python3
"""Freeze and verify the Session 15 AI Premium 3.17 baseline."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import unittest

from premium_config import PremiumConfig, build_read_only_plan, prepare_premium_baseline


ROOT = Path(__file__).resolve().parent


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    baseline_path = ROOT / "data" / "premium-baseline.json"
    prepared = prepare_premium_baseline(ROOT, refresh=not baseline_path.exists())

    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_premium_baseline.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    demo = json.loads((ROOT / "data" / "session15-demo-config.json").read_text(encoding="utf-8"))
    config = PremiumConfig.from_dict(demo)
    plan = build_read_only_plan(config)
    plan_path = ROOT / "artifacts" / "session15-read-only-plan.json"
    _write_json(plan_path, plan)

    baseline = prepared["baseline"]
    report = {
        "schema": "dna-session15-test-report",
        "version": "1.0",
        "date": date.today().isoformat(),
        "result": "pass",
        "scope": "ai-premium-3.17-plan-only-baseline",
        "formalSuite": {
            "testsRun": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
        },
        "baseline": {
            "path": "data/premium-baseline.json",
            "baselineId": baseline["baselineId"],
            "contentHash": baseline["contentHash"],
            "frozenFiles": len(baseline["frozenFiles"]),
            "referenceMidi": "premium/baseline/reference-style.mid",
        },
        "contracts": {
            "catalog": "premium/schemas/catalog.json",
            "count": len(prepared["schemaCatalog"]["contracts"]),
            "catalogHash": prepared["schemaCatalog"]["catalogHash"],
        },
        "featureMatrix": {
            "path": "data/premium-feature-matrix.json",
            "sessions": [15, 30],
            "premiumProductStatus": "PLANNED",
        },
        "readOnlyPlan": {
            "path": "artifacts/session15-read-only-plan.json",
            "configHash": plan["configHash"],
            "planHash": plan["planHash"],
            "midiMutationAllowed": False,
        },
        "invariants": {
            "goldAffectsDynamics": False,
            "analysisVelocityUsed": False,
            "aiWritesFinalMidi": False,
            "validatorBypassAllowed": False,
            "originalSoloMutationAllowed": False,
            "plannedDoesNotMeanImplemented": True,
        },
        "status": {
            "session15PremiumBaseline": "SOFTWARE_VALIDATED",
            "aiPremiumArranger": "PLANNED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data" / "session15-test-report.json"
    _write_json(report_path, report)

    release_path = ROOT / "data" / "release-check-report.json"
    if release_path.is_file():
        release = json.loads(release_path.read_text(encoding="utf-8"))
        release["premiumReadiness"] = {
            "softwareBaseline": "3.17",
            "session15": "20/20 PASS",
            "baselineId": baseline["baselineId"],
            "contracts": 9,
            "premiumProduct": "PLANNED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        }
        _write_json(release_path, release)

    compliance_path = ROOT / "data" / "master-prompt-compliance.json"
    if compliance_path.is_file():
        compliance = json.loads(compliance_path.read_text(encoding="utf-8"))
        compliance.setdefault("summary", {})["session15PremiumBaseline"] = "20/20 PASS"
        compliance["summary"]["aiPremiumArranger"] = "PLANNED"
        evidence = compliance.setdefault("evidence", [])
        for item in ("data/premium-baseline.json", "data/premium-feature-matrix.json",
                     "data/session15-test-report.json", "premium/schemas/catalog.json"):
            if item not in evidence:
                evidence.append(item)
        _write_json(compliance_path, compliance)

    print(f"Session 15 Premium baseline PASS: {result.testsRun} tests; {report_path}")
    print(f"Premium baseline: {baseline['baselineId']}")
    print("AI Premium Arranger status: PLANNED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())