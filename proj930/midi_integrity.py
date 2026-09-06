#!/usr/bin/env python3
"""Neovisni autoritet i protected-event verifier za MIDI transakcije.

Modul ne zna ništa o Factory ili GOLD patternima i ne mijenja MIDI. Prima
parsirani SMF prije i poslije kandidata te blokira nedopuštenu promjenu.
"""

from __future__ import annotations

import hashlib
import json


BANK_SELECT_CC = frozenset((0, 32))
PARAMETER_CC = frozenset((6, 38, 96, 97, 98, 99, 100, 101))
ALWAYS_PROTECTED_CC = BANK_SELECT_CC | PARAMETER_CC

AUTHORITY_CONTRACT = {
    "velocity": "factory-only",
    "programChange": "original-midi-or-approved-factory-catalog",
    "bankSelect": "original-midi-or-approved-factory-catalog",
    "rhythmGuitarStrumming": "factory-acc-only",
    "goldPatterns": "non-velocity-note-timing-gate-relationship-evidence",
    "targetHarmony": "input-song",
    "finalMidi": "deterministic-engine-and-independent-verifier",
}


def _is_note(event):
    return event.get("kind") == "channel" and event.get("command") in (8, 9)


def _signature(event):
    base = [int(event["tick"]), event["kind"]]
    if event["kind"] == "meta":
        return [*base, int(event["metaType"]), event["payload"].hex()]
    if event["kind"] == "sysex":
        return [*base, int(event["status"]), event["payload"].hex()]
    return [*base, int(event["command"]), int(event["channel"]), *map(int, event["data"])]


def _canonical_protected_track(track, allow_redundant_controller_cleanup, mutable_controllers, mutable_commands=frozenset()):
    """Vrati događaje koje kandidat mora semantički očuvati.

    Kada je cleanup izričito uključen, obični redundantni CC događaji smiju
    nestati. Bank Select i RPN/NRPN/Data Entry nikada nisu dio tog cleanupa.
    Program Change, SysEx, meta i svi drugi ne-note događaji ostaju točni.
    """
    output, controller_state = [], {}
    marker_ticks = {
        event["tick"] for event in track["events"]
        if event["kind"] == "meta" and event["metaType"] == 6
    }
    reset_ticks = set()
    for event in sorted(
            (item for item in track["events"] if not item.get("remove")),
            key=lambda item: (item["tick"], item["order"])):
        tick = event["tick"]
        if tick in marker_ticks and tick not in reset_ticks:
            controller_state.clear()
            reset_ticks.add(tick)
        if _is_note(event):
            continue
        if event["kind"] == "channel" and event.get("command") in mutable_commands:
            continue
        if event["kind"] == "meta" and event["metaType"] == 47:
            continue
        if event["kind"] == "channel" and event["command"] == 11:
            cc, value = map(int, event["data"])
            if cc in mutable_controllers:
                continue
            if allow_redundant_controller_cleanup and cc not in ALWAYS_PROTECTED_CC:
                key = (int(event["channel"]), cc)
                if controller_state.get(key) == value:
                    continue
                controller_state[key] = value
        output.append(_signature(event))
    return output


def protected_snapshot(parsed, allow_redundant_controller_cleanup=False, mutable_controllers=(), mutable_commands=()):
    mutable_controllers = frozenset(int(value) for value in mutable_controllers)
    mutable_commands = frozenset(int(value) for value in mutable_commands)
    document = {
        "format": int(parsed["format"]),
        "division": int(parsed["division"]),
        "trackCount": len(parsed["tracks"]),
        "tracks": [
            {
                "index": int(track["index"]),
                "events": _canonical_protected_track(
                    track, bool(allow_redundant_controller_cleanup), mutable_controllers, mutable_commands),
            }
            for track in parsed["tracks"]
        ],
    }
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "document": document,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "eventCount": sum(len(track["events"]) for track in document["tracks"]),
    }


def verify_protected_events(before, after):
    issues = []
    for field in ("format", "division", "trackCount"):
        if before["document"][field] != after["document"][field]:
            issues.append(
                f"Protected SMF {field} promijenjen: "
                f"{before['document'][field]} -> {after['document'][field]}"
            )
    before_tracks, after_tracks = before["document"]["tracks"], after["document"]["tracks"]
    for index in range(min(len(before_tracks), len(after_tracks))):
        expected, actual = before_tracks[index]["events"], after_tracks[index]["events"]
        if expected == actual:
            continue
        mismatch = next(
            (position for position, pair in enumerate(zip(expected, actual)) if pair[0] != pair[1]),
            min(len(expected), len(actual)),
        )
        issues.append(
            f"Protected događaji trake {index + 1} nisu očuvani "
            f"(prva razlika {mismatch}, {len(expected)} -> {len(actual)})"
        )
    return {
        "passed": not issues,
        "issues": issues,
        "beforeHash": before["sha256"],
        "afterHash": after["sha256"],
        "beforeEvents": before["eventCount"],
        "afterEvents": after["eventCount"],
    }


def transaction_plan(options):
    quantize = int(options.get("quantizeDivision", 16) or 0)
    transforms = []
    if options.get("cleanupNotes", True):
        transforms.append("repair-note-pairs-and-overlaps")
    if quantize:
        transforms.append(f"quantize-1/{quantize}-non-solo-only")
    if options.get("factoryDynamics", True):
        transforms.append("factory-only-velocity")
    if options.get("factoryMixer", False):
        transforms.append("factory-only-cc7-cc11-mixer")
    if options.get("repairKeyRange", False):
        transforms.append("octave-key-range-repair")
    if options.get("fxAuto", False):
        transforms.append("conservative-role-fx-cc91-cc93")
    if options.get("autoDelay", False):
        transforms.append("bounded-solo-delay-layer")
    if options.get("autoThird", False):
        transforms.append("bounded-chord-validated-third-layer")
    if options.get("phaseOptimization", False):
        transforms.append("section-aware-keep-repair-replace-non-solo")
    if options.get("performanceGestures", False):
        transforms.append("phrase-aware-performance-gesture-plan")
        if options.get("pitchBendSemitones"):
            transforms.append("explicit-range-monophonic-pitch-bend")
    if options.get("removeRedundantControllers", True):
        transforms.append("remove-redundant-unprotected-cc")
    return {
        "schema": "dna-midi-transaction-plan",
        "version": "1.0",
        "transforms": transforms,
        "authority": AUTHORITY_CONTRACT,
        "forbidden": [
            "gold-velocity",
            "gold-bank-select",
            "gold-program-change",
            "unknown-sysex-synthesis",
            "unverified-korg-event-rewrite",
        ],
        "protected": [
            "smf-format-division-track-count",
            "meta-except-normalized-eot",
            "sysex-payload-status-tick-order",
            "bank-select",
            "program-change",
            "rpn-nrpn-data-entry",
            "non-note-channel-events",
            "detected-solo-note-timing",
        ],
        "authorizedMutableControllers": (
            ([7, 11] if options.get("factoryMixer", False) else [])
            + ([91, 93] if options.get("fxAuto", False) else [])
        ),
        "authorizedMutableCommands": ([14] if options.get("performanceGestures", False) and options.get("pitchBendSemitones") else []),
    }