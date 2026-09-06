#!/usr/bin/env python3
"""Izradi Factory velocity profile i filtrirane Gold patterne iz DNA ZIP-a."""

from __future__ import annotations

import argparse
import gc
import hashlib
import io
import json
import math
import statistics
import struct
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import factory_velocity
import factory_style_registry
import factory_strumming
import gold_performance_registry
import gold_schema


@dataclass(frozen=True)
class Instrument:
    kind: str
    msb: int
    lsb: int
    program: int
    drum_note: int | None = None

    @property
    def key(self):
        extra = f":{self.drum_note}" if self.drum_note is not None else ""
        return f"{self.kind}:{self.msb}:{self.lsb}:{self.program}{extra}"


def numeric_id(text: str) -> str:
    """Stabilan identifikator oblika 120.111.231."""
    raw = hashlib.sha256(text.encode("utf-8")).digest()
    return ".".join(f"{int.from_bytes(raw[i:i + 4], 'big') % 1000:03d}" for i in (0, 4, 8))


def unique_numeric_id(text: str, used: set[str]) -> str:
    candidate = numeric_id(text)
    if candidate in used:
        raise ValueError(f"Kolizija stabilnog DNA ID-a: {candidate}")
    used.add(candidate)
    return candidate


def dataset_version(files, label):
    digest = hashlib.sha256(label.encode("utf-8"))
    for source, content in sorted(files, key=lambda item: item[0].lower()):
        digest.update(source.encode("utf-8", "replace"))
        digest.update(hashlib.sha256(content).digest())
    return f"{label}-{digest.hexdigest()[:16]}"


def drum_element(note):
    if note in (35, 36):
        return "Kick"
    if note in (37, 38, 40):
        return "Snare"
    if note in (42, 44):
        return "Closed Hi-Hat"
    if note == 46:
        return "Open Hi-Hat"
    if note in (49, 52, 55, 57):
        return "Crash"
    if note in (51, 53, 59):
        return "Ride"
    if note in (41, 43, 45, 47, 48, 50):
        return "Toms"
    if note == 39:
        return "Clap"
    return "Percussion"


def instrument_role(instrument):
    if instrument.kind == "drum":
        return "drums"
    if 32 <= instrument.program <= 39:
        return "bass"
    if instrument.program <= 31 or 48 <= instrument.program <= 55 or 88 <= instrument.program <= 103:
        return "chords"
    return "melody"


def varlen(data: bytes, pos: int, end: int):
    value = 0
    for _ in range(4):
        if pos >= end:
            raise ValueError("Prekinuta MIDI varijabla")
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 127)
        if byte < 128:
            break
    return value, pos


def parse_midi(data: bytes, source: str):
    if len(data) < 14 or data[:4] != b"MThd":
        raise ValueError("Nije standardni MIDI")
    header_len = struct.unpack_from(">I", data, 4)[0]
    midi_format, track_count, division = struct.unpack_from(">HHH", data, 8)
    ppq = None if division & 0x8000 else division
    pos = 8 + header_len
    tracks = []
    meter = (4, 4)
    tempo_events = []
    meter_events = []
    key_signature = None
    markers = []
    max_tick = 0

    for track_index in range(track_count):
        if pos + 8 > len(data) or data[pos:pos + 4] != b"MTrk":
            break
        size = struct.unpack_from(">I", data, pos + 4)[0]
        pos += 8
        end = min(pos + size, len(data))
        tick, running, name = 0, None, ""
        state = [{"msb": 0, "lsb": 0, "program": 0, "volume": None, "expression": None}
                 for _ in range(16)]
        opened = defaultdict(list)
        notes = []

        while pos < end:
            delta, pos = varlen(data, pos, end)
            tick += delta
            if pos >= end:
                break
            status = data[pos]
            if status < 128:
                if running is None:
                    break
                status = running
            else:
                pos += 1
                if status < 240:
                    running = status

            if status == 255:
                if pos >= end:
                    break
                kind = data[pos]
                pos += 1
                length, pos = varlen(data, pos, end)
                payload = data[pos:min(pos + length, end)]
                pos += length
                if kind == 3:
                    name = payload.decode("utf-8", "replace").strip("\0 ")
                elif kind == 6:
                    markers.append({"tick": tick, "name": payload.decode("utf-8", "replace").strip("\0 ")})
                elif kind == 81 and len(payload) == 3:
                    micros = (payload[0] << 16) | (payload[1] << 8) | payload[2]
                    if micros:
                        tempo_events.append({"tick": tick, "bpm": round(60_000_000 / micros, 3)})
                elif kind == 88 and len(payload) >= 2:
                    meter = (payload[0], 2 ** payload[1])
                    meter_events.append({"tick": tick, "numerator": meter[0], "denominator": meter[1]})
                elif kind == 89 and len(payload) >= 2:
                    sharps = payload[0] if payload[0] < 128 else payload[0] - 256
                    key_signature = {"sharps": sharps, "minor": bool(payload[1])}
                continue
            if status in (240, 247):
                length, pos = varlen(data, pos, end)
                pos += length
                running = None
                continue
            if not 128 <= status <= 239 or pos >= end:
                break

            command, channel = status >> 4, status & 15
            one = data[pos]
            pos += 1
            two = None
            if command not in (12, 13):
                if pos >= end:
                    break
                two = data[pos]
                pos += 1
            current = state[channel]

            if command == 11 and one == 0:
                current["msb"] = two
            elif command == 11 and one == 32:
                current["lsb"] = two
            elif command == 11 and one == 7:
                current["volume"] = two
            elif command == 11 and one == 11:
                current["expression"] = two
            elif command == 12:
                current["program"] = one
            elif command == 9 and two:
                instrument = Instrument(
                    "drum" if channel == 9 else "melodic",
                    current["msb"], current["lsb"], current["program"],
                    one if channel == 9 else None,
                )
                opened[(channel, one)].append({
                    "start": tick, "end": tick + 1, "pitch": one,
                    "velocity": two, "channel": channel + 1, "instrument": instrument,
                    "volume": current["volume"], "expression": current["expression"],
                })
            elif command == 8 or (command == 9 and not two):
                stack = opened.get((channel, one))
                if stack:
                    note = stack.pop(0)
                    note["end"] = max(note["start"] + 1, tick)
                    notes.append(note)

        for stack in opened.values():
            for note in stack:
                note["end"] = max(note["start"] + 1, tick)
                notes.append(note)
        tracks.append({"index": track_index, "name": name, "notes": notes})
        max_tick = max(max_tick, tick)
        pos = end
    return {
        "source": source, "format": midi_format, "ppq": ppq, "meter": meter,
        "tempo": tempo_events[0]["bpm"] if tempo_events else 120,
        "tempo_events": tempo_events, "meter_events": meter_events,
        "key_signature": key_signature, "markers": markers,
        "max_tick": max_tick, "tracks": tracks,
    }


def read_nested_archive(path: Path):
    factory, gold = [], []
    with zipfile.ZipFile(path) as outer:
        for item in outer.infolist():
            lower = item.filename.lower()
            if not lower.endswith(".zip"):
                continue
            target = gold if "gold" in lower else factory if "factory" in lower else None
            if target is None:
                continue
            with zipfile.ZipFile(io.BytesIO(outer.read(item))) as inner:
                for midi in inner.infolist():
                    if midi.filename.lower().endswith((".mid", ".midi")):
                        target.append((midi.filename, inner.read(midi)))
    return factory, gold


def factory_profiles(files):
    velocities, pitches, aliases, sources = defaultdict(list), defaultdict(list), defaultdict(Counter), defaultdict(set)
    mixer = defaultdict(lambda: {"volume": [], "expression": []})
    errors = []
    for source, content in files:
        try:
            midi = parse_midi(content, source)
        except Exception as error:
            errors.append({"file": source, "error": str(error)})
            continue
        for track in midi["tracks"]:
            track_mix = set()
            for note in track["notes"]:
                instrument = note["instrument"]
                velocities[instrument].append(note["velocity"])
                pitches[instrument].append(note["pitch"])
                sources[instrument].add(numeric_id("factory-source:" + source))
                if track["name"]:
                    aliases[instrument][track["name"]] += 1
                track_mix.add((instrument, note.get("volume"), note.get("expression")))
            for instrument, volume, expression in track_mix:
                if volume is not None:
                    mixer[instrument]["volume"].append(volume)
                if expression is not None:
                    mixer[instrument]["expression"].append(expression)

    result, profile_ids, used_ids = [], {}, set()
    for instrument in sorted(velocities, key=lambda item: item.key):
        values = velocities[instrument]
        counts = Counter(values)
        middle = statistics.median(values)
        highest = max(counts.values())
        optimal = min((v for v, count in counts.items() if count == highest), key=lambda v: abs(v - middle))
        alias = aliases[instrument].most_common(1)
        label = alias[0][0] if alias else (
            f"Drum note {instrument.drum_note}" if instrument.kind == "drum" else f"Program {instrument.program}"
        )
        profile_id = unique_numeric_id(instrument.key, used_ids)
        profile_ids[instrument.key] = profile_id
        velocity_curve = factory_velocity.build_velocity_curve(values, optimal)
        curve_values = velocity_curve["values"]
        velocity = {
            "min": curve_values["floor"], "optimal": curve_values["optimal"],
            "max": curve_values["ceiling"], **curve_values,
        }
        sample_count = len(values)
        coverage = min(1.0, math.log2(sample_count + 1) / 9)
        consistency = max(.35, 1 - statistics.pstdev(values) / 64) if sample_count > 1 else .35
        confidence = round(coverage * consistency, 3)
        volume_profile = factory_velocity.build_controller_profile(mixer[instrument]["volume"])
        expression_profile = factory_velocity.build_controller_profile(mixer[instrument]["expression"])
        result.append({
            "id": profile_id, "instrumentKey": instrument.key,
            "instrument": label, "kind": instrument.kind,
            "instrument_id": profile_id, "instrument_name": label, "role": instrument_role(instrument),
            "bankMsb": instrument.msb, "bankLsb": instrument.lsb, "program": instrument.program,
            **({"drumNote": instrument.drum_note} if instrument.drum_note is not None else {}),
            **({"drumElement": drum_element(instrument.drum_note)} if instrument.drum_note is not None else {}),
            "register": {"low": min(pitches[instrument]), "high": max(pitches[instrument])},
            "register_low": min(pitches[instrument]), "register_high": max(pitches[instrument]),
            "velocity": velocity, "velocityRange": [velocity["min"], velocity["max"]],
            "velocity_min": velocity["min"], "velocity_optimum": velocity["optimal"], "velocity_max": velocity["max"],
            "velocityCurve": velocity_curve, "velocity_curve": velocity_curve,
            "velocityQuantiles": velocity_curve["quantiles"],
            "dynamicCurve": {str(item["intensity"]): item["velocity"] for item in velocity_curve["points"]},
            "mixerProfile": {"volume": volume_profile, "expression": expression_profile,
                             "authority": "factory-only", "goldAffectsMixer": False},
            "samples": sample_count, "sample_count": sample_count, "confidence": confidence,
            "source_ids": sorted(sources[instrument]),
        })
    result.sort(key=lambda row: (-row["samples"], row["instrumentKey"]))
    document = {
        "schema": "midi-arranger.factory-velocity-profiles", "version": "3.3",
        "databaseVersion": dataset_version(files, "factory-schema3.3"),
        "rules": {"dynamicsSource": "factory-only", "goldAffectsDynamics": False,
                  "optimalMethod": "mode; ties resolved toward median",
                  "dynamicCurve": "seven-point monotone Factory curve at intensity 0/17/33/50/67/83/100",
                  "curveLabels": [label for _, label in factory_velocity.CURVE_ANCHORS],
                  "mixerProfile": "Factory CC7/CC11 observations; GOLD has zero mixer authority",
                  "drumProfiles": "per-note and classified by drum element"},
        "summary": {"inputFiles": len(files), "failedFiles": len(errors),
                    "profileCount": len(result), "velocitySamples": sum(map(len, velocities.values())),
                    "profilesWithVolume": sum(item["mixerProfile"]["volume"] is not None for item in result),
                    "profilesWithExpression": sum(item["mixerProfile"]["expression"] is not None for item in result)},
        "profiles": result, "errors": errors,
    }
    return document, profile_ids


def pattern_role(notes, instrument):
    if instrument.kind == "drum":
        return "drums"
    if statistics.median(note["pitch"] for note in notes) < 52:
        return "bass"
    starts = Counter(note["start"] for note in notes)
    return "chords" if sum(n > 1 for n in starts.values()) / len(starts) >= .2 else "melody"


def gold_patterns(files, profile_ids):
    # Argument ostaje radi kompatibilnosti build poziva, ali GOLD runtime ne
    # smije sadržavati niti koristiti Factory profile/program identitet.
    _ = profile_ids
    unique, errors, rejected = {}, [], Counter()
    for source, content in files:
        try:
            midi = parse_midi(content, source)
        except Exception as error:
            errors.append({"file": source, "error": str(error)})
            continue
        ppq = midi["ppq"]
        if not ppq:
            rejected["smpte"] += 1
            continue
        numerator, denominator = midi["meter"]
        bar_ticks, step = ppq * numerator * 4 / denominator, ppq / 4
        total_bars = max(1, math.ceil(midi["max_tick"] / bar_ticks))
        groups, instruments = defaultdict(list), {}
        for track in midi["tracks"]:
            for note in track["notes"]:
                key = note["instrument"].key
                groups[(track["index"], key)].append(note)
                instruments[key] = note["instrument"]

        for (_, key), notes in groups.items():
            instrument = instruments[key]
            bars = defaultdict(list)
            for note in notes:
                if note["end"] - note["start"] >= max(1, ppq / 32):
                    bars[int(note["start"] // bar_ticks)].append(note)
                else:
                    rejected["micro-note"] += 1
            for bar_number, selected in bars.items():
                if not 3 <= len(selected) <= 96:
                    rejected["note-count"] += 1
                    continue
                origin = bar_number * bar_ticks
                error = sum(abs((n["start"] - origin) / step - round((n["start"] - origin) / step)) for n in selected) / len(selected)
                if error > .22:
                    rejected["quantization"] += 1
                    continue
                anchor = 0 if instrument.kind == "drum" else min(n["pitch"] for n in selected)
                notes_out = sorted({(
                    max(0, round((n["start"] - origin) / step)),
                    max(1, round((n["end"] - n["start"]) / step)),
                    n["pitch"] if instrument.kind == "drum" else n["pitch"] - anchor,
                ) for n in selected})
                if len({n[0] for n in notes_out}) < 2:
                    rejected["single-position"] += 1
                    continue
                role = pattern_role(selected, instrument)
                final_quarter = sum(1 for note in notes_out if note[0] >= 12) / len(notes_out)
                source_section = ("intro" if bar_number < 2 else "ending" if bar_number >= total_bars - 2
                                  else "transition" if final_quarter >= .35 else "body")
                canonical = json.dumps([instrument.kind, role, numerator, denominator, notes_out], separators=(",", ":"))
                if canonical in unique:
                    unique[canonical]["occurrences"] += 1
                    unique[canonical]["sourceSections"][source_section] = unique[canonical]["sourceSections"].get(source_section, 0) + 1
                    source_id = numeric_id("gold-source:" + source)
                    if source_id not in unique[canonical]["sourceIds"]:
                        unique[canonical]["sourceIds"].append(source_id)
                    continue
                unique[canonical] = {
                    "_canonical": canonical,
                    "sourceInstrumentClass": instrument.kind,
                    "role": role, "meter": f"{numerator}/{denominator}",
                    "lengthBars": 1, "grid": "1/16",
                    "density": round(len(notes_out) / max(1, numerator), 3),
                    "register": {"low": min(note[2] for note in notes_out), "high": max(note[2] for note in notes_out)},
                    "sourceSection": source_section,
                    "sourceSections": {source_section: 1},
                    "pitchMode": "absolute-drum-note" if instrument.kind == "drum" else "relative-to-lowest-note",
                    "notes": [list(n) for n in notes_out], "occurrences": 1,
                    "source": Path(source).name, "sourceBar": bar_number + 1,
                    "sourceIds": [numeric_id("gold-source:" + source)],
                }
    rejected["non-recurring-pattern"] = sum(1 for row in unique.values() if row["occurrences"] < 2)
    patterns = [row for row in unique.values() if row["occurrences"] >= 2]
    used_ids = set()
    for row in patterns:
        row["id"] = unique_numeric_id("gold-pattern-v3.2:" + row.pop("_canonical"), used_ids)
    patterns.sort(key=lambda row: (-row["occurrences"], row["id"]))
    for row in patterns:
        row["sourceIds"].sort()
        row["sourceSection"] = sorted(row["sourceSections"].items(), key=lambda item: (-item[1], item[0]))[0][0]
        row["confidence"] = round(min(1.0, math.log2(row["occurrences"] + 1) / 6), 3)
    schema_validation = gold_schema.assert_valid_patterns(patterns)
    return {
        "schema": "midi-arranger.gold-patterns", "version": "3.2",
        "databaseVersion": dataset_version(files, "gold-schema3.2"),
        "rules": {"purpose": "filtered-patterns-only", "velocityDataIncluded": False,
                  "goldAffectsDynamics": False, "grid": "1/16",
                  "programDataIncluded": False, "bankDataIncluded": False,
                  "filter": "3-96 notes, 2+ positions, no micro-notes, quantization error <= 0.22, recurring 2+ times",
                  "noteTuple": ["positionStep", "durationSteps", "pitchOrOffset"]},
        "summary": {"inputFiles": len(files), "failedFiles": len(errors),
                    "patternCount": len(patterns), "rejected": dict(rejected)},
        "schemaValidation": schema_validation,
        "patterns": patterns, "errors": errors,
    }


def write_json(path, data, compact=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=None if compact else 2,
                  separators=(",", ":") if compact else None)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", nargs="?", default="prism-uploads/DNA.zip")
    parser.add_argument("--output", default="data")
    args = parser.parse_args()
    factory, gold = read_nested_archive(Path(args.archive))
    print(f"Factory MIDI: {len(factory)}; Gold MIDI: {len(gold)}")
    output = Path(args.output)
    profiles, known = factory_profiles(factory)
    write_json(output / "factory-velocity-profiles.json", profiles)
    database = {"factory": profiles["databaseVersion"]}
    summaries = {"factory": profiles["summary"]}
    del profiles
    gc.collect()
    patterns = gold_patterns(gold, known)
    write_json(output / "gold-patterns.json", patterns, compact=True)
    database["gold"] = patterns["databaseVersion"]
    summaries["gold"] = patterns["summary"]
    gold_schema_passed = patterns["schemaValidation"]["passed"]
    del patterns
    gc.collect()
    style_segments = factory_style_registry.build_registry(factory, known)
    write_json(output / "factory-style-segments.json", style_segments, compact=True)
    database["factoryStyle"] = style_segments["databaseVersion"]
    summaries["factoryStyle"] = style_segments["summary"]
    strumming = factory_strumming.build_registry(style_segments)
    write_json(output / "factory-strumming.json", strumming, compact=True)
    database["factoryStrumming"] = strumming["databaseVersion"]
    summaries["factoryStrumming"] = strumming["summary"]
    del style_segments, strumming
    gc.collect()
    performance = gold_performance_registry.build_registry(gold)
    write_json(output / "gold-performance-patterns.json", performance, compact=True)
    database["goldPerformance"] = performance["databaseVersion"]
    summaries["goldPerformance"] = performance["summary"]
    del performance
    gc.collect()
    write_json(output / "dna-build-report.json", {
        "schema": "pa800-dna-build-report", "version": "3.1",
        "database": database,
        "factory": summaries["factory"], "gold": summaries["gold"],
        "factoryStyle": summaries["factoryStyle"],
        "factoryStrumming": summaries["factoryStrumming"],
        "goldPerformance": summaries["goldPerformance"],
        "guarantees": {"dynamicsSource": "factory-only", "goldAffectsDynamics": False,
                       "goldAffectsMixer": False, "goldAffectsProgramChange": False,
                       "goldRuntimeSchemaValidated": gold_schema_passed},
    })
    print(f"Profile: {summaries['factory']['profileCount']}; legacy patterni: {summaries['gold']['patternCount']}; "
          f"performance: {summaries['goldPerformance']['patterns']}; "
          f"strumming: {summaries['factoryStrumming']['patterns']}")


if __name__ == "__main__":
    main()