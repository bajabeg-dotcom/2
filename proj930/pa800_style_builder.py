#!/usr/bin/env python3
"""Aktivni, transportno neovisan Pa800 Style Builder servis."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict

import style_intelligence


def build_style(config, context):
    tracks = context["tracks"]
    meter = config.get("meter", "4/4")
    numerator, denominator = (int(value) for value in meter.split("/"))
    tempo = max(30, min(300, int(config.get("tempo", 120))))
    seed = int(config.get("seed", 120111231))
    pattern_locks = config.get("patternLocks") or {}
    pattern_offsets = config.get("patternOffsets") or {}
    excluded_patterns = set(config.get("excludedPatternIds") or [])
    ppq = 480
    bar_ticks = round(ppq * numerator * 4 / denominator)
    elements = [item for item in config.get("elements", context["defaultElements"]) if item.get("enabled", True)]
    if not elements or any(not context["validMarker"](item.get("marker", "")) for item in elements):
        raise ValueError("Neispravan ili nedostajući Pa800 marker")
    if len({item["marker"] for item in elements}) != len(elements):
        raise ValueError("Pa800 markeri moraju biti jedinstveni")

    selected_tracks = {}
    for name in tracks:
        request = config.get("tracks", {}).get(name, {})
        if request.get("enabled", name in ("bass", "drum", "perc", "acc1", "acc2")):
            choice = context["findChoice"](name, request.get("profileId"))
            if choice:
                selected_tracks[name] = choice
    if not selected_tracks:
        raise ValueError("Uključi barem jednu Style traku")

    events = [{"tick": 0, "priority": 0, "data": context["metaText"](3, config.get("name", "DNA Pa800 Style")[:24])},
              {"tick": 0, "priority": 1, "data": context["tempoMeta"](tempo)}]
    manifest_elements, cursor, note_count = [], 0, 0
    quality = {"duplicatesRemoved": 0, "polyphonyNotesRemoved": 0, "polyphonyTailsTrimmed": 0,
               "overlapsTrimmed": 0,
               "voiceLeadingOctaveMoves": 0, "registerCollisionsResolved": 0,
               "factoryPerNoteDynamicsApplied": 0}
    active_notes, tick_occupancy, previous_centers, previous_patterns = {}, defaultdict(set), {}, {}
    for element_index, element in enumerate(elements):
        marker = element["marker"].lower()
        bars = max(1, min(32, int(element.get("bars", 2))))
        intensity = max(0, min(100, int(element.get("intensity", 60))))
        events.append({"tick": cursor, "priority": 0, "data": context["metaText"](6, marker)})
        events.append({"tick": cursor, "priority": 1, "data": context["meterMeta"](numerator, denominator)})
        pattern_ids, pattern_selection, musical_decisions = {}, {}, {}
        ordered_tracks = [name for name in ("drum", "perc", "bass", "acc1", "acc2", "acc3", "acc4", "acc5")
                          if name in selected_tracks]
        for track_name in ordered_tracks:
            choice = selected_tracks[track_name]
            info, channel = tracks[track_name], tracks[track_name]["channel"]
            events.extend([
                {"tick": cursor, "priority": 2, "data": [0xB0 | channel, 0, choice["bankMsb"]]},
                {"tick": cursor, "priority": 2, "data": [0xB0 | channel, 32, choice["bankLsb"]]},
                {"tick": cursor, "priority": 2, "data": [0xC0 | channel, choice["program"]]},
                {"tick": cursor, "priority": 2, "data": [0xB0 | channel, 11, 127]},
            ])
            lock_id = (pattern_locks.get(marker) or {}).get(track_name)
            offset = int((pattern_offsets.get(marker) or {}).get(track_name, 0))
            pattern_role = context["patternRole"](track_name, choice)
            pattern, ranking = context["choosePattern"](
                pattern_role, meter, seed, marker, track_name, intensity,
                lock_id, offset, excluded_patterns, tempo, bars,
                list(pattern_ids.values()), previous_patterns.get(track_name))
            if not pattern:
                continue
            pattern_ids[track_name] = pattern["id"]
            previous_patterns[track_name] = pattern["id"]
            pattern_selection[track_name] = {"patternId": pattern["id"], **ranking}
            notes, cleanup = context["preparedNotes"](pattern, track_name)
            notes, previous_centers[track_name], voice_leading = style_intelligence.voice_lead(
                notes, track_name, previous_centers.get(track_name))
            musical_decisions[track_name] = {"voiceLeading": voice_leading,
                                             "requestedPatternRole": pattern_role,
                                             "patternAuthority": cleanup["patternAuthority"],
                                             "trackGuidance": style_intelligence.track_recommendation(track_name)}
            quality["voiceLeadingOctaveMoves"] += int(voice_leading["applied"])
            pattern_bars = cleanup["patternLengthBars"]
            pattern_ticks = max(bar_ticks, pattern_bars * bar_ticks)
            element_end = cursor + bars * bar_ticks
            cycle_starts = list(range(cursor, element_end, pattern_ticks))
            quality["duplicatesRemoved"] += cleanup["duplicatesRemoved"] * len(cycle_starts)
            quality["polyphonyNotesRemoved"] += cleanup["polyphonyNotesRemoved"] * len(cycle_starts)
            quality["polyphonyTailsTrimmed"] += cleanup["polyphonyTailsTrimmed"] * len(cycle_starts)
            musical_decisions[track_name]["polyphony"] = {
                "limit": context["polyphonyLimits"][track_name],
                "peakBefore": cleanup["peakPolyphonyBefore"],
                "peakAfter": cleanup["peakPolyphonyAfter"],
                "tailsTrimmed": cleanup["polyphonyTailsTrimmed"],
                "notesRemoved": cleanup["polyphonyNotesRemoved"],
            }
            for cycle_start in cycle_starts:
                cycle_end = min(element_end, cycle_start + pattern_ticks)
                for position, duration, pitch, accent in notes:
                    start = cycle_start + position
                    if start >= element_end:
                        continue
                    pitch, collision_fixed = style_intelligence.resolve_unison(
                        pitch, track_name, tick_occupancy[start])
                    quality["registerCollisionsResolved"] += int(collision_fixed)
                    if track_name not in ("drum", "perc"):
                        tick_occupancy[start].add(pitch)
                    end = min(cycle_end, start + max(1, duration))
                    profile = context["drumProfile"](choice, pitch) if track_name in ("drum", "perc") else choice
                    note_intensity = context["noteIntensity"](
                        track_name, pitch, marker, intensity, accent)
                    velocity = context["velocityAt"](profile, note_intensity)
                    quality["factoryPerNoteDynamicsApplied"] += 1
                    note_key = (channel, pitch)
                    previous = active_notes.get(note_key)
                    if previous and start < previous["off"]["tick"]:
                        if start == previous["start"]:
                            previous["off"]["tick"] = max(previous["off"]["tick"], end)
                            quality["duplicatesRemoved"] += 1
                            continue
                        previous["off"]["tick"] = max(previous["start"] + 1, start)
                        quality["overlapsTrimmed"] += 1
                    on_event = {"tick": start, "priority": 4, "data": [0x90 | channel, pitch, velocity]}
                    off_event = {"tick": end, "priority": 3, "data": [0x80 | channel, pitch, 0]}
                    events.extend((on_event, off_event))
                    active_notes[note_key] = {"start": start, "off": off_event}
                    note_count += 1
        next_marker = elements[element_index + 1]["marker"].lower() if element_index + 1 < len(elements) else None
        manifest_elements.append({"marker": marker, "bars": bars, "intensity": intensity,
                                  "patterns": pattern_ids, "patternSelection": pattern_selection,
                                  "musicalDecisions": musical_decisions,
                                  "transition": style_intelligence.transition_recommendation(marker, next_marker)})
        cursor += bars * bar_ticks
    events.append({"tick": cursor, "priority": 9, "data": [0xFF, 0x2F, 0]})
    midi = context["smf0"](events, ppq)
    compliance = context["validate"](
        midi, [item["marker"] for item in manifest_elements],
        [tracks[name]["channel"] for name in selected_tracks])
    if not compliance["passed"]:
        raise ValueError("Pa800 validator: " + "; ".join(compliance["issues"][:5]))

    factory, gold = context["factory"], context["gold"]
    factory_version = factory.get("databaseVersion", factory.get("version", "unknown"))
    gold_version = gold.get("databaseVersion", gold.get("version", "unknown"))
    factory_strum_version = context["factoryStrum"].get("databaseVersion", "unknown")
    gold_performance_version = context["goldPerformance"].get("databaseVersion", "unknown")
    combined_version = hashlib.sha256(
        f"{factory_version}:{gold_version}:{factory_strum_version}:{gold_performance_version}".encode("utf-8")
    ).hexdigest()[:20]
    config_hash = hashlib.sha256(json.dumps(config, sort_keys=True, ensure_ascii=False,
                                            separators=(",", ":")).encode("utf-8")).hexdigest()
    output_hash = hashlib.sha256(midi).hexdigest()
    manifest = {
        "schema": "dna-korg-pa800-style", "version": "1.2", "target": "Korg Pa800 OS 2.0+",
        "seed": seed,
        "database": {"version": combined_version, "factory": factory_version, "gold": gold_version,
                     "factoryStrumming": factory_strum_version,
                     "goldPerformance": gold_performance_version},
        "determinism": {"sameSeedSameOutput": True, "configSha256": config_hash,
                        "selection": "ten-criteria-best-deterministic-set"},
        "midi": {"format": 0, "ppq": ppq, "tempo": tempo, "meter": meter, "noteCount": note_count,
                 "trackCount": 1, "usedChannels": [tracks[name]["channel"] + 1 for name in selected_tracks],
                 "sha256": output_hash},
        "rules": {"dynamicsSource": "factory-only", "goldAffectsDynamics": False,
                  "goldVelocityFields": 0, "goldAffectsProgramChange": False,
                  "rhythmGuitarStrummingSource": "factory-acc-only",
                  "fullGoldRhythmRoles": ["drums", "percussion", "bass", "power-riff", "riff", "accompaniment"],
                  "referenceKey": "C", "referenceChord": "Major"},
        "tracks": {name: {"channel": tracks[name]["channel"] + 1,
                          "polyphonyLimit": context["polyphonyLimits"][name],
                          "profileId": choice["id"],
                          "bankMsb": choice["bankMsb"], "bankLsb": choice["bankLsb"],
                          "program": choice["program"], "velocity": choice["velocity"],
                          "pa800Recommendation": style_intelligence.track_recommendation(name)}
                   for name, choice in selected_tracks.items()},
        "elements": manifest_elements,
        "quality": {**quality, "polyphonyLimits": context["polyphonyLimits"],
                    "peakPolyphonyByChannel": compliance["peakPolyphonyByChannel"],
                    "globalPeakConcurrentNotes": compliance["globalPeakConcurrentNotes"],
                    "polyphonyPassed": compliance["polyphonyPassed"],
                    "polyphonyMetric": compliance["polyphonyMetric"],
                    "physicalSoundVoiceCostVerified": False},
        "patternControls": {"locks": pattern_locks, "offsets": pattern_offsets,
                            "excludedPatternIds": sorted(excluded_patterns)},
        "compliance": compliance,
        "audit": {"inputHash": config_hash, "outputHash": output_hash, "seed": seed,
                  "databaseVersion": combined_version,
                  "interventionCount": sum(value for value in quality.values() if isinstance(value, int)),
                  "validationResult": "PASS"},
        "certification": {"software": "SOFTWARE_VALIDATED", "physicalPa800": "WAITING_FOR_DEVICE"},
        "pa800Import": {"mode": "Style Record > Import SMF", "initializeNewStyle": True,
                        "originalKey": "C", "originalChord": "Major",
                        "nttNote": "Sve Track Type i NTT vrijednosti su preporuke; potvrditi ih na Pa800 nakon uvoza."},
    }
    if config.get("songAnalysis"):
        manifest["songAnalysis"] = config["songAnalysis"]
    return midi, manifest