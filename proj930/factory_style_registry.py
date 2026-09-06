#!/usr/bin/env python3
"""Izgradnja stvarnog Factory Style/Chord Variation segment registryja."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter

import midi_optimizer


ELEMENTS = {
    "intro 1", "intro 2", "intro 3", "variation 1", "variation 2",
    "variation 3", "variation 4", "fill 1", "fill 2", "fill 3",
    "break", "ending 1", "ending 2", "ending 3",
}
CV_RE = re.compile(r"^(DRUMS|PERC|BASS|ACC[1-5])\s+CV([1-6])$", re.I)
BAR_RE = re.compile(r"^(\d+)\s+Bars?$", re.I)


def numeric_id(namespace, canonical):
    raw = hashlib.sha256((namespace + "\0" + canonical).encode("utf-8")).digest()
    return ".".join(f"{int.from_bytes(raw[index:index + 4], 'big') % 1000:03d}"
                    for index in (0, 4, 8))


def _texts(track):
    output = []
    for event in track["events"]:
        if event["kind"] == "meta" and event["metaType"] in (1, 3, 4, 6):
            text = event["payload"].decode("latin1", "replace").replace("\0", "").strip()
            if text:
                output.append(text)
    return output


def _meter(parsed):
    for track in parsed["tracks"]:
        for event in track["events"]:
            if event["kind"] == "meta" and event["metaType"] == 88 and len(event["payload"]) >= 2:
                return f"{event['payload'][0]}/{2 ** event['payload'][1]}"
    return "4/4"


def _tempo(parsed):
    for track in parsed["tracks"]:
        for event in track["events"]:
            if event["kind"] == "meta" and event["metaType"] == 81 and len(event["payload"]) == 3:
                micros = int.from_bytes(event["payload"], "big")
                if micros:
                    return round(60_000_000 / micros, 3)
    return 120.0


def _sound_evidence(track, notes):
    state = [{"msb": 0, "lsb": 0, "program": 0, "volume": None, "expression": None}
             for _ in range(16)]
    note_ids = {id(note["on"]) for note in notes}
    used = Counter()
    for event in sorted(track["events"], key=lambda item: (item["tick"], item["order"])):
        if event["kind"] != "channel":
            continue
        channel, command, data = event["channel"], event["command"], event["data"]
        if command == 11 and data[0] == 0:
            state[channel]["msb"] = data[1]
        elif command == 11 and data[0] == 32:
            state[channel]["lsb"] = data[1]
        elif command == 11 and data[0] == 7:
            state[channel]["volume"] = data[1]
        elif command == 11 and data[0] == 11:
            state[channel]["expression"] = data[1]
        elif command == 12:
            state[channel]["program"] = data[0]
        elif midi_optimizer.is_note_on(event) and id(event) in note_ids:
            current = state[channel]
            used[(channel, current["msb"], current["lsb"], current["program"],
                  current["volume"], current["expression"])] += 1
    if not used:
        return None
    (channel, msb, lsb, program, volume, expression), samples = used.most_common(1)[0]
    return {"channel": channel + 1, "bankMsb": msb, "bankLsb": lsb,
            "program": program, "volume": volume, "expression": expression,
            "noteSamples": samples}


def build_registry(files, profile_ids):
    segments, errors, rejected = [], [], Counter()
    id_registry, source_registry = {}, {}
    element_counts, role_counts, cv_counts = Counter(), Counter(), Counter()
    for source, data in files:
        source_hash = hashlib.sha256(data).hexdigest()
        source_id = numeric_id("factory-style-source-v1", source_hash)
        previous_source = source_registry.setdefault(source_id, source_hash)
        if previous_source != source_hash:
            raise ValueError(f"Factory source ID collision: {source_id}")
        try:
            parsed = midi_optimizer.parse_smf(data)
        except Exception as error:
            errors.append({"file": source, "error": str(error)})
            continue
        if parsed["division"] & 0x8000:
            rejected["smpte"] += 1
            continue
        ppq, meter, tempo = parsed["division"], _meter(parsed), _tempo(parsed)
        for track in parsed["tracks"]:
            texts = _texts(track)
            element = next((text.lower() for text in texts if text.lower() in ELEMENTS), None)
            bars_match = next((BAR_RE.match(text) for text in texts if BAR_RE.match(text)), None)
            cv_match = next((CV_RE.match(text) for text in texts if CV_RE.match(text)), None)
            if not element or not cv_match:
                rejected["missing-element-or-cv"] += 1
                continue
            notes = midi_optimizer.pair_notes(track)
            if not notes:
                rejected["empty-track"] += 1
                continue
            midi_optimizer.attach_instruments(track, notes)
            role, cv = cv_match.group(1).upper(), int(cv_match.group(2))
            bars = int(bars_match.group(1)) if bars_match else max(
                1, math.ceil(max(note["off"]["tick"] for note in notes) / (ppq * 4)))
            sound_name = next((text for text in texts if text.lower() not in ELEMENTS
                               and not BAR_RE.match(text) and not CV_RE.match(text)
                               and not text.upper().startswith("SN:")), "")
            style_name = next((text[3:].strip() for text in texts if text.upper().startswith("SN:")), "")
            normalized_notes = sorted([
                int(note["on"]["tick"]),
                max(1, int(note["off"]["tick"] - note["on"]["tick"])),
                int(note["pitch"]),
                int(note["on"]["data"][1]),
            ] for note in notes if not note["on"].get("remove"))
            instrument_keys = sorted({note.get("instrumentKey") for note in notes if note.get("instrumentKey")})
            profile_refs = sorted({profile_ids[key] for key in instrument_keys if key in profile_ids})
            sound = _sound_evidence(track, notes)
            canonical_document = {
                "sourceHash": source_hash, "track": track["index"], "element": element,
                "role": role, "cv": cv, "bars": bars, "meter": meter,
                "notes": normalized_notes,
            }
            canonical = json.dumps(canonical_document, sort_keys=True, separators=(",", ":"))
            segment_id = numeric_id("factory-style-segment-v1", canonical)
            previous = id_registry.setdefault(segment_id, hashlib.sha256(canonical.encode()).hexdigest())
            if previous != hashlib.sha256(canonical.encode()).hexdigest():
                raise ValueError(f"Factory Style segment ID collision: {segment_id}")
            end_tick = max(note[0] + note[1] for note in normalized_notes)
            confidence = round(min(1.0, .55 + min(.25, math.log2(len(notes) + 1) / 32)
                                       + (.1 if bars_match else 0) + (.1 if sound else 0)), 3)
            segments.append({
                "id": segment_id, "sourceId": source_id, "sourceHash": source_hash,
                "source": source, "sourceStyle": style_name, "trackIndex": track["index"],
                "element": element, "role": role, "cv": cv, "bars": bars,
                "meter": meter, "tempo": tempo, "ppq": ppq, "tickRange": [0, end_tick],
                "soundName": sound_name, "soundEvidence": sound,
                "factoryProfileIds": profile_refs,
                "pitchMode": "absolute-factory-style-evidence",
                "notes": normalized_notes, "noteCount": len(normalized_notes),
                "densityPerBar": round(len(normalized_notes) / max(1, bars), 3),
                "confidence": confidence,
                "authority": {"velocity": "factory", "program": "factory-evidence",
                              "goldUsed": False},
            })
            element_counts[element] += 1
            role_counts[role] += 1
            cv_counts[f"CV{cv}"] += 1
    segments.sort(key=lambda item: (item["element"], item["role"], item["cv"], item["id"]))
    digest = hashlib.sha256()
    for item in segments:
        digest.update(item["id"].encode("ascii"))
        digest.update(bytes.fromhex(item["sourceHash"]))
    return {
        "schema": "dna.factory-style-segments", "version": "1.1",
        "databaseVersion": "factory-style-" + digest.hexdigest()[:16],
        "rules": {"source": "factory-only", "goldUsed": False,
                  "emptyTracksIncluded": False, "idCollisionPolicy": "fail-build",
                  "idFormat": "DDD.DDD.DDD-zero-padded"},
        "summary": {"inputFiles": len(files), "segments": len(segments),
                    "notes": sum(item["noteCount"] for item in segments),
                    "elements": dict(sorted(element_counts.items())),
                    "roles": dict(sorted(role_counts.items())),
                    "chordVariations": dict(sorted(cv_counts.items())),
                    "rejected": dict(rejected), "errors": len(errors)},
        "segments": segments, "errors": errors,
    }