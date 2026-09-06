#!/usr/bin/env python3
"""Deterministički, dokazivi Phase Arranger za MIDI songove.

Modul prvo izrađuje read-only plan. APPLY je dopušten samo za nesolo uloge,
točan Factory instrument profil i unaprijed izračunat transformation budget.
GOLD daje isključivo note/timing/gate; ritam-gitara dolazi samo iz Factory
strumming registryja. Bank Select i Program Change nisu u dosegu ovog modula.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter, defaultdict

import factory_velocity
import special_track_engine


MUTABLE_ROLES = {"drums", "bass", "rhythm-guitar", "chords", "pad", "accompaniment"}
GOLD_ROLE_MAP = {
    "drums": ("drums", "percussion"),
    "bass": ("bass",),
    "chords": ("accompaniment", "riff"),
    "pad": ("accompaniment",),
    "accompaniment": ("accompaniment", "riff", "power-riff"),
}


def _stable_hash(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def _meter_parts(meter):
    match = re.match(r"^(\d+)/(\d+)$", str(meter or "4/4"))
    return (int(match.group(1)), int(match.group(2))) if match else (4, 4)


def _bar_ticks(ppq, meter):
    numerator, denominator = _meter_parts(meter)
    return max(1, round(ppq * numerator * 4 / denominator))


def _registry_patterns(registry):
    if isinstance(registry, dict):
        return registry.get("patterns", [])
    return registry or []


def _phase_ranges(analysis, ppq):
    meter = analysis.get("meter", "4/4")
    bar_ticks = _bar_ticks(ppq, meter)
    sections = analysis.get("sections") or [{
        "name": "Cijeli song", "type": "song", "startBar": 1,
        "bars": max(1, int(analysis.get("bars", 1))), "intensity": 50,
    }]
    output = []
    for index, section in enumerate(sections):
        start_bar = max(1, int(section.get("startBar", 1)))
        bars = max(1, int(section.get("bars", 1)))
        output.append({
            "index": index, "name": section.get("name") or f"Faza {index + 1}",
            "type": section.get("type", "section"), "startBar": start_bar,
            "endBar": start_bar + bars - 1, "bars": bars,
            "startTick": (start_bar - 1) * bar_ticks,
            "endTick": (start_bar - 1 + bars) * bar_ticks,
            "intensity": max(0, min(100, int(section.get("intensity", 50)))),
            "density": section.get("density", {}),
            "confidence": float(section.get("confidence", 0)),
            "labelStatus": section.get("labelStatus", "heuristic-candidate"),
        })
    return output


def _notes_in_phase(group, phase):
    return [note for note in group["notes"]
            if not note["on"].get("remove")
            and phase["startTick"] <= note["on"]["tick"] < phase["endTick"]]


def _instrument_key(notes):
    keys = Counter(note.get("instrumentKey") for note in notes if note.get("instrumentKey"))
    return keys.most_common(1)[0][0] if keys else None


def _section_score(pattern, phase):
    source = str(pattern.get("sourceSection", "")).lower()
    target = str(phase.get("type", "")).lower()
    aliases = {
        "intro": {"intro", "opening"}, "ending": {"ending", "outro"},
        "chorus": {"chorus", "variation", "main"},
        "verse": {"verse", "variation", "main"},
        "bridge": {"bridge", "transition", "fill"},
    }
    return 1.0 if source in aliases.get(target, {target}) else .58 if source in {"main", "variation"} else .32


def _tempo_score(pattern, tempo):
    low, high = (pattern.get("tempoRange") or [tempo, tempo])[:2]
    if low <= tempo <= high:
        return 1.0
    distance = min(abs(tempo - low), abs(tempo - high))
    return max(0.0, 1.0 - distance / 80)


def _density_score(pattern, existing_density):
    target = max(.01, float(pattern.get("density", 0) or 0))
    return max(0.0, 1.0 - abs(existing_density - target) / max(target, existing_density, 1.0))


def _candidate_pool(role, meter, gold_registry, strum_registry):
    if role == "rhythm-guitar":
        source, authority = _registry_patterns(strum_registry), "factory-strumming-only"
        pool = [item for item in source if item.get("role") == "factory-strum"]
    else:
        source, authority = _registry_patterns(gold_registry), "gold-performance-no-dynamics-or-program"
        allowed = GOLD_ROLE_MAP.get(role, ())
        pool = [item for item in source if item.get("role") in allowed]
    exact = [item for item in pool if item.get("meter") == meter]
    return (exact or pool), authority


def _rank_candidate(role, phase, meter, tempo, density, candidates, authority, seed):
    ranked = []
    for pattern in candidates:
        confidence = float(pattern.get("confidence", 0))
        quality = float(pattern.get("qualityScore", 0)) / 100
        scores = {
            "role": 1.0,
            "meter": 1.0 if pattern.get("meter") == meter else 0.0,
            "tempo": _tempo_score(pattern, tempo),
            "section": _section_score(pattern, phase),
            "density": _density_score(pattern, density),
            "harmony": 1.0 if role == "drums" else min(1.0, .55 + .45 * float(
                (pattern.get("harmonicAnchor") or {}).get("confidence", .5))),
            "registerArticulation": .82 if pattern.get("register") else .55,
            "evidence": min(1.0, .58 * confidence + .42 * quality),
            "transition": .9 if phase["type"] in ("intro", "ending", "bridge")
                           and pattern.get("transitionContext") else .68,
            "budget": 1.0 if len(pattern.get("events") or pattern.get("notes") or []) <= 512 else .4,
        }
        weights = {"role": .15, "meter": .12, "tempo": .10, "section": .12,
                   "density": .14, "harmony": .09, "registerArticulation": .08,
                   "evidence": .10, "transition": .05, "budget": .05}
        total = sum(scores[key] * weights[key] for key in weights)
        tie = _stable_hash([seed, phase["index"], role, pattern.get("id")])
        ranked.append((round(total, 6), tie, pattern, scores))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (-item[0], item[1]))
    total, _, pattern, scores = ranked[0]
    alternatives = [{"id": item[2].get("id"), "score": item[0]} for item in ranked[1:4]]
    return {
        "id": pattern.get("id"), "role": pattern.get("role"),
        "authority": authority, "score": total,
        "criteria": {key: round(value, 4) for key, value in scores.items()},
        "alternatives": alternatives,
        "selectionHash": _stable_hash([seed, role, phase["index"], pattern.get("id"), scores]),
    }


def _profile_coverage(role, notes, selection, profiles_by_key, gold_registry, strum_registry):
    key = _instrument_key(notes)
    exact = profiles_by_key.get(key) if key else None
    if role != "drums":
        return key, exact, 1.0 if exact and int(exact.get("samples", 0)) >= 32 else 0.0
    if not selection:
        return key, exact, 0.0
    pattern = _pattern_by_id(selection["id"], gold_registry, strum_registry)
    events = (pattern or {}).get("events") or (pattern or {}).get("notes") or []
    base = (key or "drum:0:0:0:0").split(":")
    if len(base) < 5:
        return key, exact, 0.0
    covered = 0
    for event in events:
        pitch = int(event[2])
        profile = profiles_by_key.get(":".join(["drum", base[1], base[2], base[3], str(pitch)]))
        covered += bool(profile and int(profile.get("samples", 0)) >= 32)
    return key, exact, covered / max(1, len(events))


def build_phase_plan(parsed, notes_by_track, analysis, profiles_by_key,
                     gold_registry, strum_registry, options=None, seed=None,
                     allow_replace=None):
    """Izradi JSON plan bez izmjene parsed MIDI modela."""
    options = dict(options or {})
    if seed is not None:
        options["seed"] = seed
    if allow_replace is not None:
        options["allowPhaseReplace"] = allow_replace
    ppq = parsed.get("division", 0)
    if not ppq or ppq & 0x8000:
        return {"schema": "dna-phase-plan", "version": "1.0", "enabled": False,
                "reason": "SMPTE timebase nije podržan", "decisions": [],
                "dryRun": True, "sourceMutated": False}
    seed = int(options.get("seed", analysis.get("suggestedSeed", 0)))
    allow_replace = bool(options.get("allowPhaseReplace", False))
    tempo, meter = float(analysis.get("tempo", 120)), analysis.get("meter", "4/4")
    phases = _phase_ranges(analysis, ppq)
    groups, public_roles = special_track_engine.analyze_roles(parsed, notes_by_track, ppq)
    decisions = []
    for group in groups:
        for phase in phases:
            notes = _notes_in_phase(group, phase)
            if not notes:
                continue
            role = group["role"]
            base = {
                "phase": {key: phase[key] for key in ("index", "name", "type", "startBar", "endBar",
                                                        "startTick", "endTick", "bars", "intensity")},
                "track": group["track"]["index"], "channel": group["channel"] + 1,
                "trackName": group["trackName"] or f"Track {group['track']['index'] + 1}",
                "role": role, "roleConfidence": round(float(group["confidence"]), 4),
                "sourceNotes": len(notes), "sourceTimingProtected": role == "solo",
            }
            if role == "solo" and group["confidence"] >= .7:
                decisions.append({**base, "action": "KEEP",
                                  "reason": "protected-solo-melody-and-timing",
                                  "candidate": None, "budget": {"remove": 0, "insert": 0}})
                continue
            if role not in MUTABLE_ROLES:
                decisions.append({**base, "action": "KEEP", "reason": "unsupported-or-low-confidence-role",
                                  "candidate": None, "budget": {"remove": 0, "insert": 0}})
                continue
            density = len(notes) / max(1, phase["bars"])
            pool, authority = _candidate_pool(role, meter, gold_registry, strum_registry)
            selection = _rank_candidate(role, phase, meter, tempo, density, pool, authority, seed)
            profile_key, profile, coverage = _profile_coverage(
                role, notes, selection, profiles_by_key, gold_registry, strum_registry)
            evidence_ok = bool(selection and coverage >= (.7 if role == "drums" else 1.0))
            target_density = float((_pattern_by_id(selection["id"], gold_registry, strum_registry)
                                    if selection else {}).get("density", density) or density)
            mismatch = abs(density - target_density) / max(1.0, density, target_density)
            if not evidence_ok:
                action, reason = "MANUAL_REVIEW", "missing-exact-factory-profile-or-pattern-evidence"
            elif allow_replace and mismatch >= .45:
                action, reason = "REPLACE", "phase-density-and-role-mismatch"
            elif mismatch >= .2:
                action, reason = "REPAIR", "bounded-phase-density-repair"
            else:
                action, reason = "KEEP", "existing-performance-compatible"
            remove_budget = len(notes) if action == "REPLACE" else 0
            insert_budget = (len(notes) if action == "REPLACE"
                             else min(8, max(1, math.ceil(len(notes) * .08))) if action == "REPAIR" else 0)
            decisions.append({
                **base, "action": action, "reason": reason,
                "section": base["phase"],
                "candidate": selection, "instrumentKey": profile_key,
                "factoryProfileId": profile.get("id") if profile else None,
                "factoryCoverage": round(coverage, 4),
                "density": {"source": round(density, 4), "candidate": round(target_density, 4),
                            "mismatch": round(mismatch, 4)},
                "budget": {"remove": remove_budget, "insert": insert_budget},
            })
    summary = Counter(item["action"] for item in decisions)
    total_notes = sum(len(notes) for notes in notes_by_track.values())
    plan = {
        "schema": "dna-phase-plan", "version": "1.0", "enabled": True,
        "seed": seed, "dryRun": True, "readOnly": True, "sourceMutated": False,
        "analysisHash": _stable_hash({"sections": analysis.get("sections", []),
                                      "chords": analysis.get("chordTimeline", {})}),
        "roles": public_roles, "phases": phases, "decisions": decisions,
        "summary": {key: summary.get(key, 0) for key in ("KEEP", "REPAIR", "REPLACE", "MANUAL_REVIEW")},
        "decisionCounts": {key: summary.get(key, 0)
                           for key in ("KEEP", "REPAIR", "REPLACE", "MANUAL_REVIEW")},
        "budgets": {"sourceNotes": total_notes,
                    "globalNetInsertLimit": min(4000, max(8, math.ceil(total_notes * .12)))},
        "authority": {"velocity": "factory-only", "programChange": "original-midi-only",
                      "rhythmGuitar": "factory-strumming-only",
                      "otherPerformance": "gold-notes-timing-gate-only"},
        "invariants": {"soloTimingMutable": False, "goldAffectsVelocity": False,
                       "goldAffectsProgramChange": False, "planBeforeMutation": True},
    }
    plan["planHash"] = _stable_hash(plan)
    return plan


def _pattern_by_id(pattern_id, gold_registry, strum_registry):
    if not pattern_id:
        return None
    for registry in (gold_registry, strum_registry):
        for pattern in _registry_patterns(registry):
            if pattern.get("id") == pattern_id:
                return pattern
    return None


def _chord_root(analysis, tick):
    cells = (analysis.get("chordTimeline") or {}).get("cells", [])
    for cell in cells:
        if cell.get("startTick", 0) <= tick < cell.get("endTick", 0):
            return cell.get("root")
    return (analysis.get("key") or {}).get("root", 0)


def _nearest_pitch_class(root, center):
    candidates = [pitch for pitch in range(128) if pitch % 12 == root % 12]
    return min(candidates, key=lambda pitch: (abs(pitch - center), pitch))


def _fold_pitch(pitch, profile):
    register = (profile or {}).get("register") or {}
    low, high = int(register.get("low", 0)), int(register.get("high", 127))
    candidates = [pitch + 12 * octave for octave in range(-10, 11)
                  if low <= pitch + 12 * octave <= high and 0 <= pitch + 12 * octave <= 127]
    return min(candidates, key=lambda value: (abs(value - pitch), value)) if candidates else None


def _group_lookup(parsed, notes_by_track):
    groups, _ = special_track_engine.analyze_roles(parsed, notes_by_track, parsed["division"])
    return {(group["track"]["index"], group["channel"] + 1): group for group in groups}


def _add_note(track, channel, pitch, start, end, velocity, order):
    on = {"tick": start, "order": order, "status": 0x90 | channel, "kind": "channel",
          "command": 9, "channel": channel, "data": [pitch, velocity], "remove": False,
          "phaseGenerated": True}
    off = {"tick": max(start + 1, end), "order": order + 1, "status": 0x80 | channel,
           "kind": "channel", "command": 8, "channel": channel, "data": [pitch, 0],
           "remove": False, "phaseGenerated": True}
    track["events"].extend((on, off))
    track["endTick"] = max(track["endTick"], off["tick"])
    return order + 2


def _event_profile(role, pitch, instrument_key, profiles_by_key):
    if role != "drums":
        return profiles_by_key.get(instrument_key)
    parts = (instrument_key or "").split(":")
    if len(parts) < 5:
        return None
    key = ":".join(["drum", parts[1], parts[2], parts[3], str(pitch)])
    return profiles_by_key.get(key)


def _generated_events(decision, pattern, analysis, profiles_by_key, ppq):
    raw = pattern.get("events") or pattern.get("notes") or []
    if not raw:
        return []
    phase = decision["phase"]
    start_tick, end_tick = phase["startTick"], phase["endTick"]
    resolution = max(1, int(pattern.get("timingResolution", 96)))
    meter_ticks = _bar_ticks(ppq, analysis.get("meter", "4/4"))
    pattern_ticks = max(1, int(pattern.get("lengthBars", 1)) * meter_ticks)
    instrument_key = decision.get("instrumentKey")
    source_center = 60
    profile = profiles_by_key.get(instrument_key)
    if profile:
        register = profile.get("register") or {}
        source_center = round((int(register.get("low", 48)) + int(register.get("high", 72))) / 2)
    generated = []
    cycle = 0
    while start_tick + cycle * pattern_ticks < end_tick:
        cycle_start = start_tick + cycle * pattern_ticks
        for item in raw:
            if len(item) < 3:
                continue
            onset = cycle_start + round(float(item[0]) * ppq / resolution)
            if onset >= end_tick:
                continue
            duration = max(1, round(float(item[1]) * ppq / resolution))
            raw_pitch = int(item[2])
            if decision["role"] == "drums":
                pitch = raw_pitch
            else:
                root = _chord_root(analysis, onset)
                if root is None:
                    root = (analysis.get("key") or {}).get("root", 0)
                pitch = _nearest_pitch_class(root, source_center) + raw_pitch
            event_profile = _event_profile(decision["role"], pitch, instrument_key, profiles_by_key)
            pitch = _fold_pitch(pitch, event_profile)
            if pitch is None or not event_profile or int(event_profile.get("samples", 0)) < 32:
                continue
            velocity = factory_velocity.velocity_at(event_profile, phase["intensity"])
            generated.append((onset, min(end_tick, onset + duration), pitch, velocity,
                              event_profile.get("id")))
        cycle += 1
    return generated


def apply_phase_plan(parsed, notes_by_track, plan, analysis, profiles_by_key,
                     gold_registry, strum_registry, stats=None):
    """Primijeni prethodno izračunat plan; solo i protected evente ne dira."""
    stats = stats if stats is not None else Counter()
    if not plan.get("enabled"):
        return {"enabled": False, "planHash": plan.get("planHash"), "applied": [],
                "budgets": plan.get("budgets", {})}
    groups = _group_lookup(parsed, notes_by_track)
    global_limit = int(plan.get("budgets", {}).get("globalNetInsertLimit", 0))
    net_inserted = 0
    applied = []
    for decision in plan.get("decisions", []):
        action = decision.get("action")
        if action not in ("REPAIR", "REPLACE") or decision.get("sourceTimingProtected"):
            continue
        group = groups.get((decision["track"], decision["channel"]))
        pattern = _pattern_by_id((decision.get("candidate") or {}).get("id"),
                                 gold_registry, strum_registry)
        if not group or not pattern:
            continue
        phase = decision["phase"]
        source_notes = [note for note in group["notes"] if not note["on"].get("remove")
                        and phase["startTick"] <= note["on"]["tick"] < phase["endTick"]]
        generated = _generated_events(decision, pattern, analysis, profiles_by_key, parsed["division"])
        if not generated:
            applied.append({"track": decision["track"], "channel": decision["channel"],
                            "phase": phase["name"], "action": action, "removed": 0, "inserted": 0,
                            "status": "SKIPPED_NO_SAFE_FACTORY_EVENTS"})
            continue
        removed = 0
        if action == "REPLACE":
            for note in source_notes[:int(decision["budget"]["remove"])]:
                note["on"]["remove"] = note["off"]["remove"] = True
                removed += 1
            stats["phaseNotesRemoved"] += removed
        requested = int(decision["budget"]["insert"])
        allowed = requested if action == "REPAIR" else min(requested, removed + max(0, global_limit - net_inserted))
        existing = {(note["on"]["tick"], note["pitch"]) for note in source_notes if not note["on"].get("remove")}
        track, channel = group["track"], group["channel"]
        next_order = max((event["order"] for event in track["events"]), default=0) + 1
        inserted = 0
        for start, end, pitch, velocity, profile_id in generated:
            if inserted >= allowed or (start, pitch) in existing:
                continue
            next_order = _add_note(track, channel, pitch, start, end, velocity, next_order)
            existing.add((start, pitch))
            inserted += 1
            stats["phaseNotesInserted"] += 1
            if action == "REPAIR" or inserted > removed:
                net_inserted += 1
                if net_inserted >= global_limit:
                    break
        applied.append({"track": decision["track"], "channel": decision["channel"],
                        "phase": phase["name"], "action": action, "removed": removed,
                        "inserted": inserted, "candidateId": pattern.get("id"),
                        "factoryVelocityOnly": True, "status": "APPLIED" if inserted else "NO_CHANGE"})
        if inserted:
            stats["phaseReplaceApplied" if action == "REPLACE" else "phaseRepairApplied"] += 1
    budgets_passed = net_inserted <= global_limit
    return {
        "enabled": True, "planHash": plan.get("planHash"), "applied": applied,
        "decisionsApplied": sum(item["status"] == "APPLIED" for item in applied),
        "budgetsPassed": budgets_passed,
        "budgets": {**plan.get("budgets", {}), "netInserted": net_inserted,
                    "limitRespected": budgets_passed},
        "invariants": {"soloTimingChanged": False, "programChangeChanged": False,
                       "trackCountChanged": False, "goldVelocityUsed": False,
                       "goldProgramChangeUsed": False},
    }


def plan_midi(data, profiles, gold_registry, strum_registry, analysis, options=None):
    """Javni read-only helper za API i testove."""
    import midi_optimizer  # lokalno radi izbjegavanja import ciklusa

    parsed = midi_optimizer.parse_smf(data)
    notes_by_track = {}
    for track in parsed["tracks"]:
        notes = midi_optimizer.pair_notes(track, repair=False)
        midi_optimizer.attach_instruments(track, notes)
        notes_by_track[track["index"]] = notes
    profiles_by_key = {item["instrumentKey"]: item for item in profiles}
    return build_phase_plan(parsed, notes_by_track, analysis, profiles_by_key,
                            gold_registry, strum_registry, options)