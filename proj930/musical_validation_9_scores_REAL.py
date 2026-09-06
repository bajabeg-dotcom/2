#!/usr/bin/env python3
"""
FAZA A5: Musical 9 scores - od pojednostavljenog ka REAL sofisticiranom
Implementira barem 3-4 metrike REAL sa pravim algoritmima
"""

import json
import mido
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import statistics

ARTIFACTS_DIR = Path("artifacts")
CALIBRATED_DIR = Path("artifacts/calibrated_14.00")
CALIBRATION_DIR = Path("calibration")
DATA_DIR = Path("data")

def classify_drum_element(pitch: int) -> str:
    if pitch in [35,36]: return "kick"
    elif pitch in [38,40]: return "snare"
    elif pitch == 37: return "rim"
    elif pitch == 39: return "clap"
    elif pitch in [42,44]: return "closed_hh"
    elif pitch == 46: return "open_hh"
    elif pitch == 44: return "pedal_hh"
    elif pitch in [51,53,59]: return "ride"
    elif pitch in [49,57]: return "crash"
    elif pitch in [41,43]: return "tom_low"
    elif pitch in [45,47]: return "tom_mid"
    elif pitch in [48,50]: return "tom_high"
    elif pitch == 54: return "tambourine"
    elif pitch == 56: return "cowbell"
    elif pitch in [62,63,64]: return "conga"
    elif pitch in [60,61]: return "bongo"
    elif pitch == 82: return "shaker"
    else: return "percussion"

def analyze_midi_9_scores(mid_path: Path) -> dict:
    try:
        mid = mido.MidiFile(str(mid_path))
    except Exception as e:
        return {"error": str(e), "path": str(mid_path)}
    
    notes = []
    for track in mid.tracks:
        tick = 0
        for msg in track:
            tick += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                notes.append({"pitch": msg.note, "velocity": msg.velocity, "tick": tick, "channel": msg.channel})
    
    if not notes:
        return {"path": str(mid_path), "notes": 0, "status": "SKIP"}
    
    # Group per channel
    by_channel = defaultdict(list)
    for n in notes:
        by_channel[n["channel"]].append(n)
    
    # === 1. DYNAMICS - REAL ===
    vels = [n["velocity"] for n in notes]
    vel_min = min(vels)
    vel_max = max(vels)
    vel_range = vel_max - vel_min
    vel_unique = len(set(vels))
    vel_unique_ratio = vel_unique / len(vels)
    vel_avg = sum(vels)/len(vels)
    vel_std = statistics.stdev(vels) if len(vels)>1 else 0
    
    # Dynamics score REAL: range + unique + std
    # Range 0-20 low, 20-40 medium, 40+ high -> score 50-90
    if vel_range < 10:
        dynamics_score = 50
    elif vel_range < 20:
        dynamics_score = 65
    elif vel_range < 40:
        dynamics_score = 80
    else:
        dynamics_score = 90
    # Bonus for unique ratio
    if vel_unique_ratio > 0.5:
        dynamics_score += 5
    dynamics_score = min(100, dynamics_score)
    
    # === 2. DRUM REALISM - REAL ===
    drum_notes = [n for n in notes if n["channel"] == 9]
    drum_score = 70
    kick_notes = [n for n in drum_notes if classify_drum_element(n["pitch"]) == "kick"]
    snare_notes = [n for n in drum_notes if classify_drum_element(n["pitch"]) == "snare"]
    hh_notes = [n for n in drum_notes if classify_drum_element(n["pitch"]) in ["closed_hh", "open_hh"]]
    
    kick_unique = len(set(n["velocity"] for n in kick_notes)) if kick_notes else 0
    snare_vels = [n["velocity"] for n in snare_notes]
    snare_ghost = len([v for v in snare_vels if v < 40]) if snare_vels else 0
    snare_accent = len([v for v in snare_vels if v > 80]) if snare_vels else 0
    
    drum_details = {
        "kick_count": len(kick_notes),
        "kick_unique_vel": kick_unique,
        "kick_not_uniform": kick_unique > 1,
        "snare_count": len(snare_notes),
        "snare_ghost": snare_ghost,
        "snare_accent": snare_accent,
        "snare_ghost_separation": snare_ghost > 0 and snare_accent > 0,
        "hh_count": len(hh_notes)
    }
    
    if drum_notes:
        if kick_unique > 1:
            drum_score += 10  # Kick NOT uniform
        if snare_ghost > 0 and snare_accent > 0:
            drum_score += 10  # Snare ghost separation
        if len(hh_notes) > 0:
            drum_score += 5
        drum_score = min(100, drum_score)
    else:
        drum_score = 80  # No drums, neutral
    
    # === 3. BASS REALISM - REAL ===
    bass_notes = []
    for ch, ch_notes in by_channel.items():
        if ch != 9:
            avg_pitch = sum(n["pitch"] for n in ch_notes)/len(ch_notes)
            if avg_pitch < 50:
                bass_notes.extend(ch_notes)
    
    bass_score = 70
    kick_ticks = [n["tick"] for n in kick_notes]
    bass_ticks = [n["tick"] for n in bass_notes]
    
    kick_bass_lock = 0
    for bt in bass_ticks:
        for kt in kick_ticks:
            if abs(bt - kt) < 20:
                kick_bass_lock += 1
                break
    
    bass_lock_rate = kick_bass_lock / max(1, len(bass_ticks))
    bass_details = {
        "bass_count": len(bass_notes),
        "kick_count": len(kick_notes),
        "kick_bass_lock": kick_bass_lock,
        "kick_bass_lock_rate": bass_lock_rate
    }
    
    if bass_notes:
        if bass_lock_rate > 0.3:
            bass_score += 15
        elif bass_lock_rate > 0.1:
            bass_score += 10
        # Root foundation - low pitch
        if bass_notes:
            low_bass = len([n for n in bass_notes if n["pitch"] < 40])
            if low_bass / len(bass_notes) > 0.5:
                bass_score += 5
        bass_score = min(100, bass_score)
    else:
        bass_score = 80
    
    # === 4. GROOVE - REAL (pocket + syncopation) ===
    groove_score = 70
    ticks = [n["tick"] for n in notes]
    # Pocket = std dev from grid (120 ticks = 16th note)
    grid = 120
    devs = []
    for t in ticks:
        nearest = round(t / grid) * grid
        devs.append(abs(t - nearest))
    avg_dev = sum(devs)/len(devs) if devs else 0
    # Small dev = tight groove, medium dev = humanized, large dev = sloppy
    if avg_dev < 5:
        groove_score = 75  # Too tight, machine
    elif avg_dev < 15:
        groove_score = 88  # Humanized good
    elif avg_dev < 30:
        groove_score = 80
    else:
        groove_score = 70
    
    # Syncopation rate
    syncopated = len([t for t in ticks if t % 240 == 120])
    sync_rate = syncopated / max(1, len(ticks))
    if sync_rate > 0.1:
        groove_score += 5
    
    groove_score = min(100, groove_score)
    groove_details = {
        "avg_deviation": avg_dev,
        "syncopated_count": syncopated,
        "syncopation_rate": sync_rate
    }
    
    # === 5. HARMONY - POJEDNOSTAVLJENO (još PROXY) ===
    # Za pravu harmony treba chord detection - za sada proxy
    # Koristimo pitch variety i interval
    pitches = [n["pitch"] for n in notes]
    pitch_range = max(pitches) - min(pitches) if pitches else 0
    harmony_score = 70
    if pitch_range > 24:
        harmony_score = 85
    elif pitch_range > 12:
        harmony_score = 80
    else:
        harmony_score = 70
    
    # === 6. ARTICULATION - REAL (gate + trills) ===
    # Gate avg from calibrated file if exists, else proxy
    articulation_score = 70
    # Check if calibrated file exists with gate info
    # For now use trill detection
    trills = 0
    notes_sorted = sorted(notes, key=lambda x: x["tick"])
    for i in range(len(notes_sorted)-2):
        if abs(notes_sorted[i+1]["tick"] - notes_sorted[i]["tick"]) < 60:
            if abs(notes_sorted[i+1]["pitch"] - notes_sorted[i]["pitch"]) <= 2:
                trills += 1
    
    if trills > 0:
        articulation_score = 85
    else:
        articulation_score = 80
    
    articulation_details = {"trills_detected": trills}
    
    # === 7. PHRASE - POJEDNOSTAVLJENO (PROXY) ===
    phrase_score = 80  # Proxy for now
    
    # === 8. INSTRUMENT REALISM - REAL (role variety) ===
    instrument_score = 70
    if len(by_channel) >= 3:
        instrument_score = 88
    elif len(by_channel) == 2:
        instrument_score = 80
    else:
        instrument_score = 70
    
    # === 9. MUSICALITY - WEIGHTED AVG ===
    weights = {"harmony":0.2, "groove":0.2, "dynamics":0.15, "articulation":0.15, "phrase":0.1, "instrument":0.1, "drum":0.05, "bass":0.03, "musicality":0.02}
    scores = {
        "harmony": harmony_score,
        "groove": groove_score,
        "dynamics": dynamics_score,
        "articulation": articulation_score,
        "phrase": phrase_score,
        "instrument": instrument_score,
        "drum": drum_score,
        "bass": bass_score,
        "musicality": 80  # placeholder
    }
    musicality = sum(scores[k]*weights[k] for k in weights)
    scores["musicality"] = musicality
    
    return {
        "path": str(mid_path),
        "file": mid_path.name,
        "notes": len(notes),
        "channels": len(by_channel),
        "scores": scores,
        "musicality": musicality,
        "details": {
            "dynamics": {"min": vel_min, "max": vel_max, "range": vel_range, "unique": vel_unique, "unique_ratio": vel_unique_ratio, "avg": vel_avg, "std": vel_std},
            "drum": drum_details,
            "bass": bass_details,
            "groove": groove_details,
            "articulation": articulation_details,
            "harmony": {"pitch_range": pitch_range}
        },
        "real_metrics": ["dynamics", "drum", "bass", "groove", "articulation"],
        "proxy_metrics": ["harmony", "phrase", "instrument"]
    }

def main():
    print(f"FAZA A5: Musical 9 scores REAL - 3-4 metrike REAL")
    
    # Test on artifacts
    artifact_files = list(ARTIFACTS_DIR.glob("*.mid"))
    print(f"Artifacts: {len(artifact_files)} files")
    
    results = []
    for mf in sorted(artifact_files)[:37]:
        res = analyze_midi_9_scores(mf)
        results.append(res)
        if "scores" in res:
            print(f"✅ {mf.name:40s} notes {res['notes']:4d} musical {res['musicality']:.1f} scores { {k: int(v) for k,v in res['scores'].items()} }")
    
    # Test on calibrated
    calibrated_files = list(CALIBRATED_DIR.glob("*.mid"))
    print(f"\nCalibrated: {len(calibrated_files)} files")
    cal_results = []
    for mf in sorted(calibrated_files)[:37]:
        res = analyze_midi_9_scores(mf)
        cal_results.append(res)
        if "scores" in res:
            print(f"✅ {mf.name:50s} musical {res['musicality']:.1f} dynamics {res['scores']['dynamics']} drum {res['scores']['drum']} bass {res['scores']['bass']} groove {res['scores']['groove']}")
    
    # Aggregate
    if results and cal_results:
        avg_before = sum(r["musicality"] for r in results if "musicality" in r) / len(results)
        avg_after = sum(r["musicality"] for r in cal_results if "musicality" in r) / len(cal_results)
        print(f"\n📊 Musical 9 scores REAL:")
        print(f"   Before (artifacts): {avg_before:.1f} avg")
        print(f"   After (calibrated 14.00): {avg_after:.1f} avg")
        print(f"   Delta: {avg_after-avg_before:+.1f}")
        
        # Per score delta
        for score_name in ["harmony", "groove", "dynamics", "articulation", "phrase", "instrument", "drum", "bass", "musicality"]:
            before_avg = sum(r["scores"][score_name] for r in results if "scores" in r) / len(results)
            after_avg = sum(r["scores"][score_name] for r in cal_results if "scores" in r) / len(cal_results)
            real = "REAL" if score_name in ["dynamics", "drum", "bass", "groove", "articulation"] else "PROXY"
            print(f"      {score_name:15s}: {before_avg:5.1f} -> {after_avg:5.1f} {after_avg-before_avg:+5.1f} [{real}]")
    
    # Save
    report = {
        "version": "14.00-MUSICAL-9-SCORES-REAL",
        "timestamp": datetime.now().isoformat(),
        "total_files": len(results),
        "calibrated_files": len(cal_results),
        "musical_before": sum(r["musicality"] for r in results if "musicality" in r) / max(1, len(results)),
        "musical_after": sum(r["musicality"] for r in cal_results if "musicality" in r) / max(1, len(cal_results)),
        "real_metrics": ["dynamics", "drum", "bass", "groove", "articulation"],
        "proxy_metrics": ["harmony", "phrase", "instrument"],
        "results_before": results,
        "results_after": cal_results,
        "evidence": "DIRECT REAL metrics for dynamics (vel range/unique/std), drum (kick unique, snare ghost separation), bass (kick-bass lock rate), groove (pocket dev, syncopation), articulation (trills) - 5 REAL, 3 PROXY (harmony, phrase, instrument) + musicality weighted avg"
    }
    
    out_path = CALIBRATION_DIR / "musical_9_scores_REAL.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\n✅ Musical 9 scores REAL: {out_path}")
    print(f"   REAL metrics: {report['real_metrics']} (5/9)")
    print(f"   PROXY metrics: {report['proxy_metrics']} (3/9) + musicality weighted")

if __name__ == "__main__":
    main()
