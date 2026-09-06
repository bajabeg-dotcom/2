#!/usr/bin/env python3
"""Muzička analiza MIDI songa za DNA Korg Pa800 arranger."""

from __future__ import annotations

import hashlib
import math
import re
import statistics
from collections import Counter, defaultdict

import dna_builder
import midi_optimizer


PITCH_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
MAJOR_PROFILE = (6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88)
MINOR_PROFILE = (6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17)


def correlation(left, right):
    mean_left, mean_right = statistics.mean(left), statistics.mean(right)
    numerator = sum((a - mean_left) * (b - mean_right) for a, b in zip(left, right))
    denominator = math.sqrt(sum((a - mean_left) ** 2 for a in left) * sum((b - mean_right) ** 2 for b in right))
    return numerator / denominator if denominator else 0.0


def detect_key(notes, ppq, signature=None):
    histogram = [0.0] * 12
    for note in notes:
        duration = min(note["end"] - note["start"], ppq * 4)
        histogram[note["pitch"] % 12] += max(1, duration)
    if not sum(histogram):
        return {"name": "C", "root": 0, "mode": "major", "confidence": 0.0, "source": "fallback"}
    candidates = []
    for root in range(12):
        for mode, profile in (("major", MAJOR_PROFILE), ("minor", MINOR_PROFILE)):
            rotated = [profile[(pitch - root) % 12] for pitch in range(12)]
            candidates.append((correlation(histogram, rotated), root, mode))
    candidates.sort(reverse=True)
    best, second = candidates[0], candidates[1]
    confidence = max(0.0, min(1.0, (best[0] - second[0] + 0.04) / 0.22))
    suffix = "m" if best[2] == "minor" else ""
    result = {"name": PITCH_NAMES[best[1]] + suffix, "root": best[1], "mode": best[2],
              "confidence": round(confidence, 3), "score": round(best[0], 3), "source": "pitch-class-profile"}
    if signature:
        result["midiKeySignature"] = signature
    return result


def scale_pitch_classes(key):
    intervals = (0, 2, 4, 5, 7, 9, 11) if key["mode"] == "major" else (0, 2, 3, 5, 7, 8, 10)
    return {(key["root"] + value) % 12 for value in intervals}


def chord_candidates():
    qualities = (
        ("", "major", (0, 4, 7)), ("m", "minor", (0, 3, 7)),
        ("5", "power", (0, 7)), ("dim", "diminished", (0, 3, 6)),
        ("aug", "augmented", (0, 4, 8)), ("sus2", "suspended-2", (0, 2, 7)),
        ("sus4", "suspended-4", (0, 5, 7)), ("6", "sixth", (0, 4, 7, 9)),
        ("m6", "minor-sixth", (0, 3, 7, 9)), ("7", "dominant-seventh", (0, 4, 7, 10)),
        ("maj7", "major-seventh", (0, 4, 7, 11)), ("m7", "minor-seventh", (0, 3, 7, 10)),
        ("m7b5", "half-diminished", (0, 3, 6, 10)),
        ("dim7", "diminished-seventh", (0, 3, 6, 9)),
        ("add9", "add-nine", (0, 2, 4, 7)),
    )
    return [(root, suffix, quality, {(root + value) % 12 for value in intervals}, len(intervals))
            for root in range(12) for suffix, quality, intervals in qualities]


def detect_chord(histogram, key, bass_pitch_class=None, previous_root=None):
    total = sum(histogram)
    if total <= 0:
        return {"symbol": "N.C.", "root": None, "quality": "none", "confidence": 0.0}
    scale = scale_pitch_classes(key)
    ranked = []
    for root, suffix, quality, tones, complexity in chord_candidates():
        inside = sum(histogram[pitch] for pitch in tones) / total
        outside = 1 - inside
        root_weight = histogram[root] / total
        diatonic_bonus = 0.06 if tones.issubset(scale) else 0
        bass_bonus = 0.09 if bass_pitch_class == root else 0
        continuity_bonus = 0.025 if previous_root == root else 0
        complexity_penalty = 0.018 * max(0, complexity - 3)
        power_penalty = 0.035 if quality == "power" and inside < .78 else 0
        score = (inside - 0.34 * outside + 0.19 * root_weight + diatonic_bonus
                 + bass_bonus + continuity_bonus - complexity_penalty - power_penalty)
        ranked.append((score, inside, outside, root, suffix, quality))
    ranked.sort(reverse=True)
    best, second = ranked[0], ranked[1]
    confidence = max(0.0, min(1.0, (best[0] - second[0]) / 0.18))
    alternatives = [{"symbol": PITCH_NAMES[item[3]] + item[4], "score": round(item[0], 4)}
                    for item in ranked[1:4]]
    return {"symbol": PITCH_NAMES[best[3]] + best[4], "root": best[3],
            "quality": best[5], "confidence": round(confidence, 3),
            "coverage": round(best[1], 3), "outsideRatio": round(best[2], 3),
            "bassPitchClass": bass_pitch_class, "alternatives": alternatives}


def note_role(note):
    """Vrati analitičku ulogu bez upotrebe velocityja."""
    if note["channel"] == 10:
        return "drums"
    program = note["instrument"].program
    if 32 <= program <= 39 or note["pitch"] < 48:
        return "bass"
    if program <= 31 or 48 <= program <= 55:
        return "harmony"
    return "melody"


def chord_timeline(notes, ppq, meter, total_bars, key, resolution=2):
    """Analiziraj harmoniju po pola takta i spoji jednake susjedne ćelije."""
    numerator, denominator = meter
    bar_ticks = ppq * numerator * 4 / denominator
    cell_ticks = bar_ticks / max(1, resolution)
    cells, previous_root = [], None
    for cell_index in range(total_bars * resolution):
        start, end = cell_index * cell_ticks, (cell_index + 1) * cell_ticks
        histogram = [0.0] * 12
        bass_histogram = [0.0] * 12
        role_weights = Counter()
        for note in notes:
            if note["channel"] == 10:
                continue
            overlap = max(0, min(end, note["end"]) - max(start, note["start"]))
            if not overlap:
                continue
            role = note_role(note)
            weight = overlap * {"bass": 1.35, "harmony": 1.0, "melody": .58}.get(role, 1.0)
            histogram[note["pitch"] % 12] += weight
            role_weights[role] += weight
            if role == "bass":
                bass_histogram[note["pitch"] % 12] += overlap
        bass_pc = max(range(12), key=lambda pitch: bass_histogram[pitch]) if sum(bass_histogram) else None
        chord = detect_chord(histogram, key, bass_pc, previous_root)
        if chord["root"] is not None:
            previous_root = chord["root"]
        cells.append({
            "cell": cell_index + 1, "bar": cell_index // resolution + 1,
            "part": cell_index % resolution + 1,
            "startTick": round(start), "endTick": round(end),
            "symbol": chord["symbol"], "root": chord["root"], "quality": chord["quality"],
            "confidence": chord["confidence"], "coverage": chord.get("coverage", 0),
            "bassPitchClass": bass_pc, "alternatives": chord.get("alternatives", []),
            "evidenceWeights": {key: round(value, 2) for key, value in sorted(role_weights.items())},
            "velocityUsed": False,
        })
    previous_symbol = key["name"]
    for cell in cells:
        if cell["symbol"] == "N.C.":
            cell["symbol"] = previous_symbol
            cell["confidence"] = 0.0
        else:
            previous_symbol = cell["symbol"]
    segments = []
    for cell in cells:
        if segments and segments[-1]["symbol"] == cell["symbol"]:
            segments[-1]["endTick"] = cell["endTick"]
            segments[-1]["endBar"] = cell["bar"]
            segments[-1]["cells"] += 1
            segments[-1]["confidence"] = round(
                (segments[-1]["confidence"] * (segments[-1]["cells"] - 1) + cell["confidence"])
                / segments[-1]["cells"], 3)
        else:
            segments.append({"symbol": cell["symbol"], "root": cell["root"],
                             "quality": cell["quality"], "startTick": cell["startTick"],
                             "endTick": cell["endTick"], "startBar": cell["bar"],
                             "endBar": cell["bar"], "cells": 1,
                             "confidence": cell["confidence"]})
    return {"resolution": "half-bar", "cellsPerBar": resolution,
            "velocityUsed": False, "cells": cells, "segments": segments}


def bar_analysis(notes, ppq, meter, total_bars, key):
    numerator, denominator = meter
    bar_ticks = ppq * numerator * 4 / denominator
    bars = []
    for bar_index in range(total_bars):
        start, end = bar_index * bar_ticks, (bar_index + 1) * bar_ticks
        histogram = [0.0] * 12
        onsets = drums = 0
        roles = Counter()
        pitches = []
        active_edges = []
        onset_positions = []
        for note in notes:
            if start <= note["start"] < end:
                onsets += 1
                onset_positions.append((note["start"] - start) / max(1, bar_ticks))
                if note["channel"] == 10:
                    drums += 1
                    roles["drums"] += 1
                elif 32 <= note["instrument"].program <= 39 or note["pitch"] < 48:
                    roles["bass"] += 1
                elif note["instrument"].program <= 31 or 48 <= note["instrument"].program <= 55:
                    roles["chords"] += 1
                else:
                    roles["melody"] += 1
            if note["channel"] == 10:
                continue
            overlap = max(0, min(end, note["end"]) - max(start, note["start"]))
            if overlap:
                histogram[note["pitch"] % 12] += overlap
                pitches.append(note["pitch"])
                active_edges.append((max(start, note["start"]), 1))
                active_edges.append((min(end, note["end"]), -1))
        chord = detect_chord(histogram, key)
        active = maximum_polyphony = 0
        for _, delta in sorted(active_edges, key=lambda item: (item[0], item[1])):
            active += delta
            maximum_polyphony = max(maximum_polyphony, active)
        occupied_classes = sum(1 for value in histogram if value)
        phrase_position = statistics.mean(onset_positions) if onset_positions else 0.0
        bars.append({"bar": bar_index + 1, "chord": chord["symbol"], "chordConfidence": chord["confidence"],
                     "noteDensity": onsets, "drumDensity": drums,
                     "bassDensity": roles["bass"], "chordDensity": roles["chords"],
                     "melodyDensity": roles["melody"], "polyphony": maximum_polyphony,
                     "harmonicActivity": occupied_classes,
                     "register": {"low": min(pitches) if pitches else None,
                                  "high": max(pitches) if pitches else None,
                                  "median": round(statistics.median(pitches), 1) if pitches else None},
                     "phrasePosition": round(phrase_position, 3)})
    previous = "C" if key["mode"] == "major" else key["name"]
    for bar in bars:
        if bar["chord"] == "N.C.":
            bar["chord"] = previous
            bar["chordConfidence"] = 0.0
        else:
            previous = bar["chord"]
    return bars


def block_fingerprint(block):
    def canonical(symbol):
        match = re.match(r"^([A-G](?:#|b)?)(.*)$", symbol)
        if not match:
            return symbol
        minor = match.group(2).startswith("m") and not match.group(2).startswith("maj")
        return match.group(1) + ("m" if minor else "")
    return tuple(canonical(bar["chord"]) for bar in block)


def phase_boundaries(bars):
    """Vrati dokazne kandidate granica; nazivi sekcija ostaju heuristički."""
    if not bars:
        return []
    maximum_density = max((bar["noteDensity"] + .35 * bar["drumDensity"] for bar in bars), default=1) or 1
    candidates = [{"startBar": 1, "score": 1.0, "forced": True,
                   "evidence": {"songStart": 1.0}, "velocityUsed": False}]
    last_boundary = 0
    for index in range(1, len(bars)):
        previous, current = bars[index - 1], bars[index]
        previous_energy = previous["noteDensity"] + .35 * previous["drumDensity"]
        current_energy = current["noteDensity"] + .35 * current["drumDensity"]
        density_change = min(1.0, abs(current_energy - previous_energy) / maximum_density * 2.2)
        drum_change = min(1.0, abs(current["drumDensity"] - previous["drumDensity"])
                          / max(1, current["drumDensity"] + previous["drumDensity"]) * 2)
        bass_change = min(1.0, abs(current["bassDensity"] - previous["bassDensity"])
                          / max(1, current["bassDensity"] + previous["bassDensity"]) * 2)
        harmony_change = min(1.0, abs(current["chordDensity"] - previous["chordDensity"])
                             / max(1, current["chordDensity"] + previous["chordDensity"]) * 2)
        chord_change = 1.0 if current["chord"] != previous["chord"] else 0.0
        rest_edge = 1.0 if min(previous["noteDensity"], current["noteDensity"]) == 0 else 0.0
        phrase_edge = 1.0 if index % 4 == 0 else .35 if index % 2 == 0 else 0.0
        repeated_edge = 0.0
        if index >= 2 and index + 1 < len(bars):
            left = block_fingerprint(bars[index - 2:index])
            right = block_fingerprint(bars[index:index + 2])
            repeated_edge = 1.0 if left == right else 0.0
        evidence = {
            "densityChange": round(density_change, 3), "drumChange": round(drum_change, 3),
            "bassChange": round(bass_change, 3), "harmonyChange": round(harmony_change, 3),
            "chordChange": chord_change, "restEdge": rest_edge,
            "phraseAlignment": phrase_edge, "repetitionEdge": repeated_edge,
        }
        score = (.27 * density_change + .18 * drum_change + .11 * bass_change
                 + .13 * harmony_change + .10 * chord_change + .09 * rest_edge
                 + .08 * phrase_edge + .04 * repeated_edge)
        forced = index - last_boundary >= 8
        if score >= .43 or forced:
            candidates.append({"startBar": index + 1, "score": round(score, 3),
                               "forced": forced, "evidence": evidence, "velocityUsed": False})
            last_boundary = index
    return candidates


def detect_sections(bars, boundaries=None):
    if not bars:
        return []
    boundaries = boundaries or phase_boundaries(bars)
    starts = sorted({1, *(item["startBar"] for item in boundaries if 1 <= item["startBar"] <= len(bars))})
    blocks = [bars[start - 1:(starts[index + 1] - 1 if index + 1 < len(starts) else len(bars))]
              for index, start in enumerate(starts)]
    blocks = [block for block in blocks if block]
    fingerprints = Counter(block_fingerprint(block) for block in blocks)
    energies = [statistics.mean(bar["noteDensity"] + .35 * bar["drumDensity"] for bar in block) for block in blocks]
    median_energy = statistics.median(energies)
    maximum = max(energies) or 1
    raw = []
    for index, (block, energy) in enumerate(zip(blocks, energies)):
        fingerprint = block_fingerprint(block)
        previous = block_fingerprint(blocks[index - 1]) if index else None
        novelty = 0 if previous is None else 1 - sum(a == b for a, b in zip(fingerprint, previous)) / max(1, len(fingerprint))
        if index == 0 and len(blocks) >= 3 and energy <= median_energy * .85:
            kind = "intro"
        elif index == len(blocks) - 1 and len(blocks) >= 3 and energy <= median_energy * .9:
            kind = "ending"
        elif energy >= max(median_energy * 1.18, maximum * .82):
            kind = "chorus"
        elif fingerprints[fingerprint] >= 2:
            kind = "verse"
        elif novelty >= .75 and energy >= median_energy * .9 and 1 < index < len(blocks) - 2:
            kind = "bridge"
        else:
            kind = "verse"
        intensity = round(30 + 65 * energy / maximum)
        boundary = next((item for item in boundaries if item["startBar"] == block[0]["bar"]), None)
        raw.append({"startBar": block[0]["bar"], "bars": len(block), "type": kind,
                    "intensity": max(25, min(95, intensity)), "chords": [bar["chord"] for bar in block],
                    "boundaryEvidence": boundary or {"startBar": block[0]["bar"], "score": 0.0},
                    "classificationEvidence": {"energy": round(energy, 3),
                                               "medianEnergy": round(median_energy, 3),
                                               "novelty": round(novelty, 3),
                                               "fingerprintOccurrences": fingerprints[fingerprint],
                                               "velocityUsed": False},
                    "labelStatus": "heuristic-candidate"})
    merged = []
    for section in raw:
        if merged and merged[-1]["type"] == section["type"] and merged[-1]["bars"] + section["bars"] <= 16:
            merged[-1]["bars"] += section["bars"]
            merged[-1]["chords"].extend(section["chords"])
            merged[-1]["intensity"] = round((merged[-1]["intensity"] + section["intensity"]) / 2)
        else:
            merged.append(section)
    counters = Counter()
    names = {"intro": "Intro", "verse": "Strofa", "chorus": "Refren", "bridge": "Bridge", "ending": "Ending"}
    element_map = {"intro": "Intro", "verse": "Variation 1/2", "chorus": "Variation 3/4",
                   "bridge": "Variation 3 + Fill", "ending": "Ending"}
    for section in merged:
        counters[section["type"]] += 1
        section["name"] = f"{names[section['type']]} {counters[section['type']]}"
        section_bars = bars[section["startBar"] - 1:section["startBar"] - 1 + section["bars"]]
        chord_counts = Counter(bar["chord"] for bar in section_bars)
        section["endBar"] = section["startBar"] + section["bars"] - 1
        section["dominantChord"] = chord_counts.most_common(1)[0][0] if chord_counts else "N.C."
        section["confidence"] = round(statistics.mean(
            bar["chordConfidence"] for bar in section_bars), 3) if section_bars else 0.0
        section["density"] = {
            "notes": round(statistics.mean(bar["noteDensity"] for bar in section_bars), 2),
            "drums": round(statistics.mean(bar["drumDensity"] for bar in section_bars), 2),
            "bass": round(statistics.mean(bar["bassDensity"] for bar in section_bars), 2),
            "harmony": round(statistics.mean(bar["chordDensity"] for bar in section_bars), 2),
            "melody": round(statistics.mean(bar["melodyDensity"] for bar in section_bars), 2),
        }
        section["polyphony"] = round(statistics.mean(bar["polyphony"] for bar in section_bars), 2)
        section["harmonicActivity"] = round(statistics.mean(
            bar["harmonicActivity"] for bar in section_bars), 2)
        register_values = [bar["register"]["median"] for bar in section_bars if bar["register"]["median"] is not None]
        section["registerMedian"] = round(statistics.mean(register_values), 1) if register_values else None
        section["recommendedPa800Element"] = element_map[section["type"]]
    return merged


def korg_chord_evidence(data):
    """Izdvoji Korg chord payload kao kandidat, bez nagađanja chord tablice."""
    try:
        parsed = midi_optimizer.parse_smf(data)
    except ValueError:
        return []
    output = []
    signature = b"\x42\x60\x08"
    for track in parsed["tracks"]:
        for event in track["events"]:
            if event["kind"] != "meta" or event["metaType"] != 127:
                continue
            payload = bytes(event["payload"])
            position = payload.find(signature)
            if position < 0 or len(payload) < position + 7:
                continue
            values = payload[position + 3:position + 7]
            output.append({"tick": event["tick"], "track": track["index"],
                           "typeCode": values[0], "rootCode": values[1],
                           "bassCode": values[2], "flags": values[3],
                           "payloadHex": payload.hex(),
                           "status": "EVIDENCE_CANDIDATE_DEVICE_CONFIRMATION",
                           "authoritative": False})
    return output


def global_music_metrics(notes, bars):
    melodic = [note for note in notes if note["channel"] != 10]
    pitches = [note["pitch"] for note in melodic]
    register_bands = {
        "low": sum(pitch < 48 for pitch in pitches),
        "middle": sum(48 <= pitch < 72 for pitch in pitches),
        "high": sum(pitch >= 72 for pitch in pitches),
    }
    return {
        "polyphony": {
            "averagePerBar": round(statistics.mean(bar["polyphony"] for bar in bars), 2) if bars else 0,
            "maximum": max((bar["polyphony"] for bar in bars), default=0),
        },
        "harmonicActivity": round(statistics.mean(bar["harmonicActivity"] for bar in bars), 2) if bars else 0,
        "registerDistribution": {
            **register_bands,
            "lowPitch": min(pitches) if pitches else None,
            "highPitch": max(pitches) if pitches else None,
            "medianPitch": round(statistics.median(pitches), 1) if pitches else None,
        },
        "roleDensity": {
            role: round(statistics.mean(bar[field] for bar in bars), 2) if bars else 0
            for role, field in (("drums", "drumDensity"), ("bass", "bassDensity"),
                                ("chords", "chordDensity"), ("melody", "melodyDensity"))
        },
    }


def suggested_elements(bars, sections):
    densities = sorted(bar["noteDensity"] + .35 * bar["drumDensity"] for bar in bars) or [1]
    maximum = max(densities) or 1

    def percentile(position):
        value = densities[round((len(densities) - 1) * position)]
        return max(25, min(98, round(25 + 73 * value / maximum)))

    intro = next((item for item in sections if item["type"] == "intro"), None)
    ending = next((item for item in reversed(sections) if item["type"] == "ending"), None)
    return [
        {"marker": "i1cv1", "bars": min(4, intro["bars"] if intro else 2), "intensity": intro["intensity"] if intro else percentile(.25)},
        {"marker": "i2cv1", "bars": min(8, intro["bars"] if intro else 4), "intensity": percentile(.55)},
        {"marker": "v1cv1", "bars": 4, "intensity": percentile(.15)},
        {"marker": "v2cv1", "bars": 4, "intensity": percentile(.4)},
        {"marker": "v3cv1", "bars": 4, "intensity": percentile(.68)},
        {"marker": "v4cv1", "bars": 4, "intensity": percentile(.92)},
        {"marker": "f1cv1", "bars": 1, "intensity": percentile(.72)},
        {"marker": "f2cv1", "bars": 1, "intensity": percentile(1)},
        {"marker": "e1cv1", "bars": min(4, ending["bars"] if ending else 2), "intensity": ending["intensity"] if ending else percentile(.35)},
        {"marker": "e2cv1", "bars": min(8, ending["bars"] if ending else 4), "intensity": percentile(.6)},
    ]


def detected_instruments(tracks):
    grouped = defaultdict(lambda: {"notes": 0, "pitches": [], "trackNames": Counter()})
    for track in tracks:
        for note in track["notes"]:
            instrument = note["instrument"]
            key = instrument.key
            if instrument.kind == "drum":
                key = f"drum:{instrument.msb}:{instrument.lsb}:{instrument.program}"
            item = grouped[key]
            item["notes"] += 1
            item["pitches"].append(note["pitch"])
            if track["name"]:
                item["trackNames"][track["name"]] += 1
    output = []
    for key, item in grouped.items():
        parts = key.split(":")
        kind, msb, lsb, program = parts[0], int(parts[1]), int(parts[2]), int(parts[3])
        median_pitch = statistics.median(item["pitches"])
        if kind == "drum":
            suggested = "drum"
        elif 32 <= program <= 39 or median_pitch < 52:
            suggested = "bass"
        elif program <= 31 or 48 <= program <= 55:
            suggested = "acc1"
        else:
            suggested = "acc3"
        output.append({"instrumentKey": key, "kind": kind, "bankMsb": msb, "bankLsb": lsb,
                       "program": program, "noteCount": item["notes"], "medianPitch": round(median_pitch, 1),
                       "trackName": item["trackNames"].most_common(1)[0][0] if item["trackNames"] else "",
                       "suggestedPa800Track": suggested})
    return sorted(output, key=lambda item: -item["noteCount"])[:24]


def analyze_midi(data: bytes, source="song.mid"):
    midi = dna_builder.parse_midi(data, source)
    if not midi["ppq"]:
        raise ValueError("SMPTE timebase trenutačno nije podržan")
    all_notes = [note for track in midi["tracks"] for note in track["notes"]]
    if not all_notes:
        raise ValueError("MIDI nema nota")
    harmonic_notes = [note for note in all_notes if note["channel"] != 10]
    ppq, meter = midi["ppq"], midi["meter"]
    bar_ticks = ppq * meter[0] * 4 / meter[1]
    last_tick = max([midi["max_tick"], *(note["end"] for note in all_notes)])
    total_bars = max(1, math.ceil(last_tick / bar_ticks))
    key = detect_key(harmonic_notes, ppq, midi["key_signature"])
    bars = bar_analysis(all_notes, ppq, meter, total_bars, key)
    chords = chord_timeline(all_notes, ppq, meter, total_bars, key)
    boundaries = phase_boundaries(bars)
    sections = detect_sections(bars, boundaries)
    korg_evidence = korg_chord_evidence(data)
    warnings = []
    if len(midi["tempo_events"]) > 1:
        warnings.append("Song ima više tempo događaja; Pa800 Style koristi početni tempo.")
    if len(midi["meter_events"]) > 1:
        warnings.append("Song ima više time-signature događaja; analiziran je posljednji zapisani takt.")
    return {
        "schema": "dna-midi-song-analysis", "version": "1.2",
        "source": {"fileName": source, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                   "format": midi["format"], "ppq": ppq, "tracks": len(midi["tracks"]), "notes": len(all_notes)},
        "tempo": round(midi["tempo"], 2), "meter": f"{meter[0]}/{meter[1]}", "bars": total_bars,
        "tempoMap": midi["tempo_events"] or [{"tick": 0, "bpm": round(midi["tempo"], 3)}],
        "meterMap": midi["meter_events"] or [{"tick": 0, "numerator": meter[0], "denominator": meter[1]}],
        "key": key, "barAnalysis": bars, "chordTimeline": chords,
        "korgChordEvidence": korg_evidence, "phaseBoundaries": boundaries,
        "sections": sections,
        "musicMetrics": global_music_metrics(all_notes, bars),
        "detectedInstruments": detected_instruments(midi["tracks"]),
        "suggestedPa800Elements": suggested_elements(bars, sections),
        "suggestedSeed": int.from_bytes(hashlib.sha256(data).digest()[:4], "big") % 1_000_000_000,
        "rules": {"analysisVelocityUsed": False, "goldAffectsDynamics": False,
                  "dynamicsSource": "factory-only", "chordResolution": "half-bar",
                  "sectionLabels": "heuristic-candidates-with-evidence",
                  "korgChordEvents": "evidence-candidate-requires-device-confirmation"},
        "warnings": warnings,
    }