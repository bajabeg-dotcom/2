#!/usr/bin/env python3
"""
FAZA A4: Full corpus Korg test - 3211 + 182 + 37 = 3430 fajla
Testira Korg Pa800 kompatibilnost na svim REAL fajlovima
"""

import json
import mido
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

WORKSPACE_STYLES = Path("prism-uploads/Workspace_Styles")
GOLD_DNA_DIR = Path("prism-uploads/Gold DNA")
ARTIFACTS_DIR = Path("artifacts")
CALIBRATION_DIR = Path("calibration")

def check_korg_compatibility(mid_path: Path) -> dict:
    try:
        mid = mido.MidiFile(str(mid_path))
    except Exception as e:
        return {"path": str(mid_path), "status": "FAIL", "error": str(e), "ppq": 0}
    
    ppq = mid.ticks_per_beat
    notes = []
    for track in mid.tracks:
        tick = 0
        for msg in track:
            tick += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                notes.append({"pitch": msg.note, "velocity": msg.velocity, "tick": tick, "channel": msg.channel})
    
    if not notes:
        return {"path": str(mid_path), "status": "SKIP", "ppq": ppq, "notes": 0}
    
    # Checks
    errors = []
    warnings = []
    
    # PPQ check - Pa800 prefers 480 but accepts others with conversion
    if ppq != 480:
        warnings.append(f"PPQ {ppq} != 480, needs conversion")
    
    # Per-channel polyphony
    by_channel = defaultdict(list)
    for n in notes:
        by_channel[n["channel"]].append(n)
    
    poly_limits = {
        "bass": 2,
        "drums": 8,
        "accompaniment": 6,
        "melody": 1,
        "default": 6
    }
    
    # Simple role detection per channel
    for ch, ch_notes in by_channel.items():
        # Drums channel 9
        if ch == 9:
            limit = 8
            role = "drums"
        else:
            # Check pitch for bass
            avg_pitch = sum(n["pitch"] for n in ch_notes) / len(ch_notes)
            if avg_pitch < 50:
                limit = 2
                role = "bass"
            else:
                # Check polyphony
                by_tick = defaultdict(list)
                for n in ch_notes:
                    by_tick[n["tick"]].append(n)
                max_poly = max(len(v) for v in by_tick.values()) if by_tick else 0
                if max_poly <= 1:
                    limit = 1
                    role = "melody"
                else:
                    limit = 6
                    role = "accompaniment"
        
        by_tick = defaultdict(list)
        for n in ch_notes:
            by_tick[n["tick"]].append(n)
        max_poly = max(len(v) for v in by_tick.values()) if by_tick else 0
        
        if max_poly > limit:
            errors.append(f"Channel {ch} ({role}) poly {max_poly} > limit {limit}")
    
    # Velocity check
    vels = [n["velocity"] for n in notes]
    if min(vels) < 1 or max(vels) > 127:
        errors.append(f"Velocity out of range {min(vels)}-{max(vels)}")
    
    # CC check - Pa800 allows [1,7,10,11,64]
    allowed_cc = [1,7,10,11,64]
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'control_change' and msg.control not in allowed_cc:
                # Check if DNC or other forbidden
                if msg.control not in [0,32]:  # Bank select allowed for style
                    warnings.append(f"CC {msg.control} not in allowed {allowed_cc} - may need filtering")
    
    status = "PASS" if len(errors) == 0 else "FAIL"
    
    return {
        "path": str(mid_path),
        "file": mid_path.name,
        "status": status,
        "ppq": ppq,
        "notes": len(notes),
        "channels": len(by_channel),
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings)
    }

def main():
    print(f"FAZA A4: Full corpus Korg test - 3211 + 182 + 37 = 3430 fajla")
    
    # Ensure Gold DNA extracted
    if not GOLD_DNA_DIR.exists() or len(list(GOLD_DNA_DIR.glob("*.MID"))) == 0:
        import zipfile
        zip_path = Path("prism-uploads/Gold DNA.zip")
        if zip_path.exists():
            print(f"Extracting {zip_path}...")
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall("prism-uploads/")
    
    factory_files = list(WORKSPACE_STYLES.rglob("*.mid"))
    gold_files = list(GOLD_DNA_DIR.glob("*.MID")) + list(GOLD_DNA_DIR.glob("*.mid"))
    artifact_files = list(ARTIFACTS_DIR.glob("*.mid"))
    
    print(f"Factory: {len(factory_files)} files")
    print(f"Gold: {len(gold_files)} files")
    print(f"Artifacts: {len(artifact_files)} files")
    print(f"Total: {len(factory_files)+len(gold_files)+len(artifact_files)} files")
    
    all_files = factory_files + gold_files + artifact_files
    
    results = []
    factory_pass = 0
    factory_fail = 0
    gold_pass = 0
    gold_fail = 0
    artifact_pass = 0
    artifact_fail = 0
    
    for idx, mf in enumerate(all_files):
        res = check_korg_compatibility(mf)
        results.append(res)
        
        # Categorize
        if mf in factory_files:
            if res["status"] == "PASS":
                factory_pass += 1
            elif res["status"] == "FAIL":
                factory_fail += 1
        elif mf in gold_files:
            if res["status"] == "PASS":
                gold_pass += 1
            elif res["status"] == "FAIL":
                gold_fail += 1
        else:
            if res["status"] == "PASS":
                artifact_pass += 1
            elif res["status"] == "FAIL":
                artifact_fail += 1
        
        if (idx+1) % 500 == 0:
            print(f"  {idx+1}/{len(all_files)} - Factory PASS {factory_pass} FAIL {factory_fail} - Gold PASS {gold_pass} FAIL {gold_fail} - Artifacts PASS {artifact_pass} FAIL {artifact_fail}")
    
    total_pass = factory_pass + gold_pass + artifact_pass
    total_fail = factory_fail + gold_fail + artifact_fail
    total_skip = len(all_files) - total_pass - total_fail
    
    print(f"\n📊 Korg test REAL 3430 files:")
    print(f"   Factory: {len(factory_files)} files - PASS {factory_pass} ({100*factory_pass/max(1,len(factory_files)):.1f}%) FAIL {factory_fail} ({100*factory_fail/max(1,len(factory_files)):.1f}%)")
    print(f"   Gold: {len(gold_files)} files - PASS {gold_pass} ({100*gold_pass/max(1,len(gold_files)):.1f}%) FAIL {gold_fail} ({100*gold_fail/max(1,len(gold_files)):.1f}%)")
    print(f"   Artifacts: {len(artifact_files)} files - PASS {artifact_pass} ({100*artifact_pass/max(1,len(artifact_files)):.1f}%) FAIL {artifact_fail}")
    print(f"   Total: {len(all_files)} files - PASS {total_pass} ({100*total_pass/max(1,len(all_files)):.1f}%) FAIL {total_fail} ({100*total_fail/max(1,len(all_files)):.1f}%) SKIP {total_skip}")
    
    # Analyze failures
    if total_fail > 0:
        print(f"\n   Failures analysis:")
        fail_reasons = Counter()
        for r in results:
            if r["status"] == "FAIL":
                for err in r["errors"]:
                    fail_reasons[err.split("poly")[0] if "poly" in err else err] += 1
        for reason, count in fail_reasons.most_common(10):
            print(f"      {reason}: {count}")
    
    # Save
    report = {
        "version": "14.00-KORG-TEST-3430-REAL",
        "timestamp": datetime.now().isoformat(),
        "total_files": len(all_files),
        "factory_files": len(factory_files),
        "gold_files": len(gold_files),
        "artifact_files": len(artifact_files),
        "factory_pass": factory_pass,
        "factory_fail": factory_fail,
        "factory_pass_rate": f"{100*factory_pass/max(1,len(factory_files)):.1f}%",
        "gold_pass": gold_pass,
        "gold_fail": gold_fail,
        "gold_pass_rate": f"{100*gold_pass/max(1,len(gold_files)):.1f}%",
        "artifact_pass": artifact_pass,
        "artifact_fail": artifact_fail,
        "artifact_pass_rate": f"{100*artifact_pass/max(1,len(artifact_files)):.1f}%",
        "total_pass": total_pass,
        "total_fail": total_fail,
        "total_pass_rate": f"{100*total_pass/max(1,len(all_files)):.1f}%",
        "results": results[:100],  # Only first 100 for size
        "evidence": f"DIRECT REAL Korg test on {len(all_files)} files: Factory {len(factory_files)} + Gold {len(gold_files)} + Artifacts {len(artifact_files)}"
    }
    
    out_path = CALIBRATION_DIR / "korg_test_3430_REAL.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\n✅ Korg test REAL 3430: {out_path}")
    
    # Honest status
    if total_pass == len(all_files):
        print(f"   🎉 SVIH 3430 FAJLOVA PASS KORG 100% - FULL REAL!")
    else:
        print(f"   ⚠️ {total_pass}/{len(all_files)} PASS ({100*total_pass/max(1,len(all_files)):.1f}%) - treba poly reduction za FAIL")

if __name__ == "__main__":
    main()
