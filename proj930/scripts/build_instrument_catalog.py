#!/usr/bin/env python3
"""DNA MIDI Studio Pa800 — Build Complete Instrument Catalog with Velocity Profiles.

Reads Factory calibration, Gold patterns, instrument profiles, and style segments
to produce a comprehensive catalog with VelMin/VelMax per profile.

Output: data/instrument-catalog-9.30.json
"""
from __future__ import annotations
import json, sys, os
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

GM_INSTRUMENTS = {
    0:"Acoustic Grand Piano",1:"Bright Acoustic Piano",2:"Electric Grand Piano",
    3:"Honky-tonk Piano",4:"Electric Piano 1 (Rhodes)",5:"Electric Piano 2 (FM)",
    6:"Harpsichord",7:"Clavinet",8:"Celesta",9:"Glockenspiel",
    10:"Music Box",11:"Vibraphone",12:"Marimba",13:"Xylophone",
    14:"Tubular Bells",15:"Dulcimer (Santur)",16:"Drawbar Organ",
    17:"Percussive Organ",18:"Rock Organ",19:"Church Organ",
    20:"Reed Organ",21:"Accordion",22:"Harmonica",23:"Tango Accordion",
    24:"Acoustic Guitar (nylon)",25:"Acoustic Guitar (steel)",26:"Electric Guitar (jazz)",
    27:"Electric Guitar (clean)",28:"Electric Guitar (muted)",29:"Overdriven Guitar",
    30:"Distortion Guitar",31:"Guitar Harmonics",32:"Acoustic Bass",
    33:"Electric Bass (finger)",34:"Electric Bass (pick)",35:"Fretless Bass",
    36:"Slap Bass 1",37:"Slap Bass 2",38:"Synth Bass 1",39:"Synth Bass 2",
    40:"Violin",41:"Viola",42:"Cello",43:"Contrabass",
    44:"Tremolo Strings",45:"Pizzicato Strings",46:"Orchestral Harp",47:"Timpani",
    48:"String Ensemble 1",49:"String Ensemble 2",50:"Synth Strings 1",
    51:"Synth Strings 2",52:"Choir Aahs",53:"Voice Oohs",54:"Synth Vox",
    55:"Orchestra Hit",56:"Trumpet",57:"Trombone",58:"Tuba",
    59:"Muted Trumpet",60:"French Horn",61:"Brass Section",
    62:"Synth Brass 1",63:"Synth Brass 2",64:"Soprano Sax",
    65:"Alto Sax",66:"Tenor Sax",67:"Baritone Sax",68:"Oboe",
    69:"English Horn",70:"Bassoon",71:"Clarinet",72:"Piccolo",
    73:"Flute",74:"Recorder",75:"Pan Flute",76:"Blown Bottle",
    77:"Shakuhachi",78:"Whistle",79:"Ocarina",
    80:"Syn Lead 1 (square)",81:"Syn Lead 2 (sawtooth)",82:"Syn Lead 3 (calliope)",
    83:"Syn Lead 4 (chiff)",84:"Syn Lead 5 (charang)",85:"Syn Lead 6 (voice)",
    86:"Syn Lead 7 (fifths)",87:"Syn Lead 8 (bass+lead)",88:"Syn Pad 1 (new age)",
    89:"Syn Pad 2 (warm)",90:"Syn Pad 3 (polysynth)",91:"Syn Pad 4 (choir)",
    92:"Syn Pad 5 (bowed)",93:"Syn Pad 6 (metallic)",94:"Syn Pad 7 (halo)",
    95:"Syn Pad 8 (sweep)",96:"FX 1 (rain)",97:"FX 2 (soundtrack)",
    98:"FX 3 (crystal)",99:"FX 4 (atmosphere)",100:"FX 5 (brightness)",
    101:"FX 6 (goblins)",102:"FX 7 (echoes)",103:"FX 8 (sci-fi)",
    104:"Sitar",105:"Banjo",106:"Shamisen",107:"Koto",
    108:"Kalimba",109:"Bagpipe",110:"Fiddle",111:"Shanai",
    112:"Tinkle Bell",113:"Agogo",114:"Steel Drums",115:"Woodblock",
    116:"Taiko Drum",117:"Melodic Tom",118:"Synth Drum",119:"Reverse Cymbal",
    120:"Guitar Fret Noise",121:"Breath Noise",122:"Seashore",123:"Bird Tweet",
    124:"Telephone Ring",125:"Helicopter",126:"Applause",127:"Gunshot",
}

# Pa800 CV (Chord Variation) mapping
CV_NAMES = {
    1:"CV1 (Main)",2:"CV2 (Variation)",3:"CV3 (Advanced)",
    4:"CV4 (Complex)",5:"CV5 (Full)",6:"CV6 (Maximum)"
}

# Role → GM channel mapping
ROLE_CHANNELS = {
    "drums": [9, 10],
    "bass": [4],
    "chords": [0, 1, 2, 3, 5, 6, 7, 8, 11, 12, 13, 14, 15],
    "melody": [0, 1, 5, 6, 7, 8, 11, 12, 13, 14, 15],
}

def build_catalog():
    # 1. Load Factory calibration
    print("Loading Factory calibration...")
    with open(DATA / "factory-calibration-4.37.json") as f:
        fcal = json.load(f)
    factory_profiles = fcal.get("profiles", {})
    print(f"  {len(factory_profiles)} profiles loaded")

    # 2. Load instrument profiles
    print("Loading instrument profiles...")
    with open(DATA / "complete-instrument-profiles-4.44.json") as f:
        instr_data = json.load(f)
    instrument_roles = instr_data.get("roles", {})
    print(f"  {len(instrument_roles)} roles loaded")

    # 3. Load style segments
    print("Loading style segments...")
    with open(DATA / "factory-style-segments.json") as f:
        style_data = json.load(f)
    segments = style_data.get("segments", [])
    print(f"  {len(segments)} segments loaded")

    # 4. Load Gold patterns
    print("Loading Gold performance patterns...")
    with open(DATA / "gold-performance-patterns.json") as f:
        gold_data = json.load(f)
    gold_patterns = gold_data.get("patterns", []) if isinstance(gold_data, dict) else gold_data
    if isinstance(gold_data, dict):
        gold_patterns = gold_data.get("patterns", gold_data.get("entries", []))
    print(f"  {len(gold_patterns)} Gold patterns loaded")

    # 5. Load strumming
    print("Loading strumming patterns...")
    with open(DATA / "factory-strumming.json") as f:
        strum_data = json.load(f)
    strum_count = len(strum_data) if isinstance(strum_data, list) else strum_data.get("total", 0)
    print(f"  {strum_count} strum patterns loaded")

    # ── Build per-profile velocity catalog ──
    print("\nBuilding instrument catalog...")
    catalog = {
        "schema": "dna-instrument-catalog",
        "version": "9.30.0",
        "velocityAuthority": "FACTORY_ONLY",
        "goldVelocityPolicy": "FORBIDDEN",
        "calibrationMode": "READ_ONLY",
        "generatedBy": "build_instrument_catalog.py",
        "roles": {},
        "factoryProfiles": [],
        "gmProgramCoverage": {},
        "styleElements": {},
        "summary": {},
    }

    # ── Per-role entries with full velocity envelopes ──
    for role_name, role_data in sorted(instrument_roles.items()):
        if not isinstance(role_data, dict):
            continue
        role_entry = {
            "name": role_name,
            "playerModel": role_data.get("playerModel", "unknown"),
            "velocityAuthority": role_data.get("velocityAuthority", "FACTORY_ONLY"),
            "policies": role_data.get("policies", {}),
            "behavior": role_data.get("behavior", {}),
            "factoryProfileCount": 0,
            "factoryVelMin": None,
            "factoryVelMax": None,
            "factoryVelP05": None,
            "factoryVelP50": None,
            "factoryVelP95": None,
            "velRange7Point": {},
            "profiles": [],
            "gmPrograms": [],
        }
        catalog["roles"][role_name] = role_entry

    # ── Per-profile detailed entries ──
    vel_by_role = defaultdict(list)
    prog_by_role = defaultdict(set)
    
    for pid, p in sorted(factory_profiles.items()):
        role = p.get("role", "unknown")
        inst = p.get("instrument", "UNKNOWN")
        vel_env = p.get("velocityEnvelope", {})
        reg_env = p.get("registerEnvelope", {})
        sb = p.get("soundBinding", [])
        conf = p.get("confidence", 0)
        mode = p.get("mode", "UNKNOWN")
        source_count = p.get("sourceCount", 0)
        
        vel_min = vel_env.get("min", 0)
        vel_max = vel_env.get("max", 127)
        vel_p05 = vel_env.get("p05", 0)
        vel_p50 = vel_env.get("p50", 0)
        vel_p95 = vel_env.get("p95", 0)
        sample_count = vel_env.get("sampleCount", 0)
        authority = vel_env.get("authority", "UNKNOWN")
        
        # Sound binding → GM program
        gm_prog = sb[1] if len(sb) >= 2 else -1
        gm_bank = sb[0] if len(sb) >= 1 else -1
        gm_name = GM_INSTRUMENTS.get(gm_prog, f"Unknown PC{gm_prog}") if gm_prog >= 0 else "N/A"
        
        # Register envelope
        pitch_low_p50 = reg_env.get("pitchLow", {}).get("p50", 0)
        pitch_high_p50 = reg_env.get("pitchHigh", {}).get("p50", 0)
        pitch_median_p50 = reg_env.get("pitchMedian", {}).get("p50", 0)
        density_p50 = reg_env.get("densityPerBar", {}).get("p50", 0)
        gate_p50 = reg_env.get("gateMedianQn", {}).get("p50", 0)
        
        profile_entry = {
            "profileId": pid,
            "instrument": inst,
            "role": role,
            "gmProgram": gm_prog,
            "gmProgramName": gm_name,
            "gmBank": gm_bank,
            "chordVariation": None,  # filled from CV field if present
            "mode": mode,
            "confidence": conf,
            "sourceCount": source_count,
            "trainSegments": p.get("trainSegments", 0),
            "holdoutSegments": p.get("holdoutSegments", 0),
            "sampleCount": sample_count,
            "velocity": {
                "min": vel_min,
                "max": vel_max,
                "p05": vel_p05,
                "p50": vel_p50,
                "p95": vel_p95,
                "dynamicRange": vel_max - vel_min,
                "authority": authority,
                "range7Point": {
                    "ppp": max(0, vel_min),
                    "pp": vel_p05,
                    "p": int(vel_p05 + (vel_p50 - vel_p05) * 0.33),
                    "mp": int(vel_p05 + (vel_p50 - vel_p05) * 0.67),
                    "mf": vel_p50,
                    "f": vel_p95,
                    "ff": vel_max,
                },
            },
            "register": {
                "pitchLow": pitch_low_p50,
                "pitchHigh": pitch_high_p50,
                "pitchMedian": pitch_median_p50,
                "densityPerBar": round(density_p50, 2),
                "gateMedianQn": round(gate_p50, 4),
            },
            "heldOutDeviation": p.get("heldOutDeviation", {}),
        }
        
        # Add to role profile list
        if role in catalog["roles"]:
            catalog["roles"][role]["profiles"].append(profile_entry)
            catalog["roles"][role]["factoryProfileCount"] += 1
            vel_by_role[role].append({"min": vel_min, "max": vel_max, "p05": vel_p05, "p50": vel_p50, "p95": vel_p95})
            if gm_prog >= 0:
                prog_by_role[role].add(gm_prog)
        
        catalog["factoryProfiles"].append(profile_entry)

    # ── Aggregate role velocity ranges ──
    for role, vels in vel_by_role.items():
        if role not in catalog["roles"]:
            continue
        r = catalog["roles"][role]
        if vels:
            all_min = [v["min"] for v in vels]
            all_max = [v["max"] for v in vels]
            all_p05 = [v["p05"] for v in vels]
            all_p50 = [v["p50"] for v in vels]
            all_p95 = [v["p95"] for v in vels]
            r["factoryVelMin"] = min(all_min)
            r["factoryVelMax"] = max(all_max)
            r["factoryVelP05"] = round(sum(all_p05)/len(all_p05))
            r["factoryVelP50"] = round(sum(all_p50)/len(all_p50))
            r["factoryVelP95"] = round(sum(all_p95)/len(all_p95))
            r["velRange7Point"] = {
                "ppp": min(all_min),
                "pp": min(all_p05),
                "p": int(min(all_p05) + (sum(all_p50)/len(all_p50) - min(all_p05)) * 0.33),
                "mp": int(min(all_p05) + (sum(all_p50)/len(all_p50) - min(all_p05)) * 0.67),
                "mf": round(sum(all_p50)/len(all_p50)),
                "f": max(all_p95),
                "ff": max(all_max),
            }
        r["gmPrograms"] = sorted(list(prog_by_role.get(role, set())))

    # ── Style elements breakdown ──
    element_counts = defaultdict(int)
    element_by_role = defaultdict(lambda: defaultdict(int))
    element_by_meter = defaultdict(int)
    element_by_tempo = defaultdict(lambda: defaultdict(int))
    
    for seg in segments:
        elem = seg.get("element", "unknown")
        seg_role = seg.get("role", "unknown")
        meter = seg.get("meter", "?/?")
        tempo = seg.get("tempo", 0)
        cv = seg.get("cv", 0)
        
        element_counts[elem] += 1
        element_by_role[seg_role][elem] += 1
        element_by_meter[meter] += 1
        
        # Tempo bucket
        bucket = "slow" if tempo < 80 else ("medium" if tempo < 120 else ("brisk" if tempo < 160 else "fast"))
        element_by_tempo[bucket][elem] += 1
    
    catalog["styleElements"] = {
        "total": len(segments),
        "byElement": dict(element_counts),
        "byRoleAndElement": {k: dict(v) for k, v in element_by_role.items()},
        "byMeter": dict(element_by_meter),
        "byTempoBucket": {k: dict(v) for k, v in element_by_tempo.items()},
    }

    # ── GM program coverage ──
    all_gm_progs = set()
    for pid, p in factory_profiles.items():
        sb = p.get("soundBinding", [])
        if len(sb) >= 2:
            all_gm_progs.add(sb[1])
    
    coverage = {}
    for prog in sorted(all_gm_progs):
        name = GM_INSTRUMENTS.get(prog, f"PC{prog}")
        profiles_for_prog = [p for pid, p in factory_profiles.items()
                             if len(p.get("soundBinding",[])) >= 2 and p["soundBinding"][1] == prog]
        coverage[str(prog)] = {
            "name": name,
            "profileCount": len(profiles_for_prog),
            "velMin": min(p.get("velocityEnvelope",{}).get("min",0) for p in profiles_for_prog),
            "velMax": max(p.get("velocityEnvelope",{}).get("max",127) for p in profiles_for_prog),
            "velP50": round(sum(p.get("velocityEnvelope",{}).get("p50",0) for p in profiles_for_prog)/len(profiles_for_prog)),
            "roles": list(set(p.get("role","?") for p in profiles_for_prog)),
        }
    catalog["gmProgramCoverage"] = coverage

    # ── Summary ──
    catalog["summary"] = {
        "totalFactoryProfiles": len(factory_profiles),
        "totalInstrumentRoles": len(instrument_roles),
        "totalStyleSegments": len(segments),
        "totalGoldPatterns": len(gold_patterns) if isinstance(gold_patterns, list) else 0,
        "totalStrumPatterns": strum_count,
        "roleBreakdown": {k: v["factoryProfileCount"] for k, v in catalog["roles"].items()},
        "velocityAuthority": "FACTORY_ONLY",
        "allProfilesHaveVelMin": all(p["velocity"]["min"] is not None for p in catalog["factoryProfiles"]),
        "allProfilesHaveVelMax": all(p["velocity"]["max"] is not None for p in catalog["factoryProfiles"]),
        "allProfilesHave7PointCurve": all("range7Point" in p["velocity"] for p in catalog["factoryProfiles"]),
        "hardwareValidationStatus": "ALL_HARDWARE_PENDING",
    }

    # ── Save ──
    out_path = DATA / "instrument-catalog-9.30.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print(f"\nCatalog saved: {out_path}")
    print(f"  {len(catalog['factoryProfiles'])} profiles with VelMin/VelMax/7-point curves")
    print(f"  {len(catalog['roles'])} instrument roles")
    print(f"  {len(coverage)} GM programs covered")
    return catalog


if __name__ == "__main__":
    build_catalog()
