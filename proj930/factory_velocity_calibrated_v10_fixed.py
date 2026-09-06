#!/usr/bin/env python3
"""
FACTORY VELOCITY CALIBRATION 10.01 - FIXED - SVIH 20 ROLA
Popravlja mapiranje 4 Factory role (drums, chords, melody, bass) na 20 instrument rola
"""

import json
import math
from pathlib import Path
from collections import defaultdict
from datetime import datetime

DATA_DIR = Path(__file__).parent / "data"
CALIBRATION_DIR = Path(__file__).parent / "calibration"

# Direct Factory authority only. Roles without their own Factory evidence are
# reported as unresolved instead of borrowing another instrument's curve.
FACTORY_TO_INSTRUMENT_MAP = {
    "bass": ["bass"],
    "drums": ["drums"],
    "melody": ["melody"],
    "chords": ["chords"],
}

# Default velocity adjustments per instrument family (from general-rules + musical knowledge)
INSTRUMENT_VELOCITY_ADJUSTMENTS = {
    "bass": {"floor": 65, "optimal": 105, "ceiling": 127, "reason": "Bass mora biti čujan, ispod 65 gubi definiciju"},
    "drums": {"floor": 30, "optimal": 97, "ceiling": 127, "reason": "Drums full range"},
    "percussion": {"floor": 25, "optimal": 75, "ceiling": 110, "reason": "Percussion color"},
    "rhythm_guitar": {"floor": 35, "optimal": 85, "ceiling": 120, "reason": "Rhythm guitar needs attack"},
    "solo_guitar": {"floor": 40, "optimal": 90, "ceiling": 127, "reason": "Solo must cut through"},
    "piano": {"floor": 20, "optimal": 80, "ceiling": 127, "reason": "Piano widest dynamics"},
    "organ": {"floor": 50, "optimal": 85, "ceiling": 127, "reason": "Organ no dynamics per se, volume is expression"},
    "accordion": {"floor": 40, "optimal": 85, "ceiling": 120, "reason": "Accordion bellows"},
    "strings": {"floor": 25, "optimal": 80, "ceiling": 120, "reason": "Strings sul pont to fortissimo"},
    "brass": {"floor": 50, "optimal": 95, "ceiling": 127, "reason": "Brass needs air, below 50 no tone"},
    "sax": {"floor": 40, "optimal": 85, "ceiling": 120, "reason": "Sax needs breath"},
    "woodwind": {"floor": 35, "optimal": 80, "ceiling": 115, "reason": "Woodwind breathy"},
    "clarinet": {"floor": 35, "optimal": 80, "ceiling": 115, "reason": "Clarinet folk ornament"},
    "violin": {"floor": 30, "optimal": 85, "ceiling": 120, "reason": "Violin fiddle"},
    "synth_lead": {"floor": 30, "optimal": 90, "ceiling": 127, "reason": "Synth lead must cut"},
    "pad": {"floor": 20, "optimal": 70, "ceiling": 100, "reason": "Pad sustained bed"},
    "mallet": {"floor": 30, "optimal": 85, "ceiling": 120, "reason": "Mallet clear attack"},
    "choir": {"floor": 30, "optimal": 75, "ceiling": 110, "reason": "Choir vocal texture"},
    "fx": {"floor": 1, "optimal": 80, "ceiling": 127, "reason": "FX no real dynamics"},
    "accompaniment": {"floor": 30, "optimal": 75, "ceiling": 110, "reason": "Accomp support not dominate"},
}

CURVE_ANCHORS = [(0, "floor"), (17, "soft"), (33, "lowMid"), (50, "optimal"), (67, "highMid"), (83, "strong"), (100, "ceiling")]

def pct(data, p):
    if not data:
        return 0
    s = sorted(data)
    idx = int(len(s) * p / 100)
    return s[min(idx, len(s)-1)]

def build_7point_curve(values, optimal=None, role="unknown"):
    clean = [max(1, min(127, int(v))) for v in values]
    clean.sort()
    if not clean:
        clean = [40, 80, 110]
    
    if optimal is None:
        optimal = clean[len(clean)//2]
    
    optimal = max(clean[0], min(clean[-1], int(optimal)))
    floor = clean[0]
    ceiling = clean[-1]
    
    soft = min(optimal, pct(clean, 10))
    low_mid = min(optimal, max(soft, pct(clean, 25)))
    high_mid = max(optimal, pct(clean, 75))
    strong = max(high_mid, pct(clean, 90))
    
    # Apply role-specific adjustments
    adj = INSTRUMENT_VELOCITY_ADJUSTMENTS.get(role, {})
    if adj:
        # Clamp floor to role minimum for audibility
        if "floor" in adj:
            floor = max(floor, adj["floor"])
        if "ceiling" in adj:
            ceiling = min(127, max(ceiling, adj["ceiling"]))
    
    # Ensure monotone after adjustments
    soft = max(floor, min(optimal, soft))
    low_mid = max(soft, min(optimal, low_mid))
    high_mid = max(optimal, high_mid)
    strong = max(high_mid, strong)
    ceiling = max(strong, ceiling)
    
    curve_values = {
        "floor": floor,
        "soft": soft,
        "lowMid": low_mid,
        "optimal": optimal,
        "highMid": high_mid,
        "strong": strong,
        "ceiling": ceiling
    }
    
    points = [{"intensity": i, "label": l, "velocity": curve_values[l]} for i, l in CURVE_ANCHORS]
    
    quantiles = {
        "p05": pct(clean, 5),
        "p10": pct(clean, 10),
        "p25": pct(clean, 25),
        "p50": pct(clean, 50),
        "p75": pct(clean, 75),
        "p90": pct(clean, 90),
        "p95": pct(clean, 95),
        "p99": pct(clean, 99)
    }
    
    n = len(clean)
    confidence = min(0.99, 0.1 + 0.9 * (1 - math.exp(-n/50)))
    
    # Korg realistic check
    korg_checks = {
        "min_ge_1": floor >= 1,
        "max_le_127": ceiling <= 127,
        "monotone": floor <= soft <= low_mid <= optimal <= high_mid <= strong <= ceiling,
        "range_not_zero": ceiling > floor,
        "optimal_in_range": floor <= optimal <= ceiling
    }
    
    return {
        "method": "factory-7point-v10.01-mapped",
        "points": points,
        "values": curve_values,
        "quantiles": quantiles,
        "allowedRange": [floor, ceiling],
        "sampleCount": n,
        "confidence": round(confidence, 4),
        "korgRealistic": all(korg_checks.values()),
        "korgChecks": korg_checks,
        "source": "FACTORY_MAPPED",
        "adjustment": adj
    }

def calibrate():
    print("🔧 FACTORY VELOCITY 10.01 - FIXED - Mapiranje 4 Factory role na 20 instrument rola")
    
    # Load factory profiles
    factory_path = DATA_DIR / "factory-velocity-profiles.json"
    data = json.loads(factory_path.read_text(encoding='utf-8'))
    profiles = data.get("profiles", [])
    
    # Group by factory role
    by_factory_role = defaultdict(list)
    for p in profiles:
        by_factory_role[p.get("role", "unknown")].append(p)
    
    print(f"Factory roles: {dict((k, len(v)) for k, v in by_factory_role.items())}")
    
    calibrated = {}
    
    # For each factory role, build curve, then map to instrument roles
    for factory_role, factory_profiles in by_factory_role.items():
        # Extract velocities
        all_vels = []
        for prof in factory_profiles:
            vel = prof.get("velocity", {})
            if vel:
                all_vels.append(vel.get("optimal", vel.get("optimum", 80)))
                if vel.get("min"):
                    all_vels.append(vel.get("min"))
                if vel.get("max"):
                    all_vels.append(vel.get("max"))
        
        if not all_vels:
            all_vels = [60, 80, 100]
        
        # Build base curve for factory role
        base_curve = build_7point_curve(all_vels, role=factory_role)
        
        # Map to instrument roles
        target_instrument_roles = FACTORY_TO_INSTRUMENT_MAP.get(factory_role, [factory_role])
        
        for instrument_role in target_instrument_roles:
            # Build instrument-specific curve using same base data but with instrument adjustment
            instrument_curve = build_7point_curve(all_vels, role=instrument_role)
            
            calibrated[instrument_role] = {
                "role": instrument_role,
                "factory_source_role": factory_role,
                "factory_profiles": len(factory_profiles),
                "sample_count": len(all_vels),
                "curve": instrument_curve,
                "base_factory_curve": base_curve,
                "velocity_rule": INSTRUMENT_VELOCITY_ADJUSTMENTS.get(instrument_role, {}),
                "korg_realistic": instrument_curve["korgRealistic"],
                "confidence": instrument_curve["confidence"],
                "transformation": {
                    "source_evidence": f"Factory {factory_role} {len(factory_profiles)} profiles, {len(all_vels)} samples -> mapped to {instrument_role}",
                    "musical_purpose": INSTRUMENT_VELOCITY_ADJUSTMENTS.get(instrument_role, {}).get("reason", f"Natural velocity for {instrument_role}"),
                    "target_profile": f"{instrument_role} range {instrument_curve['values']['floor']}-{instrument_curve['values']['ceiling']} optimal {instrument_curve['values']['optimal']}",
                    "constraints": f"Korg 1-127, {instrument_role} floor {INSTRUMENT_VELOCITY_ADJUSTMENTS.get(instrument_role, {}).get('floor', 1)}",
                    "transformation_rule": f"Factory {factory_role} intensity -> {instrument_role} velocity via 7-point curve with {instrument_role} adjustment",
                    "before_metric": "Original uncontrolled velocity",
                    "after_metric": f"Factory calibrated {instrument_curve['values']['floor']}-{instrument_curve['values']['ceiling']} optimal {instrument_curve['values']['optimal']}",
                    "pass_fail": "PASS" if instrument_curve["korgRealistic"] else "FAIL",
                    "explanation": f"Factory {factory_role} daje base, {instrument_role} adjustment daje final range"
                }
            }
    
    # Ensure all 20 roles are covered
    all_20_roles = ["bass", "drums", "percussion", "rhythm_guitar", "solo_guitar", "piano", "organ", "accordion", "strings", "brass", "sax", "woodwind", "clarinet", "violin", "synth_lead", "pad", "mallet", "choir", "fx", "accompaniment"]
    
    for role in all_20_roles:
        if role not in calibrated:
            calibrated[role] = {
                "role": role,
                "factory_source_role": None,
                "factory_profiles": 0,
                "sample_count": 0,
                "curve": None,
                "velocity_rule": INSTRUMENT_VELOCITY_ADJUSTMENTS.get(role, {}),
                "korg_realistic": False,
                "confidence": 0.0,
                "authority_status": "MANUAL_REVIEW",
                "transformation": {
                    "source_evidence": "No direct Factory evidence for this role",
                    "decision": "DO_NOT_BORROW",
                    "pass_fail": "BLOCKED"
                }
            }
    
    output = {
        "version": "10.01-fixed-20-roles",
        "timestamp": datetime.now().isoformat(),
        "authority": "FACTORY_ONLY_DIRECT_EVIDENCE",
        "factory_roles": dict((k, len(v)) for k, v in by_factory_role.items()),
        "instrument_roles": len(calibrated),
        "mapping": FACTORY_TO_INSTRUMENT_MAP,
        "adjustments": INSTRUMENT_VELOCITY_ADJUSTMENTS,
        "calibrations": calibrated
    }
    
    path = CALIBRATION_DIR / "factory_velocity_10.01_fixed_20_roles.json"
    path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding='utf-8')
    
    print(f"\n✅ Calibrated {len(calibrated)} instrument roles from {len(by_factory_role)} factory roles")
    for role in sorted(calibrated.keys()):
        cal = calibrated[role]
        if cal["curve"]:
            values = cal["curve"]["values"]
            print(f"   {role:20s} <- {cal['factory_source_role']:10s} : {values['floor']:3d}-{values['ceiling']:3d} opt {values['optimal']:3d} conf {cal['confidence']:.2f} {'✅' if cal['korg_realistic'] else '❌'}")
        else:
            print(f"   {role:20s} <- unresolved  : MANUAL_REVIEW")
    
    # Also create a simplified lookup for engine
    lookup = {
        role: {
            "floor": cal["curve"]["values"]["floor"],
            "optimal": cal["curve"]["values"]["optimal"],
            "ceiling": cal["curve"]["values"]["ceiling"],
            "curve": cal["curve"]
        }
        for role, cal in calibrated.items()
        if cal["curve"] is not None and cal.get("authority_status") != "MANUAL_REVIEW"
    }
    
    lookup_path = CALIBRATION_DIR / "factory_velocity_lookup_10.01.json"
    lookup_path.write_text(json.dumps(lookup, indent=2, ensure_ascii=False), encoding='utf-8')
    
    return output

if __name__ == "__main__":
    calibrate()
