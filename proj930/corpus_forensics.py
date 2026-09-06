#!/usr/bin/env python3
"""Forenzički audit stvarnih Factory i GOLD MIDI korpusa.

Ovaj modul samo čita izvore. Ne gradi runtime patterne i ne dopušta da
GOLD velocity ili Program Change postanu autoritet optimizacije.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import dna_builder
import midi_optimizer


ARCHIVE = Path("prism-uploads") / "DNA.zip"
ELEMENT_NAMES = {
    "intro 1", "intro 2", "intro 3", "variation 1", "variation 2",
    "variation 3", "variation 4", "fill 1", "fill 2", "fill 3",
    "break", "ending 1", "ending 2", "ending 3",
}
CV_RE = re.compile(r"^(DRUMS|PERC|BASS|ACC[1-5])\s+CV([1-6])$", re.I)
BAR_RE = re.compile(r"^(\d+)\s+Bars?$", re.I)
CHORD_TYPES = (
    "major", "major6", "major7", "major7b5", "sus4", "sus2", "major7sus4",
    "minor", "minor6", "minor7", "minor7b5", "minorMajor7", "dominant7",
    "dominant7b5", "dominant7sus4", "diminished", "diminishedMajor7",
    "augmented", "augmented7", "augmentedMajor7", "majorNo3", "rootOnly",
    "flat5", "diminished7",
)
ROOTS = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def percentile(values, amount):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * amount)]


def source_digest(files, namespace):
    digest = hashlib.sha256(namespace.encode("ascii"))
    for name, data in sorted(files, key=lambda item: item[0].lower()):
        digest.update(name.encode("utf-8", "surrogatepass"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(data).digest())
    return digest.hexdigest()


def text_events(track):
    output = []
    for event in track["events"]:
        if event["kind"] == "meta" and event["metaType"] in (1, 2, 3, 4, 5, 6, 7):
            text = event["payload"].decode("latin1", "replace").replace("\x00", "").strip()
            if text:
                output.append((event["tick"], event["metaType"], text))
    return output


def initial_sound_and_mix(track):
    state = {"msb": None, "lsb": None, "program": None, "volume": None, "expression": None}
    for event in sorted(track["events"], key=lambda item: (item["tick"], item["order"])):
        if event["kind"] != "channel":
            continue
        if event["command"] == 11:
            cc, value = event["data"]
            field = {0: "msb", 32: "lsb", 7: "volume", 11: "expression"}.get(cc)
            if field is not None and state[field] is None:
                state[field] = value
        elif event["command"] == 12 and state["program"] is None:
            state["program"] = event["data"][0]
    for field in ("msb", "lsb", "program"):
        if state[field] is None:
            state[field] = 0
    return state


def guitar_strum_evidence(track, ppq):
    pairs = midi_optimizer.pair_notes(track)
    onsets = sorted((note["on"]["tick"], note["pitch"], note["off"]["tick"] - note["on"]["tick"])
                    for note in pairs)
    maximum_gap = max(1, round(ppq / 16))
    clusters, current = [], []
    for item in onsets:
        if current and item[0] - current[-1][0] > maximum_gap:
            clusters.append(current)
            current = []
        current.append(item)
    if current:
        clusters.append(current)
    directions, offsets, gates, chord_sizes = Counter(), [], [], []
    for cluster in clusters:
        if len(cluster) < 3 or len({item[1] for item in cluster}) < 3:
            continue
        ordered = sorted(cluster, key=lambda item: (item[0], item[1]))
        first_tick = ordered[0][0]
        pitches = [item[1] for item in ordered]
        if pitches == sorted(pitches):
            direction = "up-pitch"
        elif pitches == sorted(pitches, reverse=True):
            direction = "down-pitch"
        else:
            direction = "mixed"
        directions[direction] += 1
        offsets.extend(item[0] - first_tick for item in ordered[1:])
        gates.extend(item[2] for item in ordered)
        chord_sizes.append(len({item[1] for item in ordered}))
    return {
        "clusters": sum(directions.values()), "directions": directions,
        "interStringOffsets": offsets, "gates": gates, "chordSizes": chord_sizes,
    }


def audit_factory(files):
    summary = Counter()
    elements, cv_tracks, cc_numbers = Counter(), Counter(), Counter()
    volume_by_sound, expression_by_sound = defaultdict(list), defaultdict(list)
    guitar = Counter()
    guitar_offsets, guitar_gates, guitar_sizes = [], [], []
    errors = []
    for source, data in files:
        try:
            parsed = midi_optimizer.parse_smf(data)
        except Exception as error:
            errors.append({"file": source, "error": str(error)})
            continue
        summary["filesParsed"] += 1
        summary["tracks"] += len(parsed["tracks"])
        for track in parsed["tracks"]:
            texts = text_events(track)
            element = next((text.lower() for _, _, text in texts if text.lower() in ELEMENT_NAMES), None)
            bars = next((int(match.group(1)) for _, _, text in texts if (match := BAR_RE.match(text))), None)
            cv = next((match.groups() for _, _, text in texts if (match := CV_RE.match(text))), None)
            if element:
                elements[element] += 1
            if cv:
                role, number = cv[0].upper(), int(cv[1])
                cv_tracks[(element or "unknown", role, number)] += 1
            sound = initial_sound_and_mix(track)
            kind = "drum" if cv and cv[0].upper() in ("DRUMS", "PERC") else "melodic"
            key = f"{kind}:{sound['msb']}:{sound['lsb']}:{sound['program']}"
            if sound["volume"] is not None:
                volume_by_sound[key].append(sound["volume"])
            if sound["expression"] is not None:
                expression_by_sound[key].append(sound["expression"])
            for event in track["events"]:
                if event["kind"] == "channel" and event["command"] == 11:
                    cc_numbers[event["data"][0]] += 1
                if midi_optimizer.is_note_on(event):
                    summary["notes"] += 1
            if cv and cv[0].upper().startswith("ACC") and 24 <= sound["program"] <= 31:
                evidence = guitar_strum_evidence(track, parsed["division"])
                guitar["candidateTracks"] += 1
                guitar["candidateNotes"] += sum(1 for event in track["events"] if midi_optimizer.is_note_on(event))
                guitar["strumClusters"] += evidence["clusters"]
                for direction, count in evidence["directions"].items():
                    guitar[direction] += count
                guitar_offsets.extend(evidence["interStringOffsets"])
                guitar_gates.extend(evidence["gates"])
                guitar_sizes.extend(evidence["chordSizes"])
                if bars:
                    guitar[f"element:{element}:bars:{bars}"] += evidence["clusters"]
    profile_path = Path("data") / "factory-velocity-profiles.json"
    if profile_path.exists():
        profiles = json.loads(profile_path.read_text(encoding="utf-8"))["profiles"]
    else:
        profiles = dna_builder.factory_profiles(files)[0]["profiles"]
    curve_support = Counter()
    for profile in profiles:
        samples = profile["samples"]
        curve_support["profiles"] += 1
        curve_support["samplesAtLeast32"] += samples >= 32
        curve_support["samplesAtLeast128"] += samples >= 128
        curve_support["samplesAtLeast512"] += samples >= 512
    mixer_profiles = sum(bool(volume_by_sound[key] or expression_by_sound[key])
                         for key in set(volume_by_sound) | set(expression_by_sound))
    return {
        "source": {"files": len(files), "sha256": source_digest(files, "factory-v3.1")},
        "parsed": dict(summary), "errors": errors,
        "styleEvidence": {
            "elementTrackLabels": dict(sorted(elements.items())),
            "cvTrackCombinations": len(cv_tracks),
            "cvTracks": [{"element": key[0], "role": key[1], "cv": key[2], "tracks": value}
                         for key, value in sorted(cv_tracks.items())],
        },
        "controllerEvidence": {
            "ccCounts": {str(key): value for key, value in sorted(cc_numbers.items())},
            "soundsWithVolumeOrExpression": mixer_profiles,
            "volumeEvents": sum(map(len, volume_by_sound.values())),
            "expressionEvents": sum(map(len, expression_by_sound.values())),
            "fxSendEvents": sum(cc_numbers[key] for key in (91, 92, 93, 94, 95)),
        },
        "velocityCurveFeasibility": dict(curve_support),
        "guitarStrummingEvidence": {
            **{key: value for key, value in guitar.items() if not key.startswith("element:")},
            "offsetTicks7": [percentile(guitar_offsets, amount) for amount in (0, .1, .25, .5, .75, .9, 1)],
            "gateTicks7": [percentile(guitar_gates, amount) for amount in (0, .1, .25, .5, .75, .9, 1)],
            "chordSize7": [percentile(guitar_sizes, amount) for amount in (0, .1, .25, .5, .75, .9, 1)],
            "byElement": {key.removeprefix("element:"): value for key, value in guitar.items()
                          if key.startswith("element:")},
        },
    }


def decode_korg_chord(payload):
    if len(payload) != 7 or payload[:3] != b"\x42\x60\x08":
        return None
    chord_type, root, bass, flags = payload[3:]
    if chord_type == 255:
        return {"kind": "no-chord", "raw": payload.hex()}
    if chord_type >= len(CHORD_TYPES) or root > 11 or bass > 11:
        return {"kind": "unknown", "raw": payload.hex(), "typeCode": chord_type,
                "rootCode": root, "bassCode": bass, "flags": flags}
    return {"kind": "chord", "typeCode": chord_type, "quality": CHORD_TYPES[chord_type],
            "root": ROOTS[root], "bass": ROOTS[bass], "flags": flags, "raw": payload.hex()}


def audit_gold(files):
    summary, formats, divisions, cc_numbers = Counter(), Counter(), Counter(), Counter()
    meta127_families, sysex_families, chord_types = Counter(), Counter(), Counter()
    chord_files, explicit_style_markers, native_note_pairs = set(), Counter(), Counter()
    errors = []
    for source, data in files:
        try:
            parsed = midi_optimizer.parse_smf(data)
        except Exception as error:
            errors.append({"file": source, "error": str(error)})
            continue
        summary["filesParsed"] += 1
        formats[parsed["format"]] += 1
        divisions[parsed["division"]] += 1
        active_native = defaultdict(list)
        for track in parsed["tracks"]:
            for _, meta_type, text in text_events(track):
                if meta_type == 6 and text.lower() in ELEMENT_NAMES:
                    explicit_style_markers[text.lower()] += 1
            for event in track["events"]:
                if event["kind"] == "meta":
                    summary[f"meta:{event['metaType']}"] += 1
                    if event["metaType"] == 127:
                        payload = event["payload"]
                        meta127_families[payload[:3].hex()] += 1
                        decoded = decode_korg_chord(payload)
                        if decoded and decoded["kind"] == "chord":
                            chord_files.add(source)
                            chord_types[decoded["quality"]] += 1
                            summary["decodedChordEvents"] += 1
                        elif decoded and decoded["kind"] == "no-chord":
                            summary["noChordEvents"] += 1
                elif event["kind"] == "sysex":
                    payload = event["payload"]
                    summary["sysexEvents"] += 1
                    sysex_families[payload[:4].hex()] += 1
                    if (len(payload) == 9 and payload[:4] == b"\x42\x3f\x78\x01"
                            and payload[4] in (0, 1) and payload[-1] == 0xF7):
                        key = (payload[5], payload[6])
                        if payload[4] == 1:
                            active_native[key].append(event["tick"])
                            native_note_pairs["on"] += 1
                        elif active_native[key]:
                            active_native[key].pop(0)
                            native_note_pairs["paired"] += 1
                        else:
                            native_note_pairs["orphanOff"] += 1
                else:
                    summary[f"command:{event['command']}"] += 1
                    if event["command"] == 11:
                        cc_numbers[event["data"][0]] += 1
                    if midi_optimizer.is_note_on(event):
                        summary["notes"] += 1
        native_note_pairs["danglingOn"] += sum(len(values) for values in active_native.values())
    return {
        "source": {"files": len(files), "sha256": source_digest(files, "gold-v3.1")},
        "parsed": dict(summary), "formats": dict(sorted(formats.items())),
        "divisions": dict(sorted(divisions.items())), "errors": errors,
        "controllerEvidence": {"ccCounts": {str(key): value for key, value in sorted(cc_numbers.items())},
                               "programChangeAuthority": False, "velocityAuthority": False},
        "korgChordEvidence": {
            "decoderStatus": "EVIDENCE_BACKED_CANDIDATE_REQUIRES_DEVICE_CONFIRMATION",
            "filesWithDecodedEvents": len(chord_files),
            "decodedEvents": summary["decodedChordEvents"],
            "qualities": dict(sorted(chord_types.items())),
            "format": "FF 7F 07 42 60 08 type root bass flags; type matches zero-based Pa chord table",
        },
        "korgNativeEventEvidence": {
            "meta127Families": dict(meta127_families.most_common()),
            "sysexFamilies": dict(sysex_families.most_common()),
            "paired42_3f_78_01": dict(native_note_pairs),
            "policy": "preserve raw bytes; do not synthesize until semantics are independently proven",
        },
        "explicitStyleMarkers": dict(explicit_style_markers),
    }


def build_report():
    factory_files, gold_files = dna_builder.read_nested_archive(ARCHIVE)
    factory = audit_factory(factory_files)
    gold = audit_gold(gold_files)
    return {
        "schema": "dna-midi-studio-corpus-forensics", "version": "3.1",
        "date": datetime.now(timezone.utc).date().isoformat(),
        "archive": {"path": str(ARCHIVE), "sha256": hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()},
        "factory": factory, "gold": gold,
        "confirmedFindings": [
            "Factory contains explicit Style Element, track-role and CV labels ignored by the current v2 builder.",
            "Factory contains CC7/CC11 mixer evidence and extensive GM guitar-program ACC evidence.",
            "Factory source contains no CC91-95 FX-send evidence, so Factory-learned FX claims are unsupported.",
            "GOLD contains Korg manufacturer meta/SysEx events, RPN/NRPN, FX sends, lyrics and complete song form.",
            "GOLD has no reliable explicit Intro/Variation/Fill/Ending markers; form must be inferred or decoded from proven events.",
            "GOLD Program Change and velocity remain non-authoritative and must not enter selection or mutation decisions.",
        ],
        "nextImplementationGates": [
            "Build Factory seven-point velocity and mixer curves with per-profile sample thresholds.",
            "Segment Factory tracks by real element/CV labels and build guitar strumming evidence.",
            "Decode GOLD Korg chord meta events read-only and validate against note-derived chords.",
            "Add independent protected-event verifier before volume, FX, key-range or relationship mutation.",
            "Do not promise equal acoustic loudness without a Pa800 audio render; expose a MIDI energy/headroom proxy instead.",
        ],
        "invariants": {"goldAffectsVelocity": False, "goldAffectsProgramChange": False,
                       "sourceFilesModified": False,
                       "auditDoesNotRewriteUnknownKorgEvents": True},
    }


def main():
    report = build_report()
    target = Path("data") / "corpus-forensics-report.json"
    dna_builder.write_json(target, report)
    print(json.dumps({
        "result": "PASS", "report": str(target),
        "factoryFiles": report["factory"]["source"]["files"],
        "goldFiles": report["gold"]["source"]["files"],
        "factoryGuitarClusters": report["factory"]["guitarStrummingEvidence"]["strumClusters"],
        "goldChordEvents": report["gold"]["korgChordEvidence"]["decodedEvents"],
    }, indent=2))


if __name__ == "__main__":
    main()