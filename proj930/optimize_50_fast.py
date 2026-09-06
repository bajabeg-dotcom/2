#!/usr/bin/env python3
"""
Optimiziraj 50 fajlova u fullu - FAST verzija, samo 50 fajlova
"""

import json
from pathlib import Path
import time
import sys
sys.path.insert(0, str(Path(__file__).parent))

from final_certified_engine_v16_80_percent_REAL import FinalCertifiedEngineV16_80Percent

print("✅ Optimiziraj 50 fajlova u fullu - FAST 50 files")

engine = FinalCertifiedEngineV16_80Percent(sigma_factor=0.3, harmony_preservation=True)

input_dir = Path("gdrive_50_files")
output_dir = Path("artifacts/gdrive_50_optimized_full_17.00")
output_dir.mkdir(parents=True, exist_ok=True)

midi_files = sorted(list(input_dir.glob("*.mid")))[:50]  # SAMO 50
print(f"   Found {len(midi_files)} files (first 50 of 163)")

start = time.time()
results = []
korg_pass = 0
korg_fail = 0
total_before = 0
total_after = 0

for idx, mid_path in enumerate(midi_files):
    out_path = output_dir / f"{mid_path.stem}_OPTIMIZED_17.00.mid"
    try:
        result = engine.process_midi_file_full(mid_path, out_path)
        results.append(result)
        if result.get("korg", {}).get("valid"):
            korg_pass += 1
        else:
            korg_fail += 1
        total_before += result.get("original", {}).get("note_count", 0)
        total_after += result.get("calibrated", {}).get("note_count", 0)
        
        elapsed = time.time() - start
        print(f"   {idx+1:2d}/50 {mid_path.name[:40]:40s} {result.get('original',{}).get('note_count',0):5d}->{result.get('calibrated',{}).get('note_count',0):5d} KORG {result.get('korg',{}).get('valid')} musical {result.get('musical',{}).get('before',0):.1f}->{result.get('musical',{}).get('after',0):.1f} elapsed {elapsed:.1f}s")
    except Exception as e:
        print(f"   ❌ {mid_path.name}: {e}")
        import traceback
        traceback.print_exc()
        korg_fail += 1

elapsed = time.time() - start
print(f"\n✅ Done {elapsed:.1f}s")
print(f"TOTAL 50 files: PASS {korg_pass}/50 ({100*korg_pass/50:.1f}%) FAIL {korg_fail}")
print(f"Notes: {total_before}->{total_after} reduced {total_before-total_after}")

# Zip
import shutil
zip_path = Path("artifacts/gdrive_50_optimized_full_17.00.zip")
if zip_path.exists():
    zip_path.unlink()
shutil.make_archive(str(zip_path).replace('.zip',''), 'zip', output_dir)
print(f"Zip: {zip_path} {zip_path.stat().st_size/1024/1024:.1f} MB")

report = {
    "version": "17.00-GDRIVE-50-FULL-FAST",
    "total_files": len(results),
    "korg_pass": korg_pass,
    "korg_fail": korg_fail,
    "pass_rate": f"{korg_pass}/50 ({100*korg_pass/50:.1f}%)",
    "notes_before": total_before,
    "notes_after": total_after,
    "elapsed": elapsed,
    "output_dir": str(output_dir),
    "zip": str(zip_path),
    "files": [r.get("file", Path(r.get("path","")).name) for r in results[:10]]
}

Path("calibration/gdrive_50_full_optimized_report_17.00.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
print(f"Report: calibration/gdrive_50_full_optimized_report_17.00.json")
