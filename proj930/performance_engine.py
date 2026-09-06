#!/usr/bin/env python3
"""Role-aware maximum performance optimizer.

This layer never changes harmony, form, program/bank data or drum pitches.
Velocity targets are obtained only from Factory profiles.  GOLD may be used by
higher planning layers, but never as a velocity authority here.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import math

import factory_velocity

DRUM_CORE = {
    "kick": {35, 36},
    "snare": {37, 38, 39, 40},
    "hat": {42, 44, 46},
    "tom": {41, 43, 45, 47, 48, 50},
    "cymbal": {49, 51, 52, 53, 55, 57, 59},
}

ROLE_QUANTIZE_FACTOR = {
    "drums": 0.92,
    "bass": 0.78,
    "rhythm-guitar": 0.62,
    "chords": 0.70,
    "accompaniment": 0.68,
    "pad": 0.78,
    "solo": 0.0,
    "echo": 0.0,
    "third": 0.0,
}


def role_quantize_strength(base_strength: int, role: str) -> int:
    return round(max(0, min(100, int(base_strength))) * ROLE_QUANTIZE_FACTOR.get(role, .7))


def _profile(note, profiles_by_key):
    item = profiles_by_key.get(note.get("instrumentKey"))
    return item if item and int(item.get("samples", 0)) >= 32 else None


def _factory_velocity_from_intensity(note, profiles_by_key, intensity):
    profile = _profile(note, profiles_by_key)
    if not profile:
        return None
    return factory_velocity.velocity_at(profile, max(0, min(100, intensity)))


def _set_gate(note, end_tick, stats, key):
    start = note["on"]["tick"]
    new_end = max(start + 1, int(end_tick))
    if new_end != note["off"]["tick"]:
        note["off"]["tick"] = new_end
        stats[key] += 1


def _group_by_onset(notes, tolerance=0):
    groups = []
    current = []
    anchor = None
    for note in sorted((n for n in notes if not n["on"].get("remove")), key=lambda n: (n["on"]["tick"], n["pitch"])):
        tick = note["on"]["tick"]
        if anchor is None or tick - anchor <= tolerance:
            current.append(note)
            anchor = tick if anchor is None else anchor
        else:
            groups.append(current)
            current = [note]
            anchor = tick
    if current:
        groups.append(current)
    return groups


def _drum_category(pitch):
    for name, pitches in DRUM_CORE.items():
        if pitch in pitches:
            return name
    return "percussion"


def optimize_drums(notes, profiles_by_key, ppq, options, stats):
    reduction = max(0, min(60, int(options.get("percussionReduction", 40))))
    changed = 0
    for note in notes:
        if note["on"].get("remove"):
            continue
        category = _drum_category(note["pitch"])
        if category != "percussion" or reduction <= 0:
            continue
        source = note["on"]["data"][1]
        intensity = (source - 1) * 100 / 126
        target = _factory_velocity_from_intensity(note, profiles_by_key, intensity - reduction)
        if target is not None and target < source:
            note["on"]["data"][1] = target
            stats["percussionFactoryAttenuated"] += 1
            changed += 1

    # Fill emphasis is restricted to dense last-quarter-bar drum activity.
    bar = ppq * 4
    buckets = defaultdict(list)
    for note in notes:
        if not note["on"].get("remove"):
            buckets[note["on"]["tick"] // bar].append(note)
    for _, bar_notes in buckets.items():
        if len(bar_notes) < 12:
            continue
        tail = [n for n in bar_notes if n["on"]["tick"] % bar >= bar * .75 and _drum_category(n["pitch"]) in ("snare", "tom")]
        if len(tail) < 3:
            continue
        for note in tail:
            source = note["on"]["data"][1]
            intensity = (source - 1) * 100 / 126
            target = _factory_velocity_from_intensity(note, profiles_by_key, intensity + 8)
            if target is not None and target > source:
                note["on"]["data"][1] = target
                stats["fillFactoryAccents"] += 1
                changed += 1
    return changed


def optimize_bass_gate(notes, ppq, stats):
    ordered = sorted((n for n in notes if not n["on"].get("remove")), key=lambda n: (n["on"]["tick"], n["pitch"]))
    changed = 0
    for i, note in enumerate(ordered[:-1]):
        nxt = ordered[i + 1]
        if nxt["on"]["tick"] <= note["on"]["tick"]:
            continue
        max_end = nxt["on"]["tick"] - max(1, round(ppq / 96))
        if note["off"]["tick"] > max_end:
            _set_gate(note, max_end, stats, "bassOverlapsReleased")
            changed += 1
    return changed


def interlock_bass_to_kick(bass_notes, drum_notes, ppq, strength, stats):
    kicks = sorted(n["on"]["tick"] for n in drum_notes if not n["on"].get("remove") and n["pitch"] in DRUM_CORE["kick"])
    if not kicks:
        return 0
    tolerance = max(2, round(ppq / 32))
    ratio = max(0, min(70, int(strength))) / 100
    changed = 0
    for note in bass_notes:
        if note["on"].get("remove"):
            continue
        start = note["on"]["tick"]
        nearest = min(kicks, key=lambda t: abs(t - start))
        delta = nearest - start
        if abs(delta) > tolerance:
            continue
        shift = round(delta * ratio)
        if not shift:
            continue
        duration = max(1, note["off"]["tick"] - start)
        new_start = max(0, start + shift)
        note["on"]["tick"] = new_start
        note["off"]["tick"] = new_start + duration
        stats["bassKickInterlocks"] += 1
        changed += 1
    return changed


def optimize_guitar_gate(notes, ppq, stats):
    # Preserve strum spread. Only shorten long chord tails before the next onset group.
    groups = _group_by_onset(notes, tolerance=max(2, round(ppq / 48)))
    changed = 0
    for index, group in enumerate(groups[:-1]):
        next_tick = min(n["on"]["tick"] for n in groups[index + 1])
        for note in group:
            start = note["on"]["tick"]
            current = note["off"]["tick"]
            max_end = next_tick - max(1, round(ppq / 64))
            if current > max_end > start:
                _set_gate(note, max_end, stats, "guitarChordTailsReleased")
                changed += 1
    return changed


def optimize_power_chords(notes, ppq, stats):
    changed = 0
    for group in _group_by_onset(notes, tolerance=max(1, round(ppq / 64))):
        pitches = sorted({n["pitch"] for n in group})
        if len(pitches) < 2 or not any((b - a) in (7, 12, 19) for a in pitches for b in pitches if b > a):
            continue
        # Keep power-chord attack intact but normalize wildly long tails.
        starts = [n["on"]["tick"] for n in group]
        anchor = min(starts)
        target_max = anchor + round(ppq * 1.8)
        for note in group:
            if note["off"]["tick"] > target_max:
                _set_gate(note, target_max, stats, "powerChordGateNormalized")
                changed += 1
    return changed


def optimize_solo_gate(notes, ppq, stats):
    # Never move solo onsets. Remove only impossible/dirty monophonic tail collisions.
    ordered = sorted((n for n in notes if not n["on"].get("remove")), key=lambda n: (n["on"]["tick"], n["pitch"]))
    changed = 0
    for i, note in enumerate(ordered[:-1]):
        nxt = ordered[i + 1]
        if nxt["on"]["tick"] <= note["on"]["tick"]:
            continue
        if note["off"]["tick"] > nxt["on"]["tick"] + round(ppq / 24):
            _set_gate(note, max(note["on"]["tick"] + 1, nxt["on"]["tick"]), stats, "soloTailCollisionsReleased")
            changed += 1
    return changed


def apply_role_performance(parsed, groups, profiles_by_key, options, stats):
    ppq = parsed["division"] if not parsed["division"] & 0x8000 else None
    if not ppq or not options.get("maxPerformance", False):
        return {"enabled": False, "roles": [], "interlock": {}}

    by_role = defaultdict(list)
    role_rows = []
    for group in groups:
        by_role[group["role"]].extend(group["notes"])
        changed_before = sum(stats.values())
        role = group["role"]
        if role == "drums":
            optimize_drums(group["notes"], profiles_by_key, ppq, options, stats)
        elif role == "bass":
            optimize_bass_gate(group["notes"], ppq, stats)
        elif role == "rhythm-guitar":
            optimize_guitar_gate(group["notes"], ppq, stats)
            optimize_power_chords(group["notes"], ppq, stats)
        elif role in ("chords", "accompaniment"):
            optimize_power_chords(group["notes"], ppq, stats)
        elif role == "solo":
            optimize_solo_gate(group["notes"], ppq, stats)
        role_rows.append({
            "track": group["track"]["index"], "channel": group["channel"] + 1,
            "role": role, "confidence": group["confidence"],
            "notes": len(group["notes"]), "interventions": max(0, sum(stats.values()) - changed_before),
        })

    interlocks = 0
    if by_role.get("bass") and by_role.get("drums"):
        interlocks = interlock_bass_to_kick(
            by_role["bass"], by_role["drums"], ppq,
            options.get("bassKickInterlockStrength", 45), stats)

    return {
        "enabled": True,
        "version": "1.0",
        "roles": role_rows,
        "interlock": {"bassKickAdjusted": interlocks,
                      "strength": int(options.get("bassKickInterlockStrength", 45))},
        "authority": {"velocity": "factory-only", "melody": "preserved", "form": "preserved"},
        "rules": {
            "percussionReduction": int(options.get("percussionReduction", 40)),
            "soloOnsetQuantize": False,
            "guitarStrumSpread": "preserved",
            "powerChordGate": "normalized-only",
        },
    }
