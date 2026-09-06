#!/usr/bin/env python3
"""DNA MIDI Studio Pa800 — Local Neural Training Script.

Standalone training script that can be run on any computer with Python 3.10+
and PyTorch installed. No GPU required (CPU-only works).

Usage:
    python scripts/train_local.py --mode core --epochs 8
    python scripts/train_local.py --mode relationship --epochs 12
    python scripts/train_local.py --mode all --promote
    python scripts/train_local.py --mode calibrate
"""
from __future__ import annotations
import argparse, hashlib, json, math, shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


def check_dependencies():
    """Verify all required packages are installed."""
    missing = []
    try:
        import torch
        print(f"  torch {torch.__version__}")
    except ImportError:
        missing.append("torch")
    try:
        import numpy
        print(f"  numpy {numpy.__version__}")
    except ImportError:
        missing.append("numpy")
    try:
        import mido
        try:
            print(f"  mido {mido.__version__}")
        except AttributeError:
            print(f"  mido (installed)")
    except ImportError:
        missing.append("mido")
    if missing:
        raise RuntimeError(
            "Neural training BLOCKED: missing packages: "
            + ", ".join(missing)
            + ". Install them before training."
        )
    print("  ✅ All dependencies available")


def finite_report(report: dict, keys: tuple) -> None:
    """Require every named training metric to be present and finite."""
    if not isinstance(report, dict):
        raise RuntimeError("Training report must be a JSON object")
    for key in keys:
        value = report.get(key)
        if isinstance(value, bool) or value is None or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise RuntimeError(f"Invalid training metric: {key}={value!r}; no metric substitution is allowed")


def holdout_count(report: dict) -> float:
    """Return an explicit holdout size; metrics without a sample count are insufficient."""
    for key in ("holdoutSamples", "holdoutNotes", "holdoutCount"):
        if key in report:
            value = report[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise RuntimeError(f"Invalid holdout sample count: {key}={value!r}")
            if float(value) <= 0:
                raise RuntimeError(f"Invalid holdout sample count: {key}={value!r}")
            return float(value)
    raise RuntimeError("Holdout sample count is missing; no sufficient-sample claim is allowed")


def validate_model_report(report: dict, model_kind: str) -> None:
    """Validate model-specific holdout evidence before training/promotion."""
    if model_kind not in {"core", "relationship"}:
        raise RuntimeError(f"Unknown model kind: {model_kind!r}")
    if model_kind == "core":
        finite_report(report, ("bestValidationLoss", "holdoutLoss"))
        holdout_count(report)
        if float(report["holdoutLoss"]) < 0:
            raise RuntimeError("Invalid core holdoutLoss: it must be non-negative")
        return
    finite_report(
        report,
        ("bestValidationLoss", "holdoutActionAccuracy", "holdoutIntervalAccuracyOnPlay"),
    )
    holdout_count(report)
    for key in ("holdoutActionAccuracy", "holdoutIntervalAccuracyOnPlay"):
        if not 0.0 <= float(report[key]) <= 1.0:
            raise RuntimeError(f"Invalid relationship holdout metric: {key}={report[key]!r}")


def validate_holdout_coverage(report: dict, model_kind: str, dataset_manifest: dict, relationship_manifest: dict) -> None:
    expected = (
        dataset_manifest.get("holdout")
        if model_kind == "core"
        else relationship_manifest.get("holdoutRows")
    )
    if isinstance(expected, bool) or not isinstance(expected, (int, float)) or expected <= 0:
        raise RuntimeError(f"{model_kind} manifest has no valid holdout denominator")
    observed = holdout_count(report)
    if observed < float(expected):
        raise RuntimeError(
            f"{model_kind} holdout coverage is incomplete: observed={observed:g}, expected>={float(expected):g}"
        )


def backup_dir(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = time.strftime("%Y%m%d-%H%M%S")
    dst = ROOT / "model_backups" / f"{path.name}-{stamp}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(path, dst)
    print(f"  📦 Backed up {path.name} → model_backups/")
    return dst


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def model_weight_files(model_dir: Path) -> list[Path]:
    """Return non-report model bytes; a JSON report alone is not a model."""
    allowed = {".pt", ".pth", ".bin", ".npz", ".safetensors", ".onnx"}
    return sorted(
        path for path in model_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in allowed and path.stat().st_size > 0
    ) if model_dir.is_dir() else []


def _read_json_object(path: Path) -> dict:
    """Read a manifest without turning missing/corrupt evidence into a crash."""
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def weight_evidence(paths: list[Path]) -> list[dict]:
    evidence = []
    for path in paths:
        try:
            label = str(path.relative_to(ROOT))
        except ValueError:
            label = str(path)
        evidence.append({
            "path": label,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return evidence


def _manifest_checks() -> tuple[list[dict], dict, dict]:
    """Validate datasets by bytes/hash before accepting neural calibration."""
    checks: list[dict] = []
    dataset_manifest_path = ROOT / "learning_data" / "dataset_manifest.json"
    dataset_path = ROOT / "learning_data" / "learning_dataset_v1.npz"
    relationship_manifest_path = ROOT / "relationship_sequence_data_v2" / "relationship_sequence_manifest_v2.json"
    relationship_path = ROOT / "relationship_sequence_data_v2" / "relationship_sequence_dataset_v2.npz"
    dm = _read_json_object(dataset_manifest_path)
    rm = _read_json_object(relationship_manifest_path)
    for path, manifest_path, expected in (
        (dataset_path, dataset_manifest_path, dm.get("dataset_hash")),
        (relationship_path, relationship_manifest_path, rm.get("datasetHash")),
    ):
        actual = sha256_file(path) if path.is_file() else None
        checks.append({
            "path": str(path.relative_to(ROOT)),
            "manifest": str(manifest_path.relative_to(ROOT)),
            "manifestExists": manifest_path.is_file(),
            "exists": path.is_file(),
            "bytes": path.stat().st_size if path.is_file() else 0,
            "expectedSha256": expected,
            "actualSha256": actual,
            "hashMatches": bool(expected and actual == expected),
        })
    return checks, dm, rm


def require_learning_promotion_evidence(staging: Path, model_kind: str) -> dict:
    """Promotion gate for a trained model, separate from MIDI export authority.

    Neural weights may be promoted only when the actual staging bytes and
    measured holdout metrics exist.  This deliberately does not grant MIDI
    transformation authority; the canonical truth gate still controls export.
    """
    if model_kind not in {"core", "relationship"}:
        raise RuntimeError(f"Unknown model kind for promotion: {model_kind!r}")
    if not staging.is_dir():
        raise RuntimeError(f"{model_kind} promotion BLOCKED: staging directory is missing")
    report_name = "training_report.json" if model_kind == "core" else "relationship_sequence_training_report.json"
    report_path = staging / report_name
    if not report_path.is_file() or report_path.stat().st_size == 0:
        raise RuntimeError(f"{model_kind} promotion BLOCKED: training report is missing")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    validate_model_report(report, model_kind)
    weights = model_weight_files(staging)
    if not weights:
        raise RuntimeError(f"{model_kind} promotion BLOCKED: no model weight bytes in staging")
    checks, dataset_manifest, relationship_manifest = _manifest_checks()
    if not all(item["hashMatches"] for item in checks):
        raise RuntimeError(f"{model_kind} promotion BLOCKED: dataset hash verification failed")
    validate_holdout_coverage(report, model_kind, dataset_manifest, relationship_manifest)
    if model_kind == "core":
        authority = report.get("authority", {})
        if authority.get("goldVelocityUsed") is not False or authority.get("velocityOutputHead") is not False:
            raise RuntimeError("core promotion BLOCKED: Factory-only velocity authority is not proven")
    if relationship_manifest.get("velocityFeature") is not False or relationship_manifest.get("velocityTarget") is not False:
        raise RuntimeError("relationship promotion BLOCKED: relationship dataset is not velocity-safe")
    return {
        "reportSha256": sha256_file(report_path),
        "weightEvidence": weight_evidence(weights),
        "datasetChecks": checks,
    }


def promote(staging: Path, production: Path, model_kind: str) -> None:
    evidence = require_learning_promotion_evidence(staging, model_kind)
    backup_dir(production)
    tmp = production.with_name(production.name + ".promote-tmp")
    if tmp.exists():
        shutil.rmtree(tmp)
    shutil.copytree(staging, tmp)
    if production.exists():
        shutil.rmtree(production)
    tmp.replace(production)
    print(f"  🚀 Promoted {staging.name} → {production.name}")
    print(f"  🔐 Promotion evidence: {evidence['reportSha256']}")


def require_learning_runtime() -> None:
    required = (
        ROOT / "src" / "dna_midi_studio" / "ai_learning" / "trainer.py",
        ROOT / "src" / "dna_midi_studio" / "ai_learning" / "relationship_sequence_trainer.py",
    )
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Neural training BLOCKED: production learning runtime is missing: "
            + ", ".join(missing)
        )


def train_core(args) -> dict:
    """Train DNA Reconstructor v2 model."""
    require_learning_runtime()
    print("\n" + "="*60)
    print("TRAINING: DNA Reconstructor v2 (Core)")
    print("="*60)
    
    from dna_midi_studio.ai_learning.trainer import LearningTrainer, TrainingConfig
    
    dataset = ROOT / "learning_data" / "learning_dataset_v1.npz"
    if not dataset.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset}")
    print(f"  Dataset: {dataset.name} ({dataset.stat().st_size/1024:.0f} KB)")
    
    staging = ROOT / "models_staging" / "dna-reconstructor-v2"
    if staging.exists():
        shutil.rmtree(staging)
    
    tc = TrainingConfig(
        epochs=args.epochs,
        batch_size=args.batch,
        learning_rate=args.lr,
        patience=args.patience,
        device=args.device,
        max_train_samples=args.max_train_samples,
        max_validation_samples=args.max_validation_samples,
        max_holdout_samples=args.max_holdout_samples,
    )
    
    print(f"  Config: epochs={args.epochs}, batch={args.batch}, lr={args.lr}, patience={args.patience}")
    print(f"  Device: {args.device}")
    print("\n  Training in progress...\n")
    
    report = LearningTrainer(training_config=tc).train(dataset, staging)
    
    # Ensure report is saved
    report_path = staging / "training_report.json"
    if not report_path.exists():
        report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        print("  📝 Training report saved manually")
    
    validate_model_report(report, "core")
    
    # Authority check
    authority = report.get("authority", {})
    if authority.get("goldVelocityUsed") is not False or authority.get("velocityOutputHead") is not False:
        raise RuntimeError("❌ VELOCITY AUTHORITY VIOLATION in core model!")
    print("  ✅ Velocity authority: FACTORY_ONLY (verified)")
    print(f"  📊 Best validation loss: {report.get('bestValidationLoss', '?'):.4f}")
    print(f"  📊 Best epoch: {report.get('bestEpoch', '?')}")
    
    if args.promote:
        promote(staging, ROOT / "models" / "dna-reconstructor-v2", "core")
    
    return {
        "model": "core",
        "staging": str(staging.relative_to(ROOT)),
        "promoted": args.promote,
        "report": report,
    }


def train_relationship(args) -> dict:
    """Train Relationship Sequence Transformer v2."""
    require_learning_runtime()
    print("\n" + "="*60)
    print("TRAINING: Relationship Sequence Transformer v2")
    print("="*60)
    
    from dna_midi_studio.ai_learning.relationship_sequence_trainer import train_sequence_model
    
    dataset = ROOT / "relationship_sequence_data_v2" / "relationship_sequence_dataset_v2.npz"
    if not dataset.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset}")
    print(f"  Dataset: {dataset.name} ({dataset.stat().st_size/1024:.0f} KB)")
    
    staging = ROOT / "models_staging" / "relationship-sequence-v2"
    if staging.exists():
        shutil.rmtree(staging)
    
    print(f"  Config: epochs={args.relationship_epochs}, batch={args.relationship_batch}, lr={args.relationship_lr}")
    print("\n  Training in progress...\n")
    
    report = train_sequence_model(
        dataset, staging,
        epochs=args.relationship_epochs,
        batch_size=args.relationship_batch,
        lr=args.relationship_lr,
        patience=args.relationship_patience,
    )
    
    # Ensure report is saved
    report_path = staging / "relationship_sequence_training_report.json"
    if not report_path.exists():
        report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        print("  📝 Training report saved manually")
    
    validate_model_report(report, "relationship")
    
    # Velocity safety check
    manifest = ROOT / "relationship_sequence_data_v2" / "relationship_sequence_manifest_v2.json"
    if manifest.exists():
        m = json.loads(manifest.read_text(encoding="utf-8"))
        if m.get("velocityFeature") is not False or m.get("velocityTarget") is not False:
            raise RuntimeError("❌ VELOCITY in relationship dataset — authority violation!")
        print("  ✅ Velocity authority: relationship dataset is velocity-safe")
    
    print(f"  📊 Best validation loss: {report.get('bestValidationLoss', '?'):.4f}")
    print(f"  📊 Holdout action accuracy: {report.get('holdoutActionAccuracy', '?')}")
    print(f"  📊 Holdout interval accuracy: {report.get('holdoutIntervalAccuracyOnPlay', '?')}")
    
    if args.promote:
        promote(staging, ROOT / "models" / "relationship-sequence-v2", "relationship")
    
    return {
        "model": "relationship-sequence",
        "staging": str(staging.relative_to(ROOT)),
        "promoted": args.promote,
        "report": report,
    }


def calibrate_only() -> dict:
    """Calibrate the neural artifacts without claiming MIDI export authority."""
    print("\n" + "="*60)
    print("NEURAL CALIBRATION GATE")
    print("="*60)

    checks, dataset_manifest, relationship_manifest = _manifest_checks()
    issues = []
    for item in checks:
        if not item["manifestExists"]:
            issues.append(f"dataset manifest is missing or unreadable: {item['manifest']}")
        if not item["exists"]:
            issues.append(f"dataset is missing: {item['path']}")
        if not item["hashMatches"]:
            issues.append(f"dataset hash failed: {item['path']}")
    model_specs = [
        ("core", ROOT / "models" / "dna-reconstructor-v2", "training_report.json"),
        ("relationship", ROOT / "models" / "relationship-sequence-v2", "relationship_sequence_training_report.json"),
    ]
    model_results = []
    for kind, model_dir, report_name in model_specs:
        report_path = model_dir / report_name
        weights = model_weight_files(model_dir)
        item = {
            "model": kind,
            "directory": str(model_dir.relative_to(ROOT)),
            "report": str(report_path.relative_to(ROOT)),
            "reportExists": report_path.is_file() and report_path.stat().st_size > 0,
            "reportSha256": sha256_file(report_path) if report_path.is_file() else None,
            "weightEvidence": weight_evidence(weights),
            "weightsPresent": bool(weights),
            "metricsFinite": False,
            "authorityValid": False,
        }
        report = {}
        if item["reportExists"]:
            try:
                report = json.loads(report_path.read_text(encoding="utf-8"))
                validate_model_report(report, kind)
                validate_holdout_coverage(report, kind, dataset_manifest, relationship_manifest)
                item["metricsFinite"] = True
            except (OSError, UnicodeError, json.JSONDecodeError, RuntimeError) as exc:
                item["metricError"] = str(exc)
        if kind == "core":
            authority = report.get("authority", {})
            item["authorityValid"] = (
                authority.get("goldVelocityUsed") is False
                and authority.get("velocityOutputHead") is False
            )
        else:
            item["authorityValid"] = (
                relationship_manifest.get("velocityFeature") is False
                and relationship_manifest.get("velocityTarget") is False
            )
        if not item["reportExists"]:
            issues.append(f"{kind} training report is missing")
        if not item["weightsPresent"]:
            issues.append(f"{kind} model weight bytes are missing")
        if not item["metricsFinite"]:
            detail = item.get("metricError", "missing or non-finite")
            issues.append(f"{kind} holdout/validation evidence is invalid: {detail}")
        if not item["authorityValid"]:
            issues.append(f"{kind} authority invariant is not proven")
        model_results.append(item)

    # This gate is intentionally separate from the neural artifact check:
    # valid weights do not authorize MIDI transformation/export.
    from truthful_evidence_gate import TruthEvidenceGate
    truth_gate = TruthEvidenceGate(ROOT).build()
    neural_ok = not issues
    neural_status = (
        "SOFTWARE_CALIBRATED_WAITING_FOR_LISTENING_DEVICE_GATE"
        if neural_ok else "BLOCKED"
    )
    result = {
        "schema": "dna-neural-calibration-gate",
        "version": "10.01-TRUTHFUL",
        "status": neural_status,
        "neural_calibration": {
            "status": neural_status,
            "datasetRows": dataset_manifest.get("samples"),
            "relationshipRows": relationship_manifest.get("rows"),
            "models": model_results,
            "datasetChecks": checks,
            "velocityAuthorityFactoryOnly": (
                relationship_manifest.get("velocityFeature") is False
                and relationship_manifest.get("velocityTarget") is False
            ),
        },
        "truth_gate": {
            "status": truth_gate.get("status"),
            "canTransform": truth_gate.get("can_transform", False),
            "canExport": truth_gate.get("can_export", False),
            "gateHash": truth_gate.get("gate_hash"),
            "blockingReasons": truth_gate.get("blocking_reasons", []),
        },
        "transform_export_gate": {
            "status": truth_gate.get("status"),
            "canTransform": truth_gate.get("can_transform", False),
            "canExport": truth_gate.get("can_export", False),
            "gateHash": truth_gate.get("gate_hash"),
            "blockingReasons": truth_gate.get("blocking_reasons", []),
        },
        "checks": checks,
        "blockingReasons": issues,
        "finalMusicalThresholds": "LISTENING_DEVICE_REQUIRED",
    }
    if neural_ok:
        print("  🟢 Neural artifact calibration: SOFTWARE_CALIBRATED")
        if truth_gate.get("status") != "PASS":
            print("  🚫 MIDI transform/export remains BLOCKED by the global truth gate")
    else:
        print("  🚫 Neural artifact calibration: BLOCKED")
        for issue in issues:
            print(f"     - {issue}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="DNA MIDI Studio Pa800 — Local Neural Training",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python scripts/train_local.py --mode core --epochs 8
  python scripts/train_local.py --mode relationship --epochs 12
  python scripts/train_local.py --mode all --promote
  python scripts/train_local.py --mode calibrate
""",
    )
    parser.add_argument("--mode", choices=("core", "relationship", "all", "calibrate"), default="all")
    parser.add_argument("--promote", action="store_true", help="Promote model to production after training")
    
    # Core model params
    parser.add_argument("--epochs", type=int, default=12, help="Core model epochs (default: 12)")
    parser.add_argument("--batch", type=int, default=64, help="Core batch size (default: 64)")
    parser.add_argument("--lr", type=float, default=3e-4, help="Core learning rate (default: 3e-4)")
    parser.add_argument("--patience", type=int, default=3, help="Core early stopping patience (default: 3)")
    parser.add_argument("--device", default="auto", help="Device: cpu/cuda/auto (default: auto)")
    parser.add_argument("--max-train-samples", type=int, default=None)
    parser.add_argument("--max-validation-samples", type=int, default=None)
    parser.add_argument("--max-holdout-samples", type=int, default=None)
    
    # Relationship model params
    parser.add_argument("--relationship-epochs", type=int, default=18, help="Relationship epochs (default: 18)")
    parser.add_argument("--relationship-batch", type=int, default=8, help="Relationship batch size (default: 8)")
    parser.add_argument("--relationship-lr", type=float, default=4e-4, help="Relationship LR (default: 4e-4)")
    parser.add_argument("--relationship-patience", type=int, default=5, help="Relationship early stopping (default: 5)")
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("DNA MIDI Studio Pa800 — Neural Training")
    print("="*60)
    output = {
        "schema": "dna-neural-training-run",
        "version": "9.30",
        "mode": args.mode,
        "promoteRequested": args.promote,
        "results": [],
    }

    try:
        if args.mode == "calibrate":
            print("\nCalibration mode: training dependencies are not required for artifact verification.")
        else:
            print("\nChecking dependencies...")
            check_dependencies()
        if args.mode in ("core", "all"):
            result = train_core(args)
            output["results"].append(result)
        if args.mode in ("relationship", "all"):
            result = train_relationship(args)
            output["results"].append(result)
        if args.mode in ("calibrate", "all"):
            output["calibration"] = calibrate_only()
    except Exception as e:
        print(f"\n  🚫 Neural run BLOCKED: {e}")
        output["status"] = "BLOCKED"
        output["error"] = str(e)
        output["blockingReasons"] = [str(e)]
        # Save a fail-closed error report rather than leaving a stale result.
        report_path = ROOT / "artifacts" / "neural_training_run_9.30.json"
        report_path.parent.mkdir(exist_ok=True)
        report_path.write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")
        return 2
    
    calibration_status = output.get("calibration", {}).get("status")
    if calibration_status is not None:
        output["status"] = calibration_status
    else:
        output["status"] = "TRAINING_ARTIFACTS_CREATED_NOT_CALIBRATED"

    # Save final report
    report_path = ROOT / "artifacts" / "neural_training_run_9.30.json"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")
    print(f"\n  📄 Report saved: {report_path.relative_to(ROOT)}")

    print("\n" + "="*60)
    if calibration_status == "BLOCKED":
        print("NEURAL CALIBRATION BLOCKED")
    elif calibration_status == "SOFTWARE_CALIBRATED_WAITING_FOR_LISTENING_DEVICE_GATE":
        print("NEURAL SOFTWARE CALIBRATION RECORDED")
    else:
        print("TRAINING ARTIFACT RUN FINISHED — NOT CERTIFIED")
    print("="*60)
    return 2 if calibration_status in {"BLOCKED", "INCOMPLETE"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
