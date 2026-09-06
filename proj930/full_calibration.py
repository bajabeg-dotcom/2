#!/usr/bin/env python3
"""Canonical full-corpus calibration runner.

The runner inventories the authoritative ZIP archives first, then asks the
truth/evidence gate for permission.  A BLOCKED gate produces a BLOCKED report
and performs zero MIDI mutations.  If (and only if) the gate later becomes
PASS, every archive member is processed; no ``[:37]`` sample, empty-file skip,
proxy role, or fallback is allowed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

from truthful_evidence_gate import EvidenceGateBlocked, TruthEvidenceGate, sha256_bytes


VERSION = "15.00-TRUTHFUL-FULL"
FACTORY_ARCHIVE = Path("prism-uploads") / "Split Factory Styles.zip"
GOLD_ARCHIVE = Path("prism-uploads") / "Gold DNA.zip"
PROFILE_PATH = Path("data") / "factory-velocity-profiles.json"


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _members(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        return sorted(
            name for name in archive.namelist()
            if not name.endswith("/") and Path(name).suffix.lower() in {".mid", ".midi"}
        )


def _source_inventory(root: Path) -> dict[str, Any]:
    inventory: dict[str, Any] = {"archives": {}, "total_inputs": 0}
    for label, relative in (("factory", FACTORY_ARCHIVE), ("gold", GOLD_ARCHIVE)):
        path = root / relative
        if not path.is_file():
            inventory["archives"][label] = {"path": str(relative), "exists": False, "members": 0, "sha256": None}
            continue
        names = _members(path)
        inventory["archives"][label] = {
            "path": str(relative),
            "exists": True,
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "members": len(names),
            "empty_member_count": 0,
            "members_sha256": sha256_bytes(_canonical(names)),
        }
        inventory["total_inputs"] += len(names)
    return inventory


def _blocked_report(root: Path, gate: dict[str, Any], inventory: dict[str, Any], output: Path) -> dict[str, Any]:
    report = {
        "schema": "dna-full-calibration-report",
        "version": VERSION,
        "status": "BLOCKED",
        "classification": "SOFTWARE_ONLY",
        "root": str(root),
        "source_inventory": inventory,
        "gate": gate,
        "execution": {
            "authorized": False,
            "executed": False,
            "mutated_inputs": False,
            "exported_outputs": False,
            "processed_inputs": 0,
            "failed_inputs": 0,
            "empty_inputs": 0,
            "results": [],
        },
        "acceptance": {
            "full_source_denominator": inventory.get("total_inputs", 0),
            "every_input_counted": True,
            "proxy_as_direct": False,
            "fallback_or_bypass": False,
            "pass_claim_allowed": False,
        },
        "blocking_reasons": gate.get("blocking_reasons", []),
        "legacy_outputs_not_authoritative": [
            "calibration/final_certified_full_corpus_13.00_full_no_bypass.json",
            "reports/FINAL_CERTIFICATION_13.00_FULL_NO_BYPASS_RIJESI_SVE_FINAL.md",
        ],
    }
    report["report_hash"] = sha256_bytes(_canonical(report))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def _run_authorized(root: Path, gate: dict[str, Any], inventory: dict[str, Any], output: Path,
                    output_dir: Path | None = None) -> dict[str, Any]:
    """Transform every source member after a PASS gate.

    This branch is unreachable in the current checkout.  It is kept explicit
    so a future run cannot accidentally revert to a partial corpus: all ZIP
    members are included in the denominator and all exceptions become FAIL.
    """
    import midi_optimizer

    profiles_path = root / PROFILE_PATH
    profiles_doc = json.loads(profiles_path.read_text(encoding="utf-8"))
    profiles = profiles_doc.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        raise RuntimeError("Factory profiles are missing; authorized branch must fail closed")

    results: list[dict[str, Any]] = []
    for kind, relative in (("factory", FACTORY_ARCHIVE), ("gold", GOLD_ARCHIVE)):
        archive_path = root / relative
        with zipfile.ZipFile(archive_path) as archive:
            names = [name for name in archive.namelist()
                     if not name.endswith("/") and Path(name).suffix.lower() in {".mid", ".midi"}]
            for name in sorted(names):
                source_id = f"{kind}:{name}"
                try:
                    data = archive.read(name)
                    if not data:
                        raise ValueError("EMPTY_INPUT")
                    optimized, transform_report = midi_optimizer.optimize_midi(
                        data,
                        profiles,
                        options={
                            "cleanupNotes": True,
                            "removeRedundantControllers": True,
                            "quantizeDivision": 16,
                            "quantizeStrength": 85,
                            "factoryDynamics": True,
                            "velocityStrength": 65,
                            "factoryMixer": True,
                            "mixerStrength": 65,
                            "insertMissingMixer": True,
                            "repairKeyRange": True,
                            "fxAuto": True,
                            "fxStrength": 60,
                            "autoDelay": True,
                            "autoThird": True,
                            "maxPerformance": True,
                            "performanceGestures": True,
                            "databaseVersion": VERSION,
                            "seed": 9302026,
                        },
                        source=source_id,
                        evidence={"gate": gate},
                    )
                    output_hash = hashlib.sha256(optimized).hexdigest()
                    if output_dir:
                        destination = output_dir / kind / Path(name)
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        destination.write_bytes(optimized)
                    results.append({
                        "source_id": source_id,
                        "input_sha256": hashlib.sha256(data).hexdigest(),
                        "output_sha256": output_hash,
                        "status": "PASS" if transform_report.get("validation", {}).get("passed") else "FAIL",
                        "validation": transform_report.get("validation", {}),
                    })
                except Exception as exc:  # every member remains in the denominator
                    results.append({"source_id": source_id, "status": "FAIL", "error": str(exc)})

    passed = sum(item.get("status") == "PASS" for item in results)
    failed = len(results) - passed
    report = {
        "schema": "dna-full-calibration-report",
        "version": VERSION,
        "status": "PASS" if failed == 0 and len(results) == inventory["total_inputs"] else "PARTIAL",
        "classification": "SOFTWARE_ONLY",
        "root": str(root),
        "source_inventory": inventory,
        "gate": gate,
        "execution": {
            "authorized": True,
            "executed": True,
            "mutated_inputs": False,
            "exported_outputs": bool(output_dir),
            "processed_inputs": len(results),
            "passed_inputs": passed,
            "failed_inputs": failed,
            "empty_inputs": sum("EMPTY_INPUT" in item.get("error", "") for item in results),
            "results": results,
        },
        "acceptance": {
            "full_source_denominator": inventory["total_inputs"],
            "every_input_counted": len(results) == inventory["total_inputs"],
            "proxy_as_direct": False,
            "fallback_or_bypass": False,
            "pass_claim_allowed": failed == 0 and len(results) == inventory["total_inputs"],
        },
    }
    report["report_hash"] = sha256_bytes(_canonical(report))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the fail-closed full calibration")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output", type=Path, default=Path("reports") / "truthful_full_calibration_15.00.json")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="write transformed MIDI only after a PASS gate")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    inventory = _source_inventory(root)
    gate = TruthEvidenceGate(root).build()
    if gate.get("status") != "PASS" or not gate.get("can_export"):
        report = _blocked_report(root, gate, inventory, output)
        print(json.dumps({
            "status": report["status"],
            "processed_inputs": report["execution"]["processed_inputs"],
            "full_source_denominator": report["acceptance"]["full_source_denominator"],
            "blocking_reasons": report["blocking_reasons"],
            "report": str(output),
        }, ensure_ascii=False, indent=2))
        return 2
    report = _run_authorized(root, gate, inventory, output,
                             args.output_dir.resolve() if args.output_dir else None)
    print(json.dumps({
        "status": report["status"],
        "processed_inputs": report["execution"]["processed_inputs"],
        "passed_inputs": report["execution"].get("passed_inputs", 0),
        "failed_inputs": report["execution"].get("failed_inputs", 0),
        "report": str(output),
    }, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
