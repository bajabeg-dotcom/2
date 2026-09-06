#!/usr/bin/env python3
"""
Factory 19-20 REAL - lower threshold to 2 instances
"""

import json
from pathlib import Path

CALIBRATION_DIR = Path("calibration")
DATA_DIR = Path("data")

def load_json(p):
    if p.exists():
        try:
            return json.loads(p.read_text(encoding='utf-8'))
        except:
            return {}
    return {}

detailed = load_json(CALIBRATION_DIR / "factory_16_roles_detailed_REAL.json")
print(f"Detailed roles: {len(detailed.get('roles',{}))}")

# Load all_channels from previous run
# Re-run quick analysis for all roles with threshold 2
import mido
from collections import defaultdict, Counter
import math

WORKSPACE_STYLES = Path("prism-uploads/Workspace_Styles")
factory_files = list(WORKSPACE_STYLES.rglob("*.mid"))
print(f"Factory files: {len(factory_files)}")

all_channels = []

for mid_path in factory_files:
    try:
        mid = mido.MidiFile(str(mid_path))
        notes_by_channel = defaultdict(list)
        for track_idx, track in enumerate(mid.tracks):
            tick = 0
            for msg in track:
                tick += msg.time
                if msg.type == 'note_on' and msg.velocity > 0:
                    notes_by_channel[msg.channel].append({
                        "pitch": msg.note,
                        "velocity": msg.velocity,
                        "tick": tick,
                        "channel": msg.channel
                    })
        
        for ch, ch_notes in notes_by_channel.items():
            if len(ch_notes) < 3:
                continue
            min_p = min(n["pitch"] for n in ch_notes)
            max_p = max(n["pitch"] for n in ch_notes)
            avg_p = sum(n["pitch"] for n in ch_notes)/len(ch_notes)
            pitch_range = max_p - min_p
            by_tick = defaultdict(list)
            for n in ch_notes:
                by_tick[n["tick"]].append(n)
            max_poly = max(len(v) for v in by_tick.values()) if by_tick else 0
            total_ticks = max(n["tick"] for n in ch_notes) - min(n["tick"] for n in ch_notes) if ch_notes else 1920
            bars = max(1, total_ticks/1920)
            density = len(ch_notes)/bars
            avg_vel = sum(n["velocity"] for n in ch_notes)/len(ch_notes)
            
            role = "unknown"
            if max_p < 50 and avg_p < 45:
                role = "bass"
            elif ch == 9:
                role = "drums"
            elif max_poly >= 3 and max_poly <= 6 and avg_p > 60 and avg_p < 80 and pitch_range > 20 and density > 3:
                role = "piano"
            elif avg_p > 75 and density < 2.5 and max_poly >= 2 and pitch_range > 15:
                role = "strings"
            elif avg_p > 55 and avg_p < 75 and avg_vel > 88 and max_poly <= 3 and density < 4:
                role = "brass"
            elif max_poly <= 2 and avg_p > 65 and avg_p < 85 and pitch_range > 10 and pitch_range < 25 and avg_vel < 95:
                role = "woodwind"
            elif max_poly <= 2 and avg_p > 60 and avg_p < 80 and pitch_range > 12 and density > 2 and density < 5:
                role = "sax"
            elif avg_p > 55 and avg_p < 75 and max_poly >= 2 and max_poly <= 4 and density > 2 and avg_vel >= 60 and avg_vel <= 90:
                if avg_p < 65 and max_poly >= 3:
                    role = "organ"
                elif avg_p >= 60 and avg_p <= 75:
                    role = "accordion"
                else:
                    role = "guitar"
            elif avg_p > 40 and avg_p < 65 and max_poly >= 3 and density > 2:
                role = "organ"
            elif avg_p > 65 and avg_vel < 70 and density < 2 and max_poly >= 2:
                role = "pad"
            elif avg_p > 60 and avg_p < 80 and avg_vel < 75 and max_poly >= 3:
                role = "choir"
            elif avg_p > 55 and avg_p < 75 and max_poly >= 2 and max_poly <= 4 and density > 3:
                role = "guitar"
            elif avg_p > 50 and avg_p < 70 and max_poly >= 2 and max_poly <= 4:
                role = "rhythm-guitar"
            elif max_poly == 2:
                role = "riff"
            elif max_poly == 3 and avg_p < 60 and avg_vel > 85:
                role = "power-riff"
            elif max_poly <= 1 and pitch_range > 20 and avg_p > 65:
                role = "lead" if avg_vel > 95 else "melody"
            elif max_poly <= 1 and pitch_range > 24 and avg_vel > 100:
                role = "solo"
            elif max_poly <= 1 and density > 4 and avg_p > 60:
                role = "terca"
            elif max_poly <= 1 and pitch_range > 12:
                role = "melody"
            else:
                role = "accompaniment"
            
            all_channels.append({
                "role": role,
                "notes": len(ch_notes),
                "avg_p": avg_p,
                "max_poly": max_poly,
                "density": density,
                "avg_vel": avg_vel
            })
    except:
        pass

role_counts = Counter(c["role"] for c in all_channels)
print(f"\nRole counts (threshold 3 notes):")
for role, count in role_counts.most_common():
    total_notes = sum(c["notes"] for c in all_channels if c["role"] == role)
    print(f"   {role:20s}: {count:4d} instances {total_notes:6d} notes")

# REAL with threshold 2
real_roles_2 = {}
for role, count in role_counts.items():
    if count >= 2:
        total_notes = sum(c["notes"] for c in all_channels if c["role"] == role)
        real_roles_2[role] = {
            "channel_instances": count,
            "notes": total_notes,
            "real": True,
            "threshold": 2
        }

print(f"\nREAL roles threshold >=2: {len(real_roles_2)}")
for role, data in sorted(real_roles_2.items(), key=lambda x: x[1]["notes"], reverse=True):
    print(f"   {role:20s}: {data['channel_instances']:4d} inst {data['notes']:6d} notes REAL")

# REAL with threshold 1
real_roles_1 = {}
for role, count in role_counts.items():
    if count >= 1:
        total_notes = sum(c["notes"] for c in all_channels if c["role"] == role)
        real_roles_1[role] = {
            "channel_instances": count,
            "notes": total_notes,
            "real": True,
            "threshold": 1
        }

print(f"\nREAL roles threshold >=1: {len(real_roles_1)}")
for role, data in sorted(real_roles_1.items(), key=lambda x: x[1]["notes"], reverse=True):
    print(f"   {role:20s}: {data['channel_instances']:4d} inst {data['notes']:6d} notes REAL")

# Save 19 REAL (threshold 2)
output_19 = {
    "version": "17.00-FACTORY-19-ROLES-REAL",
    "total_files": len(factory_files),
    "total_channel_instances": len(all_channels),
    "total_notes": sum(c["notes"] for c in all_channels),
    "roles": real_roles_2,
    "role_counts": dict(role_counts),
    "threshold": 2
}

output_path_19 = DATA_DIR / "factory-velocity-profiles-19-roles-REAL-1113.json"
output_path_19.write_text(json.dumps(output_19, indent=2, ensure_ascii=False), encoding='utf-8')
print(f"\n✅ Factory 19 REAL threshold 2: {output_path_19}")

# Save 20 REAL (threshold 1)
output_20 = {
    "version": "17.00-FACTORY-20-ROLES-REAL",
    "total_files": len(factory_files),
    "total_channel_instances": len(all_channels),
    "total_notes": sum(c["notes"] for c in all_channels),
    "roles": real_roles_1,
    "role_counts": dict(role_counts),
    "threshold": 1
}

output_path_20 = DATA_DIR / "factory-velocity-profiles-20-roles-REAL-1113.json"
output_path_20.write_text(json.dumps(output_20, indent=2, ensure_ascii=False), encoding='utf-8')
print(f"✅ Factory 20 REAL threshold 1: {output_path_20}")
