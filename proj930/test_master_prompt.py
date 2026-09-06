#!/usr/bin/env python3
"""Formalni MUST testovi za Master Prompt DNA/Pa800 ugovor."""

from __future__ import annotations

import json
import re
import struct
import unittest
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import dna_builder
import gold_schema
import midi_editor
import midi_integrity
import midi_optimizer
import phase_optimizer
import phase_optimizer
import project_model
import result_cache
import server
import song_analyzer
import style_intelligence
import web_gui


GOLD_FILES = []
STYLE_CONFIG = {
    "name": "MASTER PROMPT TEST", "tempo": 120, "meter": "4/4", "seed": 120111231,
    "elements": server.DEFAULT_ELEMENTS, "tracks": {},
}


def setUpModule():
    global GOLD_FILES
    server.load_data()
    _, GOLD_FILES = dna_builder.read_nested_archive(Path("prism-uploads") / "DNA.zip")


def one_note_midi(velocity=100, zero_duration=False):
    end_delta = 0 if zero_duration else 120
    body = bytes([
        0, 0xFF, 0x51, 3, 0x07, 0xA1, 0x20,
        0, 0xFF, 0x58, 4, 4, 2, 24, 8,
        0, 0xC0, 0,
        0, 0x90, 60, velocity,
        end_delta, 0x80, 60, 0,
        0, 0xFF, 0x2F, 0,
    ])
    return b"MThd" + struct.pack(">IHHH", 6, 0, 1, 480) + b"MTrk" + struct.pack(">I", len(body)) + body


def analysis_midi(velocity):
    events = [
        {"tick": 0, "order": 0, "status": 255, "kind": "meta", "metaType": 81,
         "payload": bytes([0x07, 0xA1, 0x20]), "remove": False},
        {"tick": 0, "order": 1, "status": 255, "kind": "meta", "metaType": 88,
         "payload": bytes([4, 2, 24, 8]), "remove": False},
    ]
    order = 2
    for start, pitch in [(0, 60), (0, 64), (0, 67), (480, 62), (480, 65), (480, 69),
                         (960, 60), (960, 64), (960, 67), (1440, 55), (1440, 59), (1440, 62)]:
        events.extend([
            {"tick": start, "order": order, "status": 0x90, "kind": "channel", "command": 9,
             "channel": 0, "data": [pitch, velocity], "remove": False},
            {"tick": start + 360, "order": order + 1, "status": 0x80, "kind": "channel", "command": 8,
             "channel": 0, "data": [pitch, 0], "remove": False},
        ])
        order += 2
    return midi_optimizer.encode_smf({"format": 0, "division": 480,
                                      "tracks": [{"index": 0, "events": events, "endTick": 1920}]})


def protected_event_midi():
    events = [
        {"tick": 0, "order": 0, "status": 255, "kind": "meta", "metaType": 3,
         "payload": b"Protected Track", "remove": False},
        {"tick": 0, "order": 1, "status": 255, "kind": "meta", "metaType": 127,
         "payload": bytes.fromhex("42600800000000"), "remove": False},
        {"tick": 0, "order": 2, "status": 240, "kind": "sysex",
         "payload": bytes.fromhex("427f600001f7"), "remove": False},
        {"tick": 0, "order": 3, "status": 0xB0, "kind": "channel", "command": 11,
         "channel": 0, "data": [0, 121], "remove": False},
        {"tick": 0, "order": 4, "status": 0xB0, "kind": "channel", "command": 11,
         "channel": 0, "data": [32, 4], "remove": False},
        {"tick": 0, "order": 5, "status": 0xC0, "kind": "channel", "command": 12,
         "channel": 0, "data": [27], "remove": False},
        {"tick": 0, "order": 6, "status": 0xB0, "kind": "channel", "command": 11,
         "channel": 0, "data": [101, 0], "remove": False},
        {"tick": 0, "order": 7, "status": 0xB0, "kind": "channel", "command": 11,
         "channel": 0, "data": [100, 0], "remove": False},
        {"tick": 0, "order": 8, "status": 0xB0, "kind": "channel", "command": 11,
         "channel": 0, "data": [6, 12], "remove": False},
        {"tick": 0, "order": 9, "status": 0xB0, "kind": "channel", "command": 11,
         "channel": 0, "data": [7, 100], "remove": False},
        {"tick": 120, "order": 10, "status": 0xB0, "kind": "channel", "command": 11,
         "channel": 0, "data": [7, 100], "remove": False},
        {"tick": 121, "order": 11, "status": 0x90, "kind": "channel", "command": 9,
         "channel": 0, "data": [60, 90], "remove": False},
        {"tick": 361, "order": 12, "status": 0x80, "kind": "channel", "command": 8,
         "channel": 0, "data": [60, 0], "remove": False},
    ]
    return midi_optimizer.encode_smf({"format": 0, "division": 480,
                                      "tracks": [{"index": 0, "events": events, "endTick": 480}]})


def fixed_controller_profile(value):
    labels = ("floor", "soft", "lowMid", "optimal", "highMid", "strong", "ceiling")
    positions = (0, 17, 33, 50, 67, 83, 100)
    return {"points": [{"intensity": intensity, "label": label, "value": value}
                       for intensity, label in zip(positions, labels)]}


def special_tracks_midi():
    chord_events = [
        {"tick": 0, "order": 0, "status": 255, "kind": "meta", "metaType": 3,
         "payload": b"Chords", "remove": False},
        {"tick": 0, "order": 1, "status": 255, "kind": "meta", "metaType": 88,
         "payload": bytes([4, 2, 24, 8]), "remove": False},
        {"tick": 0, "order": 2, "status": 0xC1, "kind": "channel", "command": 12,
         "channel": 1, "data": [0], "remove": False},
    ]
    order = 3
    for start in range(0, 3360, 480):
        for pitch in (48, 52, 55):
            chord_events.extend([
                {"tick": start, "order": order, "status": 0x91, "kind": "channel", "command": 9,
                 "channel": 1, "data": [pitch, 80], "remove": False},
                {"tick": start + 360, "order": order + 1, "status": 0x81, "kind": "channel", "command": 8,
                 "channel": 1, "data": [pitch, 0], "remove": False},
            ])
            order += 2
    solo_events = [
        {"tick": 0, "order": 0, "status": 255, "kind": "meta", "metaType": 3,
         "payload": b"Solo Lead", "remove": False},
        {"tick": 0, "order": 1, "status": 0xB0, "kind": "channel", "command": 11,
         "channel": 0, "data": [0, 0], "remove": False},
        {"tick": 0, "order": 2, "status": 0xB0, "kind": "channel", "command": 11,
         "channel": 0, "data": [32, 0], "remove": False},
        {"tick": 0, "order": 3, "status": 0xC0, "kind": "channel", "command": 12,
         "channel": 0, "data": [80], "remove": False},
    ]
    order = 4
    for start in range(37, 2917, 360):
        solo_events.extend([
            {"tick": start, "order": order, "status": 0x90, "kind": "channel", "command": 9,
             "channel": 0, "data": [60, 92], "remove": False},
            {"tick": start + 120, "order": order + 1, "status": 0x80, "kind": "channel", "command": 8,
             "channel": 0, "data": [60, 0], "remove": False},
        ])
        order += 2
    return midi_optimizer.encode_smf({"format": 1, "division": 480, "tracks": [
        {"index": 0, "events": chord_events, "endTick": 3360},
        {"index": 1, "events": solo_events, "endTick": 3000},
    ]})


def phase_fixture_midi():
    drums = [
        {"tick": 0, "order": 0, "status": 255, "kind": "meta", "metaType": 81,
         "payload": bytes([0x07, 0xA1, 0x20]), "remove": False},
        {"tick": 0, "order": 1, "status": 255, "kind": "meta", "metaType": 88,
         "payload": bytes([4, 2, 24, 8]), "remove": False},
        {"tick": 0, "order": 2, "status": 255, "kind": "meta", "metaType": 3,
         "payload": b"Drums", "remove": False},
        {"tick": 0, "order": 3, "status": 255, "kind": "meta", "metaType": 127,
         "payload": bytes.fromhex("42600801000000"), "remove": False},
        {"tick": 0, "order": 4, "status": 0xC9, "kind": "channel", "command": 12,
         "channel": 9, "data": [0], "remove": False},
    ]
    order = 5
    for start, pitch in ((0, 36), (1920, 38)):
        drums.extend([
            {"tick": start, "order": order, "status": 0x99, "kind": "channel", "command": 9,
             "channel": 9, "data": [pitch, 80], "remove": False},
            {"tick": start + 120, "order": order + 1, "status": 0x89, "kind": "channel", "command": 8,
             "channel": 9, "data": [pitch, 0], "remove": False},
        ])
        order += 2
    solo = [
        {"tick": 0, "order": 0, "status": 255, "kind": "meta", "metaType": 3,
         "payload": b"Solo Lead", "remove": False},
        {"tick": 0, "order": 1, "status": 0xC0, "kind": "channel", "command": 12,
         "channel": 0, "data": [80], "remove": False},
    ]
    order = 2
    for start, pitch in ((37, 60), (517, 64), (997, 67), (1477, 72),
                         (1957, 60), (2437, 64), (2917, 67), (3397, 72)):
        solo.extend([
            {"tick": start, "order": order, "status": 0x90, "kind": "channel", "command": 9,
             "channel": 0, "data": [pitch, 92], "remove": False},
            {"tick": start + 300, "order": order + 1, "status": 0x80, "kind": "channel", "command": 8,
             "channel": 0, "data": [pitch, 0], "remove": False},
        ])
        order += 2
    return midi_optimizer.encode_smf({"format": 1, "division": 480, "tracks": [
        {"index": 0, "events": drums, "endTick": 3840},
        {"index": 1, "events": solo, "endTick": 3840},
    ]})


def phase_arranger_midi():
    drum_events = [
        {"tick": 0, "order": 0, "status": 255, "kind": "meta", "metaType": 3,
         "payload": b"Drums", "remove": False},
        {"tick": 0, "order": 1, "status": 255, "kind": "meta", "metaType": 81,
         "payload": bytes([0x07, 0xA1, 0x20]), "remove": False},
        {"tick": 0, "order": 2, "status": 255, "kind": "meta", "metaType": 88,
         "payload": bytes([4, 2, 24, 8]), "remove": False},
        {"tick": 0, "order": 3, "status": 0xC9, "kind": "channel", "command": 12,
         "channel": 9, "data": [0], "remove": False},
    ]
    order = 4
    for start in (0, 480, 960, 1440):
        drum_events.extend([
            {"tick": start, "order": order, "status": 0x99, "kind": "channel", "command": 9,
             "channel": 9, "data": [36, 90], "remove": False},
            {"tick": start + 120, "order": order + 1, "status": 0x89, "kind": "channel", "command": 8,
             "channel": 9, "data": [36, 0], "remove": False},
        ])
        order += 2
    solo_events = [
        {"tick": 0, "order": 0, "status": 255, "kind": "meta", "metaType": 3,
         "payload": b"Solo Lead", "remove": False},
        {"tick": 0, "order": 1, "status": 0xC0, "kind": "channel", "command": 12,
         "channel": 0, "data": [80], "remove": False},
    ]
    order = 2
    for start, pitch in ((37, 60), (397, 62), (757, 64), (1117, 67), (1477, 69)):
        solo_events.extend([
            {"tick": start, "order": order, "status": 0x90, "kind": "channel", "command": 9,
             "channel": 0, "data": [pitch, 92], "remove": False},
            {"tick": start + 180, "order": order + 1, "status": 0x80, "kind": "channel", "command": 8,
             "channel": 0, "data": [pitch, 0], "remove": False},
        ])
        order += 2
    return midi_optimizer.encode_smf({"format": 1, "division": 480, "tracks": [
        {"index": 0, "events": drum_events, "endTick": 1920},
        {"index": 1, "events": solo_events, "endTick": 1920},
    ]})


def phase_fixture_evidence(source):
    analysis = song_analyzer.analyze_midi(source, "phase-fixture.mid")
    profile = {
        "id": "111.222.333", "instrumentKey": "drum:0:0:0:36", "kind": "drum",
        "program": 0, "drumNote": 36, "samples": 128, "register": {"low": 36, "high": 36},
        "velocity": {"min": 30, "optimal": 78, "max": 108},
    }
    pattern = {
        "id": "444.555.666", "role": "drums", "meter": "4/4", "lengthBars": 1,
        "timingResolution": 96, "tempoRange": [100, 140], "sourceSection": "main",
        "density": .5, "events": [[0, 24, 36]], "register": {"low": 36, "high": 36},
        "confidence": .98, "qualityScore": 98, "transitionContext": {"startsWithRest": False},
    }
    return [profile], {"analysis": analysis, "goldPatterns": [pattern], "factoryStrumPatterns": []}


def replace_once(data, old, new):
    index = data.find(old)
    if index < 0:
        raise AssertionError(f"Nije pronađen testni uzorak {old!r}")
    return data[:index] + new + data[index + len(old):]


class UnitTests(unittest.TestCase):
    def test_authority_contract_forbids_gold_velocity_and_program(self):
        plan = midi_integrity.transaction_plan({"factoryDynamics": True})
        self.assertEqual(plan["authority"]["velocity"], "factory-only")
        self.assertIn("gold-velocity", plan["forbidden"])
        self.assertIn("gold-program-change", plan["forbidden"])

    def test_piecewise_velocity_curve(self):
        profile = {"velocity": {"min": 20, "optimal": 80, "max": 120}}
        self.assertEqual(server.velocity_at(profile, 0), 20)
        self.assertEqual(server.velocity_at(profile, 50), 80)
        self.assertEqual(server.velocity_at(profile, 100), 120)
        seven = {
            "velocity": {"min": 20, "optimal": 80, "max": 120},
            "velocityCurve": {"points": [
                {"intensity": 0, "label": "floor", "velocity": 20},
                {"intensity": 17, "label": "soft", "velocity": 35},
                {"intensity": 33, "label": "lowMid", "velocity": 58},
                {"intensity": 50, "label": "optimal", "velocity": 80},
                {"intensity": 67, "label": "highMid", "velocity": 94},
                {"intensity": 83, "label": "strong", "velocity": 108},
                {"intensity": 100, "label": "ceiling", "velocity": 120},
            ]},
        }
        self.assertEqual([server.velocity_at(seven, value) for value in (0, 17, 33, 50, 67, 83, 100)],
                         [20, 35, 58, 80, 94, 108, 120])

    def test_invalid_duration_is_repaired_and_audited(self):
        output, report = midi_optimizer.optimize_midi(
            one_note_midi(zero_duration=True), [],
            {"cleanupNotes": True, "removeRedundantControllers": False, "quantizeDivision": 0,
             "factoryDynamics": False, "databaseVersion": "unit", "seed": 0}, "zero.mid")
        self.assertEqual(report["before"]["invalidDurations"], 1)
        self.assertEqual(report["changes"]["invalidDurationsFixed"], 1)
        self.assertTrue(report["validation"]["passed"])
        self.assertGreater(len(output), 0)

    def test_invalid_export_is_blocked_when_cleanup_disabled(self):
        with self.assertRaisesRegex(ValueError, "validator blokirao izvoz"):
            midi_optimizer.optimize_midi(
                one_note_midi(zero_duration=True), [],
                {"cleanupNotes": False, "removeRedundantControllers": False, "quantizeDivision": 0,
                 "factoryDynamics": False}, "invalid.mid")

    def test_song_analysis_is_velocity_independent(self):
        quiet = song_analyzer.analyze_midi(analysis_midi(20), "quiet.mid")
        loud = song_analyzer.analyze_midi(analysis_midi(120), "loud.mid")
        for key in ("tempo", "meter", "bars", "key", "barAnalysis", "sections", "suggestedPa800Elements"):
            self.assertEqual(quiet[key], loud[key])
        self.assertFalse(quiet["rules"]["analysisVelocityUsed"])

    def test_advanced_chord_timeline_and_phase_boundaries_are_evidence_based(self):
        analysis = song_analyzer.analyze_midi(phase_fixture_midi(), "phase-fixture.mid")
        self.assertEqual(analysis["version"], "1.2")
        self.assertEqual(analysis["chordTimeline"]["resolution"], "half-bar")
        self.assertEqual(len(analysis["chordTimeline"]["cells"]), analysis["bars"] * 2)
        self.assertTrue(all(cell["velocityUsed"] is False
                            for cell in analysis["chordTimeline"]["cells"]))
        self.assertTrue(all(boundary["velocityUsed"] is False
                            for boundary in analysis["phaseBoundaries"]))
        self.assertEqual(len(analysis["korgChordEvidence"]), 1)
        self.assertFalse(analysis["korgChordEvidence"][0]["authoritative"])

    def test_half_bar_chords_phase_evidence_and_korg_candidate(self):
        analysis = song_analyzer.analyze_midi(analysis_midi(80), "chords.mid")
        self.assertEqual(analysis["chordTimeline"]["resolution"], "half-bar")
        self.assertEqual(len(analysis["chordTimeline"]["cells"]), analysis["bars"] * 2)
        self.assertFalse(analysis["chordTimeline"]["velocityUsed"])
        self.assertTrue(analysis["phaseBoundaries"])
        korg = song_analyzer.korg_chord_evidence(protected_event_midi())
        self.assertEqual(len(korg), 1)
        self.assertFalse(korg[0]["authoritative"])
        self.assertEqual(korg[0]["status"], "EVIDENCE_CANDIDATE_DEVICE_CONFIRMATION")

    def test_preflight_is_read_only_and_reports_structure(self):
        source = one_note_midi()
        report = midi_optimizer.preflight_midi(source, "preflight.mid")
        self.assertTrue(report["invariants"]["readOnly"])
        self.assertFalse(report["invariants"]["goldAffectsDynamics"])
        self.assertEqual(report["technicalParameters"]["format"], 0)
        self.assertEqual(report["technicalParameters"]["ppq"], 480)
        self.assertFalse(report["energyHeadroom"]["audioLufsMeasured"])
        self.assertGreater(report["energyHeadroom"]["energyIndex"], 0)

    def test_editor_transpose_is_audited_and_preserves_structure(self):
        source = one_note_midi()
        output, report = midi_editor.apply_edits(
            source, server.FACTORY["profiles"],
            {"operation": "transpose", "selection": {"all": True}, "parameters": {"semitones": 2}},
            "edit.mid", server.FACTORY["databaseVersion"])
        preview = midi_optimizer.midi_preview(output, "edit.mid")
        self.assertEqual(preview["notes"][0]["pitch"], 62)
        self.assertTrue(report["validation"]["passed"])
        self.assertTrue(report["invariants"]["structuralDataPreserved"])

    def test_project_migration_and_safety_validation(self):
        project, validation = project_model.validate_project({"optimizer": {}, "style": {}, "editor": {}})
        self.assertTrue(validation["passed"])
        self.assertEqual(project["schema"], project_model.SCHEMA)
        self.assertEqual(len(project["projectHash"]), 64)
        project["invariants"]["goldAffectsDynamics"] = True
        _, invalid = project_model.validate_project(project)
        self.assertFalse(invalid["passed"])

    def test_result_cache_limits_and_immutable_payload(self):
        cache = result_cache.ResultCache(limit=1, max_bytes=1024, ttl_seconds=60)
        first = cache.put(b"one", {"value": 1}, "one.mid")
        second = cache.put(b"two", {"value": 2}, "two.mid")
        self.assertIsNone(cache.get(first))
        item = cache.get(second)
        self.assertEqual(item["midi"], b"two")
        self.assertEqual(cache.summary()["items"], 1)


class IntegrationTests(unittest.TestCase):
    def test_solo_timing_is_never_quantized_by_optimizer_or_editor(self):
        source = special_tracks_midi()
        source_parsed = midi_optimizer.parse_smf(source)
        source_solo = [note["on"]["tick"] for note in midi_optimizer.pair_notes(source_parsed["tracks"][1])]
        output, report = midi_optimizer.optimize_midi(
            source, [], {"cleanupNotes": True, "removeRedundantControllers": False,
                         "quantizeDivision": 16, "quantizeStrength": 100,
                         "factoryDynamics": False, "factoryMixer": False,
                         "repairKeyRange": False, "fxAuto": False,
                         "autoDelay": False, "autoThird": False}, "solo-timing.mid")
        optimized_solo = [note["on"]["tick"] for note in
                          midi_optimizer.pair_notes(midi_optimizer.parse_smf(output)["tracks"][1])]
        self.assertEqual(optimized_solo, source_solo)
        self.assertEqual(report["changes"]["soloNotesQuantizeProtected"], len(source_solo))
        self.assertFalse(report["invariants"]["soloTimingQuantized"])

        edited, edit_report = midi_editor.apply_edits(
            source, [], {"operation": "quantize", "selection": {"all": True},
                         "parameters": {"division": 16, "strength": 100}}, "solo-editor.mid", "unit")
        edited_solo = [note["on"]["tick"] for note in
                       midi_optimizer.pair_notes(midi_optimizer.parse_smf(edited)["tracks"][1])]
        self.assertEqual(edited_solo, source_solo)
        self.assertEqual(edit_report["changes"]["soloNotesQuantizeProtected"], len(source_solo))
        self.assertFalse(edit_report["invariants"]["soloTimingQuantized"])

    def test_phase_plan_and_apply_protect_solo_and_program_change(self):
        source = phase_fixture_midi()
        analysis = song_analyzer.analyze_midi(source, "phase-apply.mid")
        analysis["sections"] = [{"name": "Faza 1", "type": "verse", "startBar": 1,
                                 "endBar": 2, "bars": 2, "intensity": 68,
                                 "confidence": .8, "labelStatus": "test-fixture"}]
        profiles = [
            {"id": f"100.200.{pitch:03d}", "instrumentKey": f"drum:0:0:0:{pitch}",
             "kind": "drum", "program": 0, "samples": 100,
             "register": {"low": pitch, "high": pitch},
             "velocity": {"min": 35, "optimal": 82, "max": 116}}
            for pitch in (36, 38, 42)
        ] + [{"id": "120.111.231", "instrumentKey": "melodic:0:0:80",
              "kind": "melodic", "program": 80, "samples": 100,
              "register": {"low": 48, "high": 84},
              "velocity": {"min": 30, "optimal": 84, "max": 118}}]
        pattern = {"id": "101.202.303", "role": "drums", "meter": "4/4",
                   "tempoRange": [80, 160], "sourceSection": "main", "density": 8,
                   "confidence": .9, "qualityScore": 92, "lengthBars": 1,
                   "timingResolution": 96,
                   "events": [[0, 12, 36], [24, 12, 42], [48, 12, 38], [72, 12, 42]]}
        before = midi_optimizer.parse_smf(source)
        solo_before = [note["on"]["tick"] for note in midi_optimizer.pair_notes(before["tracks"][1])]
        output, report = midi_optimizer.optimize_midi(
            source, profiles,
            {"cleanupNotes": True, "removeRedundantControllers": False,
             "quantizeDivision": 16, "quantizeStrength": 100,
             "factoryDynamics": False, "phaseOptimization": True,
             "allowPhaseReplace": True, "seed": 120111231},
            "phase-apply.mid", {"analysis": analysis, "goldPatterns": [pattern],
                                "factoryStrumPatterns": []})
        after = midi_optimizer.parse_smf(output)
        solo_after = [note["on"]["tick"] for note in midi_optimizer.pair_notes(after["tracks"][1])]
        self.assertEqual(solo_after, solo_before)
        self.assertGreater(report["phaseOptimization"]["application"]["decisionsApplied"], 0)
        self.assertTrue(report["phaseOptimization"]["application"]["budgetsPassed"])
        self.assertTrue(report["invariants"]["phasePlanBeforeMutation"])
        self.assertFalse(report["invariants"]["phaseSoloTimingChanged"])
        self.assertTrue(report["invariants"]["programSemanticsPreserved"])
        self.assertTrue(report["transaction"]["protectedEvents"]["passed"])

    def test_phase_replace_is_deterministic_factory_dynamic_and_solo_safe(self):
        source = phase_arranger_midi()
        profiles, evidence = phase_fixture_evidence(source)
        parsed = midi_optimizer.parse_smf(source)
        source_programs = midi_optimizer.technical_parameters(parsed)["soundSelections"]
        source_solo = [note["on"]["tick"] for note in midi_optimizer.pair_notes(parsed["tracks"][1])]
        plan = phase_optimizer.plan_midi(
            source, profiles, evidence["goldPatterns"], evidence["factoryStrumPatterns"],
            evidence["analysis"], {"seed": 731, "allowPhaseReplace": True})
        self.assertTrue(plan["dryRun"])
        self.assertFalse(plan["sourceMutated"])
        self.assertIn("REPLACE", {item["action"] for item in plan["decisions"]})
        solo = [item for item in plan["decisions"] if item["role"] == "solo"]
        self.assertTrue(solo and all(item["action"] == "KEEP" for item in solo))
        settings = {
            "cleanupNotes": True, "removeRedundantControllers": False,
            "quantizeDivision": 16, "quantizeStrength": 100,
            "factoryDynamics": False, "factoryMixer": False, "repairKeyRange": False,
            "fxAuto": False, "autoDelay": False, "autoThird": False,
            "phaseOptimization": True, "allowPhaseReplace": True,
            "databaseVersion": "phase-fixture", "seed": 731,
        }
        first, report = midi_optimizer.optimize_midi(
            source, profiles, settings, "phase-fixture.mid", evidence)
        second, _ = midi_optimizer.optimize_midi(
            source, profiles, settings, "phase-fixture.mid", evidence)
        result = midi_optimizer.parse_smf(first)
        result_solo = [note["on"]["tick"] for note in midi_optimizer.pair_notes(result["tracks"][1])]
        generated_velocities = [event["data"][1] for event in result["tracks"][0]["events"]
                                if midi_optimizer.is_note_on(event)]
        self.assertEqual(first, second)
        self.assertEqual(result_solo, source_solo)
        self.assertEqual(midi_optimizer.technical_parameters(result)["soundSelections"], source_programs)
        self.assertGreater(report["changes"].get("phaseNotesRemoved", 0), 0)
        self.assertGreater(report["changes"].get("phaseNotesInserted", 0), 0)
        self.assertTrue(all(30 <= value <= 108 for value in generated_velocities))
        self.assertTrue(report["phaseOptimization"]["application"]["budgetsPassed"])
        self.assertTrue(report["invariants"]["phasePlanBeforeMutation"])
        self.assertFalse(report["invariants"]["phaseSoloTimingChanged"])

    def test_fx_solo_delay_and_third_are_bounded_and_factory_dynamic(self):
        source = special_tracks_midi()
        profile = {"id": "120.111.231", "instrumentKey": "melodic:0:0:80",
                   "kind": "melodic", "program": 80, "samples": 100,
                   "register": {"low": 48, "high": 84},
                   "velocity": {"min": 30, "optimal": 82, "max": 116}}
        output, report = midi_optimizer.optimize_midi(
            source, [profile], {"cleanupNotes": True, "removeRedundantControllers": True,
                                "quantizeDivision": 0, "factoryDynamics": False,
                                "factoryMixer": False, "repairKeyRange": False,
                                "fxAuto": True, "fxStrength": 100,
                                "autoDelay": True, "autoThird": True, "delayDivision": 8},
            "special.mid")
        before_notes = sum(len(midi_optimizer.pair_notes(track))
                           for track in midi_optimizer.parse_smf(source)["tracks"])
        after_parsed = midi_optimizer.parse_smf(output)
        after_notes = sum(len(midi_optimizer.pair_notes(track)) for track in after_parsed["tracks"])
        self.assertEqual(after_notes - before_notes, 4)
        self.assertEqual(report["changes"]["delayNotesGenerated"], 2)
        self.assertEqual(report["changes"]["thirdNotesGenerated"], 2)
        self.assertGreaterEqual(report["changes"]["fxControllersInserted"], 4)
        self.assertTrue(report["specialTracks"]["budgets"]["limitRespected"])
        self.assertTrue(report["transaction"]["protectedEvents"]["passed"])
        self.assertTrue(report["invariants"]["programSemanticsPreserved"])
        self.assertFalse(report["specialTracks"]["authority"]["goldVelocity"])
    def test_factory_mixer_and_key_range_apply_without_program_mutation(self):
        parsed = midi_optimizer.parse_smf(protected_event_midi())
        for event in parsed["tracks"][0]["events"]:
            if event["kind"] == "channel" and event["command"] in (8, 9) and event["data"][0] == 60:
                event["data"][0] = 84
        source = midi_optimizer.encode_smf(parsed)
        profile = {
            "id": "120.111.231", "instrumentKey": "melodic:121:4:27", "kind": "melodic",
            "program": 27, "samples": 100, "register": {"low": 48, "high": 72},
            "velocity": {"min": 20, "optimal": 80, "max": 120},
            "mixerProfile": {"volume": fixed_controller_profile(90),
                             "expression": fixed_controller_profile(110)},
        }
        output, report = midi_optimizer.optimize_midi(
            source, [profile], {"cleanupNotes": True, "removeRedundantControllers": True,
                                "quantizeDivision": 0, "factoryDynamics": False,
                                "factoryMixer": True, "mixerStrength": 100,
                                "insertMissingMixer": True, "repairKeyRange": True},
            "mixer-range.mid")
        result = midi_optimizer.parse_smf(output)
        notes = midi_optimizer.pair_notes(result["tracks"][0])
        controllers = [(event["data"][0], event["data"][1]) for event in result["tracks"][0]["events"]
                       if event["kind"] == "channel" and event["command"] == 11]
        self.assertEqual(notes[0]["pitch"], 72)
        self.assertIn((7, 90), controllers)
        self.assertIn((11, 110), controllers)
        self.assertEqual(report["changes"]["keyRangeNotesFolded"], 1)
        self.assertTrue(report["transaction"]["protectedEvents"]["passed"])
        self.assertTrue(report["invariants"]["programSemanticsPreserved"])

    def test_optimizer_preserves_protected_events_transactionally(self):
        source = protected_event_midi()
        output, report = midi_optimizer.optimize_midi(
            source, [], {"cleanupNotes": True, "removeRedundantControllers": True,
                         "quantizeDivision": 16, "quantizeStrength": 100,
                         "factoryDynamics": False, "databaseVersion": "integrity"},
            "protected.mid")
        self.assertTrue(report["transaction"]["protectedEvents"]["passed"])
        self.assertTrue(report["invariants"]["programSemanticsPreserved"])
        self.assertTrue(report["invariants"]["goldAffectsProgramChange"] is False)
        self.assertEqual(report["changes"]["redundantControllersRemoved"], 1)
        self.assertNotEqual(source, output)

    def test_style_survives_optimizer_and_pa800_validator(self):
        midi, manifest = server.build_pa800_style(STYLE_CONFIG)
        optimized, report = midi_optimizer.optimize_midi(
            midi, server.FACTORY["profiles"],
            {"cleanupNotes": True, "removeRedundantControllers": True, "quantizeDivision": 0,
             "factoryDynamics": False, "databaseVersion": server.FACTORY["databaseVersion"]}, "style.mid")
        channels = [channel - 1 for channel in manifest["midi"]["usedChannels"]]
        validation = server.validate_pa800_smf(optimized, [e["marker"] for e in manifest["elements"]], channels)
        self.assertTrue(validation["passed"], validation["issues"])
        self.assertEqual(report["audit"]["validationResult"], "PASS")

    def test_pattern_ranking_has_all_required_criteria(self):
        _, manifest = server.build_pa800_style(STYLE_CONFIG)
        required = {"role_match", "meter_match", "tempo_match", "section_match",
                    "density_accent_match", "harmonic_compatibility",
                    "register_articulation_match", "evidence_quality",
                    "transition_compatibility", "transformation_budget_safety"}
        selections = [selection for element in manifest["elements"]
                      for selection in element["patternSelection"].values()]
        self.assertTrue(selections)
        self.assertTrue(all(set(item["criteria"]) == required for item in selections))

    def test_style_uses_full_gold_performance_and_factory_strumming(self):
        _, manifest = server.build_pa800_style(STYLE_CONFIG)
        authorities = [decision["patternAuthority"] for element in manifest["elements"]
                       for decision in element["musicalDecisions"].values()]
        self.assertIn("gold-performance", authorities)
        bass_selections = [element["patternSelection"]["bass"] for element in manifest["elements"]
                           if "bass" in element["patternSelection"]]
        self.assertTrue(bass_selections)
        self.assertTrue(all(item["relationshipConstrained"] for item in bass_selections))
        self.assertEqual(manifest["rules"]["rhythmGuitarStrummingSource"], "factory-acc-only")
        self.assertFalse(manifest["rules"]["goldAffectsProgramChange"])

        guitar = next(item for item in server.OPTIONS["tracks"]["acc1"] if 24 <= item["program"] <= 28)
        tracks = {name: {"enabled": False} for name in server.TRACKS}
        tracks["acc1"] = {"enabled": True, "profileId": guitar["id"]}
        _, guitar_manifest = server.build_pa800_style({**STYLE_CONFIG, "tracks": tracks})
        guitar_authorities = [element["musicalDecisions"]["acc1"]["patternAuthority"]
                              for element in guitar_manifest["elements"]]
        self.assertTrue(all(authority == "factory-strumming" for authority in guitar_authorities))

    def test_pattern_lock_next_and_exclude_workflow(self):
        _, base = server.build_pa800_style(STYLE_CONFIG)
        first = base["elements"][0]
        track, pattern_id = next(iter(first["patterns"].items()))
        locked_config = {**STYLE_CONFIG, "patternLocks": {first["marker"]: {track: pattern_id}}}
        _, locked = server.build_pa800_style(locked_config)
        selection = locked["elements"][0]["patternSelection"][track]
        self.assertEqual(selection["selectionMode"], "locked-by-user")
        next_config = {**STYLE_CONFIG, "excludedPatternIds": [pattern_id],
                       "patternOffsets": {first["marker"]: {track: 1}}}
        _, changed = server.build_pa800_style(next_config)
        self.assertNotEqual(changed["elements"][0]["patterns"][track], pattern_id)

    def test_style_intelligence_and_device_confirmation_are_manifested(self):
        _, manifest = server.build_pa800_style(STYLE_CONFIG)
        self.assertGreaterEqual(manifest["quality"]["registerCollisionsResolved"], 0)
        self.assertTrue(manifest["quality"]["polyphonyPassed"])
        self.assertEqual(manifest["quality"]["polyphonyMetric"], "simultaneous-midi-notes")
        self.assertFalse(manifest["quality"]["physicalSoundVoiceCostVerified"])
        self.assertEqual(server.OPTIONS["polyphonyLimits"], server.POLYPHONY_LIMITS)
        self.assertTrue(all(item["polyphonyLimit"] == server.POLYPHONY_LIMITS[name]
                            for name, item in manifest["tracks"].items()))
        for channel, peak in manifest["quality"]["peakPolyphonyByChannel"].items():
            self.assertLessEqual(peak, manifest["compliance"]["polyphonyLimits"][channel])
        self.assertTrue(all(item["pa800Recommendation"]["status"] == "DEVICE_CONFIRMATION_REQUIRED"
                            for item in manifest["tracks"].values()))
        self.assertTrue(all("transition" in element and "musicalDecisions" in element
                            for element in manifest["elements"]))

    def test_song_analysis_exposes_professional_metrics(self):
        analysis = song_analyzer.analyze_midi(analysis_midi(80), "analysis.mid")
        self.assertIn("tempoMap", analysis)
        self.assertIn("meterMap", analysis)
        self.assertIn("registerDistribution", analysis["musicMetrics"])
        self.assertIn("polyphony", analysis["barAnalysis"][0])
        self.assertIn("recommendedPa800Element", analysis["sections"][0])


class E2ETests(unittest.TestCase):
    def test_same_seed_same_style_bytes(self):
        first, manifest = server.build_pa800_style(STYLE_CONFIG)
        second, _ = server.build_pa800_style(STYLE_CONFIG)
        self.assertEqual(first, second)
        self.assertTrue(manifest["determinism"]["sameSeedSameOutput"])
        self.assertEqual(manifest["audit"]["validationResult"], "PASS")

    def test_real_gold_phase_plan_is_repeatable_and_read_only(self):
        source, midi = next((item for item in GOLD_FILES if "AKO TE DRUGI PR" in item[0]), GOLD_FILES[0])
        first_analysis, first = server.build_phase_plan(midi, source, seed=8675309, allow_replace=False)
        _, second = server.build_phase_plan(midi, source, seed=8675309, allow_replace=False)
        self.assertEqual(first["planHash"], second["planHash"])
        self.assertEqual(first["decisions"], second["decisions"])
        self.assertTrue(first["readOnly"])
        self.assertFalse(first["sourceMutated"])
        self.assertTrue(first["decisions"])
        self.assertFalse(first["invariants"]["soloTimingMutable"])
        self.assertFalse(first["invariants"]["goldAffectsVelocity"])
        self.assertEqual(first_analysis["rules"]["chordResolution"], "half-bar")

    def test_real_song_optimizer_is_deterministic(self):
        source, midi = next((item for item in GOLD_FILES if "AKO TE DRUGI PR" in item[0]), GOLD_FILES[0])
        settings = {"cleanupNotes": True, "removeRedundantControllers": True, "quantizeDivision": 16,
                    "quantizeStrength": 85, "factoryDynamics": True, "velocityStrength": 65,
                    "factoryMixer": True, "mixerStrength": 65, "insertMissingMixer": True,
                    "repairKeyRange": True,
                    "fxAuto": True, "fxStrength": 60, "autoDelay": True,
                    "autoThird": True, "delayDivision": 8,
                    "databaseVersion": server.FACTORY["databaseVersion"], "seed": 0}
        first, report = midi_optimizer.optimize_midi(midi, server.FACTORY["profiles"], settings, source)
        second, _ = midi_optimizer.optimize_midi(midi, server.FACTORY["profiles"], settings, source)
        self.assertEqual(first, second)
        self.assertGreater(report["quality"]["after"], report["quality"]["before"])
        self.assertFalse(report["invariants"]["goldAffectsDynamics"])
        self.assertFalse(report["invariants"]["goldAffectsMixer"])
        self.assertTrue(report["transaction"]["protectedEvents"]["passed"])
        self.assertIn("energyHeadroom", report)
        self.assertFalse(report["energyHeadroom"]["after"]["audioLufsMeasured"])
        self.assertTrue(report["specialTracks"]["budgets"]["limitRespected"])
        self.assertGreater(report["changes"].get("delayNotesGenerated", 0)
                           + report["changes"].get("thirdNotesGenerated", 0), 0)

    def test_real_gold_phase_plan_is_deterministic_and_read_only(self):
        source, midi = next((item for item in GOLD_FILES if "AKO TE DRUGI PR" in item[0]), GOLD_FILES[0])
        analysis = song_analyzer.analyze_midi(midi, source)
        first = phase_optimizer.plan_midi(
            midi, server.FACTORY["profiles"], server.GOLD_PERFORMANCE,
            server.FACTORY_STRUM, analysis, {"seed": 120111231, "allowPhaseReplace": True})
        second = phase_optimizer.plan_midi(
            midi, server.FACTORY["profiles"], server.GOLD_PERFORMANCE,
            server.FACTORY_STRUM, analysis, {"seed": 120111231, "allowPhaseReplace": True})
        self.assertEqual(first["planHash"], second["planHash"])
        self.assertTrue(first["readOnly"])
        self.assertFalse(first["sourceMutated"])
        self.assertFalse(first["invariants"]["soloTimingMutable"])
        self.assertFalse(first["invariants"]["goldAffectsVelocity"])
        self.assertGreater(len(first["decisions"]), 0)


class RegressionTests(unittest.TestCase):
    def test_factory_style_strum_and_gold_performance_registries(self):
        style = server.FACTORY_STYLE
        strum = server.FACTORY_STRUM
        performance = server.GOLD_PERFORMANCE
        self.assertEqual(style["summary"]["segments"], 26922)
        self.assertEqual(style["summary"]["notes"], 1283645)
        self.assertEqual(set(style["summary"]["roles"]),
                         {"DRUMS", "PERC", "BASS", "ACC1", "ACC2", "ACC3", "ACC4", "ACC5"})
        self.assertGreater(strum["summary"]["patterns"], 2500)
        self.assertGreater(strum["summary"]["strokes"], 45000)
        self.assertGreater(performance["summary"]["patterns"], 12000)
        self.assertGreater(performance["summary"]["relationships"], 4000)
        self.assertTrue({"drums", "percussion", "bass", "power-riff", "riff", "accompaniment"}
                        <= set(performance["summary"]["roles"]))
        all_patterns = [*server.GOLD["patterns"], *strum["patterns"], *performance["patterns"]]
        ids = [item["id"] for item in all_patterns]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(re.fullmatch(r"\d{3}\.\d{3}\.\d{3}", value) for value in ids))
        self.assertTrue(all(not item["authority"].get("goldUsed", False) for item in strum["patterns"]))
        self.assertTrue(gold_schema.validate_patterns(performance["patterns"])["passed"])

    def test_dna_counts_ids_and_gold_velocity_invariant(self):
        factory, gold = server.FACTORY, server.GOLD
        self.assertEqual(factory["summary"]["profileCount"], 1964)
        self.assertEqual(gold["summary"]["patternCount"], 10637)
        profile_ids = [item["id"] for item in factory["profiles"]]
        pattern_ids = [item["id"] for item in gold["patterns"]]
        self.assertEqual(len(profile_ids), len(set(profile_ids)))
        self.assertEqual(len(pattern_ids), len(set(pattern_ids)))
        schema = gold_schema.validate_patterns(gold["patterns"])
        self.assertTrue(schema["passed"], schema["forbiddenPaths"][:5])
        self.assertEqual(gold["version"], "3.2")

    def test_factory_schema_and_drum_elements(self):
        required = {"instrument_id", "instrument_name", "role", "register_low", "register_high",
                    "velocity_min", "velocity_optimum", "velocity_max", "confidence",
                    "sample_count", "source_ids", "velocityCurve", "velocity_curve", "velocityQuantiles"}
        self.assertTrue(all(required <= set(item) for item in server.FACTORY["profiles"]))
        labels = ["floor", "soft", "lowMid", "optimal", "highMid", "strong", "ceiling"]
        for profile in server.FACTORY["profiles"]:
            points = profile["velocityCurve"]["points"]
            self.assertEqual([item["label"] for item in points], labels)
            values = [item["velocity"] for item in points]
            self.assertEqual(values, sorted(values))
            self.assertFalse(profile["velocityCurve"]["goldAffectsDynamics"])
            self.assertEqual(profile["mixerProfile"]["authority"], "factory-only")
            self.assertFalse(profile["mixerProfile"]["goldAffectsMixer"])
        expected = {"Kick", "Snare", "Closed Hi-Hat", "Open Hi-Hat", "Crash", "Ride",
                    "Toms", "Clap", "Percussion"}
        actual = {item.get("drumElement") for item in server.FACTORY["profiles"] if item["kind"] == "drum"}
        self.assertEqual(actual, expected)

    def test_professional_gui_surfaces_remain_available(self):
        required = ("MIDI Optimizer", "PIANO ROLL & MIDI EDITOR", "Pa800 Style Builder",
                    "DNA Library", "Reports & Safety", "songTimeline", "patternDialog",
                    "Factory Style/CV", "Factory strumming", "GOLD performance",
                    "solo trake uvijek se preskaču", "/api/device-test-kit",
                    "Preuzmi Pa800 test-paket")
        self.assertTrue(all(value in web_gui.HTML for value in required))


class NegativeValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.midi, cls.manifest = server.build_pa800_style(STYLE_CONFIG)
        cls.markers = [item["marker"] for item in cls.manifest["elements"]]
        cls.channels = [channel - 1 for channel in cls.manifest["midi"]["usedChannels"]]

    def assertBlocked(self, midi, markers=None, channels=None):
        result = server.validate_pa800_smf(midi, markers or self.markers, channels or self.channels)
        self.assertFalse(result["passed"], result)

    def test_independent_verifier_detects_program_mutation(self):
        parsed = midi_optimizer.parse_smf(protected_event_midi())
        before = midi_integrity.protected_snapshot(parsed, True)
        program = next(event for event in parsed["tracks"][0]["events"]
                       if event["kind"] == "channel" and event["command"] == 12)
        program["data"][0] += 1
        after = midi_integrity.protected_snapshot(parsed, True)
        result = midi_integrity.verify_protected_events(before, after)
        self.assertFalse(result["passed"])
        self.assertTrue(result["issues"])

    def test_recursive_gold_schema_rejects_nested_velocity_and_program(self):
        adversarial = [{"notes": [{"timing": 0, "hidden": {"velocity_curve": [20, 80, 120]}}],
                        "metadata": {"instrument": {"programChange": 27}}}]
        result = gold_schema.validate_patterns(adversarial)
        self.assertFalse(result["passed"])
        self.assertGreaterEqual(len(result["forbiddenPaths"]), 2)
        with self.assertRaisesRegex(ValueError, "GOLD runtime schema"):
            gold_schema.assert_valid_patterns(adversarial)

    def test_format_1(self):
        data = bytearray(self.midi); data[8:10] = struct.pack(">H", 1); self.assertBlocked(bytes(data))

    def test_multiple_tracks(self):
        data = bytearray(self.midi); data[10:12] = struct.pack(">H", 2); self.assertBlocked(bytes(data))

    def test_invalid_ppq(self):
        data = bytearray(self.midi); data[12:14] = struct.pack(">H", 960); self.assertBlocked(bytes(data))

    def test_invalid_channel(self):
        data = bytearray(self.midi)
        index = next(i for i, value in enumerate(data[22:], 22) if value in range(0xB8, 0xC0))
        data[index] = 0xB0
        self.assertBlocked(bytes(data))

    def test_uppercase_marker(self):
        self.assertBlocked(replace_once(self.midi, b"i1cv1", b"I1cv1"))

    def test_unsupported_marker(self):
        self.assertBlocked(replace_once(self.midi, b"i1cv1", b"x1cv1"), ["x1cv1", *self.markers[1:]])

    def test_duplicate_marker_ids(self):
        self.assertBlocked(replace_once(self.midi, b"i2cv1", b"i1cv1"),
                           [self.markers[0], self.markers[0], *self.markers[2:]])

    def test_missing_eot(self):
        self.assertBlocked(replace_once(self.midi, b"\xff\x2f\x00", b"\xff\x01\x00"))

    def test_invalid_note_pairing(self):
        data = bytearray(self.midi)
        index = next(i for i, value in enumerate(data[22:], 22) if value in range(0x98, 0xA0))
        data[index] = 0x88 | (data[index] & 15)
        self.assertBlocked(bytes(data))

    def test_invalid_note_duration(self):
        channel = 8
        events = [
            {"tick": 0, "priority": 0, "data": server.meta_text(6, "v1cv1")},
            {"tick": 0, "priority": 1, "data": server.meter_meta(4, 4)},
            {"tick": 0, "priority": 2, "data": [0xB0 | channel, 0, 0]},
            {"tick": 0, "priority": 2, "data": [0xB0 | channel, 32, 0]},
            {"tick": 0, "priority": 2, "data": [0xC0 | channel, 32]},
            {"tick": 0, "priority": 2, "data": [0xB0 | channel, 11, 127]},
            {"tick": 120, "priority": 4, "data": [0x90 | channel, 36, 90]},
            {"tick": 120, "priority": 5, "data": [0x80 | channel, 36, 0]},
            {"tick": 240, "priority": 9, "data": [0xFF, 0x2F, 0]},
        ]
        self.assertBlocked(server.smf0(events, 480), ["v1cv1"], [channel])


def main():
    suite = unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    def flatten(node):
        for item in node:
            if isinstance(item, unittest.TestSuite):
                yield from flatten(item)
            else:
                yield item
    cases = list(flatten(suite))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    by_type = Counter(case.__class__.__name__ for case in cases)
    report = {
        "schema": "dna-master-prompt-test-report", "version": "1.0",
        "date": datetime.now(timezone.utc).date().isoformat(),
        "result": "pass" if result.wasSuccessful() else "fail",
        "testsRun": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "testTypes": dict(by_type),
        "invariants": {"goldAffectsDynamics": False, "analysisVelocityUsed": False,
                       "sameSeedSameOutput": True, "invalidMidiExported": False},
        "certification": {"software": "SOFTWARE_VALIDATED" if result.wasSuccessful() else "FAILED",
                          "physicalPa800": "WAITING_FOR_DEVICE"},
    }
    dna_builder.write_json(Path("data") / "master-prompt-test-report.json", report)
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()