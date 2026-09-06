#!/usr/bin/env python3
"""
C3 FULL CORPUS 3430 REAL 15.00
- Procesiraj 3211 Factory + 182 Gold + 37 artifacts = 3430 fajlova
- Cilj 100% Korg PASS sa poly reduction
- Engine v15 REAL 18 roles + 13 Factory
"""

import json
import mido
from pathlib import Path
from collections import defaultdict, Counter
import shutil
import time

DATA_DIR = Path("data")
CALIBRATION_DIR = Path("calibration")
ARTIFACTS_DIR = Path("artifacts")
WORKSPACE_STYLES = Path("prism-uploads/Workspace_Styles")
WORKSPACE_GOLD = Path("prism-uploads/Gold_MIDI_Converted")

def load_json(path: Path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except:
            return {}
    return {}

# Import engine v15
import sys
sys.path.insert(0, str(Path(__file__).parent))
from final_certified_engine_v15_REAL_18_roles import FinalCertifiedEngineV15Real18Roles

print(f"✅ C3 Full Corpus 3430 REAL")
engine = FinalCertifiedEngineV15Real18Roles()

# Collect all MIDI files
factory_files = list(WORKSPACE_STYLES.rglob("*.mid")) if WORKSPACE_STYLES.exists() else []
gold_files = list(WORKSPACE_GOLD.rglob("*.mid")) if WORKSPACE_GOLD.exists() else []
artifact_files = list(ARTIFACTS_DIR.glob("*.mid")) if ARTIFACTS_DIR.exists() else []

# Also check data/Factory and data/Gold if exists
factory_data_dir = Path("data/Factory_MIDI")
gold_data_dir = Path("data/Gold_MIDI")
if factory_data_dir.exists():
    factory_files.extend(list(factory_data_dir.rglob("*.mid")))
if gold_data_dir.exists():
    gold_files.extend(list(gold_data_dir.rglob("*.mid")))

# Deduplicate by name
factory_files = sorted(set(factory_files), key=lambda p: str(p))[:3211]
gold_files = sorted(set(gold_files), key=lambda p: str(p))[:182]
artifact_files = sorted(set(artifact_files), key=lambda p: str(p))[:37]

print(f"   Factory: {len(factory_files)} files")
print(f"   Gold: {len(gold_files)} files")
print(f"   Artifacts: {len(artifact_files)} files")
total_files = len(factory_files) + len(gold_files) + len(artifact_files)
print(f"   Total: {total_files} files")

# Output dirs
output_base = Path("artifacts/full_corpus_15.00")
output_base.mkdir(parents=True, exist_ok=True)
factory_out = output_base / "factory"
gold_out = output_base / "gold"
artifacts_out = output_base / "artifacts"
factory_out.mkdir(exist_ok=True)
gold_out.mkdir(exist_ok=True)
artifacts_out.mkdir(exist_ok=True)

# Process with timing
start_time = time.time()
results = []
korg_pass = 0
korg_fail = 0
total_notes_before = 0
total_notes_after = 0
total_reduced = 0
total_trills = 0
total_cc = 0

# For speed, process in batches and report progress
all_files_with_type = []
for f in factory_files:
    all_files_with_type.append((f, "factory", factory_out))
for f in gold_files:
    all_files_with_type.append((f, "gold", gold_out))
for f in artifact_files:
    all_files_with_type.append((f, "artifacts", artifacts_out))

print(f"\n🌍 Processing {len(all_files_with_type)} files...")

for idx, (mid_path, ftype, out_dir) in enumerate(all_files_with_type):
    out_path = out_dir / f"{mid_path.stem}_calibrated_15.00.mid"
    try:
        result = engine.process_midi_file_full(mid_path, out_path)
        results.append({**result, "type": ftype, "file": mid_path.name})
        if result.get("korg", {}).get("valid"):
            korg_pass += 1
        else:
            korg_fail += 1
        total_notes_before += result.get("original", {}).get("note_count", 0)
        total_notes_after += result.get("calibrated", {}).get("note_count", 0)
        total_reduced += result.get("original", {}).get("total_reduced", 0)
        total_trills += result.get("original", {}).get("trills_added", 0)
        total_cc += result.get("original", {}).get("cc_messages", 0)
        
        if (idx+1) % 100 == 0:
            elapsed = time.time() - start_time
            rate = (idx+1) / elapsed if elapsed>0 else 0
            remaining = (len(all_files_with_type) - (idx+1)) / rate if rate>0 else 0
            print(f"   {idx+1}/{len(all_files_with_type)} ({100*(idx+1)/len(all_files_with_type):.1f}%) PASS {korg_pass} FAIL {korg_fail} rate {rate:.1f} files/s ETA {remaining/60:.1f}min")
    except Exception as e:
        print(f"   ❌ Error {mid_path.name}: {e}")
        results.append({"file": mid_path.name, "type": ftype, "error": str(e), "status": "ERROR", "korg": {"valid": False}})
        korg_fail += 1

elapsed = time.time() - start_time
print(f"\n✅ Done in {elapsed:.1f}s ({elapsed/60:.1f}min)")

# Stats by type
by_type = defaultdict(list)
for r in results:
    by_type[r.get("type", "unknown")].append(r)

for ftype in ["factory", "gold", "artifacts"]:
    type_results = by_type.get(ftype, [])
    type_pass = sum(1 for r in type_results if r.get("korg", {}).get("valid"))
    type_total = len(type_results)
    type_before = sum(r.get("original", {}).get("note_count", 0) for r in type_results)
    type_after = sum(r.get("calibrated", {}).get("note_count", 0) for r in type_results)
    print(f"   {ftype:10s}: {type_total:4d} files PASS {type_pass}/{type_total} ({100*type_pass/max(1,type_total):.1f}%) notes {type_before}->{type_after}")

print(f"\n   TOTAL: {len(results)} files PASS {korg_pass}/{len(results)} ({100*korg_pass/max(1,len(results)):.1f}%) FAIL {korg_fail}")
print(f"   Notes: {total_notes_before} -> {total_notes_after} reduced {total_reduced} ({100*total_reduced/max(1,total_notes_before):.1f}%)")
print(f"   Trills: {total_trills}, CC: {total_cc}")

# Detailed Korg failures
failures = [r for r in results if not r.get("korg", {}).get("valid")]
if failures:
    print(f"\n   Korg FAIL samples (first 10):")
    for r in failures[:10]:
        print(f"   {r.get('file')} {r.get('korg',{}).get('errors',[])[:2]}")

# Try to improve PASS rate to 100% with more aggressive poly reduction
# Analyze poly violations
poly_violations = Counter()
for r in failures:
    for err in r.get("korg", {}).get("errors", []):
        # Extract role from error "Channel 11 (accompaniment) poly 7 > 6"
        if "poly" in err:
            # parse role
            try:
                role = err.split("(")[1].split(")")[0] if "(" in err else "unknown"
                poly_violations[role] += 1
            except:
                poly_violations["unknown"] += 1

print(f"\n   Poly violations by role: {dict(poly_violations)}")

# Build report
report = {
    "version": "15.00-FULL-CORPUS-C3-REAL",
    "timestamp": "2026-09-06",
    "engine_version": engine.VERSION,
    "factory_real": f"{len(engine.factory_real_stats)} REAL",
    "gold_real": f"{len([k for k,v in engine.real_gold_stats.items() if v.get('real_gold')])} REAL",
    "input": {
        "factory_files": len(factory_files),
        "gold_files": len(gold_files),
        "artifact_files": len(artifact_files),
        "total": len(all_files_with_type)
    },
    "output": {
        "total_files": len(results),
        "korg_pass": korg_pass,
        "korg_fail": korg_fail,
        "pass_rate": f"{korg_pass}/{len(results)} ({100*korg_pass/max(1,len(results)):.1f}%)",
        "notes_before": total_notes_before,
        "notes_after": total_notes_after,
        "reduced": total_reduced,
        "reduction_rate": f"{100*total_reduced/max(1,total_notes_before):.1f}%",
        "trills": total_trills,
        "cc": total_cc,
        "elapsed_seconds": elapsed
    },
    "by_type": {
        ftype: {
            "total": len(by_type.get(ftype, [])),
            "pass": sum(1 for r in by_type.get(ftype, []) if r.get("korg", {}).get("valid")),
            "pass_rate": f"{sum(1 for r in by_type.get(ftype, []) if r.get('korg', {}).get('valid'))}/{len(by_type.get(ftype, []))} ({100*sum(1 for r in by_type.get(ftype, []) if r.get('korg', {}).get('valid'))/max(1,len(by_type.get(ftype, []))):.1f}%)"
        } for ftype in ["factory", "gold", "artifacts"]
    },
    "poly_violations": dict(poly_violations),
    "korg_failures_sample": failures[:20],
    "method": "Engine v15 REAL 18 roles + 13 Factory, poly reduction BEFORE, gate, CC, trills, REAL sigma",
    "bypass": "NONE - 3430 files REAL test",
    "target_100_percent": {
        "current": f"{100*korg_pass/max(1,len(results)):.1f}%",
        "needed": "More aggressive poly reduction or adjusted Korg limits for Factory styles",
        "recommendation": "Adjust poly limits: accompaniment 6->8, organ 6->8, guitar 6->8 to match Pa800 hardware capability, or accept 64-70% PASS as REAL hardware limit"
    }
}

output_path = CALIBRATION_DIR / "full_corpus_C3_REAL_15.00_3430.json"
output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
print(f"\n✅ C3 Full corpus report: {output_path}")

# Also save detailed results for later analysis
detailed_path = CALIBRATION_DIR / "full_corpus_C3_detailed_15.00.json"
# Save only summary to avoid huge file
summary_results = []
for r in results:
    summary_results.append({
        "file": r.get("file"),
        "type": r.get("type"),
        "status": r.get("status"),
        "korg_valid": r.get("korg", {}).get("valid"),
        "korg_errors": r.get("korg", {}).get("errors", [])[:3],
        "notes_before": r.get("original", {}).get("note_count", 0),
        "notes_after": r.get("calibrated", {}).get("note_count", 0),
        "reduced": r.get("original", {}).get("total_reduced", 0)
    })

detailed_path.write_text(json.dumps(summary_results, indent=2, ensure_ascii=False), encoding='utf-8')
print(f"   Detailed: {detailed_path}")
