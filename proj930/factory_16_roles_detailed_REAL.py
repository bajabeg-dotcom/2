#!/usr/bin/env python3
"""
Factory 16 REAL detailed - poboljšana klasifikacija da se dobije brass, woodwind, accordion, organ REAL
"""

import json
import mido
from pathlib import Path
from collections import defaultdict, Counter
import math

WORKSPACE_STYLES = Path("prism-uploads/Workspace_Styles")
CALIBRATION_DIR = Path("calibration")
DATA_DIR = Path("data")

def load_json(p):
    if p.exists():
        try:
            return json.loads(p.read_text(encoding='utf-8'))
        except:
            return {}
    return {}

factory_files = list(WORKSPACE_STYLES.rglob("*.mid"))
print(f"Factory files: {len(factory_files)}")

# Extract notes per channel per file with more detailed features
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
                        "channel": msg.channel,
                        "track": track_idx
                    })
        
        for ch, ch_notes in notes_by_channel.items():
            if len(ch_notes) < 5:
                continue
            min_p = min(n["pitch"] for n in ch_notes)
            max_p = max(n["pitch"] for n in ch_notes)
            avg_p = sum(n["pitch"] for n in ch_notes)/len(ch_notes)
            pitch_range = max_p - min_p
            by_tick = defaultdict(list)
            for n in ch_notes:
                by_tick[n["tick"]].append(n)
            max_poly = max(len(v) for v in by_tick.values()) if by_tick else 0
            avg_poly = sum(len(v) for v in by_tick.values())/len(by_tick) if by_tick else 0
            total_ticks = max(n["tick"] for n in ch_notes) - min(n["tick"] for n in ch_notes) if ch_notes else 1920
            bars = max(1, total_ticks/1920)
            density = len(ch_notes)/bars
            avg_vel = sum(n["velocity"] for n in ch_notes)/len(ch_notes)
            vel_std = math.sqrt(sum((n["velocity"]-avg_vel)**2 for n in ch_notes)/len(ch_notes)) if len(ch_notes)>1 else 0
            vel_range = max(n["velocity"] for n in ch_notes) - min(n["velocity"] for n in ch_notes)
            
            # More detailed classification
            # Brass: avg pitch 55-75, vel >90, max_poly <=3, density <4, vel_std low
            # Woodwind: avg 65-85, pitch_range 10-25, max_poly <=2, vel <95
            # Accordion: avg 55-75, max_poly 2-4, density >2, vel 60-90
            # Organ: avg 40-65, max_poly >=3, density >2, avg_vel 60-90
            
            role = "unknown"
            if max_p < 50 and avg_p < 45:
                role = "bass"
            elif ch == 9:
                role = "drums"
            elif max_poly >= 3 and max_poly <= 6 and avg_p > 60 and avg_p < 80 and pitch_range > 20 and density > 3:
                role = "piano"
            elif avg_p > 75 and density < 2.5 and max_poly >= 2 and pitch_range > 15:
                role = "strings"
            elif avg_p > 55 and avg_p < 75 and avg_vel > 88 and max_poly <= 3 and density < 4 and vel_std < 15:
                role = "brass"  # improved brass detection
            elif max_poly <= 2 and avg_p > 65 and avg_p < 85 and pitch_range > 10 and pitch_range < 25 and avg_vel < 95 and vel_std < 20:
                role = "woodwind"  # improved woodwind
            elif max_poly <= 2 and avg_p > 60 and avg_p < 80 and pitch_range > 12 and density > 2 and density < 5:
                role = "sax"
            elif avg_p > 55 and avg_p < 75 and max_poly >= 2 and max_poly <= 4 and density > 2 and avg_vel >= 60 and avg_vel <= 90 and pitch_range > 10:
                # Distinguish accordion vs guitar vs organ by pitch and velocity
                if avg_p < 65 and max_poly >= 3:
                    role = "organ"  # organ lower pitch, higher poly
                elif avg_p >= 60 and avg_p <= 75 and vel_range < 30:
                    role = "accordion"  # accordion more stable velocity
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
            elif max_poly == 2 and len(by_tick) > 0 and sum(1 for v in by_tick.values() if len(v)>1)/len(by_tick) < 0.3:
                role = "riff"
            elif max_poly == 3 and avg_p < 60 and avg_vel > 85:
                role = "power-riff"
            elif max_poly <= 1 and pitch_range > 20 and avg_p > 65:
                if avg_vel > 95:
                    role = "lead"
                else:
                    role = "melody"
            elif max_poly <= 1 and pitch_range > 24 and avg_vel > 100:
                role = "solo"
            elif max_poly <= 1 and density > 4 and avg_p > 60:
                role = "terca"
            elif max_poly <= 1 and pitch_range > 12:
                role = "melody"
            else:
                role = "accompaniment"
            
            all_channels.append({
                "file": mid_path.name,
                "channel": ch,
                "role": role,
                "notes": len(ch_notes),
                "min_p": min_p,
                "max_p": max_p,
                "avg_p": avg_p,
                "pitch_range": pitch_range,
                "max_poly": max_poly,
                "avg_poly": avg_poly,
                "density": density,
                "avg_vel": avg_vel,
                "vel_std": vel_std,
                "vel_range": vel_range
            })
    except Exception as e:
        print(f"Error {mid_path.name}: {e}")

print(f"Total channel instances: {len(all_channels)}")

# Count by role
role_counts = Counter(c["role"] for c in all_channels)
print(f"\nRole counts detailed:")
for role, count in role_counts.most_common():
    total_notes = sum(c["notes"] for c in all_channels if c["role"] == role)
    print(f"   {role:20s}: {count:4d} instances {total_notes:6d} notes")

# Group by role and calculate velocity profiles
roles_data = defaultdict(list)
for c in all_channels:
    roles_data[c["role"]].append(c)

# Build REAL profiles for roles with enough instances
real_roles = {}
for role, instances in roles_data.items():
    if len(instances) >= 10:  # at least 10 instances to be REAL
        total_notes = sum(c["notes"] for c in instances)
        avg_vel = sum(c["avg_vel"] for c in instances)/len(instances)
        # Collect all velocities
        # For simplicity, use avg_vel and vel_range from instances
        real_roles[role] = {
            "channel_instances": len(instances),
            "notes": total_notes,
            "velocity": {
                "avg": avg_vel,
                "instances": len(instances)
            },
            "real": True
        }

print(f"\nREAL roles (>=10 instances): {len(real_roles)}")
for role, data in sorted(real_roles.items(), key=lambda x: x[1]["notes"], reverse=True):
    print(f"   {role:20s}: {data['channel_instances']:4d} inst {data['notes']:6d} notes REAL")

# Save
output = {
    "version": "16.00-FACTORY-DETAILED-16-ROLES",
    "total_files": len(factory_files),
    "total_channel_instances": len(all_channels),
    "total_notes": sum(c["notes"] for c in all_channels),
    "roles": real_roles,
    "role_counts": dict(role_counts),
    "all_channels": all_channels[:100]  # sample
}

output_path = CALIBRATION_DIR / "factory_16_roles_detailed_REAL.json"
output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding='utf-8')
print(f"\n✅ Factory 16 roles detailed: {output_path}")

# Also update factory-velocity-profiles
# Load existing 13 REAL
existing = load_json(DATA_DIR / "factory-velocity-profiles-20-roles-REAL-3211.json")
print(f"\nExisting 13 REAL: {list(existing.get('roles',{}).keys())}")

# Merge
merged_roles = existing.get("roles", {}).copy()
for role, data in real_roles.items():
    if role not in merged_roles:
        merged_roles[role] = {
            "channel_instances": data["channel_instances"],
            "notes": data["notes"],
            "velocity": data["velocity"],
            "real": True,
            "new": True
        }

print(f"Merged roles: {len(merged_roles)} (was {len(existing.get('roles',{}))})")
new_roles = [r for r in merged_roles.keys() if r not in existing.get("roles",{})]
print(f"New REAL roles: {new_roles}")

# Save merged
merged_output = {
    "version": "16.00-FACTORY-16-ROLES-REAL",
    "total_files": len(factory_files),
    "total_channel_instances": len(all_channels),
    "total_notes": sum(c["notes"] for c in all_channels),
    "roles": merged_roles,
    "authority": "FACTORY REAL 16 roles detailed classification"
}

merged_path = DATA_DIR / "factory-velocity-profiles-16-roles-REAL-1113.json"
merged_path.write_text(json.dumps(merged_output, indent=2, ensure_ascii=False), encoding='utf-8')
print(f"✅ Merged Factory 16 REAL: {merged_path}")
