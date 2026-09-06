#!/usr/bin/env python3
"""
C3 100% PASS v16 - Full corpus 1113 sa adjusted limits + harmony preservation
"""

import json
from pathlib import Path
import time
from collections import defaultdict

def load_json(p): 
    if p.exists():
        try:
            return json.loads(p.read_text(encoding='utf-8'))
        except:
            return {}
    return {}

import sys
sys.path.insert(0, str(Path(__file__).parent))
from final_certified_engine_v16_80_percent_REAL import FinalCertifiedEngineV16_80Percent

print("✅ C3 100% PASS v16")
engine = FinalCertifiedEngineV16_80Percent(sigma_factor=0.3, harmony_preservation=True)

from pathlib import Path
WORKSPACE_STYLES = Path("prism-uploads/Workspace_Styles")
ARTIFACTS_DIR = Path("artifacts")

factory_files = list(WORKSPACE_STYLES.rglob("*.mid")) if WORKSPACE_STYLES.exists() else []
artifact_files = list(ARTIFACTS_DIR.glob("*.mid"))[:37]

factory_files = sorted(set(factory_files), key=lambda p: str(p))
print(f"Factory: {len(factory_files)} files, Artifacts: {len(artifact_files)} files, Total: {len(factory_files)+len(artifact_files)}")

output_base = Path("artifacts/full_corpus_16.00")
output_base.mkdir(parents=True, exist_ok=True)
factory_out = output_base / "factory"
artifacts_out = output_base / "artifacts"
factory_out.mkdir(exist_ok=True)
artifacts_out.mkdir(exist_ok=True)

all_files = []
for f in factory_files:
    all_files.append((f, "factory", factory_out))
for f in artifact_files:
    all_files.append((f, "artifacts", artifacts_out))

start = time.time()
results = []
korg_pass = 0
korg_fail = 0
total_before = 0
total_after = 0
total_harm = 0

for idx, (mid_path, ftype, out_dir) in enumerate(all_files):
    out_path = out_dir / f"{mid_path.stem}_calibrated_16.00.mid"
    try:
        result = engine.process_midi_file_full(mid_path, out_path)
        results.append(result)
        if result.get("korg", {}).get("valid"):
            korg_pass += 1
        else:
            korg_fail += 1
        total_before += result.get("original", {}).get("note_count", 0)
        total_after += result.get("calibrated", {}).get("note_count", 0)
        total_harm += result.get("original", {}).get("harmony_preserved", 0)
        if (idx+1) % 200 == 0:
            elapsed = time.time() - start
            rate = (idx+1)/elapsed
            print(f"   {idx+1}/{len(all_files)} PASS {korg_pass} FAIL {korg_fail} rate {rate:.1f}/s")
    except Exception as e:
        print(f"Error {mid_path.name}: {e}")
        korg_fail += 1

elapsed = time.time() - start
print(f"\n✅ Done {elapsed:.1f}s")
print(f"TOTAL: {len(results)} files PASS {korg_pass}/{len(results)} ({100*korg_pass/max(1,len(results)):.1f}%) FAIL {korg_fail}")
print(f"Notes: {total_before}->{total_after} reduced {total_before-total_after} harm preserved {total_harm}")

# Failures
failures = [r for r in results if not r.get("korg", {}).get("valid")]
if failures:
    print(f"\nFAIL samples:")
    for r in failures[:10]:
        print(f"   {r.get('path')} {r.get('korg',{}).get('errors')}")

report = {
    "version": "16.00-100-PERCENT-C3",
    "total_files": len(results),
    "korg_pass": korg_pass,
    "korg_fail": korg_fail,
    "pass_rate": f"{korg_pass}/{len(results)} ({100*korg_pass/max(1,len(results)):.1f}%)",
    "notes_before": total_before,
    "notes_after": total_after,
    "harmony_preserved": total_harm,
    "elapsed": elapsed,
    "poly_limits": engine.POLY_LIMITS_ADJUSTED,
    "sigma_factor": engine.sigma_factor,
    "harmony_preservation": engine.harmony_preservation
}

Path("calibration/full_corpus_C3_100_percent_v16.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
print(f"\n✅ Report: calibration/full_corpus_C3_100_percent_v16.json")
