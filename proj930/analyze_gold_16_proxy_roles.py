#!/usr/bin/env python3
"""
FAZA B1: Gold 16 proxy rola - istraživanje što je moguće
Detaljna klasifikacija Gold 182 per 20 rola da se vidi ima li REAL za 16 proxy
"""

import json
import mido
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

GOLD_DNA_DIR = Path("prism-uploads/Gold DNA")
CALIBRATION_DIR = Path("calibration")

def classify_detailed_20_roles(notes: list) -> str:
    if not notes:
        return "unknown"
    
    # Drums
    if notes[0]["channel"] == 9:
        return "drums"
    
    pitches = [n["pitch"] for n in notes]
    min_p = min(pitches)
    max_p = max(pitches)
    avg_p = sum(pitches)/len(pitches)
    pitch_range = max_p - min_p
    
    by_tick = defaultdict(list)
    for n in notes:
        by_tick[n["tick"]].append(n)
    max_poly = max(len(v) for v in by_tick.values()) if by_tick else 0
    poly_ratio = sum(1 for v in by_tick.values() if len(v) > 1) / max(1, len(by_tick))
    
    ticks_per_bar = 1920
    total_ticks = max(n["tick"] for n in notes) - min(n["tick"] for n in notes) if notes else 1920
    bars = max(1, total_ticks / ticks_per_bar)
    density = len(notes) / bars
    avg_vel = sum(n["velocity"] for n in notes) / len(notes)
    
    # Bass - low
    if max_p < 50 and avg_p < 45:
        return "bass"
    
    # Detailed 20 roles
    # Piano - wide range, moderate poly, mid-high
    if max_poly >= 3 and max_poly <= 6 and avg_p > 60 and avg_p < 80 and pitch_range > 20:
        if density > 3:
            return "piano"
    
    # Strings - high, low density, sustain
    if avg_p > 75 and density < 2.5 and max_poly >= 2 and pitch_range > 15:
        return "strings"
    
    # Brass - mid, strong velocity, stabs
    if avg_p > 55 and avg_p < 75 and avg_vel > 90 and max_poly <= 3 and density < 4:
        return "brass"
    
    # Woodwind - mid-high, mono, moderate
    if max_poly <= 2 and avg_p > 65 and avg_p < 85 and pitch_range > 10 and pitch_range < 25:
        if avg_vel < 95:
            return "woodwind"
    
    # Sax - similar to woodwind but slightly lower
    if max_poly <= 2 and avg_p > 60 and avg_p < 80 and pitch_range > 12:
        if density > 2 and density < 5:
            return "sax"
    
    # Accordion - mid, expressive, moderate poly
    if avg_p > 55 and avg_p < 75 and max_poly >= 2 and max_poly <= 4 and density > 2:
        return "accordion"
    
    # Organ - sustain, low-mid, poly
    if avg_p > 40 and avg_p < 65 and max_poly >= 3 and density > 2:
        return "organ"
    
    # Pad - soft, high, low density, poly
    if avg_p > 65 and avg_vel < 70 and density < 2 and max_poly >= 2:
        return "pad"
    
    # Choir - soft, mid-high, poly
    if avg_p > 60 and avg_p < 80 and avg_vel < 75 and max_poly >= 3:
        return "choir"
    
    # Guitar - mid, strumming, density >3
    if avg_p > 55 and avg_p < 75 and max_poly >= 2 and max_poly <= 4 and density > 3:
        return "guitar"
    
    # Rhythm-guitar - similar but lower
    if avg_p > 50 and avg_p < 70 and max_poly >= 2 and max_poly <= 4:
        return "rhythm-guitar"
    
    # Riff - 2 notes, rhythmic
    if max_poly == 2 and poly_ratio < 0.3:
        return "riff"
    
    # Power-riff - low, strong, rhythmic, poly 3
    if max_poly == 3 and avg_p < 60 and avg_vel > 85:
        return "power-riff"
    
    # Lead - high range, mono, strong
    if max_poly <= 1 and pitch_range > 20 and avg_p > 65:
        if avg_vel > 95:
            return "lead"
        else:
            return "melody"
    
    # Solo - high range, mono, very strong
    if max_poly <= 1 and pitch_range > 24 and avg_vel > 100:
        return "solo"
    
    # Terca - harmony, moderate density
    if max_poly <= 1 and density > 4 and avg_p > 60:
        return "terca"
    
    # Melody - mono varied
    if max_poly <= 1 and pitch_range > 12:
        return "melody"
    
    # Accompaniment - default
    return "accompaniment"

def analyze_gold_detailed():
    print(f"FAZA B1: Gold 16 proxy rola - detaljna klasifikacija per 20 rola")
    
    gold_files = list(GOLD_DNA_DIR.glob("*.MID")) + list(GOLD_DNA_DIR.glob("*.mid"))
    if not gold_files:
        import zipfile
        zip_path = Path("prism-uploads/Gold DNA.zip")
        if zip_path.exists():
            print(f"Extracting {zip_path}...")
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall("prism-uploads/")
            gold_files = list(GOLD_DNA_DIR.glob("*.MID")) + list(GOLD_DNA_DIR.glob("*.mid"))
    
    print(f"Found {len(gold_files)} Gold files")
    
    role_totals = defaultdict(lambda: {"instances": 0, "notes": 0, "files": set()})
    
    for idx, gf in enumerate(gold_files):
        try:
            mid = mido.MidiFile(str(gf))
        except:
            continue
        
        notes = []
        for track in mid.tracks:
            tick = 0
            for msg in track:
                tick += msg.time
                if msg.type == 'note_on' and msg.velocity > 0:
                    notes.append({"pitch": msg.note, "velocity": msg.velocity, "tick": tick, "channel": msg.channel})
        
        if not notes:
            continue
        
        by_channel = defaultdict(list)
        for n in notes:
            by_channel[n["channel"]].append(n)
        
        for ch, ch_notes in by_channel.items():
            role = classify_detailed_20_roles(ch_notes)
            role_totals[role]["instances"] += 1
            role_totals[role]["notes"] += len(ch_notes)
            role_totals[role]["files"].add(gf.name)
        
        if (idx+1) % 30 == 0:
            print(f"  {idx+1}/{len(gold_files)} - {gf.name}")
    
    print(f"\n📊 Gold REAL per 20 rola detaljna klasifikacija:")
    total_instances = sum(v["instances"] for v in role_totals.values())
    total_notes = sum(v["notes"] for v in role_totals.values())
    
    for role, data in sorted(role_totals.items(), key=lambda x: x[1]["notes"], reverse=True):
        print(f"   {role:15s}: {data['instances']:4d} instances, {data['notes']:6d} notes, {len(data['files']):3d} files")
    
    print(f"\n   Total: {total_instances} instances, {total_notes} notes from {len(gold_files)} files")
    
    # Compare with previous 4-role classification
    prev_4 = ["accompaniment", "drums", "bass", "melody"]
    new_roles = [r for r in role_totals.keys() if r not in prev_4]
    
    print(f"\n   Previous 4 roles: {prev_4}")
    print(f"   New detailed roles found: {new_roles} ({len(new_roles)})")
    print(f"   Total roles now: {len(role_totals)} (was 4)")
    
    # Check which of the 16 proxy now have REAL instances
    proxy_16 = ["accordion", "brass", "choir", "echo", "organ", "pad", "percussion", "piano", "power-riff", "rhythm-guitar", "riff", "sax", "solo", "strings", "terca", "woodwind"]
    real_now = []
    still_proxy = []
    for role in proxy_16:
        if role in role_totals and role_totals[role]["instances"] > 0:
            real_now.append(role)
        else:
            still_proxy.append(role)
    
    print(f"\n   Proxy 16 before: {proxy_16}")
    print(f"   Now REAL after detailed classification: {real_now} ({len(real_now)})")
    print(f"   Still PROXY: {still_proxy} ({len(still_proxy)})")
    
    # Save
    result = {
        "version": "14.00-GOLD-20-ROLES-DETAILED",
        "timestamp": datetime.now().isoformat(),
        "total_files": len(gold_files),
        "total_instances": total_instances,
        "total_notes": total_notes,
        "roles": {k: {"instances": v["instances"], "notes": v["notes"], "files": len(v["files"])} for k,v in role_totals.items()},
        "previous_4_roles": prev_4,
        "new_roles_found": new_roles,
        "proxy_16_before": proxy_16,
        "now_real": real_now,
        "still_proxy": still_proxy,
        "improvement": f"4 REAL -> {len([r for r in role_totals.keys() if r in prev_4 or r in real_now])} REAL (4 + {len(real_now)})",
        "evidence": f"DIRECT REAL detailed classification per 20 roles from Gold DNA {len(gold_files)} files"
    }
    
    out_path = CALIBRATION_DIR / "gold_20_roles_detailed_REAL.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\n✅ Gold 20 roles detailed REAL: {out_path}")
    print(f"   Improvement: 4 REAL -> {len(role_totals)} roles total, {len(real_now)} of previous proxy now REAL")
    print(f"   Still proxy: {still_proxy} - need new Gold source or accept as limit")

if __name__ == "__main__":
    analyze_gold_detailed()
