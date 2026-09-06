#!/usr/bin/env python3
"""Chunked batch DNA optimization of valja.zip MIDI files.
Resumes from where previous run left off."""
import json, sys, os, time
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ))
import midi_optimizer
from truthful_evidence_gate import TruthEvidenceGate

EVIDENCE = {"gate": TruthEvidenceGate(PROJ).build()}

# Load factory profiles
OPT_PROFILES_PATH = PROJ / "data" / "factory-profiles-optimizer.json"
factory_profiles = json.loads(OPT_PROFILES_PATH.read_text(encoding="utf-8"))
print(f"Loaded {len(factory_profiles)} factory profiles")

INPUT_DIR = Path("/nfs/105096944/temp/valja_check")
OUTPUT_DIR = PROJ / "artifacts" / "valja-optimized"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

opts = {
    "cleanupNotes": True,
    "removeRedundantControllers": True,
    "quantizeDivision": 16,
    "quantizeStrength": 85,
    "velocityStrength": 65,
    "factoryDynamics": True,
    "factoryMixer": False,
    "insertMissingMixer": True,
    "repairKeyRange": False,
    "energyTarget": 64,
    "performanceGestures": False,
    "phaseOptimization": False,
}

def process_file(fpath, idx, total):
    name = fpath.name
    out_path = OUTPUT_DIR / name
    if out_path.exists() and out_path.stat().st_size > 100:
        return {"file": name, "status": "skipped", "outputBytes": out_path.stat().st_size}
    print(f"  [{idx+1}/{total}] {name[:55]}", end=" ", flush=True)
    try:
        data = fpath.read_bytes()
        result_data, report = midi_optimizer.optimize_midi(data, factory_profiles, options=opts, source=name, evidence=EVIDENCE)
        out_path.write_bytes(result_data)
        vel = report.get('velocityProfilesMatched', 0)
        qnt = report.get('notesQuantized', 0)
        print(f"-> {len(result_data):,} bytes (vel={vel} quant={qnt}) OK")
        return {"file": name, "status": "ok", "outputBytes": len(result_data)}
    except Exception as e:
        print(f"ERROR: {e}")
        return {"file": name, "status": "error", "error": str(e)[:200]}

def main():
    if EVIDENCE["gate"].get("status") != "PASS" or not EVIDENCE["gate"].get("can_export"):
        print("Chunked batch optimization BLOCKED by truth/evidence gate; no files were transformed")
        return {"status": "BLOCKED", "truth_gate": EVIDENCE["gate"]}
    all_files = sorted(INPUT_DIR.glob("*.mid"))
    already_done = {f.name for f in OUTPUT_DIR.glob("*.mid") if f.stat().st_size > 100}
    remaining = [f for f in all_files if f.name not in already_done]
    total = len(all_files)
    print(f"\n{'='*60}")
    print(f"DNA MIDI Studio — Chunked Batch Optimization")
    print(f"{'='*60}")
    print(f"Total: {total}, Already done: {len(already_done)}, Remaining: {len(remaining)}")
    if not remaining:
        print("All files already processed!")
        return
    print()

    results = []
    t0 = time.time()
    for i, f in enumerate(remaining):
        r = process_file(f, len(already_done) + i, total)
        results.append(r)

    elapsed = time.time() - t0
    ok = sum(1 for r in results if r["status"] == "ok")
    err = sum(1 for r in results if r["status"] == "error")
    skip = sum(1 for r in results if r["status"] == "skipped")

    total_done = len(already_done) + ok
    print(f"\n{'='*60}")
    print(f"Chunk done: {ok} new OK, {err} errors, {skip} skipped")
    print(f"Total progress: {total_done}/{total} ({total_done*100//total}%)")
    print(f"Elapsed: {elapsed:.1f}s")

    # Update manifest
    manifest_path = OUTPUT_DIR / "optimization-manifest.json"
    existing_manifest = {}
    if manifest_path.exists():
        existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    existing_results = existing_manifest.get("results", [])
    existing_results.extend(results)
    manifest = {
        "schema": "dna-midi-batch-optimization",
        "version": "9.30",
        "source": "valja.zip",
        "total": total,
        "processed": total_done,
        "errors": err,
        "elapsedSeconds": round(elapsed, 1),
        "options": opts,
        "results": existing_results
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

if __name__ == "__main__":
    result = main()
    raise SystemExit(0 if not isinstance(result, dict) or result.get("status") != "BLOCKED" else 2)
