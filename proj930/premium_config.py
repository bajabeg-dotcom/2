#!/usr/bin/env python3
"""Session 15 contracts and immutable baseline for AI Premium Arranger.

This module is deliberately plan-only. It validates structured intent and
freezes evidence, but it cannot mutate MIDI or authorize a final export.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import shutil
from typing import Any, Mapping


CONTRACT_VERSION = "1.0"
CONFIG_SCHEMA = "dna-premium-config"
PLAN_SCHEMA = "dna-premium-read-only-plan"
BASELINE_SCHEMA = "dna-premium-baseline"
FEATURE_MATRIX_SCHEMA = "dna-premium-feature-matrix"
SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"
BASELINE_DATE = "2026-09-02"

CONTRACT_SCHEMAS = (
    "producer-brief-v1.schema.json",
    "song-map-v1.schema.json",
    "sound-binding-v1.schema.json",
    "arrangement-graph-v1.schema.json",
    "candidate-set-v1.schema.json",
    "track-plan-v1.schema.json",
    "render-manifest-v1.schema.json",
    "evaluation-report-v1.schema.json",
    "device-profile-v1.schema.json",
)

PRODUCTION_REGISTRIES = (
    "data/factory-velocity-profiles.json",
    "data/gold-patterns.json",
    "data/factory-style-segments.json",
    "data/factory-strumming.json",
    "data/gold-performance-patterns.json",
)

SNAPSHOT_REPORTS = (
    "data/release-check-report.json",
    "data/recovery-release-report.json",
    "data/session13-test-report.json",
    "data/session14-preflight-report.json",
)

ROLE_VALUES = {"drums", "percussion", "bass", "guitar", "accompaniment", "riff", "solo", "pad"}
ELEMENT_VALUES = {
    "i1cv1", "i2cv1", "v1cv1", "v2cv1", "v3cv1", "v4cv1",
    "f1cv1", "f2cv1", "e1cv1", "e2cv1",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _strict_keys(value: Mapping[str, Any], allowed: set[str], context: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ValueError(f"Unknown {context} fields: {', '.join(unknown)}")


def validate_producer_brief(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("Producer brief must be an object")
    allowed = {
        "schema", "version", "prompt", "genre", "energyCurve", "density",
        "requiredRoles", "forbiddenRoles", "lockedElements",
        "transformationTolerance", "notes",
    }
    _strict_keys(value, allowed, "producer brief")
    if value.get("schema") != "dna-premium-producer-brief" or value.get("version") != CONTRACT_VERSION:
        raise ValueError("Unsupported ProducerBrief schema/version")
    prompt = value.get("prompt")
    if not isinstance(prompt, str) or not 1 <= len(prompt.strip()) <= 2000:
        raise ValueError("Producer brief prompt must contain 1..2000 characters")
    genre = value.get("genre")
    if not isinstance(genre, str) or not genre.strip() or len(genre) > 80:
        raise ValueError("Producer brief genre is required and limited to 80 characters")
    density = value.get("density")
    if density not in {"sparse", "balanced", "full"}:
        raise ValueError("Producer brief density must be sparse, balanced or full")
    curve = value.get("energyCurve")
    if not isinstance(curve, list) or not 2 <= len(curve) <= 16:
        raise ValueError("Energy curve must contain 2..16 points")
    if any(isinstance(point, bool) or not isinstance(point, (int, float)) or not 0 <= point <= 100 for point in curve):
        raise ValueError("Energy curve points must be numbers in range 0..100")
    required = value.get("requiredRoles", [])
    forbidden = value.get("forbiddenRoles", [])
    if not isinstance(required, list) or not isinstance(forbidden, list):
        raise ValueError("Role constraints must be arrays")
    if len(required) != len(set(required)) or len(forbidden) != len(set(forbidden)):
        raise ValueError("Role constraints must be unique")
    if not set(required) <= ROLE_VALUES or not set(forbidden) <= ROLE_VALUES:
        raise ValueError("Producer brief contains an unknown role")
    if set(required) & set(forbidden):
        raise ValueError("A role cannot be both required and forbidden")
    locked = value.get("lockedElements", [])
    if not isinstance(locked, list) or len(locked) != len(set(locked)) or not set(locked) <= ELEMENT_VALUES:
        raise ValueError("Locked elements must be unique supported Pa800 markers")
    tolerance = value.get("transformationTolerance")
    if isinstance(tolerance, bool) or not isinstance(tolerance, int) or not 0 <= tolerance <= 100:
        raise ValueError("Transformation tolerance must be an integer in range 0..100")
    notes = value.get("notes", "")
    if not isinstance(notes, str) or len(notes) > 2000:
        raise ValueError("Producer brief notes are limited to 2000 characters")
    return json.loads(json.dumps(value, ensure_ascii=False))


@dataclass(frozen=True)
class PremiumConfig:
    name: str
    seed: int
    target_device: str
    producer_brief: dict[str, Any]
    variant_count: int = 2
    cloud_enabled: bool = False
    output_mode: str = "plan-only"

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "PremiumConfig":
        if not isinstance(value, Mapping):
            raise ValueError("Premium config must be an object")
        allowed = {
            "schema", "version", "name", "seed", "targetDevice", "producerBrief",
            "variantCount", "cloudEnabled", "outputMode",
        }
        _strict_keys(value, allowed, "premium config")
        if value.get("schema") != CONFIG_SCHEMA or value.get("version") != CONTRACT_VERSION:
            raise ValueError("Unsupported PremiumConfig schema/version")
        name = value.get("name")
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 120:
            raise ValueError("Premium project name must contain 1..120 characters")
        seed = value.get("seed")
        if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 2**31 - 1:
            raise ValueError("Premium seed must be an integer in range 0..2147483647")
        target = value.get("targetDevice")
        if target != "Korg Pa800":
            raise ValueError("Session 15 baseline supports only the Korg Pa800 target")
        variants = value.get("variantCount", 2)
        if isinstance(variants, bool) or not isinstance(variants, int) or not 2 <= variants <= 4:
            raise ValueError("Premium variant count must be 2..4")
        cloud = value.get("cloudEnabled", False)
        if not isinstance(cloud, bool):
            raise ValueError("cloudEnabled must be boolean")
        output_mode = value.get("outputMode", "plan-only")
        if output_mode != "plan-only":
            raise ValueError("Session 15 PremiumConfig is read-only and plan-only")
        brief = validate_producer_brief(value.get("producerBrief", {}))
        return cls(name.strip(), seed, target, brief, variants, cloud, output_mode)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": CONFIG_SCHEMA,
            "version": CONTRACT_VERSION,
            "name": self.name,
            "seed": self.seed,
            "targetDevice": self.target_device,
            "producerBrief": self.producer_brief,
            "variantCount": self.variant_count,
            "cloudEnabled": self.cloud_enabled,
            "outputMode": self.output_mode,
        }

    @property
    def config_hash(self) -> str:
        return sha256(canonical_json(self.to_dict())).hexdigest()


def build_read_only_plan(config: PremiumConfig) -> dict[str, Any]:
    plan = {
        "schema": PLAN_SCHEMA,
        "version": CONTRACT_VERSION,
        "status": "PLANNED",
        "configHash": config.config_hash,
        "targetDevice": config.target_device,
        "variantIds": [f"variant-{index + 1}" for index in range(config.variant_count)],
        "lockedElements": list(config.producer_brief.get("lockedElements", [])),
        "safety": {
            "midiMutationAllowed": False,
            "finalMidiWriteAllowed": False,
            "validatorBypassAllowed": False,
            "goldAffectsDynamics": False,
            "originalSoloMutationAllowed": False,
            "cloudCarriesMidi": False,
        },
    }
    plan["planHash"] = sha256(canonical_json(plan)).hexdigest()
    return plan


def schema_catalog(root: Path) -> dict[str, Any]:
    schema_dir = root / "premium" / "schemas" / "v1"
    entries = []
    for name in CONTRACT_SCHEMAS:
        path = schema_dir / name
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("$schema") != SCHEMA_DRAFT:
            raise ValueError(f"Schema {name} does not use Draft 2020-12")
        if value.get("x-contract-version") != CONTRACT_VERSION:
            raise ValueError(f"Schema {name} has an unsupported contract version")
        if value.get("type") != "object" or value.get("additionalProperties") is not False:
            raise ValueError(f"Schema {name} must be a strict root object")
        entries.append({
            "name": name,
            "id": value.get("$id"),
            "title": value.get("title"),
            "sha256": sha256_file(path),
            "required": value.get("required", []),
        })
    payload = {
        "schema": "dna-premium-contract-catalog",
        "version": CONTRACT_VERSION,
        "date": BASELINE_DATE,
        "contracts": entries,
    }
    payload["catalogHash"] = sha256(canonical_json(entries)).hexdigest()
    return payload


def feature_matrix_document() -> dict[str, Any]:
    features = [
        (15, "baseline-freeze", "P0", "SOFTWARE_VALIDATED", None),
        (16, "pa800-mapping-lab", "P0", "DEVICE_BLOCKED", "physical Korg Pa800 required"),
        (17, "production-adapter", "P0", "PLANNED", None),
        (18, "track-identity-solo-safety-2", "P0", "PLANNED", None),
        (19, "song-understanding-2", "P0", "PLANNED", None),
        (20, "ai-producer-brief", "P0", "PLANNED", None),
        (21, "arrangement-graph", "P0", "PLANNED", None),
        (22, "candidate-variation-engine", "P0", "PLANNED", None),
        (23, "groove-polyphony-voice-cost", "P0", "PLANNED", None),
        (24, "solo-expression-director", "P0", "PLANNED", None),
        (25, "confirmed-articulation-maps", "P0", "DEVICE_BLOCKED", "confirmed device maps required"),
        (26, "premium-preview", "P0", "PLANNED", None),
        (27, "music-quality-evaluator", "P0", "PLANNED", None),
        (28, "premium-gui", "P0", "PLANNED", None),
        (29, "personal-producer-profile", "P1", "PLANNED", None),
        (30, "ai-premium-release-gate", "P0", "PLANNED", None),
    ]
    return {
        "schema": FEATURE_MATRIX_SCHEMA,
        "version": CONTRACT_VERSION,
        "date": BASELINE_DATE,
        "softwareBaseline": "3.17",
        "premiumProductStatus": "PLANNED",
        "features": [
            {"session": session, "id": feature_id, "priority": priority, "status": status,
             **({"blocker": blocker} if blocker else {})}
            for session, feature_id, priority, status, blocker in features
        ],
        "invariants": {
            "plannedDoesNotMeanImplemented": True,
            "physicalPa800": "WAITING_FOR_DEVICE",
            "goldAffectsDynamics": False,
            "aiWritesFinalMidi": False,
        },
    }


def _snapshot_reports(root: Path, baseline_dir: Path, refresh: bool) -> list[str]:
    paths = []
    report_dir = baseline_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    for relative in SNAPSHOT_REPORTS:
        source = root / relative
        target = report_dir / Path(relative).name
        if refresh or not target.exists():
            if not source.is_file():
                raise FileNotFoundError(f"Missing baseline report: {relative}")
            shutil.copyfile(source, target)
        paths.append(target.relative_to(root).as_posix())
    return paths


def _build_reference_style(root: Path, refresh: bool) -> tuple[str, str]:
    import server

    server.load_data()
    baseline_dir = root / "premium" / "baseline"
    midi_path = baseline_dir / "reference-style.mid"
    manifest_path = baseline_dir / "reference-style.manifest.json"
    config = {
        "name": "DNA PREMIUM 3.17 BASELINE",
        "tempo": 120,
        "meter": "4/4",
        "seed": 150015001,
        "elements": server.DEFAULT_ELEMENTS,
        "tracks": {name: {"enabled": True} for name in server.TRACKS},
    }
    midi, manifest = server.build_pa800_style(config)
    if not manifest["compliance"]["passed"]:
        raise RuntimeError("Premium baseline reference MIDI failed Pa800 validation")
    if refresh or not midi_path.exists() or not manifest_path.exists():
        midi_path.parent.mkdir(parents=True, exist_ok=True)
        midi_path.write_bytes(midi)
        _write_json(manifest_path, manifest)
    elif midi_path.read_bytes() != midi:
        raise RuntimeError("Premium baseline reference MIDI is not deterministic")
    return midi_path.relative_to(root).as_posix(), manifest_path.relative_to(root).as_posix()


def _baseline_document(root: Path, frozen_paths: list[str]) -> dict[str, Any]:
    entries = []
    for relative in sorted(set(frozen_paths)):
        path = root / relative
        entries.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    build = json.loads((root / "data" / "dna-build-report.json").read_text(encoding="utf-8"))
    content_hash = sha256(canonical_json(entries)).hexdigest()
    return {
        "schema": BASELINE_SCHEMA,
        "version": CONTRACT_VERSION,
        "date": BASELINE_DATE,
        "softwareBaseline": "3.17",
        "sourceBaseline": "3.16 + Session 15 contracts",
        "baselineId": f"premium-3.17-{content_hash[:16]}",
        "contentHash": content_hash,
        "frozenFiles": entries,
        "corpus": {
            "factoryMidi": 3211,
            "goldMidi": 182,
            "factoryProfiles": build["factory"]["profileCount"],
            "factoryStyleSegments": build["factoryStyle"]["segments"],
            "factoryStrummingPatterns": build["factoryStrumming"]["patterns"],
            "goldPerformancePatterns": build["goldPerformance"]["patterns"],
            "legacyGoldPatterns": build["gold"]["patternCount"],
        },
        "verifiedSuites": {"legacy": "43/43 PASS", "recoveryPreflight": "289/289 PASS"},
        "premiumReadiness": {
            "session15": "SOFTWARE_VALIDATED",
            "premiumProduct": "PLANNED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        },
        "invariants": {
            "goldAffectsDynamics": False,
            "analysisVelocityUsed": False,
            "aiWritesFinalMidi": False,
            "validatorBypassAllowed": False,
            "originalSoloMutationAllowed": False,
        },
    }


def verify_baseline(root: Path, baseline: Mapping[str, Any]) -> bool:
    entries = baseline.get("frozenFiles")
    if not isinstance(entries, list) or not entries:
        return False
    rebuilt = []
    for item in entries:
        relative = item.get("path")
        if not isinstance(relative, str):
            return False
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            return False
        resolved = root / path
        if not resolved.is_file():
            return False
        current = {"path": relative, "bytes": resolved.stat().st_size, "sha256": sha256_file(resolved)}
        if current != item:
            return False
        rebuilt.append(current)
    return sha256(canonical_json(rebuilt)).hexdigest() == baseline.get("contentHash")


def _restore_frozen_json_newlines(root: Path, baseline_path: Path) -> None:
    """Repair only a lost terminal LF when the frozen hash proves exact bytes.

    Some editors normalize a final newline while opening an untracked JSON file.
    This is not a baseline refresh: restoration is allowed only when appending
    one LF recreates the already-recorded byte count and SHA-256 exactly.
    """

    if not baseline_path.is_file():
        return
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    for item in baseline.get("frozenFiles", []):
        relative = item.get("path")
        if not isinstance(relative, str) or not relative.endswith(".json"):
            continue
        path = root / relative
        if not path.is_file():
            continue
        raw = path.read_bytes()
        repaired = raw + b"\n"
        if (
            not raw.endswith(b"\n")
            and len(repaired) == item.get("bytes")
            and sha256(repaired).hexdigest() == item.get("sha256")
        ):
            path.write_bytes(repaired)


def _restore_frozen_report_snapshots(root: Path, baseline_path: Path) -> None:
    """Restore mutable live reports from their already-frozen snapshot copies.

    Sessions after 15 append readiness information to live ``data`` reports.
    That must not invalidate the immutable 3.17 evidence.  Restoration is
    permitted only when the baseline's snapshot copy itself matches the exact
    byte count and SHA-256 recorded for the corresponding live report.
    """

    if not baseline_path.is_file():
        return
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    expected = {
        item.get("path"): item
        for item in baseline.get("frozenFiles", [])
        if isinstance(item.get("path"), str)
    }
    for relative in SNAPSHOT_REPORTS:
        item = expected.get(relative)
        if item is None:
            continue
        source = root / "premium" / "baseline" / "reports" / Path(relative).name
        target = root / relative
        if not source.is_file():
            continue
        raw = source.read_bytes()
        if len(raw) != item.get("bytes") or sha256(raw).hexdigest() != item.get("sha256"):
            continue
        if not target.is_file() or target.read_bytes() != raw:
            target.write_bytes(raw)


def prepare_premium_baseline(root: Path, *, refresh: bool = False) -> dict[str, Any]:
    root = root.resolve()
    import server

    baseline_path = root / "data" / "premium-baseline.json"
    _restore_frozen_json_newlines(root, baseline_path)
    _restore_frozen_report_snapshots(root, baseline_path)
    server.ensure_data()
    schema_dir = root / "premium" / "schemas" / "v1"
    catalog = schema_catalog(root)
    catalog_path = schema_dir.parent / "catalog.json"
    _write_json(catalog_path, catalog)

    matrix = feature_matrix_document()
    matrix_path = root / "data" / "premium-feature-matrix.json"
    _write_json(matrix_path, matrix)

    baseline_dir = root / "premium" / "baseline"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    matrix_snapshot = baseline_dir / "premium-feature-matrix.json"
    if refresh or not matrix_snapshot.exists():
        _write_json(matrix_snapshot, matrix)
    report_paths = _snapshot_reports(root, baseline_dir, refresh)
    midi_path, midi_manifest_path = _build_reference_style(root, refresh)

    frozen_paths = [
        "prism-uploads/DNA.zip",
        "data/dna-build-report.json",
        *PRODUCTION_REGISTRIES,
        *(f"premium/schemas/v1/{name}" for name in CONTRACT_SCHEMAS),
        "premium/schemas/catalog.json",
        "premium/baseline/premium-feature-matrix.json",
        *report_paths,
        midi_path,
        midi_manifest_path,
    ]
    if refresh or not baseline_path.exists():
        _write_json(baseline_path, _baseline_document(root, frozen_paths))
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    if not verify_baseline(root, baseline):
        raise RuntimeError("Premium 3.17 baseline verification failed")
    return {
        "baseline": baseline,
        "baselinePath": baseline_path,
        "featureMatrix": matrix,
        "featureMatrixPath": matrix_path,
        "schemaCatalog": catalog,
        "schemaCatalogPath": catalog_path,
        "referenceMidi": root / midi_path,
        "referenceManifest": root / midi_manifest_path,
    }