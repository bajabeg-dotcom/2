#!/usr/bin/env python3
"""Factory-only rhythm-guitar strumming evidence and runtime registry."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict


RUNTIME_RESOLUTION = 96
GUITAR_WORDS = ("guitar", "gtr", "nylon", "steel", "clean", "muted", "overdrive", "distortion")


def numeric_id(namespace, canonical):
    raw = hashlib.sha256((namespace + "\0" + canonical).encode("utf-8")).digest()
    return ".".join(f"{int.from_bytes(raw[index:index + 4], 'big') % 1000:03d}"
                    for index in (0, 4, 8))


def _is_guitar(segment):
    sound = segment.get("soundEvidence") or {}
    program = sound.get("program")
    name = (segment.get("soundName", "") + " " + segment.get("sourceStyle", "")).lower()
    return program is not None and 24 <= int(program) <= 31 or any(word in name for word in GUITAR_WORDS)


def _section(element):
    if element.startswith("intro"): return "intro"
    if element.startswith("ending"): return "ending"
    if element.startswith("fill") or element == "break": return "transition"
    return "body"


def _stroke_direction(notes):
    ordered = sorted(notes, key=lambda item: (item[0], item[2]))
    if len({item[0] for item in ordered}) == 1:
        return "block"
    pitch_change = ordered[-1][2] - ordered[0][2]
    if abs(pitch_change) < 3:
        return "mixed"
    return "down" if pitch_change > 0 else "up"


def build_registry(factory_style):
    unique, rejected = {}, Counter()
    id_registry = {}
    for segment in factory_style["segments"]:
        if not segment["role"].startswith("ACC") or not _is_guitar(segment):
            continue
        ppq = segment["ppq"]
        threshold = max(1, round(ppq / 32))
        notes = sorted(segment["notes"], key=lambda item: (item[0], item[2]))
        clusters, current = [], []
        for note in notes:
            if current and note[0] - current[-1][0] > threshold:
                clusters.append(current)
                current = []
            current.append(note)
        if current:
            clusters.append(current)
        strokes = [cluster for cluster in clusters if len({note[2] for note in cluster}) >= 3]
        if len(strokes) < 2:
            rejected["insufficient-strokes"] += 1
            continue
        source_min = min(note[3] for stroke in strokes for note in stroke)
        source_max = max(note[3] for stroke in strokes for note in stroke)
        events, stroke_rows, directions = [], [], Counter()
        for stroke_index, stroke in enumerate(strokes):
            stroke = sorted(stroke, key=lambda item: (item[0], item[2]))
            origin = min(note[0] for note in stroke)
            base_pitch = min(note[2] for note in stroke)
            direction = _stroke_direction(stroke)
            directions[direction] += 1
            stroke_event_indexes = []
            for note in stroke:
                onset = round(note[0] * RUNTIME_RESOLUTION / ppq)
                duration = max(1, round(note[1] * RUNTIME_RESOLUTION / ppq))
                relative_pitch = note[2] - base_pitch
                accent = 50 if source_max == source_min else round((note[3] - source_min) * 100 / (source_max - source_min))
                stroke_event_indexes.append(len(events))
                events.append([onset, duration, relative_pitch, accent, stroke_index])
            offsets = [round((note[0] - origin) * RUNTIME_RESOLUTION / ppq) for note in stroke]
            gates = [max(1, round(note[1] * RUNTIME_RESOLUTION / ppq)) for note in stroke]
            stroke_rows.append({"index": stroke_index, "onset": round(origin * RUNTIME_RESOLUTION / ppq),
                                "direction": direction, "chordSize": len(stroke),
                                "interStringOffsets": offsets,
                                "medianGate": round(statistics.median(gates), 3),
                                "shortGateEvidence": statistics.median(gates) <= RUNTIME_RESOLUTION / 4,
                                "eventIndexes": stroke_event_indexes})
        canonical_document = {"meter": segment["meter"], "bars": segment["bars"],
                              "element": segment["element"], "cv": segment["cv"],
                              "resolution": RUNTIME_RESOLUTION, "events": events,
                              "directions": [stroke["direction"] for stroke in stroke_rows]}
        canonical = json.dumps(canonical_document, sort_keys=True, separators=(",", ":"))
        proof = {"sourceId": segment["sourceId"], "sourceHash": segment["sourceHash"],
                 "trackIndex": segment["trackIndex"], "role": segment["role"],
                 "element": segment["element"], "cv": segment["cv"],
                 "tickRange": segment["tickRange"], "segmentId": segment["id"]}
        row = unique.get(canonical)
        if row:
            row["occurrences"] += 1
            if len(row["sourceProof"]) < 16 and proof not in row["sourceProof"]:
                row["sourceProof"].append(proof)
        else:
            unique[canonical] = {
                "canonical": canonical, "role": "factory-strum", "meter": segment["meter"],
                "lengthBars": segment["bars"], "timingResolution": RUNTIME_RESOLUTION,
                "tempoRange": [max(30, round(segment.get("tempo", 120) * .86)),
                               min(300, round(segment.get("tempo", 120) * 1.14))],
                "sourceSection": _section(segment["element"]), "sourceElement": segment["element"],
                "cv": segment["cv"], "density": round(len(events) / max(1, segment["bars"]), 3),
                "register": {"low": min(event[2] for event in events),
                             "high": max(event[2] for event in events)},
                "pitchMode": "factory-strum-relative-voicing",
                "events": events, "notes": [event[:4] for event in events],
                "strokes": stroke_rows, "directions": dict(directions),
                "articulation": {"shortGateStrokes": sum(item["shortGateEvidence"] for item in stroke_rows),
                                 "muteStopSemantics": "timing-evidence-only-no-control-note-synthesis"},
                "soundEvidence": segment.get("soundEvidence"),
                "factoryProfileIds": segment.get("factoryProfileIds", []),
                "occurrences": 1, "sourceProof": [proof],
            }
    patterns = []
    for canonical, row in unique.items():
        pattern_id = numeric_id("factory-strum-pattern-v1", canonical)
        canonical_hash = hashlib.sha256(canonical.encode()).hexdigest()
        previous = id_registry.setdefault(pattern_id, canonical_hash)
        if previous != canonical_hash:
            raise ValueError(f"Factory strum ID collision: {pattern_id}")
        row.pop("canonical")
        row["id"] = pattern_id
        evidence = min(1.0, math.log2(row["occurrences"] + 1) / 5)
        stroke_strength = min(1.0, len(row["strokes"]) / 8)
        row["confidence"] = round(.55 + .25 * evidence + .2 * stroke_strength, 4)
        row["qualityScore"] = round(row["confidence"] * 100, 1)
        row["authority"] = {"strumming": "factory-acc-only", "velocityShape": "factory",
                            "goldUsed": False, "guitarModeControlNotesSynthesized": False}
        patterns.append(row)
    patterns.sort(key=lambda item: (-item["qualityScore"], -item["occurrences"], item["id"]))
    digest = hashlib.sha256()
    for item in patterns:
        digest.update(item["id"].encode("ascii"))
    return {
        "schema": "dna.factory-strumming", "version": "1.1",
        "databaseVersion": "factory-strum-" + digest.hexdigest()[:16],
        "rules": {"source": "factory-acc-only", "goldUsed": False,
                  "genericArpeggioFallback": False, "guitarModeControlNotesSynthesized": False,
                  "runtimeResolution": RUNTIME_RESOLUTION,
                  "idCollisionPolicy": "fail-build", "idFormat": "DDD.DDD.DDD-zero-padded"},
        "summary": {"patterns": len(patterns), "events": sum(len(item["events"]) for item in patterns),
                    "strokes": sum(len(item["strokes"]) for item in patterns),
                    "directions": dict(sum((Counter(item["directions"]) for item in patterns), Counter())),
                    "elements": dict(Counter(item["sourceElement"] for item in patterns)),
                    "rejected": dict(rejected)},
        "patterns": patterns,
    }