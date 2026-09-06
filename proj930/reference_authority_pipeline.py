#!/usr/bin/env python3
"""Build a strict, auditable plan for using every available reference domain."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REFERENCE_DOMAINS: dict[str, dict[str, Any]] = {
    "velocity": {
        "authority": "FACTORY",
        "required": ["data/factory-velocity-profiles.json", "calibration/factory_velocity_13.00_final_20_roles_full.json"],
        "consumers": ["factory_velocity", "drum_calibration", "musical_validation"],
    },
    "dynamics": {
        "authority": "FACTORY",
        "required": ["data/factory-velocity-profiles.json", "calibration/factory_20_roles_REAL_3211.json"],
        "consumers": ["factory_velocity", "expression_engine", "musical_validation"],
    },
    "range": {
        "authority": "FACTORY",
        "required": ["data/factory-velocity-profiles.json", "data/instrument-playing-profiles-9.30.json"],
        "consumers": ["instrument_profiles", "korg_engine", "final_regression"],
    },
    "timing": {
        "authority": "GOLD",
        "required": ["data/gold-performance-patterns.json", "calibration/gold_dna_real_per_channel_11.00.json"],
        "consumers": ["timing_engine", "full_corpus", "musical_validation"],
    },
    "groove": {
        "authority": "GOLD",
        "required": ["data/gold-performance-patterns.json", "data/reference-pattern-ingest-v6-all.json"],
        "consumers": ["timing_engine", "full_corpus", "musical_validation"],
    },
    "articulation": {
        "authority": "GOLD",
        "required": ["data/gold-performance-patterns.json", "calibration/gold_playing_logic_v13_full.json"],
        "consumers": ["trill_engine", "gold_logic", "musical_validation"],
    },
    "expression": {
        "authority": "GOLD",
        "required": ["data/gold-performance-patterns.json", "data/performance-dna-status-4.35.json"],
        "consumers": ["expression_engine", "humanization_engine", "musical_validation"],
    },
    "humanization": {
        "authority": "GOLD",
        "required": ["data/gold-performance-patterns.json", "data/deterministic-humanization-9.30.json"],
        "consumers": ["humanization_engine", "full_corpus", "final_regression"],
    },
    "drum_elements": {
        "authority": "FACTORY",
        "required": ["data/drum-element-profiles-9.30.json", "calibration/drum_elements_v13_full.json"],
        "consumers": ["drum_calibration", "full_corpus", "korg_engine"],
    },
    "korg_constraints": {
        "authority": "ENGINE",
        "required": ["final_certified_engine_v13_full_no_bypass.py", "pa800_validator.py"],
        "consumers": ["korg_engine", "final_regression", "export"],
    },
    "musical_validation": {
        "authority": "VALIDATION",
        "required": ["musical_validation_9_scores_REAL.py", "musical_validation_scorer_v10.py"],
        "consumers": ["musical_validation", "failure_analysis", "final_regression"],
    },
    "determinism": {
        "authority": "ENGINE",
        "required": ["KOREKCIJA_BAZDARENJE_KALIBRACIJA_ENGINE.py", "deterministic_humanizer.py"],
        "consumers": ["baseline", "full_corpus", "final_regression"],
    },
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_reference_plan(root: Path) -> dict[str, Any]:
    """Resolve all mandatory references without silently substituting proxies."""
    domains: dict[str, Any] = {}
    missing: list[str] = []
    referenced_files: dict[str, str] = {}

    for name, spec in REFERENCE_DOMAINS.items():
        files = []
        for relative in spec["required"]:
            path = root / relative
            present = path.is_file()
            item = {"path": relative, "exists": present}
            if present:
                item["sha256"] = _sha256(path)
                referenced_files[relative] = item["sha256"]
            else:
                missing.append(f"{name}:{relative}")
            files.append(item)
        domains[name] = {
            "authority": spec["authority"],
            "required_files": files,
            "consumers": list(spec["consumers"]),
            "coverage": sum(item["exists"] for item in files) / len(files),
            # Existence and hash are only a path-integrity result.  This
            # function intentionally cannot certify semantic provenance,
            # direct/proxy role status, model promotion, or runtime wiring.
            "status": "PATH_ONLY" if all(item["exists"] for item in files) else "BLOCKED",
            "path_coverage_only": True,
            "proxy_allowed": False,
        }

    covered = sum(domain["status"] == "PATH_ONLY" for domain in domains.values())
    total = len(domains)
    plan = {
        "schema": "reference-authority-plan-1.1",
        "policy": {
            "result_scope": "PATH_COVERAGE_ONLY_NOT_CERTIFICATION",
            "semantic_gate": "truthful_evidence_gate.py",
            "path_coverage_pass_is_not_export_authority": True,
            "mode": "FULL_REFERENCE_REQUIRED",
            "fallbacks": "FORBIDDEN",
            "proxy_sources": "FORBIDDEN",
            "unresolved_action": "BLOCK_TRANSFORMATION_AND_MANUAL_REVIEW",
        },
        "domains": domains,
        "coverage": {
            "covered_domains": covered,
            "total_domains": total,
            "ratio": covered / total if total else 0.0,
            "missing": missing,
            "status": "PATH_ONLY" if not missing else "BLOCKED",
            "path_coverage_only": True,
        },
        "referenced_files": referenced_files,
    }
    return plan


def write_reference_plan(root: Path, output: Path) -> dict[str, Any]:
    plan = build_reference_plan(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return plan
