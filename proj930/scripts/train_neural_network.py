from __future__ import annotations
import argparse, json, math, shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def finite_report(report: dict, keys: tuple[str, ...]) -> None:
    for key in keys:
        value = report.get(key)
        if value is None or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise RuntimeError(f'invalid training metric: {key}={value!r}')


def backup_dir(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = time.strftime('%Y%m%d-%H%M%S')
    dst = ROOT / 'model_backups' / f'{path.name}-{stamp}'
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(path, dst)
    return dst


def promote(staging: Path, production: Path) -> None:
    backup_dir(production)
    tmp = production.with_name(production.name + '.promote-tmp')
    if tmp.exists():
        shutil.rmtree(tmp)
    shutil.copytree(staging, tmp)
    if production.exists():
        shutil.rmtree(production)
    tmp.replace(production)


def train_core(args) -> dict:
    from dna_midi_studio.ai_learning.trainer import LearningTrainer, TrainingConfig
    dataset = ROOT / 'learning_data' / 'learning_dataset_v1.npz'
    if not dataset.exists():
        raise FileNotFoundError(dataset)
    staging = ROOT / 'models_staging' / 'dna-reconstructor-v2'
    if staging.exists(): shutil.rmtree(staging)
    tc = TrainingConfig(epochs=args.epochs, batch_size=args.batch, learning_rate=args.lr,
                        patience=args.patience, device=args.device,
                        max_train_samples=args.max_train_samples,
                        max_validation_samples=args.max_validation_samples,
                        max_holdout_samples=args.max_holdout_samples)
    report = LearningTrainer(training_config=tc).train(dataset, staging)
    finite_report(report, ('bestValidationLoss','holdoutLoss'))
    authority = report.get('authority', {})
    if authority.get('goldVelocityUsed') is not False or authority.get('velocityOutputHead') is not False:
        raise RuntimeError('velocity authority violation in core neural report')
    if args.promote:
        promote(staging, ROOT / 'models' / 'dna-reconstructor-v2')
    return {'model':'core','staging':str(staging.relative_to(ROOT)),'promoted':args.promote,'report':report}


def train_relationship(args) -> dict:
    from dna_midi_studio.ai_learning.relationship_sequence_trainer import train_sequence_model
    dataset = ROOT / 'relationship_sequence_data_v2' / 'relationship_sequence_dataset_v2.npz'
    if not dataset.exists():
        raise FileNotFoundError(dataset)
    staging = ROOT / 'models_staging' / 'relationship-sequence-v2'
    if staging.exists(): shutil.rmtree(staging)
    report = train_sequence_model(dataset, staging, epochs=args.relationship_epochs,
                                  batch_size=args.relationship_batch, lr=args.relationship_lr,
                                  patience=args.relationship_patience)
    finite_report(report, ('bestValidationLoss','holdoutLoss'))
    manifest = ROOT / 'relationship_sequence_data_v2' / 'relationship_sequence_manifest_v2.json'
    if manifest.exists():
        m = json.loads(manifest.read_text(encoding='utf-8'))
        if m.get('velocityFeature') is not False or m.get('velocityTarget') is not False:
            raise RuntimeError('velocity authority violation in relationship dataset')
    if args.promote:
        promote(staging, ROOT / 'models' / 'relationship-sequence-v2')
    return {'model':'relationship-sequence','staging':str(staging.relative_to(ROOT)),'promoted':args.promote,'report':report}


def calibrate_only() -> dict:
    """Truthful post-training gate: verify reports, datasets, invariants and tests.

    This does not alter model weights. Audible threshold calibration remains corpus/device work.
    """
    checks=[]
    required=[
        ROOT/'learning_data'/'dataset_manifest.json',
        ROOT/'relationship_sequence_data_v2'/'relationship_sequence_manifest_v2.json',
        ROOT/'models'/'dna-reconstructor-v2'/'training_report.json',
        ROOT/'models'/'relationship-sequence-v2'/'relationship_sequence_training_report.json',
    ]
    for p in required:
        checks.append({'path':str(p.relative_to(ROOT)),'exists':p.exists()})
    if not all(x['exists'] for x in checks):
        raise RuntimeError('missing dataset/model evidence; see calibration report')
    dm=json.loads((ROOT/'learning_data'/'dataset_manifest.json').read_text(encoding='utf-8'))
    rm=json.loads((ROOT/'relationship_sequence_data_v2'/'relationship_sequence_manifest_v2.json').read_text(encoding='utf-8'))
    velocity_safe = rm.get('velocityFeature') is False and rm.get('velocityTarget') is False
    if not velocity_safe:
        raise RuntimeError('relationship calibration is not velocity-safe')
    return {
        'schema':'dna-neural-calibration-gate','version':'9.02',
        'status':'SOFTWARE_CALIBRATED_WAITING_FOR_LISTENING_DEVICE_GATE',
        'checks':checks,
        'datasetRows':dm.get('rows') or dm.get('samples'),
        'relationshipRows':rm.get('rows'),
        'velocityAuthorityFactoryOnly':True,
        'note':'Calibration verifies holdout/evidence/invariants. Final musical thresholds still require VALJA blind A/B and physical Pa800 listening.'
    }


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--mode',choices=('core','relationship','all','calibrate'),default='all')
    ap.add_argument('--promote',action='store_true',help='promote only after successful validation; old model is backed up')
    ap.add_argument('--epochs',type=int,default=12); ap.add_argument('--batch',type=int,default=64)
    ap.add_argument('--lr',type=float,default=3e-4); ap.add_argument('--patience',type=int,default=3)
    ap.add_argument('--device',default='auto')
    ap.add_argument('--max-train-samples',type=int); ap.add_argument('--max-validation-samples',type=int); ap.add_argument('--max-holdout-samples',type=int)
    ap.add_argument('--relationship-epochs',type=int,default=18); ap.add_argument('--relationship-batch',type=int,default=8)
    ap.add_argument('--relationship-lr',type=float,default=4e-4); ap.add_argument('--relationship-patience',type=int,default=5)
    args=ap.parse_args()
    out={'schema':'dna-neural-training-run','version':'9.02','mode':args.mode,'promoteRequested':args.promote,'results':[]}
    if args.mode in ('core','all'): out['results'].append(train_core(args))
    if args.mode in ('relationship','all'): out['results'].append(train_relationship(args))
    if args.mode in ('calibrate','all'): out['calibration']=calibrate_only()
    report=ROOT/'artifacts'/'neural_training_run_9.02.json'; report.parent.mkdir(exist_ok=True)
    report.write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps(out,indent=2))
    return 0

if __name__=='__main__': raise SystemExit(main())
