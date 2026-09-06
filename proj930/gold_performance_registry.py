#!/usr/bin/env python3
"""GOLD performance registry without velocity, Bank Select or Program Change.

The builder uses sound/program information only while classifying source tracks.
That transient evidence is never serialized. Runtime patterns contain musical
timing, gates, drum identities or harmonic offsets and full source proof.
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict

import gold_schema
import midi_optimizer


RUNTIME_RESOLUTION = 96  # ticks per quarter; preserves timing far beyond 1/16


def numeric_id(namespace, canonical):
    raw = hashlib.sha256((namespace + "\0" + canonical).encode("utf-8")).digest()
    return ".".join(f"{int.from_bytes(raw[index:index + 4], 'big') % 1000:03d}"
                    for index in (0, 4, 8))


def _track_name(track):
    for event in track["events"]:
        if event["kind"] == "meta" and event["metaType"] == 3:
            return event["payload"].decode("utf-8", "replace").strip("\0 ")
    return ""


def _meter(parsed):
    for track in parsed["tracks"]:
        for event in track["events"]:
            if event["kind"] == "meta" and event["metaType"] == 88 and len(event["payload"]) >= 2:
                return max(1, event["payload"][0]), 2 ** event["payload"][1]
    return 4, 4


def _tempo(parsed):
    for track in parsed["tracks"]:
        for event in track["events"]:
            if event["kind"] == "meta" and event["metaType"] == 81 and len(event["payload"]) == 3:
                micros = int.from_bytes(event["payload"], "big")
                if micros:
                    return round(60_000_000 / micros, 3)
    return 120.0


def _max_polyphony(notes):
    sweep = []
    for note in notes:
        sweep.extend(((note["on"]["tick"], 1), (note["off"]["tick"], -1)))
    active = maximum = 0
    for _, change in sorted(sweep, key=lambda item: (item[0], item[1])):
        active += change
        maximum = max(maximum, active)
    return maximum


def _role(notes, channel, name):
    """Classify source evidence; program is intentionally not returned."""
    if channel == 9:
        main = sum(note["pitch"] in (35, 36, 37, 38, 40, 42, 44, 46, 49, 51, 57)
                   for note in notes)
        return "drums" if main / max(1, len(notes)) >= .42 else "percussion"
    pitches = [note["pitch"] for note in notes]
    median_pitch = statistics.median(pitches)
    programs = Counter(note.get("program", 0) for note in notes)
    program = programs.most_common(1)[0][0] if programs else 0
    onsets = defaultdict(list)
    for note in notes:
        onsets[note["on"]["tick"]].append(note["pitch"])
    poly_ratio = sum(len(values) > 1 for values in onsets.values()) / max(1, len(onsets))
    fifth_ratio = sum(any(abs(a - b) in (5, 7, 12, 19) for a in values for b in values if a != b)
                      for values in onsets.values()) / max(1, len(onsets))
    lowered = name.lower()
    if 32 <= program <= 39 or (median_pitch < 48 and _max_polyphony(notes) <= 2):
        return "bass"
    if 24 <= program <= 31:
        # GOLD may provide power/riff behavior, never rhythm-guitar strumming.
        return "power-riff" if fifth_ratio >= .18 else None
    if any(word in lowered for word in ("solo", "lead", "melody", "vocal")):
        return None  # protected solo material is not a replacement rhythm pattern
    if fifth_ratio >= .28 and poly_ratio >= .12:
        return "power-riff"
    if poly_ratio >= .2 or _max_polyphony(notes) >= 3:
        return "accompaniment"
    repeated = len(onsets) >= 4 and len(set(pitches)) <= max(4, len(pitches) // 3)
    return "riff" if repeated else None


def _harmonic_anchor(notes):
    histogram = Counter(note["pitch"] % 12 for note in notes)
    total = sum(histogram.values())
    candidates = []
    for root in range(12):
        for quality, intervals in (("major", (0, 4, 7)), ("minor", (0, 3, 7))):
            pcs = {(root + interval) % 12 for interval in intervals}
            support = sum(histogram[pitch] for pitch in pcs)
            root_support = histogram[root]
            score = support + root_support * .35 - (total - support) * .15
            candidates.append((score, support / max(1, total), root_support, root, quality))
    score, confidence, _, root, quality = max(candidates)
    return {"model": "note-derived-triad-v1", "rootPitchClass": root, "quality": quality,
            "confidence": round(confidence, 4), "deviceChordEventUsed": False,
            "score": round(score, 4)}


def _section(bar, total_bars, events):
    if bar < 2:
        return "intro"
    if bar >= max(2, total_bars - 2):
        return "ending"
    if not events:
        return "body"
    final_quarter = sum(event[0] >= max(item[0] for item in events) * .75 for event in events)
    return "transition" if final_quarter / len(events) >= .38 else "body"


def _drum_element(pitch):
    if pitch in (35, 36): return "kick"
    if pitch in (37, 38, 40): return "snare"
    if pitch in (42, 44): return "closed-hat"
    if pitch == 46: return "open-hat"
    if pitch in (49, 52, 55, 57): return "crash"
    if pitch in (51, 53, 59): return "ride"
    if pitch in (41, 43, 45, 47, 48, 50): return "tom"
    return "percussion"


def build_registry(files):
    unique, errors, rejected = {}, [], Counter()
    id_registry, source_registry = {}, {}
    evidence_to_canonical = defaultdict(dict)
    for source, data in files:
        source_hash = hashlib.sha256(data).hexdigest()
        source_id = numeric_id("gold-performance-source-v1", source_hash)
        previous_source = source_registry.setdefault(source_id, source_hash)
        if previous_source != source_hash:
            raise ValueError(f"GOLD source ID collision: {source_id}")
        try:
            parsed = midi_optimizer.parse_smf(data)
        except Exception as error:
            errors.append({"file": source, "error": str(error)})
            continue
        ppq = parsed["division"]
        if ppq & 0x8000:
            rejected["smpte"] += 1
            continue
        numerator, denominator = _meter(parsed)
        meter = f"{numerator}/{denominator}"
        bar_ticks = max(1, round(ppq * numerator * 4 / denominator))
        tempo = _tempo(parsed)
        max_tick = max((track["endTick"] for track in parsed["tracks"]), default=bar_ticks)
        total_bars = max(1, math.ceil(max_tick / bar_ticks))
        for track in parsed["tracks"]:
            pairs = midi_optimizer.pair_notes(track)
            if not pairs:
                continue
            midi_optimizer.attach_instruments(track, pairs)
            grouped = defaultdict(list)
            for note in pairs:
                grouped[note["channel"]].append(note)
            for channel, notes in grouped.items():
                role = _role(notes, channel, _track_name(track))
                if not role:
                    rejected["protected-or-unsupported-role"] += 1
                    continue
                by_bar = defaultdict(list)
                for note in notes:
                    if note["off"]["tick"] - note["on"]["tick"] < max(1, ppq // 96):
                        rejected["micro-note"] += 1
                        continue
                    by_bar[note["on"]["tick"] // bar_ticks].append(note)
                # One-bar windows remain complete patterns; two-bar windows add phrase behavior.
                windows = [(bar, 1) for bar in sorted(by_bar)]
                windows += [(bar, 2) for bar in range(0, max(0, total_bars - 1), 2)
                            if by_bar.get(bar) and by_bar.get(bar + 1)]
                for start_bar, length_bars in windows:
                    selected = [note for bar in range(start_bar, start_bar + length_bars)
                                for note in by_bar.get(bar, [])]
                    if not 3 <= len(selected) <= 384:
                        rejected["note-count"] += 1
                        continue
                    origin = start_bar * bar_ticks
                    anchor = None if role in ("drums", "percussion") else _harmonic_anchor(selected)
                    root = anchor["rootPitchClass"] if anchor else 0
                    root_reference = min((pitch for note in selected for pitch in [note["pitch"]]
                                          if pitch % 12 == root), default=min(note["pitch"] for note in selected))
                    events = []
                    for note in selected:
                        onset = max(0, round((note["on"]["tick"] - origin) * RUNTIME_RESOLUTION / ppq))
                        duration = max(1, round((note["off"]["tick"] - note["on"]["tick"])
                                                * RUNTIME_RESOLUTION / ppq))
                        pitch = note["pitch"] if role in ("drums", "percussion") else note["pitch"] - root_reference
                        events.append([onset, duration, pitch])
                    events = sorted(set(map(tuple, events)))
                    if len({event[0] for event in events}) < 2:
                        rejected["single-position"] += 1
                        continue
                    section = _section(start_bar, total_bars, events)
                    semantic = Counter(_drum_element(event[2]) for event in events) if role in ("drums", "percussion") else Counter()
                    syncopation = sum(event[0] % (RUNTIME_RESOLUTION // 2) != 0 for event in events) / len(events)
                    first_limit = RUNTIME_RESOLUTION
                    end_limit = length_bars * numerator * RUNTIME_RESOLUTION * 4 / denominator - RUNTIME_RESOLUTION
                    transition = {"entryNotes": sum(event[0] < first_limit for event in events),
                                  "exitNotes": sum(event[0] >= end_limit for event in events),
                                  "startsWithRest": min(event[0] for event in events) > RUNTIME_RESOLUTION // 4,
                                  "endsWithSpace": max(event[0] + event[1] for event in events)
                                                   < length_bars * numerator * RUNTIME_RESOLUTION * 4 / denominator}
                    canonical_document = {"role": role, "meter": meter, "bars": length_bars,
                                          "resolution": RUNTIME_RESOLUTION, "events": events,
                                          "section": section,
                                          "anchor": None if not anchor else [anchor["quality"], root]}
                    canonical = json.dumps(canonical_document, sort_keys=True, separators=(",", ":"))
                    proof = {"sourceId": source_id, "sourceHash": source_hash,
                             "trackIndex": track["index"], "channel": channel + 1,
                             "measureRange": [start_bar + 1, start_bar + length_bars],
                             "tickRange": [origin, origin + length_bars * bar_ticks]}
                    row = unique.get(canonical)
                    if row:
                        row["occurrences"] += 1
                        row["sourceSections"][section] += 1
                        if len(row["sourceProof"]) < 16 and proof not in row["sourceProof"]:
                            row["sourceProof"].append(proof)
                    else:
                        unique[canonical] = {
                            "canonical": canonical, "role": role, "meter": meter,
                            "lengthBars": length_bars, "timingResolution": RUNTIME_RESOLUTION,
                            "tempoRange": [max(30, round(tempo * .86)), min(300, round(tempo * 1.14))],
                            "sourceSection": section, "sourceSections": Counter({section: 1}),
                            "density": round(len(events) / length_bars, 3),
                            "register": {"low": min(event[2] for event in events),
                                         "high": max(event[2] for event in events)},
                            "harmonicAnchor": anchor or {"model": "drum-identity", "confidence": 1.0},
                            "pitchMode": "absolute-drum-note" if role in ("drums", "percussion")
                                         else "semitones-from-local-root",
                            "events": [list(event) for event in events],
                            "notes": [list(event) for event in events],
                            "articulation": {"medianGate": round(statistics.median(event[1] for event in events), 3),
                                             "syncopation": round(syncopation, 4)},
                            "drumElements": dict(sorted(semantic.items())),
                            "transitionContext": transition, "occurrences": 1,
                            "sourceProof": [proof], "sourceIds": [source_id],
                            "rejectionReasons": [],
                        }
                    evidence_to_canonical[(source_hash, start_bar, length_bars)][role] = canonical

    rejected["non-recurring-pattern"] = sum(row["occurrences"] < 2 for row in unique.values())
    patterns, canonical_to_id = [], {}
    for canonical, row in unique.items():
        if row["occurrences"] < 2:
            continue
        # Fixed namespace salt was selected before release so this corpus has
        # no cross-registry collision; any future collision still fails build.
        pattern_id = numeric_id("gold-performance-pattern-v1-salt1", canonical)
        canonical_hash = hashlib.sha256(canonical.encode()).hexdigest()
        previous = id_registry.setdefault(pattern_id, canonical_hash)
        if previous != canonical_hash:
            raise ValueError(f"GOLD performance ID collision: {pattern_id}")
        canonical_to_id[canonical] = pattern_id
        row.pop("canonical")
        row["id"] = pattern_id
        row["sourceSections"] = dict(sorted(row["sourceSections"].items()))
        row["sourceSection"] = max(row["sourceSections"], key=lambda key: (row["sourceSections"][key], key))
        row["sourceIds"] = sorted({proof["sourceId"] for proof in row["sourceProof"]})
        evidence = min(1.0, math.log2(row["occurrences"] + 1) / 7)
        harmonic = float(row["harmonicAnchor"].get("confidence", 1.0))
        row["confidence"] = round(.55 * evidence + .45 * harmonic, 4)
        row["qualityScore"] = round(100 * (.5 * row["confidence"]
                                            + .25 * min(1, len(row["events"]) / 24)
                                            + .25 * min(1, len(row["sourceIds"]) / 4)), 1)
        row["authority"] = {"musicalPattern": "gold",
                            "dynamicsEvidence": "none",
                            "soundSelectionEvidence": "none",
                            "rhythmGuitarStrumming": False}
        patterns.append(row)
    patterns.sort(key=lambda item: (-item["qualityScore"], -item["occurrences"], item["id"]))

    relationships = []
    relationship_ids = set()
    for evidence_key, roles in sorted(evidence_to_canonical.items()):
        mapped = {role: canonical_to_id[canonical] for role, canonical in roles.items()
                  if canonical in canonical_to_id}
        if "bass" not in mapped or not ({"drums", "percussion"} & set(mapped)):
            continue
        canonical = json.dumps(mapped, sort_keys=True, separators=(",", ":"))
        relation_id = numeric_id("gold-groove-relationship-v1", canonical)
        if relation_id in relationship_ids:
            continue
        relationship_ids.add(relation_id)
        source_hash, start_bar, length_bars = evidence_key
        relationships.append({"id": relation_id, "patterns": mapped,
                              "sourceHash": source_hash, "measureRange": [start_bar + 1, start_bar + length_bars],
                              "lengthBars": length_bars, "relationship": "shared-source-groove",
                              "dynamicsEvidence": "none"})

    validation = gold_schema.assert_valid_patterns(patterns)
    digest = hashlib.sha256()
    for item in patterns:
        digest.update(item["id"].encode("ascii"))
    return {
        "schema": "dna.gold-performance-patterns", "version": "1.1",
        "databaseVersion": "gold-performance-" + digest.hexdigest()[:16],
        "rules": {"source": "gold-only", "velocityDataIncluded": False,
                  "bankProgramIncluded": False, "runtimeResolution": RUNTIME_RESOLUTION,
                  "soloReplacementPatterns": False, "rhythmGuitarStrumming": False,
                  "idCollisionPolicy": "fail-build", "idFormat": "DDD.DDD.DDD-zero-padded"},
        "summary": {"inputFiles": len(files), "patterns": len(patterns),
                    "events": sum(len(item["events"]) for item in patterns),
                    "roles": dict(Counter(item["role"] for item in patterns)),
                    "relationships": len(relationships), "rejected": dict(rejected),
                    "errors": len(errors)},
        "schemaValidation": validation, "patterns": patterns,
        "relationships": relationships, "errors": errors,
    }