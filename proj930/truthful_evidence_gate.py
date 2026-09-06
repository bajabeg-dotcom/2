#!/usr/bin/env python3
"""Fail-closed evidence authority for calibration and MIDI transformation.

This module is deliberately dependency-free.  It is the one place where a
calibration/export operation is allowed to decide whether evidence is usable.
A JSON report is *not* trusted merely because it exists: the gate checks the
bytes, hashes, corpus members, role classifications and production runtime
artifacts before it can authorize a mutation.

The current checkout is expected to be BLOCKED.  That is intentional: the
production neural models/runtime and direct evidence for every mapped role are
not present.  Callers must propagate BLOCKED/PARTIAL rather than substituting
an original value, a proxy, or a default.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "dna-truthful-evidence-gate"
VERSION = "1.0"

# These are the 20 target roles used by the Factory->instrument mapping.  A
# family mapping is not direct per-instrument evidence and is never promoted to
# DIRECT by this module.
TARGET_ROLES = (
    "bass",
    "drums",
    "percussion",
    "violin",
    "sax",
    "clarinet",
    "woodwind",
    "solo_guitar",
    "synth_lead",
    "mallet",
    "choir",
    "fx",
    "rhythm_guitar",
    "piano",
    "organ",
    "accordion",
    "strings",
    "brass",
    "pad",
    "accompaniment",
)

REQUIRED_DOMAINS = (
    "source_corpus",
    "factory_velocity",
    "gold_performance",
    "drum_context",
    "learning",
    "runtime",
    "full_corpus",
)

# A caller cannot turn these into an evidence record through a convenient
# option name.  They are listed here for diagnostics and are also scanned in
# the old certification engines by the integration checks.
FORBIDDEN_OPTION_KEYS = {
    "allowfallback",
    "usefallback",
    "fallback",
    "proxy",
    "useproxy",
    "bypass",
    "skip",
    "skipstages",
    "force",
    "unsafe",
    "defaultvelocity",
    "originalvelocityfallback",
}


class EvidenceGateBlocked(RuntimeError):
    """Raised when a caller attempts a transformation without valid evidence."""

    def __init__(self, report: dict[str, Any], operation: str = "transform") -> None:
        self.report = report
        self.operation = operation
        reasons = report.get("blocking_reasons") or ["evidence gate is not exportable"]
        super().__init__(f"{operation} BLOCKED by {SCHEMA}: " + "; ".join(str(x) for x in reasons[:8]))


def _json_default(value: Any) -> str:
    return str(value)


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=_json_default).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _zip_members(path: Path, suffixes: tuple[str, ...] = (".mid", ".midi")) -> list[str]:
    if not path.is_file():
        return []
    try:
        with zipfile.ZipFile(path) as archive:
            return sorted(
                name for name in archive.namelist()
                if not name.endswith("/") and Path(name).suffix.lower() in suffixes
            )
    except (OSError, zipfile.BadZipFile):
        return []


def _tree_count(root: Path, suffixes: tuple[str, ...] = (".mid", ".midi")) -> int:
    if not root.is_dir():
        return 0
    return sum(1 for path in root.rglob("*") if path.is_file() and path.suffix.lower() in suffixes)


def _read_npy_header(path: Path) -> dict[str, Any]:
    """Read only the NumPy header; no NumPy dependency is required."""
    try:
        data = path.read_bytes()[:4096]
        if not data.startswith(b"\x93NUMPY"):
            return {}
        major, minor = data[6], data[7]
        header_len_size = 2 if major == 1 else 4
        offset = 8
        header_len = int.from_bytes(data[offset:offset + header_len_size], "little")
        offset += header_len_size
        header = data[offset:offset + header_len].decode("latin1").strip()
        parsed = ast.literal_eval(header)
        return parsed if isinstance(parsed, dict) else {}
    except (OSError, UnicodeError, ValueError, SyntaxError):
        return {}


def _source_record(root: Path, path: Path, *, evidence_id: str, domain: str,
                   role: str, target_transform: str, source_span: str,
                   classification: str = "SOURCE_DIRECT") -> dict[str, Any]:
    relative = str(path.relative_to(root)) if path.is_absolute() and path.is_relative_to(root) else str(path)
    exists = path.is_file()
    return {
        "id": evidence_id,
        "source_path": relative,
        "bytes": path.stat().st_size if exists else 0,
        "sha256": sha256_file(path) if exists else None,
        "source_span": source_span,
        "domain": domain,
        "role": role,
        "target_transform": target_transform,
        "classification": classification,
        "usable": exists and path.stat().st_size > 0,
    }


def _status(blocking: bool, partial: bool = False) -> str:
    if blocking:
        return "BLOCKED"
    if partial:
        return "PARTIAL"
    return "PASS"


def _claim_number(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        match = re.search(r"\d+", value.replace(",", ""))
        return int(match.group(0)) if match else None
    return None


class TruthEvidenceGate:
    """Build and verify a content-addressed, fail-closed evidence decision."""

    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root or Path(__file__).resolve().parent).resolve()

    def _paths(self) -> dict[str, Path]:
        return {
            "factory_archive": self.root / "prism-uploads" / "Split Factory Styles.zip",
            "gold_archive": self.root / "prism-uploads" / "Gold DNA.zip",
            "factory_profiles": self.root / "data" / "factory-velocity-profiles.json",
            "gold_patterns": self.root / "data" / "gold-performance-patterns.json",
            "gold_detailed": self.root / "calibration" / "gold_20_roles_detailed_REAL.json",
            "gold_raw": self.root / "calibration" / "gold_dna_real_per_channel_11.00.json",
            "factory_roles": self.root / "calibration" / "factory_20_roles_REAL_3211.json",
            "factory_mapping": self.root / "calibration" / "factory_velocity_13.00_final_20_roles_full.json",
            "drum_profiles": self.root / "data" / "drum-element-profiles-9.30.json",
            "drum_runtime": self.root / "calibration" / "drum_elements_v13_full.json",
            "learning_manifest": self.root / "learning_data" / "dataset_manifest.json",
            "learning_dataset": self.root / "learning_data" / "learning_dataset_v1.npz",
            "relationship_manifest": self.root / "relationship_sequence_data_v2" / "relationship_sequence_manifest_v2.json",
            "relationship_dataset": self.root / "relationship_sequence_data_v2" / "relationship_sequence_dataset_v2.npz",
            "core_model_report": self.root / "models" / "dna-reconstructor-v2" / "training_report.json",
            "relationship_model_report": self.root / "models" / "relationship-sequence-v2" / "relationship_sequence_training_report.json",
            "midi_runtime": self.root / "src" / "dna_midi_studio",
            "factory_extracted": self.root / "prism-uploads" / "Workspace_Styles",
            "gold_extracted": self.root / "prism-uploads" / "Gold DNA",
        }

    def _records(self, paths: dict[str, Path]) -> list[dict[str, Any]]:
        return [
            _source_record(self.root, paths["factory_archive"], evidence_id="EV-SOURCE-FACTORY-ZIP",
                           domain="source_corpus", role="all_factory_files", target_transform="corpus_enumeration",
                           source_span="ZIP member list: *.mid/*.midi", classification="SOURCE_DIRECT"),
            _source_record(self.root, paths["gold_archive"], evidence_id="EV-SOURCE-GOLD-ZIP",
                           domain="source_corpus", role="all_gold_files", target_transform="corpus_enumeration",
                           source_span="ZIP member list: *.mid/*.midi", classification="SOURCE_DIRECT"),
            _source_record(self.root, paths["factory_profiles"], evidence_id="EV-FACTORY-PROFILES",
                           domain="factory_velocity", role="factory_family_profiles", target_transform="velocity",
                           source_span="JSON profiles and summary", classification="SOURCE_DIRECT"),
            _source_record(self.root, paths["gold_patterns"], evidence_id="EV-GOLD-PATTERNS",
                           domain="gold_performance", role="gold_source_roles", target_transform="timing_articulation",
                           source_span="playing_logic.*.timing", classification="SOURCE_DIRECT"),
            _source_record(self.root, paths["gold_detailed"], evidence_id="EV-GOLD-ROLE-CLASSIFICATION",
                           domain="gold_performance", role="role_classification", target_transform="role_assignment",
                           source_span="now_real/still_proxy", classification="DERIVED_ROLE_CLASSIFICATION"),
            _source_record(self.root, paths["drum_profiles"], evidence_id="EV-DRUM-PROFILES",
                           domain="drum_context", role="drum_elements_observed", target_transform="drum_velocity",
                           source_span="elements and drumEvidence", classification="SOURCE_DIRECT"),
            _source_record(self.root, paths["learning_dataset"], evidence_id="EV-LEARNING-DATASET",
                           domain="learning", role="core_dataset", target_transform="learning_runtime",
                           source_span="NPZ bytes and manifest dataset_hash", classification="SOURCE_DIRECT"),
            _source_record(self.root, paths["relationship_dataset"], evidence_id="EV-RELATIONSHIP-DATASET",
                           domain="learning", role="relationship_dataset", target_transform="learning_runtime",
                           source_span="NPZ bytes and manifest datasetHash", classification="SOURCE_DIRECT"),
            _source_record(self.root, paths["core_model_report"], evidence_id="EV-CORE-MODEL-REPORT",
                           domain="learning", role="dna_reconstructor_v2", target_transform="learning_runtime",
                           source_span="training report bytes", classification="TRAINING_OUTPUT"),
            _source_record(self.root, paths["relationship_model_report"], evidence_id="EV-RELATIONSHIP-MODEL-REPORT",
                           domain="learning", role="relationship_sequence_v2", target_transform="learning_runtime",
                           source_span="training report bytes", classification="TRAINING_OUTPUT"),
        ]

    def build(self) -> dict[str, Any]:
        paths = self._paths()
        records = self._records(paths)
        issues: list[str] = []
        warnings: list[str] = []
        domains: dict[str, dict[str, Any]] = {}

        factory_members = _zip_members(paths["factory_archive"])
        gold_members = _zip_members(paths["gold_archive"])
        factory_tree = _tree_count(paths["factory_extracted"])
        gold_tree = _tree_count(paths["gold_extracted"])
        factory_claims = _load_json(paths["factory_profiles"])
        gold_claims = _load_json(paths["gold_patterns"])
        detailed = _load_json(paths["gold_detailed"])
        raw_gold = _load_json(paths["gold_raw"])
        raw_factory = _load_json(paths["factory_profiles"])
        direct_factory_roles = sorted({
            str(row.get("role")) for row in raw_factory.get("profiles", [])
            if isinstance(row, dict) and row.get("role")
        })
        factory_role_calibrations = _load_json(paths["factory_roles"]).get("calibrations", {})
        factory_mapping = _load_json(paths["factory_mapping"])
        mapped_roles = sorted(set((factory_mapping.get("adjustments") or {}).keys()))

        source_ok = bool(factory_members and gold_members)
        source_issues: list[str] = []
        if len(factory_members) != 3211:
            source_issues.append(f"Factory archive contains {len(factory_members)} MIDI members, expected 3211")
        if len(gold_members) != 182:
            source_issues.append(f"Gold archive contains {len(gold_members)} MIDI members, expected 182")
        if not source_ok:
            source_issues.append("one or more authoritative source archives are missing or unreadable")
        claimed_factory_files = _claim_number(factory_claims.get("summary", {}).get("inputFiles"))
        if claimed_factory_files is not None and claimed_factory_files != len(factory_members):
            source_issues.append(f"Factory registry inputFiles={claimed_factory_files} differs from archive={len(factory_members)}")
        claimed_gold_files = _claim_number(gold_claims.get("total_files"))
        if claimed_gold_files is not None and claimed_gold_files != len(gold_members):
            source_issues.append(f"Gold registry total_files={claimed_gold_files} differs from archive={len(gold_members)}")
        if factory_tree != len(factory_members):
            warnings.append(f"extracted Factory tree has {factory_tree}/{len(factory_members)} files; zip is authoritative")
        if gold_tree != len(gold_members):
            warnings.append(f"extracted Gold tree has {gold_tree}/{len(gold_members)} files; zip is authoritative")
        domains["source_corpus"] = {
            "status": _status(bool(source_issues)),
            "archive_members": {"factory": len(factory_members), "gold": len(gold_members), "total": len(factory_members) + len(gold_members)},
            "extracted_tree_members": {"factory": factory_tree, "gold": gold_tree},
            "claims_checked": {"factory_inputFiles": claimed_factory_files, "gold_total_files": claimed_gold_files},
            "issues": source_issues,
            "full_source_enumeration": not bool(source_issues),
        }
        issues.extend(f"source_corpus: {item}" for item in source_issues)

        profile_rows = raw_factory.get("profiles") if isinstance(raw_factory.get("profiles"), list) else []
        profile_summary = raw_factory.get("summary") if isinstance(raw_factory.get("summary"), dict) else {}
        factory_issues: list[str] = []
        if not profile_rows:
            factory_issues.append("Factory velocity profile rows are missing")
        if _claim_number(profile_summary.get("inputFiles")) != len(factory_members):
            factory_issues.append("Factory velocity registry is not tied to the complete archive count")
        claimed_profile_count = _claim_number(profile_summary.get("profileCount"))
        if claimed_profile_count != len(profile_rows):
            factory_issues.append("Factory velocity profileCount does not match profile rows")
        observed_samples = sum(
            int(row.get("sample_count", row.get("samples", 0)) or 0)
            for row in profile_rows if isinstance(row, dict)
        )
        claimed_samples = _claim_number(profile_summary.get("velocitySamples"))
        if claimed_samples != observed_samples:
            factory_issues.append(
                f"Factory velocity sample count {observed_samples} differs from registry {claimed_samples}"
            )
        if not direct_factory_roles:
            factory_issues.append("no direct Factory role profiles")
        missing_factory_roles = sorted(set(TARGET_ROLES) - set(direct_factory_roles))
        factory_partial = bool(missing_factory_roles or mapped_roles != list(TARGET_ROLES))
        domains["factory_velocity"] = {
            "status": _status(bool(factory_issues), factory_partial),
            "direct_source_roles": direct_factory_roles,
            "derived_role_calibrations": sorted(factory_role_calibrations),
            "mapped_target_roles": mapped_roles,
            "missing_direct_target_roles": missing_factory_roles,
            "profiles": len(profile_rows),
            "issues": factory_issues,
            "authority": "FACTORY_ONLY",
        }
        issues.extend(f"factory_velocity: {item}" for item in factory_issues)
        if missing_factory_roles:
            issues.append("factory_velocity: direct evidence is missing for target roles: " + ", ".join(missing_factory_roles))

        playing_logic = gold_claims.get("playing_logic") if isinstance(gold_claims.get("playing_logic"), dict) else {}
        raw_playing = raw_gold.get("playing_logic") if isinstance(raw_gold.get("playing_logic"), dict) else {}
        raw_gold_roles = sorted({
            role for role, value in raw_playing.items()
            if isinstance(value, dict) and isinstance(value.get("timing"), dict) and value["timing"].get("real_gold") is True
        })
        declared_gold_real = sorted({
            role for role, value in playing_logic.items()
            if isinstance(value, dict) and isinstance(value.get("timing"), dict) and value["timing"].get("real_gold") is True
        })
        declared_gold_proxy = sorted(set(playing_logic) - set(declared_gold_real))
        detailed_real = sorted(set(detailed.get("now_real", [])) | set(detailed.get("previous_real", [])))
        detailed_proxy = sorted(set(detailed.get("still_proxy", [])))
        gold_issues: list[str] = []
        if len(gold_members) != _claim_number(gold_claims.get("total_files")):
            gold_issues.append("Gold pattern registry is not tied to the complete Gold archive count")
        if not raw_gold_roles:
            gold_issues.append("no raw direct Gold role evidence")
        if set(declared_gold_real) != set(detailed_real) and detailed_real:
            gold_issues.append("Gold real-role declaration differs between registries")
        if set(declared_gold_proxy) != set(detailed_proxy) and detailed_proxy:
            gold_issues.append("Gold proxy-role declaration differs between registries")
        missing_gold_roles = sorted(set(TARGET_ROLES) - set(raw_gold_roles))
        domains["gold_performance"] = {
            "status": _status(bool(gold_issues), bool(missing_gold_roles or detailed_proxy)),
            "raw_direct_roles": raw_gold_roles,
            "derived_real_roles": detailed_real,
            "proxy_roles": detailed_proxy or declared_gold_proxy,
            "missing_direct_target_roles": missing_gold_roles,
            "registry_real_role_count": len(declared_gold_real),
            "registry_proxy_role_count": len(declared_gold_proxy),
            "issues": gold_issues,
            "authority": "GOLD_TIMING_ARTICULATION_ONLY; FACTORY_VELOCITY_REQUIRED",
        }
        issues.extend(f"gold_performance: {item}" for item in gold_issues)
        if missing_gold_roles:
            issues.append("gold_performance: direct evidence is missing for target roles: " + ", ".join(missing_gold_roles))
        if detailed_proxy:
            issues.append("gold_performance: proxy roles cannot authorize export: " + ", ".join(detailed_proxy))

        drum_profile = _load_json(paths["drum_profiles"])
        drum_runtime = _load_json(paths["drum_runtime"])
        observed_elements = sorted((drum_profile.get("elements") or {}).keys())
        runtime_elements = sorted((drum_runtime.get("elements") or {}).keys())
        runtime_contexts = sorted(set(drum_runtime.get("full_contexts") or []))
        counted_contexts = sorted((drum_runtime.get("counts") or {}).keys())
        required_contexts = ["normal", "accent", "ghost", "fill", "transition", "phrase_end", "syncopated"]
        drum_issues: list[str] = []
        if len(observed_elements) < 19:
            drum_issues.append(f"direct drum evidence covers {len(observed_elements)}/19 required elements")
        if len(runtime_elements) < 19:
            drum_issues.append(f"runtime drum calibration covers {len(runtime_elements)}/19 required elements")
        if set(required_contexts) - set(runtime_contexts):
            drum_issues.append("runtime drum calibration lacks contexts: " + ", ".join(sorted(set(required_contexts) - set(runtime_contexts))))
        if set(required_contexts) - set(counted_contexts):
            drum_issues.append("runtime drum report has no counts for contexts: " + ", ".join(sorted(set(required_contexts) - set(counted_contexts))))
        domains["drum_context"] = {
            "status": _status(bool(drum_issues)),
            "direct_observed_elements": observed_elements,
            "runtime_elements": runtime_elements,
            "runtime_contexts": runtime_contexts,
            "counted_contexts": counted_contexts,
            "required_elements": 19,
            "required_contexts": required_contexts,
            "issues": drum_issues,
        }
        issues.extend(f"drum_context: {item}" for item in drum_issues)

        learning_manifest = _load_json(paths["learning_manifest"])
        relationship_manifest = _load_json(paths["relationship_manifest"])
        learning_issues: list[str] = []
        dataset_hash = sha256_file(paths["learning_dataset"]) if paths["learning_dataset"].is_file() else None
        relationship_hash = sha256_file(paths["relationship_dataset"]) if paths["relationship_dataset"].is_file() else None
        if dataset_hash != learning_manifest.get("dataset_hash"):
            learning_issues.append("core NPZ is missing or its SHA-256 differs from dataset_manifest")
        if relationship_hash != relationship_manifest.get("datasetHash"):
            learning_issues.append("relationship NPZ is missing or its SHA-256 differs from manifest")
        core_shape = _read_npy_header(paths["learning_dataset"]) if paths["learning_dataset"].is_file() else {}
        relationship_shape = _read_npy_header(paths["relationship_dataset"]) if paths["relationship_dataset"].is_file() else {}
        if not paths["core_model_report"].is_file():
            learning_issues.append("promoted core model/training report is missing")
        if not paths["relationship_model_report"].is_file():
            learning_issues.append("promoted relationship model/training report is missing")
        legacy_training_claims = []
        for legacy_path in sorted((self.root / "artifacts").glob("neural_training_run_*.json")):
            legacy_doc = _load_json(legacy_path)
            false_exists = []
            calibration = legacy_doc.get("calibration") if isinstance(legacy_doc.get("calibration"), dict) else {}
            for check in calibration.get("checks", []):
                if not isinstance(check, dict) or check.get("exists") is not True:
                    continue
                claimed_path = self.root / str(check.get("path", ""))
                if not claimed_path.is_file():
                    false_exists.append(str(check.get("path")))
            legacy_training_claims.append({
                "report": str(legacy_path.relative_to(self.root)),
                "claimed_exists_without_bytes": false_exists,
            })
        if any(item["claimed_exists_without_bytes"] for item in legacy_training_claims):
            learning_issues.append("legacy training reports claim model paths exist although the paths are absent")
        domains["learning"] = {
            "status": _status(bool(learning_issues)),
            "dataset": {
                "path": str(paths["learning_dataset"].relative_to(self.root)),
                "sha256": dataset_hash,
                "manifest_sha256": learning_manifest.get("dataset_hash"),
                "shape": core_shape.get("shape"),
                "manifest_samples": learning_manifest.get("samples"),
            },
            "relationship_dataset": {
                "path": str(paths["relationship_dataset"].relative_to(self.root)),
                "sha256": relationship_hash,
                "manifest_sha256": relationship_manifest.get("datasetHash"),
                "shape": relationship_shape.get("shape"),
                "manifest_rows": relationship_manifest.get("rows"),
                "velocity_safe": relationship_manifest.get("velocityFeature") is False and relationship_manifest.get("velocityTarget") is False,
            },
            "model_artifacts": {
                "core_report_exists": paths["core_model_report"].is_file(),
                "relationship_report_exists": paths["relationship_model_report"].is_file(),
            },
            "legacy_training_claims": legacy_training_claims,
            "issues": learning_issues,
        }
        issues.extend(f"learning: {item}" for item in learning_issues)

        runtime_issues: list[str] = []
        if not paths["midi_runtime"].is_dir():
            runtime_issues.append("src/dna_midi_studio production runtime package is missing")
        # mido is optional for the byte-level optimizer, but the certified
        # engine explicitly imports it.  Report the dependency state without
        # importing third-party code in the gate.
        try:
            import importlib.util
            mido_available = importlib.util.find_spec("mido") is not None
        except (ImportError, ModuleNotFoundError, ValueError):
            mido_available = False
        if not mido_available:
            runtime_issues.append("mido dependency required by certified engine is not installed")
        domains["runtime"] = {
            "status": _status(bool(runtime_issues)),
            "production_package": str(paths["midi_runtime"].relative_to(self.root)),
            "production_package_exists": paths["midi_runtime"].is_dir(),
            "mido_available": mido_available,
            "issues": runtime_issues,
        }
        issues.extend(f"runtime: {item}" for item in runtime_issues)

        old_corpus = _load_json(self.root / "calibration" / "full_corpus_C3_REAL_15.00_3430.json")
        old_total = old_corpus.get("output", {}).get("total_files") if isinstance(old_corpus.get("output"), dict) else old_corpus.get("total_files")
        expected_total = len(factory_members) + len(gold_members)
        corpus_issues: list[str] = []
        if expected_total != 3393:
            corpus_issues.append(f"authoritative source total is {expected_total}, expected 3393")
        if _claim_number(old_total) != expected_total:
            corpus_issues.append(f"previous transformation denominator is {old_total!r}, source denominator is {expected_total}")
        corpus_issues.append("no new transformation was authorized because this gate is BLOCKED")
        # The full-corpus pass is an execution stage, not a pre-existing
        # authority.  A prior partial report is PENDING evidence and must not
        # authorize a PASS claim, but it must also not create a circular
        # prerequisite that prevents the newly authorized run from filling the
        # denominator.
        domains["full_corpus"] = {
            "status": "PENDING" if expected_total == 3393 else "BLOCKED",
            "authoritative_input_total": expected_total,
            "factory_input_total": len(factory_members),
            "gold_input_total": len(gold_members),
            "previous_report_total": old_total,
            "processed_every_input": False,
            "issues": corpus_issues,
        }
        if expected_total != 3393:
            issues.extend(f"full_corpus: {item}" for item in corpus_issues if "no new transformation" not in item)

        # Direct evidence is required for every mapped target role.  Derived
        # role labels, family mappings and proxy roles stay visible but never
        # satisfy this set.
        direct_factory_missing = sorted(set(TARGET_ROLES) - set(direct_factory_roles))
        direct_gold_missing = sorted(set(TARGET_ROLES) - set(raw_gold_roles))
        role_matrix = {}
        for role in TARGET_ROLES:
            role_matrix[role] = {
                "factory": "DIRECT" if role in direct_factory_roles else ("DERIVED_MAPPING" if role in mapped_roles else "MISSING"),
                "gold": "DIRECT" if role in raw_gold_roles else ("PROXY" if role in detailed_proxy else "DERIVED_ROLE_CLASSIFICATION" if role in detailed_real else "MISSING"),
                "exportable": role in direct_factory_roles and role in raw_gold_roles,
                "evidence_ids": [
                    "EV-FACTORY-PROFILES" if role in direct_factory_roles else None,
                    "EV-GOLD-PATTERNS" if role in raw_gold_roles else None,
                ],
            }
            role_matrix[role]["evidence_ids"] = [x for x in role_matrix[role]["evidence_ids"] if x]
        if direct_factory_missing:
            issues.append("role_matrix: direct Factory evidence missing for " + ", ".join(direct_factory_missing))
        if direct_gold_missing:
            issues.append("role_matrix: direct Gold evidence missing for " + ", ".join(direct_gold_missing))

        # Do not use a path-only PASS from reference_authority_pipeline.  This
        # gate makes its semantic limitations explicit.
        gate_status = "BLOCKED" if issues else "PASS"
        report: dict[str, Any] = {
            "schema": SCHEMA,
            "version": VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "root": str(self.root),
            "status": gate_status,
            "can_transform": gate_status == "PASS",
            "can_export": gate_status == "PASS",
            "blocking_reasons": issues,
            "warnings": warnings,
            "required_domains": list(REQUIRED_DOMAINS),
            "domains": domains,
            "role_matrix": role_matrix,
            "evidence_ledger": records,
            "direct_evidence_policy": {
                "required_for_every_target_role": True,
                "derived_mapping_satisfies_direct": False,
                "proxy_satisfies_direct": False,
                "self_generated_report_satisfies_direct": False,
                "stale_report_satisfies_direct": False,
            },
            "source_counts": {
                "factory_archive_members": len(factory_members),
                "gold_archive_members": len(gold_members),
                "expected_full_source_inputs": expected_total,
            },
            "legacy_reports_are_non_authoritative": [
                "calibration/final_certified_full_corpus_13.00_full_no_bypass.json",
                "artifacts/neural_training_run_9.02.json",
                "artifacts/neural_training_run_9.30.json",
            ],
        }
        # The content hash is stable across invocations; wall-clock time is
        # informational and must not invalidate an otherwise unchanged gate.
        hash_payload = dict(report)
        hash_payload.pop("generated_at", None)
        report["gate_hash"] = sha256_bytes(_canonical(hash_payload))
        return report

    @staticmethod
    def verify_report(report: dict[str, Any], root: Path | str | None = None,
                      *, require_exportable: bool = True) -> dict[str, Any]:
        """Verify a previously built report before allowing a transformation.

        Re-hashing the ledger paths prevents a stale JSON report from becoming
        authority after a source file changes.  Verification intentionally
        rejects a BLOCKED report; callers must not add a local override.
        """
        if not isinstance(report, dict) or report.get("schema") != SCHEMA:
            raise EvidenceGateBlocked(report if isinstance(report, dict) else {}, "transform")
        expected_hash = report.get("gate_hash")
        without_hash = dict(report)
        without_hash.pop("gate_hash", None)
        without_hash.pop("generated_at", None)
        if expected_hash != sha256_bytes(_canonical(without_hash)):
            raise EvidenceGateBlocked(report, "transform")
        base = Path(root or report.get("root") or Path(__file__).resolve().parent).resolve()
        for record in report.get("evidence_ledger", []):
            if not isinstance(record, dict) or not record.get("usable"):
                continue
            path = base / str(record.get("source_path"))
            if not path.is_file() or path.stat().st_size != int(record.get("bytes", -1)) or sha256_file(path) != record.get("sha256"):
                raise EvidenceGateBlocked({**report, "blocking_reasons": [f"stale or changed evidence: {path}"]}, "transform")
        if require_exportable and (report.get("status") != "PASS" or not report.get("can_export")):
            raise EvidenceGateBlocked(report, "transform")
        return report

    def assert_transform_allowed(self, evidence: dict[str, Any] | None,
                                 options: dict[str, Any] | None = None,
                                 *, roles: Iterable[str] | None = None,
                                 operation: str = "transform") -> dict[str, Any]:
        options = options or {}
        forbidden = [str(key) for key in options if str(key).lower() in FORBIDDEN_OPTION_KEYS]
        if forbidden:
            report = {"schema": SCHEMA, "status": "BLOCKED", "can_export": False,
                      "blocking_reasons": ["forbidden bypass/fallback options: " + ", ".join(forbidden)]}
            raise EvidenceGateBlocked(report, operation)
        report = (evidence or {}).get("gate") if isinstance(evidence, dict) else None
        if report is None:
            report = {"schema": SCHEMA, "status": "BLOCKED", "can_export": False,
                      "blocking_reasons": ["no signed evidence gate supplied"]}
            raise EvidenceGateBlocked(report, operation)
        verified = self.verify_report(report, self.root)
        if roles:
            missing = [role for role in roles if not report.get("role_matrix", {}).get(role, {}).get("exportable")]
            if missing:
                raise EvidenceGateBlocked({**report, "blocking_reasons": ["roles lack direct evidence: " + ", ".join(missing)]}, operation)
        return verified


def build_truth_report(root: Path | str | None = None) -> dict[str, Any]:
    return TruthEvidenceGate(root).build()


def write_truth_report(path: Path | str, root: Path | str | None = None) -> dict[str, Any]:
    report = build_truth_report(root)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build the fail-closed truth/evidence gate report")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    report = build_truth_report(args.root)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "can_transform": report["can_transform"],
        "can_export": report["can_export"],
        "blocking_reasons": report["blocking_reasons"],
        "gate_hash": report["gate_hash"],
    }, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["status"] == "PASS" else 2)
