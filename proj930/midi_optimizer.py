#!/usr/bin/env python3
"""Ne-destruktivni Standard MIDI File optimizer s Factory velocity profilima."""

from __future__ import annotations

import copy
import hashlib
import math
import struct
from bisect import bisect_right
from collections import Counter, defaultdict

import midi_integrity
import factory_velocity
import phase_optimizer
import special_track_engine
import performance_engine
import performance_gesture_engine


def read_vlq(data, pos, end):
    value = 0
    for _ in range(4):
        if pos >= end:
            raise ValueError("Prekinuta MIDI variable-length vrijednost")
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 127)
        if byte < 128:
            return value, pos
    return value, pos


def write_vlq(value):
    buffer, output = value & 127, []
    value >>= 7
    while value:
        buffer = (buffer << 8) | ((value & 127) | 128)
        value >>= 7
    while True:
        output.append(buffer & 255)
        if buffer & 128:
            buffer >>= 8
        else:
            return output


def parse_smf(data: bytes):
    if len(data) < 14 or data[:4] != b"MThd":
        raise ValueError("Datoteka nije Standard MIDI File")
    header_length, midi_format, track_count, division = struct.unpack_from(">IHHH", data, 4)
    if header_length < 6:
        raise ValueError("Neispravno MIDI zaglavlje")
    pos, tracks = 8 + header_length, []
    for track_index in range(track_count):
        if pos + 8 > len(data) or data[pos:pos + 4] != b"MTrk":
            raise ValueError(f"Nedostaje MTrk {track_index + 1}")
        length = struct.unpack_from(">I", data, pos + 4)[0]
        pos += 8
        end = min(pos + length, len(data))
        tick, running, order, events = 0, None, 0, []
        while pos < end:
            delta, pos = read_vlq(data, pos, end)
            tick += delta
            if pos >= end:
                break
            status = data[pos]
            if status < 128:
                if running is None:
                    raise ValueError("Running status bez prethodnog statusa")
                status = running
            else:
                pos += 1
                if status < 240:
                    running = status
            event = {"tick": tick, "order": order, "status": status, "remove": False}
            order += 1
            if status == 255:
                if pos >= end:
                    raise ValueError("Prekinut meta event")
                meta_type = data[pos]
                pos += 1
                size, pos = read_vlq(data, pos, end)
                payload = bytes(data[pos:pos + size])
                pos += size
                event.update({"kind": "meta", "metaType": meta_type, "payload": payload})
            elif status in (240, 247):
                size, pos = read_vlq(data, pos, end)
                payload = bytes(data[pos:pos + size])
                pos += size
                event.update({"kind": "sysex", "payload": payload})
                running = None
            elif 128 <= status <= 239:
                command, channel = status >> 4, status & 15
                if pos >= end:
                    raise ValueError("Prekinut channel event")
                one = data[pos]
                pos += 1
                values = [one]
                if command not in (12, 13):
                    if pos >= end:
                        raise ValueError("Prekinut channel event")
                    values.append(data[pos])
                    pos += 1
                event.update({"kind": "channel", "command": command, "channel": channel, "data": values})
            else:
                raise ValueError(f"Nepodržan MIDI status 0x{status:02X}")
            events.append(event)
        tracks.append({"index": track_index, "events": events, "endTick": tick})
        pos = end
    return {"format": midi_format, "division": division, "tracks": tracks}


def event_priority(event):
    if event["kind"] == "meta":
        return 9 if event["metaType"] == 47 else 0
    if event["kind"] == "channel":
        command = event["command"]
        if command == 8 or (command == 9 and len(event["data"]) > 1 and event["data"][1] == 0):
            return 3
        if command == 9:
            return 4
        if command in (11, 12):
            return 2
    return 5


def encode_event(event):
    if event["kind"] == "meta":
        payload = event["payload"]
        return bytes([255, event["metaType"], *write_vlq(len(payload))]) + payload
    if event["kind"] == "sysex":
        payload = event["payload"]
        return bytes([event["status"], *write_vlq(len(payload))]) + payload
    return bytes([event["status"], *event["data"]])


def encode_smf(parsed):
    chunks = []
    for track in parsed["tracks"]:
        events = [event for event in track["events"] if not event.get("remove") and not (event["kind"] == "meta" and event["metaType"] == 47)]
        # Izvorni redoslijed na istom ticku važan je za nepoznate Korg
        # meta/SysEx događaje. Samo ciljano popravljeni note-off dobiva
        # privremeni sortOrder neposredno prije sljedećeg note-on događaja.
        events.sort(key=lambda event: (event["tick"], event.get("sortOrder", event["order"])))
        end_tick = max([track["endTick"], *(event["tick"] for event in events)] if events else [track["endTick"]])
        events.append({"tick": end_tick, "order": 10**9, "kind": "meta", "metaType": 47, "payload": b"", "status": 255})
        body, previous, running_status = bytearray(), 0, None
        for event in events:
            body.extend(write_vlq(max(0, round(event["tick"] - previous))))
            encoded = encode_event(event)
            if event["kind"] == "channel" and encoded[0] == running_status:
                body.extend(encoded[1:])
            else:
                body.extend(encoded)
            running_status = encoded[0] if event["kind"] == "channel" else None
            previous = event["tick"]
        chunks.append(b"MTrk" + struct.pack(">I", len(body)) + body)
    header = b"MThd" + struct.pack(">IHHH", 6, parsed["format"], len(chunks), parsed["division"])
    return header + b"".join(chunks)


def is_note_on(event):
    return event["kind"] == "channel" and event["command"] == 9 and len(event["data"]) > 1 and event["data"][1] > 0


def is_note_off(event):
    return event["kind"] == "channel" and (event["command"] == 8 or (event["command"] == 9 and len(event["data"]) > 1 and event["data"][1] == 0))


def pair_notes(track, repair=False, stats=None):
    stats = stats if stats is not None else Counter()
    active, notes = defaultdict(list), []
    events = sorted((event for event in track["events"] if not event.get("remove")), key=lambda event: (event["tick"], event["order"]))
    for event in events:
        if is_note_on(event):
            key = (event["channel"], event["data"][0])
            active[key].append(event)
        elif is_note_off(event):
            key = (event["channel"], event["data"][0])
            if active[key]:
                on = active[key].pop(0)
                if event["tick"] <= on["tick"]:
                    if repair:
                        event["tick"] = on["tick"] + 1
                        stats["invalidDurationsFixed"] += 1
                    else:
                        stats["invalidDurations"] += 1
                notes.append({"on": on, "off": event, "channel": key[0], "pitch": key[1]})
            else:
                stats["orphanNoteOffs"] += 1
                if repair:
                    event["remove"] = True
    if repair:
        next_order = max((event["order"] for event in track["events"]), default=0) + 1
        for (channel, pitch), note_ons in active.items():
            for on in note_ons:
                end_tick = max(track["endTick"], on["tick"] + 1)
                off = {"tick": end_tick, "order": next_order, "status": 0x80 | channel, "kind": "channel",
                       "command": 8, "channel": channel, "data": [pitch, 0], "remove": False}
                next_order += 1
                track["events"].append(off)
                notes.append({"on": on, "off": off, "channel": channel, "pitch": pitch})
                stats["danglingNotesFixed"] += 1
    else:
        stats["danglingNotes"] += sum(len(values) for values in active.values())
    return notes


def profile_indexes(profiles):
    by_key = {
        item["instrumentKey"]: item
        for item in profiles
        if item.get("instrumentKey") and item.get("kind") in {"drum", "melodic"}
    }
    melodic_program, drum_note = defaultdict(list), defaultdict(list)
    for profile in profiles:
        if profile.get("kind") == "drum":
            drum_note[profile.get("drumNote")].append(profile)
        elif profile.get("kind") == "melodic" and profile.get("program") is not None:
            melodic_program[profile["program"]].append(profile)
    for values in (*melodic_program.values(), *drum_note.values()):
        values.sort(key=lambda item: (
            -int(item.get("samples", 0)),
            str(item.get("instrumentKey", "")),
        ))
    return by_key, melodic_program, drum_note


def attach_instruments(track, notes):
    note_map = {id(note["on"]): note for note in notes}
    state = [{"msb": 0, "lsb": 0, "program": 0} for _ in range(16)]
    for event in sorted((item for item in track["events"] if not item.get("remove")), key=lambda item: (item["tick"], item["order"])):
        if event["kind"] != "channel":
            continue
        channel, command, values = event["channel"], event["command"], event["data"]
        if command == 11 and values[0] == 0:
            state[channel]["msb"] = values[1]
        elif command == 11 and values[0] == 32:
            state[channel]["lsb"] = values[1]
        elif command == 12:
            state[channel]["program"] = values[0]
        elif is_note_on(event) and id(event) in note_map:
            current = state[channel]
            note = note_map[id(event)]
            note["instrumentKey"] = (f"drum:{current['msb']}:{current['lsb']}:{current['program']}:{note['pitch']}"
                                     if channel == 9 else f"melodic:{current['msb']}:{current['lsb']}:{current['program']}")
            note["program"] = current["program"]


def audit_tracks(parsed, grid_ticks=None):
    stats = Counter()
    for track in parsed["tracks"]:
        notes = pair_notes(track, repair=False, stats=stats)
        stats["notes"] += len(notes)
        grouped = defaultdict(list)
        for note in notes:
            grouped[(note["channel"], note["pitch"])].append(note)
            if grid_ticks and note["on"]["tick"] % grid_ticks:
                stats["offGridNotes"] += 1
        for values in grouped.values():
            values.sort(key=lambda note: (note["on"]["tick"], note["off"]["tick"]))
            for index, note in enumerate(values):
                if index and note["on"]["tick"] == values[index - 1]["on"]["tick"]:
                    stats["duplicateNotes"] += 1
                elif index and note["on"]["tick"] < values[index - 1]["off"]["tick"]:
                    stats["overlappingNotes"] += 1
        controller_state = {}
        marker_ticks = {event["tick"] for event in track["events"] if event["kind"] == "meta" and event["metaType"] == 6}
        for event in sorted(track["events"], key=lambda item: (item["tick"], item["order"])):
            if event["tick"] in marker_ticks:
                controller_state.clear()
            if event["kind"] == "channel" and event["command"] in (11, 12):
                key = (event["channel"], event["command"], event["data"][0] if event["command"] == 11 else -1)
                value = tuple(event["data"])
                if controller_state.get(key) == value:
                    stats["redundantControllers"] += 1
                controller_state[key] = value
    return stats


def quality_score(stats):
    notes = max(1, stats.get("notes", 0))
    weighted = (stats.get("duplicateNotes", 0) * 2.4 + stats.get("overlappingNotes", 0) * 2.0
                + stats.get("danglingNotes", 0) * 3.0 + stats.get("orphanNoteOffs", 0) * 2.0
                + stats.get("invalidDurations", 0) * 3.0
                + stats.get("redundantControllers", 0) * .35 + stats.get("offGridNotes", 0) * .12)
    return max(0, min(100, round(100 - 100 * weighted / notes, 1)))


def clean_note_pairs(track, notes, stats):
    grouped = defaultdict(list)
    for note in notes:
        if note["on"].get("remove") or note["off"].get("remove"):
            continue
        grouped[(note["channel"], note["pitch"])].append(note)
    for values in grouped.values():
        values.sort(key=lambda note: (note["on"]["tick"], note["off"]["tick"]))
        kept = []
        for note in values:
            if kept and note["on"]["tick"] == kept[-1]["on"]["tick"]:
                current, previous = note, kept[-1]
                keep_current = (current["on"]["data"][1], current["off"]["tick"]) > (previous["on"]["data"][1], previous["off"]["tick"])
                loser = previous if keep_current else current
                loser["on"]["remove"] = loser["off"]["remove"] = True
                stats["duplicateNotesRemoved"] += 1
                if keep_current:
                    kept[-1] = current
                continue
            if kept and note["on"]["tick"] < kept[-1]["off"]["tick"]:
                kept[-1]["off"]["tick"] = max(kept[-1]["on"]["tick"] + 1, note["on"]["tick"])
                kept[-1]["off"]["sortOrder"] = note["on"]["order"] - 0.25
                stats["overlapsFixed"] += 1
            kept.append(note)


def quantize_notes(notes, grid_ticks, strength, stats):
    ratio = max(0, min(100, strength)) / 100
    if not grid_ticks or ratio <= 0:
        return
    for note in notes:
        if note["on"].get("remove"):
            continue
        start, end = note["on"]["tick"], note["off"]["tick"]
        target_start = round(start / grid_ticks) * grid_ticks
        target_end = round(end / grid_ticks) * grid_ticks
        new_start = round(start + (target_start - start) * ratio)
        new_end = round(end + (target_end - end) * ratio)
        new_end = max(new_start + max(1, grid_ticks // 8), new_end)
        if (new_start, new_end) != (start, end):
            stats["notesQuantized"] += 1
            note["on"]["tick"], note["off"]["tick"] = max(0, new_start), new_end


def optimize_velocities(notes, indexes, strength, stats):
    ratio = max(0, min(100, strength)) / 100
    for note in notes:
        if note["on"].get("remove"):
            continue
        profile, selection = resolve_profile(note, indexes, with_selection=True)
        if not profile:
            stats["velocityProfilesMissing"] += 1
            continue
        if selection["ambiguous"]:
            stats["velocityProfilesAmbiguous"] += 1
            continue
        stats["velocityProfilesMatched"] += 1
        original = note["on"]["data"][1]
        adjusted = factory_velocity.remap_velocity(profile, original, round(ratio * 100))
        if adjusted != original:
            note["on"]["data"][1] = adjusted
            stats["velocitiesAdjusted"] += 1


def _profile_register(profile):
    register = profile.get("register") or profile.get("keyRange") or {}
    try:
        low = int(register.get("low", register.get("min")))
        high = int(register.get("high", register.get("max")))
    except (TypeError, ValueError):
        return None
    return (low, high) if 0 <= low <= high <= 127 else None


def resolve_profile(note, indexes, with_selection=False):
    by_key, melodic_program, drum_note = indexes
    profile = by_key.get(note.get("instrumentKey"))
    if profile:
        result = (profile, {
            "method": "exact_instrument_key",
            "candidate_count": 1,
            "ambiguous": False,
        })
        return result if with_selection else profile
    candidates = drum_note.get(note["pitch"]) if note["channel"] == 9 else melodic_program.get(note.get("program"))
    if not candidates:
        return (None, {
            "method": "missing",
            "candidate_count": 0,
            "ambiguous": False,
        }) if with_selection else None

    pitch = int(note["pitch"])
    scored = []
    for candidate in candidates:
        register = _profile_register(candidate)
        in_register = register is not None and register[0] <= pitch <= register[1]
        distance = 0 if in_register else (
            min(abs(pitch - register[0]), abs(pitch - register[1]))
            if register else 999
        )
        scored.append((
            1 if in_register else 0,
            -distance,
            int(candidate.get("samples", 0)),
            str(candidate.get("instrumentKey", "")),
            candidate,
        ))
    scored.sort(key=lambda item: item[:-1], reverse=True)
    best = scored[0][-1]
    # Equal evidence with different profiles must not silently alter dynamics.
    top_evidence = scored[0][:-2]
    tied = [item for item in scored if item[:-2] == top_evidence]
    selection = {
        "method": "register_then_samples",
        "candidate_count": len(candidates),
        "ambiguous": len(tied) > 1,
    }
    result = (best, selection)
    return result if with_selection else best


def repair_key_ranges(notes, indexes, stats):
    by_key = indexes[0]
    for note in notes:
        if note["on"].get("remove") or note["channel"] == 9:
            continue
        # Registar se ne smije posuditi samo po GM programu iz druge banke.
        # Za automatski pomak traži se točan Factory instrumentKey.
        profile = by_key.get(note.get("instrumentKey"))
        register = profile.get("register") if profile else None
        if not register:
            stats["keyRangeProfilesMissing"] += 1
            continue
        low, high, pitch = int(register["low"]), int(register["high"]), int(note["pitch"])
        if int(profile.get("samples", 0)) < 32 or high - low < 12:
            stats["keyRangeInsufficientEvidence"] += 1
            continue
        if low <= pitch <= high:
            continue
        candidates = [pitch + octave * 12 for octave in range(-10, 11)
                      if low <= pitch + octave * 12 <= high and 0 <= pitch + octave * 12 <= 127]
        if not candidates:
            stats["keyRangeManualReview"] += 1
            continue
        center = (low + high) / 2
        repaired = min(candidates, key=lambda value: (abs(value - pitch), abs(value - center), value))
        note["pitch"] = repaired
        note["on"]["data"][0] = repaired
        note["off"]["data"][0] = repaired
        stats["keyRangeNotesFolded"] += 1


def optimize_track_mixer(track, notes, indexes, strength, insert_missing, stats):
    ratio = max(0, min(100, int(strength))) / 100
    if ratio <= 0:
        return
    profiles_by_channel = defaultdict(list)
    velocities_by_channel = defaultdict(list)
    first_note_by_channel = {}
    by_key = indexes[0]
    for note in notes:
        if note["on"].get("remove"):
            continue
        # CC7/CC11 automatski se mijenjaju samo uz točan bank/program profil.
        profile = by_key.get(note.get("instrumentKey"))
        if not profile:
            continue
        channel = note["channel"]
        profiles_by_channel[channel].append(profile)
        velocities_by_channel[channel].append(note["on"]["data"][1])
        current = first_note_by_channel.get(channel)
        if current is None or (note["on"]["tick"], note["on"]["order"]) < (current["tick"], current["order"]):
            first_note_by_channel[channel] = note["on"]

    def target_for(channel, field, intensity):
        values = [factory_velocity.controller_at(profile.get("mixerProfile", {}).get(field), intensity)
                  for profile in profiles_by_channel[channel]]
        values = [value for value in values if value is not None]
        return round(sum(values) / len(values)) if values else None

    insert_targets = {}
    for channel, profiles in profiles_by_channel.items():
        source_values = sorted(velocities_by_channel[channel])
        source_median = source_values[len(source_values) // 2]
        intensity = (source_median - 1) * 100 / 126
        for cc, field in ((7, "volume"), (11, "expression")):
            target = target_for(channel, field, intensity)
            if target is not None:
                insert_targets[(channel, cc)] = target
                stats["mixerProfilesMatched"] += 1

    present = set()
    for event in sorted(track["events"], key=lambda item: (item["tick"], item["order"])):
        if event.get("remove") or event["kind"] != "channel" or event["command"] != 11:
            continue
        cc = event["data"][0]
        key = (event["channel"], cc)
        if cc not in (7, 11) or key not in insert_targets:
            continue
        present.add(key)
        original = event["data"][1]
        field = "volume" if cc == 7 else "expression"
        event_intensity = original * 100 / 127
        target = target_for(event["channel"], field, event_intensity)
        adjusted = max(0, min(127, round(original + (target - original) * ratio)))
        if adjusted != original:
            event["data"][1] = adjusted
            stats["mixerControllersAdjusted"] += 1

    if not insert_missing:
        return
    next_order = max((event["order"] for event in track["events"]), default=0) + 1
    for key, target in sorted(insert_targets.items()):
        if key in present:
            continue
        channel, cc = key
        first_note = first_note_by_channel[channel]
        event = {"tick": first_note["tick"], "order": next_order,
                 "sortOrder": first_note["order"] - 0.5 + cc / 1000,
                 "status": 0xB0 | channel, "kind": "channel", "command": 11,
                 "channel": channel, "data": [cc, target], "remove": False}
        next_order += 1
        track["events"].append(event)
        stats["mixerControllersInserted"] += 1


def clean_controllers(track, stats):
    marker_ticks = {event["tick"] for event in track["events"] if event["kind"] == "meta" and event["metaType"] == 6}
    state, exact, reset_ticks = {}, set(), set()
    for event in sorted(track["events"], key=lambda item: (item["tick"], item["order"])):
        if event.get("remove"):
            continue
        if event["tick"] in marker_ticks and event["tick"] not in reset_ticks:
            state.clear()
            reset_ticks.add(event["tick"])
        if event["kind"] == "channel" and event["command"] == 11:
            cc = event["data"][0]
            # Bank Select te RPN/NRPN/Data Entry su protected događaji.
            # Program Change se uopće ne obrađuje ovdje.
            if cc in midi_integrity.ALWAYS_PROTECTED_CC:
                continue
            key = (event["channel"], event["command"], cc)
            value = tuple(event["data"])
            signature = (event["tick"], event["status"], value)
            if signature in exact or state.get(key) == value:
                event["remove"] = True
                stats["redundantControllersRemoved"] += 1
            else:
                state[key] = value
                exact.add(signature)


def _tempo_segments(parsed):
    """Vrati globalnu tick/sekunda mapu; format 1 koristi conductor tempo događaje."""
    division = parsed["division"]
    if division & 0x8000:
        fps_byte = (division >> 8) & 255
        fps = 256 - fps_byte if fps_byte >= 128 else fps_byte
        ticks_per_frame = division & 255
        rate = max(1, fps * ticks_per_frame)
        return {"smpte": True, "rate": rate, "ticks": [0], "segments": [(0, 0.0, 500000)]}

    tempo_events = [(0, -1, 500000)]
    for track in parsed["tracks"]:
        for event in track["events"]:
            if event["kind"] == "meta" and event["metaType"] == 81 and len(event["payload"]) == 3:
                tempo_events.append((event["tick"], event["order"], int.from_bytes(event["payload"], "big")))
    tempo_events.sort(key=lambda item: (item[0], item[1]))
    collapsed = []
    for tick, _, micros in tempo_events:
        micros = max(1, micros)
        if collapsed and collapsed[-1][0] == tick:
            collapsed[-1] = (tick, micros)
        else:
            collapsed.append((tick, micros))
    seconds, previous_tick, previous_tempo, segments = 0.0, collapsed[0][0], collapsed[0][1], []
    segments.append((previous_tick, seconds, previous_tempo))
    for tick, micros in collapsed[1:]:
        seconds += (tick - previous_tick) * previous_tempo / (division * 1_000_000)
        segments.append((tick, seconds, micros))
        previous_tick, previous_tempo = tick, micros
    return {"smpte": False, "ppq": division, "ticks": [item[0] for item in segments], "segments": segments}


def _tick_seconds(tick, tempo_map):
    if tempo_map["smpte"]:
        return tick / tempo_map["rate"]
    index = max(0, bisect_right(tempo_map["ticks"], tick) - 1)
    start_tick, start_seconds, micros = tempo_map["segments"][index]
    return start_seconds + (tick - start_tick) * micros / (tempo_map["ppq"] * 1_000_000)


def midi_preview(data: bytes, source="song.mid", max_notes=25_000, max_seconds=600):
    """Kompaktan, read-only piano-roll/playback prikaz za lokalni Web GUI."""
    parsed = parse_smf(data)
    tempo_map = _tempo_segments(parsed)
    notes, channels, duration_tick = [], Counter(), 0
    track_names = {}
    meter = "4/4"
    for track in parsed["tracks"]:
        name = next((event["payload"].decode("utf-8", "replace") for event in track["events"]
                     if event["kind"] == "meta" and event["metaType"] == 3), f"Track {track['index'] + 1}")
        track_names[track["index"]] = name[:80]
        signature = next((event for event in track["events"]
                          if event["kind"] == "meta" and event["metaType"] == 88 and len(event["payload"]) >= 2), None)
        if signature:
            meter = f"{signature['payload'][0]}/{2 ** signature['payload'][1]}"
        paired = pair_notes(track)
        attach_instruments(track, paired)
        for note in paired:
            start_tick, end_tick = note["on"]["tick"], max(note["on"]["tick"] + 1, note["off"]["tick"])
            start, end = _tick_seconds(start_tick, tempo_map), _tick_seconds(end_tick, tempo_map)
            channels[note["channel"]] += 1
            duration_tick = max(duration_tick, end_tick)
            notes.append({
                "id": f"{track['index']}:{note['on']['order']}",
                "start": round(start, 5), "duration": round(max(0.01, end - start), 5),
                "tick": start_tick, "endTick": end_tick, "pitch": note["pitch"],
                "velocity": note["on"]["data"][1], "channel": note["channel"] + 1,
                "track": track["index"], "program": note.get("program", 0),
            })
    notes.sort(key=lambda item: (item["start"], item["channel"], item["pitch"]))
    total_notes = len(notes)
    preview_notes = [note for note in notes if note["start"] <= max_seconds][:max_notes]
    duration_seconds = _tick_seconds(duration_tick, tempo_map)
    first_tempo = tempo_map["segments"][0][2]
    return {
        "schema": "dna-midi-preview", "version": "1.0",
        "source": source, "format": parsed["format"], "tracks": len(parsed["tracks"]),
        "ppq": None if tempo_map["smpte"] else parsed["division"],
        "tempo": round(60_000_000 / first_tempo, 3), "meter": meter,
        "durationSeconds": round(duration_seconds, 3), "durationTicks": duration_tick,
        "noteCount": total_notes, "notesReturned": len(preview_notes),
        "truncated": len(preview_notes) < total_notes,
        "previewLimit": {"notes": max_notes, "seconds": max_seconds},
        "trackNames": track_names,
        "channels": [{"channel": channel + 1, "notes": count, "drums": channel == 9}
                     for channel, count in sorted(channels.items())],
        "notes": preview_notes,
        "invariants": {"readOnly": True, "goldAffectsDynamics": False},
    }


def technical_parameters(parsed):
    channels, tempos, meters, markers, sysex, eot, sound_selections = set(), [], [], [], 0, 0, []
    for track in parsed["tracks"]:
        sound_state = [{"msb": None, "lsb": None, "program": None} for _ in range(16)]
        for event in sorted(track["events"], key=lambda item: (item["tick"], item["order"])):
            if event["kind"] == "channel":
                channels.add(event["channel"] + 1)
                channel, command, values = event["channel"], event["command"], event["data"]
                field = None
                if command == 11 and values[0] == 0:
                    field, value = "msb", values[1]
                elif command == 11 and values[0] == 32:
                    field, value = "lsb", values[1]
                elif command == 12:
                    field, value = "program", values[0]
                if field and sound_state[channel][field] != value:
                    sound_state[channel][field] = value
                    sound_selections.append([track["index"], event["tick"], channel + 1, field, value])
            elif event["kind"] == "sysex":
                sysex += 1
            elif event["kind"] == "meta":
                if event["metaType"] == 81 and len(event["payload"]) == 3:
                    micros = int.from_bytes(event["payload"], "big")
                    if micros:
                        tempos.append(round(60_000_000 / micros, 3))
                elif event["metaType"] == 88 and len(event["payload"]) >= 2:
                    meters.append(f"{event['payload'][0]}/{2 ** event['payload'][1]}")
                elif event["metaType"] == 6:
                    markers.append(event["payload"].decode("utf-8", "replace"))
                elif event["metaType"] == 47:
                    eot += 1
    return {"format": parsed["format"], "tracks": len(parsed["tracks"]),
            "ppq": None if parsed["division"] & 0x8000 else parsed["division"],
            "channels": sorted(channels), "tempos": tempos, "meters": meters,
            "markers": markers, "sysexEvents": sysex, "endOfTrackEvents": eot,
            "soundSelections": sound_selections}


def midi_energy_headroom(parsed, target_index=64.0):
    """Vrati uređajno neovisan MIDI proxy, nikada audio/LUFS tvrdnju.

    Indeks je duration-weighted RMS pojedinačne note nakon velocity, CC7 i
    CC11 faktora. Ne modelira Pa800 sample, EQ, insert/master FX ni zvučnik.
    """
    weighted_energy, duration_weight, peak, note_count = 0.0, 0.0, 0.0, 0
    for track in parsed["tracks"]:
        notes = pair_notes(track)
        note_map = {id(note["on"]): note for note in notes}
        state = [{"volume": 100, "expression": 127} for _ in range(16)]
        for event in sorted((item for item in track["events"] if not item.get("remove")),
                            key=lambda item: (item["tick"], item["order"])):
            if event["kind"] != "channel":
                continue
            channel = event["channel"]
            if event["command"] == 11 and event["data"][0] == 7:
                state[channel]["volume"] = event["data"][1]
            elif event["command"] == 11 and event["data"][0] == 11:
                state[channel]["expression"] = event["data"][1]
            elif is_note_on(event) and id(event) in note_map:
                note = note_map[id(event)]
                duration = max(1, note["off"]["tick"] - note["on"]["tick"])
                amplitude = ((event["data"][1] / 127) * (state[channel]["volume"] / 127)
                             * (state[channel]["expression"] / 127))
                weighted_energy += amplitude * amplitude * duration
                duration_weight += duration
                peak = max(peak, amplitude)
                note_count += 1
    rms = math.sqrt(weighted_energy / duration_weight) if duration_weight else 0.0
    index = round(rms * 100, 2)
    headroom = round(-20 * math.log10(max(peak, 1e-9)), 2) if note_count else None
    target = max(0.0, min(100.0, float(target_index)))
    return {
        "energyIndex": index,
        "targetIndex": round(target, 2),
        "deviation": round(index - target, 2),
        "withinTolerance": abs(index - target) <= 2.5,
        "peakNoteAmplitude": round(peak, 6),
        "perVoiceHeadroomDb": headroom,
        "noteCount": note_count,
        "measurement": "duration-weighted MIDI velocity*CC7*CC11 RMS proxy",
        "audioLufsMeasured": False,
    }


def validate_optimized_smf(parsed, stats):
    issues = []
    if stats.get("orphanNoteOffs"):
        issues.append(f"{stats['orphanNoteOffs']} note-off događaja nema note-on")
    if stats.get("danglingNotes"):
        issues.append(f"{stats['danglingNotes']} note-on događaja nema note-off")
    if stats.get("invalidDurations"):
        issues.append(f"{stats['invalidDurations']} nota ima nevaljano trajanje")
    for index, track in enumerate(parsed["tracks"]):
        eot = [event for event in track["events"] if event["kind"] == "meta" and event["metaType"] == 47]
        if len(eot) != 1:
            issues.append(f"Traka {index + 1} mora imati točno jedan End Of Track")
    return {"passed": not issues, "issues": issues, "invalidMidiExported": False}


def preflight_midi(data: bytes, source="song.mid"):
    parsed = parse_smf(data)
    ppq = None if parsed["division"] & 0x8000 else parsed["division"]
    grid = round(ppq / 4) if ppq else None
    stats = audit_tracks(parsed, grid)
    technical = technical_parameters(parsed)
    velocities, pitches = [], []
    for track in parsed["tracks"]:
        for note in pair_notes(track):
            velocities.append(note["on"]["data"][1])
            pitches.append(note["pitch"])
    critical, important, information = [], [], []
    for key, label in (("orphanNoteOffs", "note-off bez note-on"),
                       ("danglingNotes", "note-on bez note-off"),
                       ("invalidDurations", "nota s nevaljanim trajanjem")):
        if stats.get(key):
            critical.append({"code": key, "count": stats[key], "message": label})
    if technical["endOfTrackEvents"] != technical["tracks"]:
        critical.append({"code": "endOfTrack", "count": technical["endOfTrackEvents"],
                         "message": "broj End Of Track događaja ne odgovara broju traka"})
    for key, label in (("duplicateNotes", "dupliciranih nota"), ("overlappingNotes", "preklopljenih nota"),
                       ("redundantControllers", "redundantnih CC/Program događaja")):
        if stats.get(key):
            important.append({"code": key, "count": stats[key], "message": label})
    extreme = sum(1 for value in velocities if value <= 5 or value >= 124)
    if extreme:
        important.append({"code": "extremeVelocity", "count": extreme, "message": "ekstremnih velocity vrijednosti"})
    if stats.get("offGridNotes"):
        information.append({"code": "offGridNotes", "count": stats["offGridNotes"],
                            "message": "nota izvan 1/16 mreže"})
    if len(technical["tempos"]) > 1:
        information.append({"code": "tempoMap", "count": len(technical["tempos"]), "message": "tempo događaja"})
    if len(technical["meters"]) > 1:
        information.append({"code": "meterMap", "count": len(technical["meters"]), "message": "time-signature događaja"})
    if len(data) > 8_000_000:
        information.append({"code": "largeFile", "count": len(data), "message": "velika MIDI datoteka"})
    return {
        "schema": "dna-midi-preflight", "version": "1.0", "source": source,
        "qualityScore": quality_score(stats), "blocking": bool(critical),
        "severity": {"critical": critical, "important": important, "information": information},
        "metrics": {**dict(stats), "velocityMin": min(velocities) if velocities else None,
                    "velocityMax": max(velocities) if velocities else None,
                    "pitchLow": min(pitches) if pitches else None, "pitchHigh": max(pitches) if pitches else None},
        "technicalParameters": technical,
        "energyHeadroom": midi_energy_headroom(parsed),
        "invariants": {"readOnly": True, "analysisVelocityUsed": False, "goldAffectsDynamics": False},
    }


def _apply_general_rules(parsed: dict, changes: Counter) -> dict:
    """General Rules Export Gate 9.30 — hard Pa800 instrument limits.

    Enforces:
      - Key range per GM program (bass guitar E1–G3, trumpet E3–A#5, etc.)
      - Drum channel (9): only valid Pa800 GM drum keys (27–87)
      - Velocity min/max per instrument category
      - Polyphony check (Pa800 limit = 54 voices)
    All violations are CLAMPED (keys/velocity) or REMOVED (drum keys).
    Key clamping also updates the corresponding note-off so pairs stay matched.
    """
    import json as _json
    from pathlib import Path as _Path

    _PROJ = _Path(__file__).resolve().parent
    _RULES_PATH = _PROJ / "data" / "general-rules-9.30.json"
    if not _RULES_PATH.exists():
        return {"enabled": False, "reason": "general-rules-9.30.json not found", "violations": 0}

    _rules = _json.loads(_RULES_PATH.read_text(encoding="utf-8"))
    _gm = {int(k): v for k, v in _rules["gmMelodicRanges"].items()}
    _drum_keys = {int(k) for k, v in _rules["drumValidKeys"].items()}
    _vel_rules = _rules["velocityRules"]
    _poly_rules = _rules["polyphonyRules"]
    _max_poly = int(_poly_rules.get("pa800_total", {}).get("maxVoices", 54))

    _notes = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    def _nn(n): return f"{_notes[n%12]}{n//12-1}"

    channel_state = {}
    violations = 0
    clamped_low = 0
    clamped_high = 0
    drum_blocked = 0
    vel_clamped = 0
    drum_validated = 0

    # Phase 1: Build pitch clamping map per (channel, original_pitch) so
    # note-off events get the same clamped pitch as their note-on.
    # We also mark drum keys for removal (note-off included).
    clamp_map = {}   # (track_idx, channel, orig_pitch) -> clamped_pitch
    drum_remove = set()  # set of (track_idx, event_id) to remove

    for track in parsed["tracks"]:
        ti = track["index"]
        for ev in track["events"]:
            if ev.get("remove") or ev["kind"] != "channel":
                continue
            ch = ev["channel"]
            cmd = ev["command"]
            data = ev["data"]

            if ch not in channel_state:
                channel_state[ch] = {"program": 0}
            if cmd == 12:
                channel_state[ch]["program"] = data[0]

            # Note-on: determine clamping
            if cmd == 9 and data[1] > 0:
                pitch = data[0]
                velocity = data[1]
                program = channel_state[ch]["program"]

                if ch == 9:
                    drum_validated += 1
                    if pitch not in _drum_keys:
                        # Mark both note-on and matching note-off for removal
                        ev["remove"] = True
                        drum_blocked += 1
                        violations += 1
                        drum_remove.add((ti, id(ev)))
                        continue
                else:
                    if program in _gm:
                        info = _gm[program]
                        lo, hi = info["lo"], info["hi"]
                        if pitch < lo:
                            data[0] = lo
                            clamp_map[(ti, ch, pitch)] = lo
                            clamped_low += 1
                            violations += 1
                        elif pitch > hi:
                            data[0] = hi
                            clamp_map[(ti, ch, pitch)] = hi
                            clamped_high += 1
                            violations += 1

                # Velocity limits
                cat = "drums" if ch == 9 else (_gm.get(program, {}).get("cat", "unknown") if program in _gm else "unknown")
                if cat in _vel_rules:
                    vr = _vel_rules[cat]
                    if velocity < vr["lo"]:
                        data[1] = vr["lo"]
                        vel_clamped += 1
                    elif velocity > vr["hi"]:
                        data[1] = vr["hi"]
                        vel_clamped += 1
                        violations += 1

    # Phase 2: Apply clamping to note-off events so pairs stay matched
    # Also remove note-off for blocked drum keys
    drum_channels_by_track = {}  # track_idx -> set of channels that are drum
    for track in parsed["tracks"]:
        ti = track["index"]
        for ev in track["events"]:
            if ev.get("remove") or ev["kind"] != "channel":
                continue
            ch = ev["channel"]
            cmd = ev["command"]
            data = ev["data"]

            # Note-off (command 8) or note-on with vel=0
            if cmd == 8 or (cmd == 9 and data[1] == 0):
                pitch = data[0]
                # Check if this pitch was clamped
                key = (ti, ch, pitch)
                if key in clamp_map:
                    data[0] = clamp_map[key]

                # Check if this is a drum note-off for a blocked key
                if ch == 9 and pitch not in _drum_keys:
                    ev["remove"] = True
                    drum_blocked += 1

    changes["gr_key_clamped_low"] = clamped_low
    changes["gr_key_clamped_high"] = clamped_high
    changes["gr_drum_key_blocked"] = drum_blocked
    changes["gr_velocity_clamped"] = vel_clamped
    changes["gr_drum_validated"] = drum_validated

    # Polyphony check (advisory — doesn't modify data, just warns)
    active_by_ch = defaultdict(list)
    total_active = 0
    peak = 0
    all_note_evs = []
    for track in parsed["tracks"]:
        for ev in track["events"]:
            if ev.get("remove") or ev["kind"] != "channel":
                continue
            if ev["command"] in (8, 9):
                all_note_evs.append((ev["tick"], ev.get("order", 0), ev))
    all_note_evs.sort(key=lambda x: (x[0], x[1]))

    for tick, order, ev in all_note_evs:
        ch = ev["channel"]
        pitch = ev["data"][0]
        if ev["command"] == 9 and ev["data"][1] > 0:
            active_by_ch[ch].append({"pitch": pitch, "tick": tick})
            total_active += 1
            if total_active > peak:
                peak = total_active
        elif ev["command"] == 8 or (ev["command"] == 9 and ev["data"][1] == 0):
            for i, n in enumerate(active_by_ch.get(ch, [])):
                if n["pitch"] == pitch:
                    active_by_ch[ch].pop(i)
                    total_active -= 1
                    break

    poly_exceeded = max(0, peak - _max_poly)
    if poly_exceeded:
        changes["gr_polyphony_exceeded"] = poly_exceeded
        violations += poly_exceeded

    return {
        "enabled": True,
        "violations": violations,
        "keyClampedLow": clamped_low,
        "keyClampedHigh": clamped_high,
        "drumKeyBlocked": drum_blocked,
        "velocityClamped": vel_clamped,
        "drumNotesValidated": drum_validated,
        "peakPolyphony": peak,
        "polyphonyLimit": _max_poly,
        "polyphonyExceeded": poly_exceeded,
    }


def optimize_midi(data: bytes, profiles: list[dict], options=None, source="song.mid", evidence=None):
    options = options or {}
    evidence = evidence or {}
    source_parsed = parse_smf(data)
    if source_parsed["division"] & 0x8000 and options.get("quantizeDivision", 0):
        raise ValueError("Quantize nije podržan za SMPTE timebase")
    ppq = None if source_parsed["division"] & 0x8000 else source_parsed["division"]
    division = int(options.get("quantizeDivision", 16) or 0)
    if division not in (0, 8, 16, 32):
        raise ValueError("Quantize division mora biti 0, 8, 16 ili 32")
    quantize_strength = max(0, min(100, int(options.get("quantizeStrength", 85))))
    velocity_strength = max(0, min(100, int(options.get("velocityStrength", 65))))
    grid_ticks = round(ppq * 4 / division) if ppq and division else None
    controller_cleanup = bool(options.get("removeRedundantControllers", True))
    factory_mixer = bool(options.get("factoryMixer", False))
    repair_range = bool(options.get("repairKeyRange", False))
    fx_auto = bool(options.get("fxAuto", False))
    fx_strength = max(0, min(100, int(options.get("fxStrength", 60))))
    auto_delay = bool(options.get("autoDelay", False))
    auto_third = bool(options.get("autoThird", False))
    phase_enabled = bool(options.get("phaseOptimization", False))
    phase_replace = bool(options.get("allowPhaseReplace", False))
    mixer_strength = max(0, min(100, int(options.get("mixerStrength", 65))))
    energy_target = max(0, min(100, float(options.get("energyTarget", 64))))
    insert_mixer = bool(options.get("insertMissingMixer", True))
    mutable_controllers = ((*((7, 11) if factory_mixer else ()),
                            *((91, 93) if fx_auto else ())))
    performance_gestures = bool(options.get("performanceGestures", False))
    mutable_commands = (14,) if performance_gestures and options.get("pitchBendSemitones") else ()
    plan = midi_integrity.transaction_plan(options)
    before_protected = midi_integrity.protected_snapshot(
        source_parsed, allow_redundant_controller_cleanup=controller_cleanup,
        mutable_controllers=mutable_controllers, mutable_commands=mutable_commands)
    before = audit_tracks(source_parsed, grid_ticks)
    before_technical = technical_parameters(source_parsed)
    before_energy = midi_energy_headroom(source_parsed, energy_target)
    indexes = profile_indexes(profiles)
    phase_plan = {"schema": "dna-phase-plan", "version": "1.0", "readOnly": True,
                  "enabled": False, "reason": "disabled", "decisions": []}
    if phase_enabled:
        analysis = evidence.get("analysis")
        if not analysis:
            raise ValueError("Phase Arranger zahtijeva prethodnu song analizu")
        if analysis.get("source", {}).get("sha256") != hashlib.sha256(data).hexdigest():
            raise ValueError("Phase Arranger analiza ne pripada učitanom MIDI-ju")
        phase_source = copy.deepcopy(source_parsed)
        phase_notes = {}
        for track in phase_source["tracks"]:
            notes = pair_notes(track)
            attach_instruments(track, notes)
            phase_notes[track["index"]] = notes
        phase_plan = phase_optimizer.build_phase_plan(
            phase_source, phase_notes, analysis, indexes[0],
            evidence.get("goldPatterns", []), evidence.get("factoryStrumPatterns", []),
            seed=int(options.get("seed", 0)), allow_replace=phase_replace)
    # Kandidat se uvijek gradi na memorijskoj kopiji. Izvorni bytes i izvorni
    # parsed model ostaju read-only sve dok ne prođe neovisna provjera.
    parsed = copy.deepcopy(source_parsed)
    changes = Counter()
    expected_eot = len(parsed["tracks"])
    if before_technical["endOfTrackEvents"] != expected_eot:
        changes["endOfTrackFixed"] = abs(before_technical["endOfTrackEvents"] - expected_eot) or 1
    notes_by_track = {}
    for track in parsed["tracks"]:
        notes = pair_notes(track, repair=bool(options.get("cleanupNotes", True)), stats=changes)
        notes_by_track[track["index"]] = notes
        attach_instruments(track, notes)
        if options.get("cleanupNotes", True):
            clean_note_pairs(track, notes, changes)

    phase_application = phase_optimizer.apply_phase_plan(
        parsed, notes_by_track, phase_plan, evidence.get("analysis", {}), indexes[0],
        evidence.get("goldPatterns", []), evidence.get("factoryStrumPatterns", []), changes
    ) if phase_enabled else {
            "enabled": False, "decisionsApplied": 0, "budgetsPassed": True}
    if phase_enabled and phase_application.get("decisionsApplied"):
        notes_by_track = {}
        for track in parsed["tracks"]:
            notes = pair_notes(track, repair=True, stats=changes)
            attach_instruments(track, notes)
            notes_by_track[track["index"]] = notes

    role_groups, pre_transform_roles = (special_track_engine.analyze_roles(parsed, notes_by_track, ppq)
                                        if ppq else ([], []))
    solo_keys = {(group["track"]["index"], group["channel"])
                 for group in role_groups if group["role"] == "solo" and group["confidence"] >= .7}
    role_by_key = {(group["track"]["index"], group["channel"]): group["role"] for group in role_groups}

    for track in parsed["tracks"]:
        notes = notes_by_track[track["index"]]
        if factory_mixer:
            optimize_track_mixer(track, notes, indexes, mixer_strength, insert_mixer, changes)
        if repair_range:
            repair_key_ranges(notes, indexes, changes)
        quantize_candidates = [note for note in notes
                               if (track["index"], note["channel"]) not in solo_keys]
        if grid_ticks and quantize_strength:
            changes["soloNotesQuantizeProtected"] += sum(
                not note["on"].get("remove") for note in notes
                if (track["index"], note["channel"]) in solo_keys)
        if options.get("maxPerformance", False):
            grouped_quantize = defaultdict(list)
            for note in quantize_candidates:
                grouped_quantize[role_by_key.get((track["index"], note["channel"]), "accompaniment")].append(note)
            for role, role_notes in grouped_quantize.items():
                role_strength = performance_engine.role_quantize_strength(quantize_strength, role)
                quantize_notes(role_notes, grid_ticks, role_strength, changes)
                changes[f"roleQuantize_{role}"] += sum(1 for note in role_notes if not note["on"].get("remove"))
        else:
            quantize_notes(quantize_candidates, grid_ticks, quantize_strength, changes)
        if options.get("cleanupNotes", True):
            clean_note_pairs(track, notes, changes)
        if options.get("factoryDynamics", True):
            optimize_velocities(notes, indexes, velocity_strength, changes)
        if controller_cleanup:
            clean_controllers(track, changes)
    performance_report = performance_engine.apply_role_performance(
        parsed, role_groups, indexes[0], options, changes)
    gesture_report = (performance_gesture_engine.apply_gestures(parsed, role_groups, ppq, options, changes)
                      if ppq and performance_gestures else {"enabled": False, "plans": [], "applied": 0})
    special_options = {**options, "fxAuto": fx_auto, "fxStrength": fx_strength,
                       "autoDelay": auto_delay, "autoThird": auto_third}
    special_report = special_track_engine.apply_special_tracks(
        parsed, notes_by_track, indexes[0], special_options, changes)
    if options.get("cleanupNotes", True) and special_report.get("budgets", {}).get("generated", 0):
        for track in parsed["tracks"]:
            generated_pairs = pair_notes(track, repair=True, stats=changes)
            clean_note_pairs(track, generated_pairs, changes)
    # ── General Rules Export Gate (9.30) ──
    # Hard key/velocity/drum/polyphony limits for Pa800 export.
    # Runs AFTER all other optimization, BEFORE final encode.
    gr_report = _apply_general_rules(parsed, changes)

    optimized = encode_smf(parsed)
    reparsed = parse_smf(optimized)
    after = audit_tracks(reparsed, grid_ticks)
    after_technical = technical_parameters(reparsed)
    after_energy = midi_energy_headroom(reparsed, energy_target)
    validation = validate_optimized_smf(reparsed, after)
    after_protected = midi_integrity.protected_snapshot(
        reparsed, allow_redundant_controller_cleanup=controller_cleanup,
        mutable_controllers=mutable_controllers, mutable_commands=mutable_commands)
    protected_validation = midi_integrity.verify_protected_events(before_protected, after_protected)
    preserved_keys = ("format", "tracks", "ppq", "tempos", "meters", "markers", "sysexEvents")
    structural_preserved = all(before_technical[key] == after_technical[key] for key in preserved_keys)
    program_semantics_preserved = before_technical["soundSelections"] == after_technical["soundSelections"]
    if not structural_preserved:
        validation["issues"].append("Strukturni meta događaji nisu očuvani")
    if not program_semantics_preserved:
        validation["issues"].append("Program/bank semantika nije očuvana")
    if not protected_validation["passed"]:
        validation["issues"].extend(protected_validation["issues"])
    if not phase_application.get("budgetsPassed", True):
        validation["issues"].append("Phase Arranger prekoračio je transformation budget")
    validation["passed"] = not validation["issues"]
    if not validation["passed"]:
        raise ValueError("MIDI validator blokirao izvoz: " + "; ".join(validation["issues"][:5]))
    database_version = options.get("databaseVersion", "unknown")
    seed = int(options.get("seed", 0))
    intervention_count = sum(value for value in changes.values() if isinstance(value, int))
    report = {
        "schema": "dna-midi-optimization-report", "version": "1.0",
        "source": {"fileName": source, "inputBytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                   "format": parsed["format"], "tracks": len(parsed["tracks"]), "ppq": ppq},
        "output": {"bytes": len(optimized), "sha256": hashlib.sha256(optimized).hexdigest(),
                   "format": reparsed["format"], "tracks": len(reparsed["tracks"]), "ppq": ppq},
        "settings": {"cleanupNotes": bool(options.get("cleanupNotes", True)),
                     "removeRedundantControllers": controller_cleanup,
                     "quantizeDivision": division, "quantizeStrength": quantize_strength,
                     "factoryDynamics": bool(options.get("factoryDynamics", True)),
                     "velocityStrength": velocity_strength,
                     "factoryMixer": factory_mixer, "mixerStrength": mixer_strength,
                     "insertMissingMixer": insert_mixer, "repairKeyRange": repair_range,
                     "energyTarget": energy_target, "fxAuto": fx_auto,
                     "fxStrength": fx_strength, "autoDelay": auto_delay,
                     "autoThird": auto_third,
                     "phaseOptimization": phase_enabled,
                     "allowPhaseReplace": phase_replace,
                     "maxPerformance": bool(options.get("maxPerformance", False)),
                     "performanceGestures": performance_gestures,
                     "pitchBendSemitones": options.get("pitchBendSemitones"),
                     "echoDensity": float(options.get("echoDensity", .42)),
                     "percussionReduction": int(options.get("percussionReduction", 40)),
                     "bassKickInterlockStrength": int(options.get("bassKickInterlockStrength", 45)),
                     "delayDivision": int(options.get("delayDivision", 8) or 8)},
        "before": dict(before), "after": dict(after), "changes": dict(changes),
        "quality": {"before": quality_score(before), "after": quality_score(after)},
        "technicalParameters": {"before": before_technical, "after": after_technical},
        "energyHeadroom": {"before": before_energy, "after": after_energy,
                           "claim": "MIDI proxy only; audio LUFS requires a rendered Pa800 signal"},
        "performanceEngine": performance_report,
        "performanceGestures": gesture_report,
        "specialTracks": special_report,
        "phaseOptimization": {"plan": phase_plan, "application": phase_application},
        "soloTimingProtection": {"enabled": True,
                                 "protectedTrackChannels": [
                                     {"track": track, "channel": channel + 1}
                                     for track, channel in sorted(solo_keys)],
                                 "protectedNotes": changes.get("soloNotesQuantizeProtected", 0),
                                 "roleEvidence": pre_transform_roles},
        "audit": {"inputHash": hashlib.sha256(data).hexdigest(),
                  "outputHash": hashlib.sha256(optimized).hexdigest(), "seed": seed,
                  "databaseVersion": database_version, "interventionCount": intervention_count,
                  "validationResult": "PASS"},
        "transaction": {
            "plan": plan,
            "stages": [
                {"name": "ANALYZE", "passed": True, "inputHash": hashlib.sha256(data).hexdigest()},
                {"name": "PLAN", "passed": True, "transformCount": len(plan["transforms"]),
                 "phaseDecisionCount": len(phase_plan.get("decisions", [])),
                 "phasePlanHash": phase_plan.get("planHash")},
                {"name": "DRY_RUN", "passed": True, "candidateHash": hashlib.sha256(optimized).hexdigest()},
                {"name": "APPLY", "passed": True, "interventionCount": intervention_count},
                {"name": "VERIFY", "passed": protected_validation["passed"] and validation["passed"]},
                {"name": "COMMIT", "passed": True, "outputHash": hashlib.sha256(optimized).hexdigest()},
            ],
            "protectedEvents": protected_validation,
        },
        "validation": validation,
        "determinism": {"seed": seed, "sameInputSameConfigurationSameOutput": True},
        "invariants": {"originalOverwritten": False, "goldAffectsDynamics": False,
                       "goldAffectsProgramChange": False,
                       "goldAffectsMixer": False,
                       "goldAffectsFx": False,
                       "goldControlsRhythmGuitar": False,
                       "soloTimingQuantized": False,
                       "phasePlanBeforeMutation": not phase_enabled or phase_plan.get("readOnly") is True,
                       "phaseSoloTimingChanged": bool(
                           phase_application.get("invariants", {}).get("soloTimingChanged", False)),
                       "factoryProfilesOnly": bool(options.get("factoryDynamics", True)),
                       "structuralMetaPreserved": structural_preserved,
                       "programSemanticsPreserved": program_semantics_preserved,
                       "protectedEventsPreserved": protected_validation["passed"],
                       "invalidMidiExported": False,
                       "generalRulesEnforced": True},
    }
    report["generalRules"] = gr_report
    return optimized, report