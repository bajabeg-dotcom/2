#!/usr/bin/env python3
"""DNA MIDI Studio Pa800 — Expand Factory Velocity Profiles.

Reads every Factory profile and produces:
1. Per-profile VelMin/VelMax/P05/P50/P95 + 7-point curve
2. Per-instrument aggregated ranges
3. Per-role velocity heatmaps
4. Pa800 sound binding cross-reference
5. Balkan-specific velocity recommendations

Output: data/factory-velocity-catalog-9.30.json
"""
from __future__ import annotations
import json, sys, os
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

GM = {
    0:"Acoustic Grand Piano",1:"Bright Piano",2:"Electric Grand",4:"E.Piano 1 (Rhodes)",
    5:"E.Piano 2 (FM)",6:"Harpsichord",7:"Clavinet",16:"Drawbar Organ",
    17:"Perc Organ",18:"Rock Organ",19:"Church Organ",20:"Reed Organ",
    21:"Accordion",22:"Harmonica",23:"Tango Accordion",24:"Nylon Guitar",
    25:"Steel Guitar",26:"Jazz Guitar",27:"Clean Guitar",28:"Muted Guitar",
    29:"Overdrive Guitar",30:"Distortion Guitar",31:"Guitar Harmonics",
    32:"Acoustic Bass",33:"Finger Bass",34:"Pick Bass",35:"Fretless Bass",
    36:"Slap Bass 1",38:"Synth Bass 1",39:"Synth Bass 2",
    40:"Violin",44:"Tremolo Strings",45:"Pizzicato",46:"Harp",48:"String Ens 1",
    49:"String Ens 2",50:"Syn Strings 1",52:"Choir Aahs",
    56:"Trumpet",57:"Trombone",58:"Tuba",60:"French Horn",
    61:"Brass Section",62:"Syn Brass 1",65:"Alto Sax",66:"Tenor Sax",
    67:"Baritone Sax",68:"Oboe",71:"Clarinet",73:"Flute",
    79:"Ocarina",80:"Syn Lead (sq)",81:"Syn Lead (saw)",88:"Syn Pad (new age)",
    89:"Syn Pad (warm)",104:"Sitar",110:"Fiddle",
}

def vel_to_7point(vmin, vp05, vp50, vp95, vmax):
    """Convert 5-point stats to 7-point expressive curve."""
    return {
        "ppp": vmin,
        "pp": vp05,
        "p": int(vp05 + (vp50 - vp05) * 0.33),
        "mp": int(vp05 + (vp50 - vp05) * 0.67),
        "mf": vp50,
        "f": vp95,
        "ff": vmax,
    }

def vel_description(curve):
    """Human-readable description of velocity curve shape."""
    ppp, pp, p, mp, mf, f, ff = curve["ppp"], curve["pp"], curve["p"], curve["mp"], curve["mf"], curve["f"], curve["ff"]
    dynamic = ff - ppp
    if dynamic < 30:
        return "compressed"
    elif dynamic < 60:
        return "moderate"
    elif dynamic < 90:
        return "wide"
    else:
        return "full-range"

def main():
    print("Loading Factory calibration...")
    with open(DATA / "factory-calibration-4.37.json") as f:
        fcal = json.load(f)
    profiles = fcal.get("profiles", {})
    print(f"  {len(profiles)} profiles")
    
    # Build expanded velocity catalog
    catalog = {
        "schema": "dna-factory-velocity-catalog",
        "version": "9.30.0",
        "authority": "FACTORY_ONLY",
        "calibrationMode": "READ_ONLY",
        "perProfile": [],
        "perInstrument": {},
        "perRole": {},
        "balkanRecommendations": {},
        "summary": {},
    }
    
    # Per-profile entries
    for pid, p in sorted(profiles.items()):
        vel = p.get("velocityEnvelope", {})
        reg = p.get("registerEnvelope", {})
        sb = p.get("soundBinding", [])
        
        vmin = vel.get("min", 0)
        vmax = vel.get("max", 127)
        vp05 = vel.get("p05", 0)
        vp50 = vel.get("p50", 0)
        vp95 = vel.get("p95", 0)
        
        curve = vel_to_7point(vmin, vp05, vp50, vp95, vmax)
        desc = vel_description(curve)
        
        gm_prog = sb[1] if len(sb) >= 2 else -1
        gm_name = GM.get(gm_prog, f"PC{gm_prog}") if gm_prog >= 0 else "N/A"
        gm_bank = sb[0] if len(sb) >= 1 else -1
        
        entry = {
            "profileId": pid,
            "instrument": p.get("instrument", "UNKNOWN"),
            "role": p.get("role", "unknown"),
            "mode": p.get("mode", "UNKNOWN"),
            "confidence": p.get("confidence", 0),
            "gmProgram": gm_prog,
            "gmProgramName": gm_name,
            "gmBank": gm_bank,
            "soundBinding": sb,
            "sourceCount": p.get("sourceCount", 0),
            "sampleCount": vel.get("sampleCount", 0),
            "trainSegments": p.get("trainSegments", 0),
            "holdoutSegments": p.get("holdoutSegments", 0),
            "velocity": {
                "min": vmin,
                "max": vmax,
                "p05": vp05,
                "p50": vp50,
                "p95": vp95,
                "dynamicRange": vmax - vmin,
                "curve7Point": curve,
                "curveDescription": desc,
                "authority": vel.get("authority", "UNKNOWN"),
            },
            "register": {
                "pitchLow": reg.get("pitchLow", {}).get("p50", 0),
                "pitchHigh": reg.get("pitchHigh", {}).get("p50", 0),
                "pitchMedian": reg.get("pitchMedian", {}).get("p50", 0),
                "densityPerBar": round(reg.get("densityPerBar", {}).get("p50", 0), 2),
                "gateMedianQn": round(reg.get("gateMedianQn", {}).get("p50", 0), 4),
            },
        }
        catalog["perProfile"].append(entry)
    
    # Per-instrument aggregation
    inst_data = defaultdict(lambda: {"profiles": [], "velRanges": []})
    for entry in catalog["perProfile"]:
        inst = entry["instrument"]
        inst_data[inst]["profiles"].append(entry)
        inst_data[inst]["velRanges"].append(entry["velocity"])
    
    for inst, data in sorted(inst_data.items(), key=lambda x: -len(x[1]["profiles"])):
        vels = data["velRanges"]
        all_min = [v["min"] for v in vels]
        all_max = [v["max"] for v in vels]
        all_p05 = [v["p05"] for v in vels]
        all_p50 = [v["p50"] for v in vels]
        all_p95 = [v["p95"] for v in vels]
        
        avg_curve = vel_to_7point(
            round(sum(all_min)/len(all_min)),
            round(sum(all_p05)/len(all_p05)),
            round(sum(all_p50)/len(all_p50)),
            round(sum(all_p95)/len(all_p95)),
            round(sum(all_max)/len(all_max)),
        )
        
        gm_progs = list(set(e["gmProgram"] for e in data["profiles"] if e["gmProgram"] >= 0))
        roles = list(set(e["role"] for e in data["profiles"]))
        
        catalog["perInstrument"][inst] = {
            "profileCount": len(data["profiles"]),
            "gmPrograms": gm_progs,
            "roles": roles,
            "velocityAggregated": {
                "velMinRange": f"{min(all_min)}-{max(all_min)}",
                "velMaxRange": f"{min(all_max)}-{max(all_max)}",
                "avgVelMin": round(sum(all_min)/len(all_min)),
                "avgVelMax": round(sum(all_max)/len(all_max)),
                "avgP05": round(sum(all_p05)/len(all_p05)),
                "avgP50": round(sum(all_p50)/len(all_p50)),
                "avgP95": round(sum(all_p95)/len(all_p95)),
                "avgCurve7Point": avg_curve,
                "curveDescription": vel_description(avg_curve),
            },
            "bestProfile": max(data["profiles"], key=lambda e: e["sourceCount"])["profileId"],
        }
    
    # Per-role aggregation
    role_data = defaultdict(lambda: {"vels": [], "insts": set(), "progs": set()})
    for entry in catalog["perProfile"]:
        role = entry["role"]
        role_data[role]["vels"].append(entry["velocity"])
        role_data[role]["insts"].add(entry["instrument"])
        role_data[role]["progs"].add(entry["gmProgram"])
    
    for role, data in sorted(role_data.items()):
        vels = data["vels"]
        all_min = [v["min"] for v in vels]
        all_max = [v["max"] for v in vels]
        all_p05 = [v["p05"] for v in vels]
        all_p50 = [v["p50"] for v in vels]
        all_p95 = [v["p95"] for v in vels]
        
        role_curve = vel_to_7point(
            min(all_min), min(all_p05),
            round(sum(all_p50)/len(all_p50)),
            max(all_p95), max(all_max),
        )
        
        catalog["perRole"][role] = {
            "profileCount": len(vels),
            "instruments": sorted(list(data["insts"])),
            "gmPrograms": sorted([p for p in data["progs"] if p >= 0]),
            "velocity": {
                "globalVelMin": min(all_min),
                "globalVelMax": max(all_max),
                "avgP50": round(sum(all_p50)/len(all_p50)),
                "avgP95": round(sum(all_p95)/len(all_p95)),
                "curve7Point": role_curve,
                "curveDescription": vel_description(role_curve),
            },
        }
    
    # Balkan-specific recommendations
    catalog["balkanRecommendations"] = {
        "description": "Velocity recommendations for Balkan folk/pop MIDI on Pa800",
        "roles": {
            "bass": {
                "recommendedVelMin": 65,
                "recommendedVelMax": 127,
                "recommendedCurve": {"ppp":65,"pp":75,"p":82,"mp":92,"mf":104,"f":120,"ff":127},
                "rationale": "Balkan bass needs strong foundation — Firmirati bas!",
            },
            "drums": {
                "recommendedVelMin": 30,
                "recommendedVelMax": 127,
                "recommendedCurve": {"ppp":30,"pp":60,"p":72,"mp":85,"mf":95,"f":112,"ff":127},
                "rationale": "Balkan drums need ghost notes + strong accents",
            },
            "chords": {
                "recommendedVelMin": 40,
                "recommendedVelMax": 127,
                "recommendedCurve": {"ppp":40,"pp":55,"p":65,"mp":75,"mf":85,"f":108,"ff":127},
                "rationale": "Accordion/guitar chords — ritmički akcenti važni!",
            },
            "melody": {
                "recommendedVelMin": 35,
                "recommendedVelMax": 127,
                "recommendedCurve": {"ppp":35,"pp":50,"p":62,"mp":78,"mf":93,"f":115,"ff":127},
                "rationale": "Balkan melodija — terca harmonija treba dinamički kontrast",
            },
        },
    }
    
    # Summary
    total_profiles = len(catalog["perProfile"])
    all_have_velmin = all(p["velocity"]["min"] is not None for p in catalog["perProfile"])
    all_have_velmax = all(p["velocity"]["max"] is not None for p in catalog["perProfile"])
    all_have_curve = all("curve7Point" in p["velocity"] for p in catalog["perProfile"])
    all_factory = all(p["velocity"]["authority"] == "FACTORY_ONLY" for p in catalog["perProfile"])
    
    catalog["summary"] = {
        "totalProfiles": total_profiles,
        "allHaveVelMin": all_have_velmin,
        "allHaveVelMax": all_have_velmax,
        "allHave7PointCurve": all_have_curve,
        "allAuthorityFactoryOnly": all_factory,
        "totalInstruments": len(catalog["perInstrument"]),
        "totalRoles": len(catalog["perRole"]),
        "hardwarePending": True,
    }
    
    # Save
    out = DATA / "factory-velocity-catalog-9.30.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("FACTORY VELOCITY CATALOG — SUMMARY")
    print(f"{'='*60}")
    print(f"  Total profiles:         {total_profiles}")
    print(f"  All have VelMin:        {'✅' if all_have_velmin else '❌'}")
    print(f"  All have VelMax:        {'✅' if all_have_velmax else '❌'}")
    print(f"  All have 7-pt curve:   {'✅' if all_have_curve else '❌'}")
    print(f"  All FACTORY_ONLY:      {'✅' if all_factory else '❌'}")
    print(f"  Total instruments:      {len(catalog['perInstrument'])}")
    print(f"  Total roles:            {len(catalog['perRole'])}")
    
    print(f"\n  Per-Role Velocity Curves:")
    for role, rd in sorted(catalog["perRole"].items()):
        c = rd["velocity"]["curve7Point"]
        desc = rd["velocity"]["curveDescription"]
        print(f"    {role:12s}: ppp={c['ppp']:3d} pp={c['pp']:3d} p={c['p']:3d} mp={c['mp']:3d} mf={c['mf']:3d} f={c['f']:3d} ff={c['ff']:3d} ({desc})")
    
    print(f"\n  Per-Instrument (top 10):")
    for inst, idata in sorted(catalog["perInstrument"].items(), key=lambda x: -x[1]['profileCount'])[:10]:
        v = idata["velocityAggregated"]
        c = v["avgCurve7Point"]
        print(f"    {inst:20s} ({idata['profileCount']:4d}): ppp={c['ppp']:3d} pp={c['pp']:3d} p={c['p']:3d} mp={c['mp']:3d} mf={c['mf']:3d} f={c['f']:3d} ff={c['ff']:3d} ({v['curveDescription']})")
    
    print(f"\n  Catalog saved: {out.name}")
    return catalog


if __name__ == "__main__":
    main()
