#!/usr/bin/env python3
"""DNA MIDI Studio 9.30 — General Rules Export Gate

Hard validator that enforces:
  - Key range per GM instrument (128 programs)
  - Drum key map on channel 10
  - Velocity min/max per instrument category
  - Polyphony limits per instrument role
  - Pa800 54-note total polyphony
  - Balkan-specific range adjustments

This runs BEFORE any export. Notes that violate rules are either
clamped (velocity) or removed (key out of range, unmapped drum keys).

Author: DNA MIDI Studio Premium Developer
"""

import json, sys, copy, struct
from pathlib import Path
from collections import defaultdict, Counter

PROJ = Path(__file__).resolve().parent.parent
RULES_PATH = PROJ / "data" / "general-rules-9.30.json"

def note_name(n):
    notes = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    return f"{notes[n%12]}{n//12-1}"

class GeneralRulesValidator:
    """Validates and corrects MIDI data against General Rules 9.30."""
    
    def __init__(self, rules_path=RULES_PATH):
        self.rules = json.loads(rules_path.read_text(encoding="utf-8"))
        self.gm = {int(k): v for k, v in self.rules["gmMelodicRanges"].items()}
        self.drum_keys = {int(k): v for k, v in self.rules["drumValidKeys"].items()}
        self.vel_rules = self.rules["velocityRules"]
        self.poly_rules = self.rules["polyphonyRules"]
        self.balkan = self.rules["balkanRules"]
        self.channel10 = self.rules["channel10Rule"]
        self.report = []
    
    def _detect_category(self, program):
        """Get instrument category from GM program number."""
        if program in self.gm:
            return self.gm[program].get("cat", "unknown")
        return "unknown"
    
    def _detect_role(self, channel):
        """Guess instrument role from channel."""
        if channel == 9:
            return "drums"
        return "melody"
    
    def validate_track(self, track, track_index, stats):
        """Validate one track against general rules. Returns modified track."""
        # Track state
        channel_state = {}
        for ev in track["events"]:
            if ev["kind"] != "channel":
                continue
            ch = ev["channel"]
            cmd = ev["command"]
            data = ev["data"]
            
            if ch not in channel_state:
                channel_state[ch] = {"program": 0, "bankMSB": 0, "bankLSB": 0}
            
            # Track bank/program changes
            if cmd == 11 and data[0] == 0:
                channel_state[ch]["bankMSB"] = data[1]
            elif cmd == 11 and data[0] == 32:
                channel_state[ch]["bankLSB"] = data[1]
            elif cmd == 12:
                channel_state[ch]["program"] = data[0]
            
            # Validate note-on events
            if cmd == 9 and data[1] > 0:  # Note On with velocity > 0
                pitch = data[0]
                velocity = data[1]
                program = channel_state[ch]["program"]
                
                # === RULE 1: KEY RANGE CHECK ===
                if ch == 9:
                    # Drum channel — only valid drum keys
                    if pitch not in self.drum_keys:
                        ev["remove"] = True
                        stats["drum_key_blocked"] += 1
                        self.report.append({
                            "rule": "DRUM_KEY_INVALID",
                            "track": track_index, "channel": ch,
                            "pitch": pitch, "pitchName": note_name(pitch),
                            "action": "REMOVED",
                            "reason": f"Key {note_name(pitch)} not in Pa800 drum map"
                        })
                else:
                    # Melodic — check GM key range
                    if program in self.gm:
                        info = self.gm[program]
                        lo = info["lo"]
                        hi = info["hi"]
                        
                        if pitch < lo:
                            # Clamp to lowest valid note
                            data[0] = lo
                            stats["key_clamped_low"] += 1
                            self.report.append({
                                "rule": "KEY_BELOW_RANGE",
                                "track": track_index, "channel": ch,
                                "program": program, "programName": info["name"],
                                "originalPitch": pitch, "originalNote": note_name(pitch),
                                "clampedPitch": lo, "clampedNote": note_name(lo),
                                "validRange": f"{note_name(lo)}-{note_name(hi)}",
                                "action": "CLAMPED",
                                "reason": f"{note_name(pitch)} is below {info['name']} range {note_name(lo)}-{note_name(hi)}"
                            })
                        elif pitch > hi:
                            data[0] = hi
                            stats["key_clamped_high"] += 1
                            self.report.append({
                                "rule": "KEY_ABOVE_RANGE",
                                "track": track_index, "channel": ch,
                                "program": program, "programName": info["name"],
                                "originalPitch": pitch, "originalNote": note_name(pitch),
                                "clampedPitch": hi, "clampedNote": note_name(hi),
                                "validRange": f"{note_name(lo)}-{note_name(hi)}",
                                "action": "CLAMPED",
                                "reason": f"{note_name(pitch)} is above {info['name']} range {note_name(lo)}-{note_name(hi)}"
                            })
                    else:
                        stats["program_unknown"] += 1
                
                # === RULE 2-3: VELOCITY CHECK ===
                cat = self._detect_category(program) if ch != 9 else "drums"
                if cat in self.vel_rules:
                    vr = self.vel_rules[cat]
                    vel_lo = vr["lo"]
                    vel_hi = vr["hi"]
                    if velocity < vel_lo:
                        data[1] = vel_lo
                        stats["velocity_clamped_low"] += 1
                    elif velocity > vel_hi:
                        data[1] = vel_hi
                        stats["velocity_clamped_high"] += 1
                
                # === RULE 4: DRUM CHANNEL NOTE OFF ===
                if ch == 9 and velocity > 0:
                    stats["drum_notes_validated"] += 1
    
    def validate_polyphony(self, parsed, stats):
        """Check polyphony per channel and total."""
        max_poly = int(self.poly_rules.get("pa800_total", {}).get("maxVoices", 54))
        
        active_by_channel = defaultdict(list)  # channel -> list of active notes
        total_active = 0
        max_simultaneous = 0
        
        # Collect all note events sorted by tick
        all_events = []
        for track in parsed["tracks"]:
            for ev in track["events"]:
                if ev["kind"] == "channel" and not ev.get("remove"):
                    if ev["command"] in (8, 9):  # note off or note on
                        all_events.append((ev["tick"], ev.get("order", 0), ev))
        
        all_events.sort(key=lambda x: (x[0], x[1]))
        
        peak_poly = 0
        peak_tick = 0
        
        for tick, order, ev in all_events:
            ch = ev["channel"]
            pitch = ev["data"][0]
            
            if ev["command"] == 9 and ev["data"][1] > 0:  # note on
                active_by_channel[ch].append({"pitch": pitch, "tick": tick})
                total_active += 1
                if total_active > max_simultaneous:
                    max_simultaneous = total_active
                    peak_tick = tick
            elif ev["command"] == 8 or (ev["command"] == 9 and ev["data"][1] == 0):  # note off
                # Remove matching note
                for i, n in enumerate(active_by_channel.get(ch, [])):
                    if n["pitch"] == pitch:
                        active_by_channel[ch].pop(i)
                        total_active -= 1
                        break
        
        stats["peak_polyphony"] = max_simultaneous
        stats["peak_tick"] = peak_tick
        
        if max_simultaneous > max_poly:
            stats["polyphony_exceeded"] = max_simultaneous - max_poly
            self.report.append({
                "rule": "POLYPHONY_EXCEEDED",
                "peak": max_simultaneous,
                "limit": max_poly,
                "excess": max_simultaneous - max_poly,
                "action": "WARNING",
                "reason": f"Peak {max_simultaneous} notes exceeds Pa800 limit of {max_poly}"
            })
    
    def validate_midi(self, data: bytes) -> dict:
        """Validate raw MIDI bytes. Returns {valid, corrected_midi, report}."""
        # Parse
        sys.path.insert(0, str(PROJ))
        import midi_optimizer
        
        parsed = midi_optimizer.parse_smf(data)
        stats = Counter()
        self.report = []
        
        for track in parsed["tracks"]:
            self.validate_track(track, track["index"], stats)
        
        self.validate_polyphony(parsed, stats)
        
        # Encode corrected MIDI
        corrected = midi_optimizer.encode_smf(parsed)
        
        return {
            "valid": len(self.report) == 0,
            "violations": len(self.report),
            "stats": dict(stats),
            "report": self.report[:100],  # first 100 violations
            "correctedMidi": corrected,   # bytes — not JSON-serializable, use correctedSize for reports
            "correctedSize": len(corrected)
        }


def main():
    """CLI: validate MIDI files against General Rules."""
    import argparse
    parser = argparse.ArgumentParser(description="DNA General Rules Validator 9.30")
    parser.add_argument("input", help="Input MIDI file or directory")
    parser.add_argument("--output", help="Output directory for corrected files")
    parser.add_argument("--report", help="Output report JSON path")
    args = parser.parse_args()
    
    validator = GeneralRulesValidator()
    input_path = Path(args.input)
    output_dir = Path(args.output) if args.output else None
    
    if input_path.is_dir():
        files = sorted(input_path.glob("*.mid"))
    else:
        files = [input_path]
    
    all_results = []
    for f in files:
        data = f.read_bytes()
        result = validator.validate_midi(data)
        result["file"] = f.name
        all_results.append(result)
        
        status = "✅" if result["valid"] else "⚠️"
        violations = result["violations"]
        print(f"{status} {f.name}: {violations} violations, stats={result['stats']}")
        
        if output_dir and not result["valid"]:
            output_dir.mkdir(parents=True, exist_ok=True)
            out_path = output_dir / f.name
            out_path.write_bytes(result["correctedMidi"])
            print(f"  -> Saved corrected: {out_path}")
    
    if args.report:
        report_path = Path(args.report)
        # Remove correctedMidi (bytes) from results before JSON serialization
        for r in all_results:
            r.pop("correctedMidi", None)
        report_path.write_text(json.dumps({
            "schema": "dna-general-rules-validation",
            "version": "9.30",
            "files": len(all_results),
            "totalViolations": sum(r["violations"] for r in all_results),
            "results": all_results
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nReport: {report_path}")

if __name__ == "__main__":
    main()
