#!/usr/bin/env python3
"""Convert factory-calibration-4.37.json profiles into the format
expected by midi_optimizer.optimize_midi() (instrumentKey, kind, program, drumNote, samples)."""
import json, sys
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
CALIB_PATH = PROJ / "data" / "factory-calibration-4.37.json"
OUT_PATH = PROJ / "data" / "factory-profiles-optimizer.json"

def convert():
    calib = json.loads(CALIB_PATH.read_text(encoding="utf-8"))
    raw = list(calib["profiles"].values())
    converted = []

    for p in raw:
        sb = p.get("soundBinding", [])  # [bankMSB, program, note]
        ve = p.get("velocityEnvelope", {})
        role = p.get("role", "")
        instrument = p.get("instrument", "")
        profile_id = p.get("profileId", "")

        # Parse soundBinding
        bank_msb = sb[0] if len(sb) > 0 else 0
        program = sb[1] if len(sb) > 1 else 0
        note = sb[2] if len(sb) > 2 else 0

        # Determine kind: DRUMS and PERC are drum profiles
        is_drum = role == "drums" or instrument.startswith("DRUMS") or instrument.startswith("PERC")
        kind = "drum" if is_drum else "melodic"

        # Build instrumentKey matching midi_optimizer format
        # melodic:{msb}:{lsb}:{program}  or  drum:{msb}:{lsb}:{program}:{pitch}
        # Since Pa800 profiles use bankMSB and program, we map accordingly
        lsb = 0  # Pa800 factory profiles don't specify LSB
        if is_drum:
            instrument_key = f"drum:{bank_msb}:{lsb}:{program}:{note}"
        else:
            instrument_key = f"melodic:{bank_msb}:{lsb}:{program}"

        entry = {
            "instrumentKey": instrument_key,
            "kind": kind,
            "program": program,
            "bankMSB": bank_msb,
            "bankLSB": lsb,
            "drumNote": note if is_drum else None,
            "instrument": instrument,
            "role": role,
            "profileId": profile_id,
            "samples": ve.get("sampleCount", 0),
            "velocityEnvelope": ve,
            "authority": ve.get("authority", "FACTORY_ONLY"),
            "mode": p.get("mode", ""),
        }
        converted.append(entry)

    print(f"Converted {len(converted)} profiles")
    print(f"  Drum profiles: {sum(1 for p in converted if p['kind'] == 'drum')}")
    print(f"  Melodic profiles: {sum(1 for p in converted if p['kind'] == 'melodic')}")
    print(f"  Unique programs: {len(set(p['program'] for p in converted))}")

    # Save
    OUT_PATH.write_text(json.dumps(converted, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Saved to: {OUT_PATH}")
    return converted

if __name__ == "__main__":
    convert()
