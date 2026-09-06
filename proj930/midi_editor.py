#!/usr/bin/env python3
"""Sigurne, auditirane operacije stvarnog DNA MIDI editora."""

from __future__ import annotations

import hashlib
from collections import Counter
from pathlib import Path

import midi_optimizer
import special_track_engine
from truthful_evidence_gate import TruthEvidenceGate


ALLOWED_OPERATIONS = {"move", "resize", "velocity", "transpose", "quantize", "delete", "duplicate"}


def note_id(track, note):
    return f"{track['index']}:{note['on']['order']}"


def snapshot(track, note):
    return {"id": note_id(track, note), "track": track["index"], "channel": note["channel"] + 1,
            "startTick": note["on"]["tick"], "endTick": note["off"]["tick"],
            "pitch": note["pitch"], "velocity": note["on"]["data"][1]}


def selected_note_pairs(parsed, selection, repair_stats=None):
    requested_ids = {str(value) for value in selection.get("noteIds", [])}
    channels = {int(value) - 1 for value in selection.get("channels", [])}
    tracks = {int(value) for value in selection.get("tracks", [])}
    select_all = bool(selection.get("all"))
    output = []
    for track in parsed["tracks"]:
        pairs = midi_optimizer.pair_notes(track, repair=repair_stats is not None, stats=repair_stats)
        midi_optimizer.attach_instruments(track, pairs)
        for note in pairs:
            identifier = note_id(track, note)
            selected = (identifier in requested_ids or note["channel"] in channels
                        or track["index"] in tracks or select_all)
            if selected:
                note["editorId"] = identifier
                output.append((track, note))
    return output


def profile_for(note, indexes):
    profile, selection = midi_optimizer.resolve_profile(note, indexes, with_selection=True)
    if selection["ambiguous"]:
        return None
    return profile


def validate_request(request):
    if not isinstance(request, dict):
        raise ValueError("Editor zahtjev mora biti JSON objekt")
    operation = request.get("operation")
    if operation not in ALLOWED_OPERATIONS:
        raise ValueError("Nepodržana editor operacija")
    selection = request.get("selection") or {}
    if not isinstance(selection, dict):
        raise ValueError("Neispravan selection objekt")
    if len(selection.get("noteIds", [])) > 10_000:
        raise ValueError("Jedna operacija može obuhvatiti najviše 10.000 eksplicitno odabranih nota")
    return operation, selection, request.get("parameters") or {}


def apply_edits(data, profiles, request, source="song.mid", database_version="unknown", evidence=None):
    TruthEvidenceGate(Path(__file__).resolve().parent).assert_transform_allowed(
        evidence, {}, operation="MIDI edit/export"
    )
    operation, selection, parameters = validate_request(request)
    parsed = midi_optimizer.parse_smf(data)
    before_technical = midi_optimizer.technical_parameters(parsed)
    grid_division = int(parameters.get("division", 16) or 16)
    if grid_division not in (8, 16, 32):
        raise ValueError("Editor quantize podržava 1/8, 1/16 ili 1/32")
    if parsed["division"] & 0x8000 and operation in ("move", "quantize", "duplicate"):
        raise ValueError("Ova editor operacija nije podržana za SMPTE timebase")
    ppq = None if parsed["division"] & 0x8000 else parsed["division"]
    before_audit = midi_optimizer.audit_tracks(parsed)
    changes = Counter()
    selected = selected_note_pairs(parsed, selection, changes)
    if not selected:
        raise ValueError("Nije odabrana nijedna MIDI nota")
    log, manual_overrides = [], 0
    indexes = midi_optimizer.profile_indexes(profiles)

    def remember(track, note, before):
        if len(log) < 500:
            log.append({"before": before, "after": snapshot(track, note)})

    if operation in ("move", "transpose"):
        semitones = int(parameters.get("semitones", parameters.get("deltaPitch", 0)))
        semitones = max(-48, min(48, semitones))
        delta_ticks = int(parameters.get("deltaTicks", 0)) if operation == "move" else 0
        if ppq:
            delta_ticks = max(-ppq * 16, min(ppq * 16, delta_ticks))
        include_drums = bool(parameters.get("includeDrums", False))
        for track, note in selected:
            if note["channel"] == 9 and not include_drums and semitones:
                continue
            before = snapshot(track, note)
            pitch = max(0, min(127, note["pitch"] + semitones))
            note["pitch"] = pitch
            note["on"]["data"][0] = note["off"]["data"][0] = pitch
            if delta_ticks:
                duration = max(1, note["off"]["tick"] - note["on"]["tick"])
                start = max(0, note["on"]["tick"] + delta_ticks)
                note["on"]["tick"], note["off"]["tick"] = start, start + duration
            remember(track, note, before)
            changes["notesMoved" if operation == "move" else "notesTransposed"] += 1

    elif operation == "resize":
        requested_duration = parameters.get("durationTicks")
        delta = int(parameters.get("deltaTicks", 0))
        for track, note in selected:
            before = snapshot(track, note)
            duration = int(requested_duration) if requested_duration is not None else note["off"]["tick"] - note["on"]["tick"] + delta
            note["off"]["tick"] = note["on"]["tick"] + max(1, duration)
            remember(track, note, before)
            changes["notesResized"] += 1

    elif operation == "velocity":
        mode = parameters.get("mode", "set")
        policy = parameters.get("policy", "factory-clamp")
        requested = int(parameters.get("value", 96))
        for track, note in selected:
            before = snapshot(track, note)
            profile = profile_for(note, indexes)
            if mode == "factory-optimal" and profile:
                value = profile["velocity"]["optimal"]
            elif mode == "delta":
                value = note["on"]["data"][1] + requested
            else:
                value = requested
            value = max(1, min(127, value))
            if profile and policy != "manual-override":
                value = max(profile["velocity"]["min"], min(profile["velocity"]["max"], value))
            elif profile and not profile["velocity"]["min"] <= value <= profile["velocity"]["max"]:
                manual_overrides += 1
            if not profile:
                changes["factoryProfilesMissing"] += 1
                if mode == "factory-optimal" or policy == "factory-clamp":
                    raise ValueError(
                        "Velocity izmjena zahtijeva jedinstven Factory profil; "
                        "nejasan ili nedostajući profil ide na manual review"
                    )
            note["on"]["data"][1] = value
            remember(track, note, before)
            changes["velocitiesEdited"] += 1

    elif operation == "quantize":
        strength = max(0, min(100, int(parameters.get("strength", 100))))
        grid_ticks = round(ppq * 4 / grid_division)
        all_notes_by_track = {}
        for candidate_track in parsed["tracks"]:
            candidate_notes = midi_optimizer.pair_notes(candidate_track)
            midi_optimizer.attach_instruments(candidate_track, candidate_notes)
            all_notes_by_track[candidate_track["index"]] = candidate_notes
        role_groups, _ = special_track_engine.analyze_roles(parsed, all_notes_by_track, ppq)
        solo_keys = {(group["track"]["index"], group["channel"])
                     for group in role_groups if group["role"] == "solo" and group["confidence"] >= .7}
        grouped = {}
        for track, note in selected:
            if (track["index"], note["channel"]) in solo_keys:
                changes["soloNotesQuantizeProtected"] += 1
                continue
            grouped.setdefault(track["index"], []).append(note)
        before_items = {(track["index"], note["editorId"]): snapshot(track, note) for track, note in selected}
        for notes in grouped.values():
            midi_optimizer.quantize_notes(notes, grid_ticks, strength, changes)
        for track, note in selected:
            remember(track, note, before_items[(track["index"], note["editorId"])])

    elif operation == "delete":
        for track, note in selected:
            before = snapshot(track, note)
            note["on"]["remove"] = note["off"]["remove"] = True
            if len(log) < 500:
                log.append({"before": before, "after": None})
            changes["notesDeleted"] += 1

    elif operation == "duplicate":
        offset = int(parameters.get("offsetTicks", ppq or 120))
        pitch_delta = max(-48, min(48, int(parameters.get("semitones", 0))))
        for track, note in selected:
            before = snapshot(track, note)
            order = max((event["order"] for event in track["events"]), default=0) + 1
            pitch = max(0, min(127, note["pitch"] + pitch_delta))
            start, end = max(0, note["on"]["tick"] + offset), max(1, note["off"]["tick"] + offset)
            if end <= start:
                end = start + 1
            on = {**note["on"], "tick": start, "order": order, "data": [pitch, note["on"]["data"][1]], "remove": False}
            off = {**note["off"], "tick": end, "order": order + 1, "data": [pitch, 0], "remove": False}
            track["events"].extend((on, off))
            track["endTick"] = max(track["endTick"], end)
            if len(log) < 500:
                log.append({"before": before, "after": {"track": track["index"], "channel": note["channel"] + 1,
                                                          "startTick": start, "endTick": end, "pitch": pitch,
                                                          "velocity": note["on"]["data"][1]}})
            changes["notesDuplicated"] += 1

    output = midi_optimizer.encode_smf(parsed)
    reparsed = midi_optimizer.parse_smf(output)
    after_audit = midi_optimizer.audit_tracks(reparsed)
    validation = midi_optimizer.validate_optimized_smf(reparsed, after_audit)
    after_technical = midi_optimizer.technical_parameters(reparsed)
    preserved = all(before_technical[key] == after_technical[key]
                    for key in ("format", "tracks", "ppq", "tempos", "meters", "markers", "sysexEvents", "soundSelections"))
    if not preserved:
        validation["issues"].append("Editor nije očuvao strukturne meta/program podatke")
        validation["passed"] = False
    if not validation["passed"]:
        raise ValueError("Editor validator blokirao izvoz: " + "; ".join(validation["issues"][:5]))
    report = {
        "schema": "dna-midi-editor-report", "version": "1.0", "operation": operation,
        "source": {"fileName": source, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)},
        "output": {"sha256": hashlib.sha256(output).hexdigest(), "bytes": len(output)},
        "selection": {"requestedNoteIds": len(selection.get("noteIds", [])),
                      "selectedNotes": len(selected)},
        "parameters": parameters, "changes": dict(changes), "changeLog": log,
        "changeLogTruncated": len(selected) > len(log), "manualOverrides": manual_overrides,
        "quality": {"before": midi_optimizer.quality_score(before_audit),
                    "after": midi_optimizer.quality_score(after_audit)},
        "audit": {"databaseVersion": database_version, "interventionCount": sum(changes.values()),
                  "validationResult": "PASS"},
        "validation": validation,
        "invariants": {"originalOverwritten": False, "goldAffectsDynamics": False,
                       "soloTimingQuantized": False,
                       "structuralDataPreserved": preserved, "invalidMidiExported": False},
    }
    return output, report