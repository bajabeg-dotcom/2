#!/usr/bin/env python3
"""Batch DNA optimization of all 163 valja.zip MIDI files."""
import json, sys, os, time
from pathlib import Path

# Ensure project root on path
PROJ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ))

import midi_optimizer

# Load factory calibration profiles (converted for optimizer)
OPT_PROFILES_PATH = PROJ / "data" / "factory-profiles-optimizer.json"
CALIB_PATH = PROJ / "data" / "factory-calibration-4.37.json"

print("Loading Factory profiles...")
if OPT_PROFILES_PATH.exists():
    factory_profiles = json.loads(OPT_PROFILES_PATH.read_text(encoding="utf-8"))
    print(f"  {len(factory_profiles)} optimized profiles loaded")
else:
    # Fallback: convert on the fly
    calib = json.loads(CALIB_PATH.read_text(encoding="utf-8"))
    raw = list(calib["profiles"].values())
    factory_profiles = []
    for p in raw:
        sb = p.get("soundBinding", [])
        bank_msb = sb[0] if len(sb) > 0 else 0
        program = sb[1] if len(sb) > 1 else 0
        note = sb[2] if len(sb) > 2 else 0
        role = p.get("role", "")
        instrument = p.get("instrument", "")
        is_drum = role == "drums" or instrument.startswith("DRUMS") or instrument.startswith("PERC")
        kind = "drum" if is_drum else "melodic"
        lsb = 0
        ikey = f"drum:{bank_msb}:{lsb}:{program}:{note}" if is_drum else f"melodic:{bank_msb}:{lsb}:{program}"
        ve = p.get("velocityEnvelope", {})
        factory_profiles.append({
            "instrumentKey": ikey, "kind": kind, "program": program,
            "bankMSB": bank_msb, "bankLSB": lsb,
            "drumNote": note if is_drum else None,
            "instrument": instrument, "role": role,
            "profileId": p.get("profileId", ""),
            "samples": ve.get("sampleCount", 0),
            "velocityEnvelope": ve,
            "authority": ve.get("authority", "FACTORY_ONLY"),
        })
    print(f"  {len(factory_profiles)} profiles converted on-the-fly")

# Input/output dirs
INPUT_DIR = Path("/nfs/105096944/temp/valja_check")
OUTPUT_DIR = PROJ / "artifacts" / "valja-optimized"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# DNA optimization options (FULL AI Optimization 6.0 default)
opts = {
    "cleanupNotes": True,
    "removeRedundantControllers": True,
    "quantizeDivision": 16,
    "quantizeStrength": 85,
    "velocityStrength": 65,
    "factoryMixer": True,
    "mixerStrength": 65,
    "insertMissingMixer": True,
    "repairKeyRange": False,
    "energyTarget": 64,
    "performanceGestures": False,
    "phaseOptimization": False,
    "allowPhaseReplace": False,
}

def process_file(fpath: Path, idx: int, total: int):
    """Optimize one MIDI file."""
    name = fpath.name
    print(f"  [{idx+1}/{total}] {name}", end=" ", flush=True)
    try:
        data = fpath.read_bytes()
        result_data, report = midi_optimizer.optimize_midi(
            data,
            factory_profiles,
            options=opts,
            source=name,
            evidence=None
        )
        out_path = OUTPUT_DIR / name
        out_path.write_bytes(result_data)
        sz = len(result_data)
        vel_matched = report.get('velocityProfilesMatched', 0)
        vel_adjusted = report.get('velocitiesAdjusted', 0)
        quantized = report.get('notesQuantized', 0)
        print(f"-> {sz:,} bytes (vel={vel_matched} adjusted, quant={quantized}) OK")
        return {"file": name, "status": "ok", "outputBytes": sz, "report": {k: v for k, v in report.items() if isinstance(v, (int, float, str, bool))}}
    except Exception as e:
        print(f"ERROR: {e}")
        return {"file": name, "status": "error", "error": str(e)}

def main():
    files = sorted(INPUT_DIR.glob("*.mid"))
    total = len(files)
    print(f"\n{'='*60}")
    print(f"DNA MIDI Studio — Batch Optimization: valja corpus")
    print(f"{'='*60}")
    print(f"Input: {INPUT_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Files: {total}")
    print(f"Options: FULL AI Optimization 6.0")
    print()

    results = []
    t0 = time.time()
    for i, f in enumerate(files):
        r = process_file(f, i, total)
        results.append(r)

    elapsed = time.time() - t0
    ok = sum(1 for r in results if r["status"] == "ok")
    err = sum(1 for r in results if r["status"] == "error")

    print(f"\n{'='*60}")
    print(f"DONE: {ok} OK, {err} errors, {elapsed:.1f}s")
    print(f"{'='*60}")

    # Save manifest
    manifest_path = OUTPUT_DIR / "optimization-manifest.json"
    manifest = {
        "schema": "dna-midi-batch-optimization",
        "version": "9.30",
        "source": "valja.zip",
        "total": total,
        "ok": ok,
        "errors": err,
        "elapsedSeconds": round(elapsed, 1),
        "options": opts,
        "results": results
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Manifest: {manifest_path}")

if __name__ == "__main__":
    main()
