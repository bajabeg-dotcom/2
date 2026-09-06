#!/usr/bin/env python3
"""Deterministički muzički pomoćni sloj za Pa800 Style engine.

Funkcije ne pišu MIDI i ne odlučuju o dinamici. One samo optimiziraju
oktavni položaj, uklanjaju nepotrebne unisone između ACC traka i zapisuju
preporuke koje korisnik mora potvrditi na fizičkom Pa800.
"""

from __future__ import annotations

import statistics


TRACK_RANGES = {
    "bass": (28, 55), "drum": (0, 127), "perc": (0, 127),
    "acc1": (43, 76), "acc2": (50, 84), "acc3": (55, 88),
    "acc4": (64, 96), "acc5": (48, 84),
}

TRACK_GUIDANCE = {
    "bass": ("Bass", "Bass transposition candidate"),
    "drum": ("Drum", "No-transpose drum candidate"),
    "perc": ("Percussion", "No-transpose percussion candidate"),
    "acc1": ("Acc", "Parallel chord candidate"),
    "acc2": ("Acc", "Parallel chord candidate"),
    "acc3": ("Acc", "Melodic/fixed-note candidate"),
    "acc4": ("Acc", "Melodic/fixed-note candidate"),
    "acc5": ("Acc", "Parallel chord candidate"),
}


def voice_lead(notes, track_name, previous_center=None):
    """Odaberi oktavnu inverziju s najmanjim pomakom između elemenata."""
    if track_name in ("drum", "perc") or not notes:
        return list(notes), previous_center, {"octaveShift": 0, "movement": 0, "applied": False}
    low, high = TRACK_RANGES[track_name]
    candidates = []
    for shift in (-24, -12, 0, 12, 24):
        pitches = [note[2] + shift for note in notes]
        if min(pitches) < low or max(pitches) > high:
            continue
        center = statistics.mean(pitches)
        movement = abs(center - previous_center) if previous_center is not None else abs(shift) * .25
        candidates.append((movement + abs(shift) * .02, abs(shift), shift, center))
    if not candidates:
        center = statistics.mean(note[2] for note in notes)
        return list(notes), center, {"octaveShift": 0, "movement": 0, "applied": False}
    _, _, shift, center = min(candidates)
    output = [(note[0], note[1], note[2] + shift, *note[3:]) for note in notes]
    movement = 0 if previous_center is None else round(abs(center - previous_center), 3)
    return output, center, {"octaveShift": shift, "movement": movement, "applied": bool(shift)}


def resolve_unison(pitch, track_name, occupied):
    """Pomakni ACC notu za oktavu kada druga ACC traka već koristi isti ton."""
    if track_name in ("bass", "drum", "perc") or pitch not in occupied:
        return pitch, False
    low, high = TRACK_RANGES[track_name]
    order = (12, -12, 24, -24) if track_name in ("acc3", "acc4") else (-12, 12, -24, 24)
    for shift in order:
        candidate = pitch + shift
        if low <= candidate <= high and candidate not in occupied:
            return candidate, True
    return pitch, False


def track_recommendation(track_name):
    track_type, ntt_candidate = TRACK_GUIDANCE[track_name]
    low, high = TRACK_RANGES[track_name]
    return {
        "trackTypeCandidate": track_type,
        "nttCandidate": ntt_candidate,
        "register": {"low": low, "high": high},
        "status": "DEVICE_CONFIRMATION_REQUIRED",
        "note": "Potvrditi Track Type i NTT na fizičkom Korg Pa800 nakon SMF importa.",
    }


def transition_recommendation(marker, next_marker):
    current_kind = marker[:1]
    next_kind = (next_marker or "")[:1]
    if current_kind == "f":
        purpose = "fill-to-variation"
    elif next_kind == "f":
        purpose = "variation-to-fill"
    elif current_kind == "i":
        purpose = "intro-release"
    elif current_kind == "e":
        purpose = "ending-resolution"
    else:
        purpose = "section-continuity"
    return {"purpose": purpose, "nextMarker": next_marker, "deterministic": True}