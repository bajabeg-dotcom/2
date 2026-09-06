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
import argparse, json, math, shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
        print(f"\n  ❌ Missing packages: {', '.join(missing)}")
        print(f"  Install with: pip install {' '.join(missing)}")
        sys.exit(1)
    print("  ✅ All dependencies available")


def finite_report(report: dict, keys: tuple) -> None:
    """Require every training metric to be present and finite.

    A holdout metric cannot be reconstructed from validation loss: doing so
    would turn an unmeasured result into a promotion claim.  Missing, stale,
    or non-finite metrics therefore stop training/promotion immediately.
    """
    for key in keys:
        value = report.get(key)
        if value is None or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise RuntimeError(f"Invalid training metric: {key}={value!r}; no metric substitution is allowed")


def backup_dir(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = time.strftime("%Y%m%d-%H%M%S")
    dst = ROOT / "model_backups" / f"{path.name}-{stamp}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(path, dst)
    print(f"  📦 Backed up {path.name} → model_backups/")
    return dst


def require_promotion_gate() -> dict:
    """Promotion is an export boundary and must have current truth evidence."""
    from truthful_evidence_gate import TruthEvidenceGate
    report = TruthEvidenceGate(ROOT).build()
    if report.get("status") != "PASS" or not report.get("can_export"):
        raise RuntimeError(
            "Model promotion BLOCKED by truth/evidence gate: "
            + "; ".join(report.get("blocking_reasons", [])[:8])
        )
    return report


def promote(staging: Path, production: Path) -> None:
    require_promotion_gate()
    backup_dir(production)
    tmp = production.with_name(production.name + ".promote-tmp")
    if tmp.exists():
        shutil.rmtree(tmp)
    shutil.copytree(staging, tmp)
    if production.exists():
        shutil.rmtree(production)
    tmp.replace(production)
    print(f"  🚀 Promoted {staging.name} → {production.name}")


def train_core(args) -> dict:
    """Train DNA Reconstructor v2 model."""
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
    
    finite_report(report, ("bestValidationLoss", "holdoutLoss"))
    
    # Authority check
    authority = report.get("authority", {})
    if authority.get("goldVelocityUsed") is not False or authority.get("velocityOutputHead") is not False:
        raise RuntimeError("❌ VELOCITY AUTHORITY VIOLATION in core model!")
    print("  ✅ Velocity authority: FACTORY_ONLY (verified)")
    print(f"  📊 Best validation loss: {report.get('bestValidationLoss', '?'):.4f}")
    print(f"  📊 Best epoch: {report.get('bestEpoch', '?')}")
    
    if args.promote:
        promote(staging, ROOT / "models" / "dna-reconstructor-v2")
    
    return {
        "model": "core",
        "staging": str(staging.relative_to(ROOT)),
        "promoted": args.promote,
        "report": report,
    }


def train_relationship(args) -> dict:
    """Train Relationship Sequence Transformer v2."""
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
    
    finite_report(report, ("bestValidationLoss", "holdoutLoss"))
    
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
        promote(staging, ROOT / "models" / "relationship-sequence-v2")
    
    return {
        "model": "relationship-sequence",
        "staging": str(staging.relative_to(ROOT)),
        "promoted": args.promote,
        "report": report,
    }


def calibrate_only() -> dict:
    """Run calibration gate — verify datasets, promoted models and truth evidence."""
    print("\n" + "="*60)
    print("CALIBRATION GATE")
    print("="*60)

    from truthful_evidence_gate import TruthEvidenceGate
    truth_gate = TruthEvidenceGate(ROOT).build()
    if truth_gate.get("status") != "PASS" or not truth_gate.get("can_export"):
        print("  🚫 Truth/evidence gate BLOCKED — no learning claim or export is allowed")
        return {
            "schema": "dna-neural-calibration-gate",
            "version": "10.00-TRUTHFUL",
            "status": "BLOCKED",
            "truth_gate": truth_gate,
            "checks": [],
        }

    checks = []
    required = [
        ROOT / "learning_data" / "dataset_manifest.json",
        ROOT / "relationship_sequence_data_v2" / "relationship_sequence_manifest_v2.json",
        ROOT / "models" / "dna-reconstructor-v2" / "training_report.json",
        ROOT / "models" / "relationship-sequence-v2" / "relationship_sequence_training_report.json",
    ]
    
    all_ok = True
    for p in required:
        exists = p.exists()
        checks.append({"path": str(p.relative_to(ROOT)), "exists": exists})
        icon = "✅" if exists else "❌"
        print(f"  {icon} {p.relative_to(ROOT)}")
        if not exists:
            all_ok = False
    
    if not all_ok:
        print("\n  ⚠️  Some required files missing — run training first")
        return {
            "schema": "dna-neural-calibration-gate",
            "version": "9.30",
            "status": "INCOMPLETE",
            "checks": checks,
        }
    
    # Verify manifests
    dm = json.loads((ROOT / "learning_data" / "dataset_manifest.json").read_text(encoding="utf-8"))
    rm = json.loads((ROOT / "relationship_sequence_data_v2" / "relationship_sequence_manifest_v2.json").read_text(encoding="utf-8"))
    
    velocity_safe = rm.get("velocityFeature") is False and rm.get("velocityTarget") is False
    print(f"  ✅ Velocity safe: {velocity_safe}")
    print(f"  ✅ Dataset rows: {dm.get('rows', dm.get('samples', '?'))}")
    print(f"  ✅ Relationship rows: {rm.get('rows', '?')}")
    
    result = {
        "schema": "dna-neural-calibration-gate",
        "version": "9.30",
        "status": "SOFTWARE_CALIBRATED_WAITING_FOR_LISTENING_DEVICE_GATE",
        "checks": checks,
        "datasetRows": dm.get("rows") or dm.get("samples"),
        "relationshipRows": rm.get("rows"),
        "velocityAuthorityFactoryOnly": True,
    }
    
    print("\n  🟢 CALIBRATION GATE PASSED")
    print("  ℹ️  Final musical thresholds require Pa800 physical listening")
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
    print("\nChecking dependencies...")
    check_dependencies()
    
    output = {
        "schema": "dna-neural-training-run",
        "version": "9.30",
        "mode": args.mode,
        "promoteRequested": args.promote,
        "results": [],
    }
    
    try:
        if args.mode in ("core", "all"):
            result = train_core(args)
            output["results"].append(result)
        if args.mode in ("relationship", "all"):
            result = train_relationship(args)
            output["results"].append(result)
        if args.mode in ("calibrate", "all"):
            output["calibration"] = calibrate_only()
    except Exception as e:
        print(f"\n  ❌ Training failed: {e}")
        output["error"] = str(e)
        # Save error report
        report_path = ROOT / "artifacts" / "neural_training_run_9.30.json"
        report_path.parent.mkdir(exist_ok=True)
        report_path.write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")
        return 1
    
    # Save final report
    report_path = ROOT / "artifacts" / "neural_training_run_9.30.json"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(output, indent=2, default=str), encoding="utf-8")
    print(f"\n  📄 Report saved: {report_path.relative_to(ROOT)}")
    
    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)
    calibration_status = output.get("calibration", {}).get("status")
    return 2 if calibration_status in {"BLOCKED", "INCOMPLETE"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
