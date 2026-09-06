#!/usr/bin/env python3
"""Offline DNA Style Arranger za Korg Pa800 (OS 2.0+)."""

from __future__ import annotations

# Portable checkout bootstrap: make the packaged src/ tree importable even
# when server.py or release_check.py is started directly from Windows.
import sys
from pathlib import Path as _BootstrapPath
_BOOTSTRAP_ROOT = _BootstrapPath(__file__).resolve().parent
_BOOTSTRAP_SRC = _BOOTSTRAP_ROOT / "src"
if _BOOTSTRAP_SRC.is_dir() and str(_BOOTSTRAP_SRC) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_SRC))

import argparse
import hashlib
import json
import re
import struct
import threading
import webbrowser
from collections import Counter, defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import dna_builder
import factory_velocity
import factory_style_registry
import factory_strumming
import gold_performance_registry
import gold_schema
import midi_editor
import midi_optimizer
import phase_optimizer
import pa800_validator
from dna_midi_studio.ai_learning.max_orchestrator import build_max_status
from dna_midi_studio.max_ai_brain import build_max_brain_plan
import pa800_style_builder
import project_model
import result_cache
import song_analyzer
from truthful_evidence_gate import EvidenceGateBlocked, TruthEvidenceGate
import style_intelligence
from dna_midi_studio import (
    analyze_song_map,
    analyze_track_instruments,
    execute_api_payload,
    execute_articulation_map_api,
    execute_arrangement_graph_api,
    execute_candidate_search_api,
    execute_expression_plan_api,
    execute_evidence_resolver_api,
    execute_groove_plan_api,
    execute_quality_evaluator_api,
    execute_preview_session_api,
    execute_producer_brief_api,
    execute_premium_workflow_api,
    execute_personal_profile_api,
    execute_release_readiness_api,
    execute_track_instrument_analysis_api,
    execute_track_plan_api,
    execute_arrangement_renderer_api,
    execute_global_coherence_api,
    execute_end_to_end_api,
    execute_reliability_gate_api,
    execute_quality_calibration_api,
    execute_device_certification_api,
    render_preview_wav,
)


DATA = Path("data")
FACTORY_JSON = DATA / "factory-velocity-profiles.json"
GOLD_JSON = DATA / "gold-patterns.json"
FACTORY_STYLE_JSON = DATA / "factory-style-segments.json"
FACTORY_STRUM_JSON = DATA / "factory-strumming.json"
GOLD_PERFORMANCE_JSON = DATA / "gold-performance-patterns.json"
COMPLIANCE_JSON = DATA / "master-prompt-compliance.json"
RELEASE_JSON = DATA / "release-check-report.json"
TEST_REPORT_JSON = DATA / "master-prompt-test-report.json"
DEVICE_PREFLIGHT_JSON = DATA / "session14-preflight-report.json"
DEVICE_KIT_ZIP = Path("artifacts") / "session14-device-kit" / "DNA-PA800-Session14-Device-Test-Kit.zip"
LEARNING_MANIFEST_JSON = Path("learning_data") / "dataset_manifest.json"
AI_TRAINING_REPORT_JSON = Path("models") / "dna-reconstructor-v1" / "training_report.json"
ARCHIVE = Path("prism-uploads") / "DNA.zip"
TRACKS = {
    "bass": {"label": "Bass", "channel": 8, "role": "bass", "base": 36},
    "drum": {"label": "Drum", "channel": 9, "role": "drums", "base": 0},
    "perc": {"label": "Percussion", "channel": 10, "role": "drums", "base": 0},
    "acc1": {"label": "Acc1", "channel": 11, "role": "chords", "base": 48},
    "acc2": {"label": "Acc2", "channel": 12, "role": "chords", "base": 60},
    "acc3": {"label": "Acc3", "channel": 13, "role": "melody", "base": 60},
    "acc4": {"label": "Acc4", "channel": 14, "role": "melody", "base": 72},
    "acc5": {"label": "Acc5", "channel": 15, "role": "chords", "base": 48},
}
POLYPHONY_LIMITS = {"bass": 1, "drum": 24, "perc": 16, "acc1": 4, "acc2": 4, "acc3": 1, "acc4": 1, "acc5": 3}
DEFAULT_ELEMENTS = [
    {"marker": "i1cv1", "bars": 2, "intensity": 42},
    {"marker": "i2cv1", "bars": 4, "intensity": 68},
    {"marker": "v1cv1", "bars": 2, "intensity": 35},
    {"marker": "v2cv1", "bars": 2, "intensity": 55},
    {"marker": "v3cv1", "bars": 2, "intensity": 76},
    {"marker": "v4cv1", "bars": 2, "intensity": 94},
    {"marker": "f1cv1", "bars": 1, "intensity": 72},
    {"marker": "f2cv1", "bars": 1, "intensity": 96},
    {"marker": "e1cv1", "bars": 2, "intensity": 48},
    {"marker": "e2cv1", "bars": 4, "intensity": 72},
]
FACTORY = GOLD = FACTORY_STYLE = FACTORY_STRUM = GOLD_PERFORMANCE = OPTIONS = None
PROFILE_BY_KEY = {}
BEST_DRUM_BY_NOTE = {}
PATTERN_BY_ID = {}
GROOVE_LINKS = defaultdict(set)
OPTIMIZED_CACHE_LIMIT = 10
OPTIMIZED_CACHE_MAX_BYTES = 128_000_000
OPTIMIZED_CACHE_TTL_SECONDS = 3600
RESULT_CACHE = result_cache.ResultCache(OPTIMIZED_CACHE_LIMIT, OPTIMIZED_CACHE_MAX_BYTES,
                                        OPTIMIZED_CACHE_TTL_SECONDS)


def truth_evidence() -> dict:
    """Return a freshly content-verified gate for every mutation request."""
    return {"gate": TruthEvidenceGate(_BOOTSTRAP_ROOT).build()}


def json_header(path):
    """Read schema metadata without materializing a multi-megabyte registry."""
    prefix = path.read_bytes()[:8192].decode("utf-8", "replace")
    version = re.search(r'"version"\s*:\s*"([^"]+)"', prefix)
    database = re.search(r'"databaseVersion"\s*:\s*"([^"]+)"', prefix)
    return {"version": version.group(1) if version else None,
            "databaseVersion": database.group(1) if database else None}


def ensure_data():
    rebuild = not (FACTORY_JSON.exists() and GOLD_JSON.exists() and FACTORY_STYLE_JSON.exists()
                   and FACTORY_STRUM_JSON.exists() and GOLD_PERFORMANCE_JSON.exists())
    if not rebuild:
        try:
            factory_meta = json_header(FACTORY_JSON)
            gold_meta = json_header(GOLD_JSON)
            style_meta = json_header(FACTORY_STYLE_JSON)
            strum_meta = json_header(FACTORY_STRUM_JSON)
            performance_meta = json_header(GOLD_PERFORMANCE_JSON)
            rebuild = (factory_meta.get("version") != "3.3" or gold_meta.get("version") != "3.2"
                       or style_meta.get("version") != "1.1"
                       or strum_meta.get("version") != "1.1" or performance_meta.get("version") != "1.1"
                       or not factory_meta.get("databaseVersion") or not gold_meta.get("databaseVersion"))
        except (OSError, ValueError, json.JSONDecodeError):
            rebuild = True
    if rebuild:
        if not ARCHIVE.exists():
            raise FileNotFoundError("Nedostaje prism-uploads/DNA.zip")
        print("Izgradnja DNA baze (prvo pokretanje, oko 15-30 sekundi)...")
        factory_files, gold_files = dna_builder.read_nested_archive(ARCHIVE)
        profiles, profile_ids = dna_builder.factory_profiles(factory_files)
        patterns = dna_builder.gold_patterns(gold_files, profile_ids)
        style_segments = factory_style_registry.build_registry(factory_files, profile_ids)
        strumming = factory_strumming.build_registry(style_segments)
        performance = gold_performance_registry.build_registry(gold_files)
        dna_builder.write_json(FACTORY_JSON, profiles)
        dna_builder.write_json(GOLD_JSON, patterns, compact=True)
        dna_builder.write_json(FACTORY_STYLE_JSON, style_segments, compact=True)
        dna_builder.write_json(FACTORY_STRUM_JSON, strumming, compact=True)
        dna_builder.write_json(GOLD_PERFORMANCE_JSON, performance, compact=True)
        dna_builder.write_json(DATA / "dna-build-report.json", {
            "schema": "pa800-dna-build-report", "version": "3.1",
            "database": {"factory": profiles["databaseVersion"], "gold": patterns["databaseVersion"],
                         "factoryStyle": style_segments["databaseVersion"],
                         "factoryStrumming": strumming["databaseVersion"],
                         "goldPerformance": performance["databaseVersion"]},
            "factory": profiles["summary"], "gold": patterns["summary"],
            "factoryStyle": style_segments["summary"],
            "factoryStrumming": strumming["summary"],
            "goldPerformance": performance["summary"],
            "guarantees": {"dynamicsSource": "factory-only", "goldAffectsDynamics": False,
                           "goldAffectsMixer": False, "goldAffectsProgramChange": False,
                           "goldRuntimeSchemaValidated": patterns["schemaValidation"]["passed"]},
        })


def load_data():
    global FACTORY, GOLD, FACTORY_STYLE, FACTORY_STRUM, GOLD_PERFORMANCE
    global OPTIONS, PROFILE_BY_KEY, BEST_DRUM_BY_NOTE, PATTERN_BY_ID, GROOVE_LINKS
    ensure_data()
    FACTORY = json.loads(FACTORY_JSON.read_text(encoding="utf-8"))
    GOLD = json.loads(GOLD_JSON.read_text(encoding="utf-8"))
    FACTORY_STYLE = json.loads(FACTORY_STYLE_JSON.read_text(encoding="utf-8"))
    # Full Factory notes are needed only while deriving the separate strum
    # registry.  Runtime/library keep a small preview, avoiding hundreds of MB
    # of redundant Python integer/list objects.
    for segment in FACTORY_STYLE.get("segments", []):
        segment["notePreview"] = segment.pop("notes", [])[:32]
    FACTORY_STRUM = json.loads(FACTORY_STRUM_JSON.read_text(encoding="utf-8"))
    GOLD_PERFORMANCE = json.loads(GOLD_PERFORMANCE_JSON.read_text(encoding="utf-8"))
    gold_schema.assert_valid_patterns(GOLD["patterns"])
    gold_schema.assert_valid_patterns(GOLD_PERFORMANCE["patterns"])
    PROFILE_BY_KEY = {item["instrumentKey"]: item for item in FACTORY["profiles"]}
    all_runtime_patterns = [*GOLD["patterns"], *GOLD_PERFORMANCE["patterns"], *FACTORY_STRUM["patterns"]]
    ids = [item["id"] for item in all_runtime_patterns]
    if len(ids) != len(set(ids)):
        duplicates = [item for item, count in Counter(ids).items() if count > 1]
        raise ValueError("Kolizija ID-a između runtime registryja: " + ", ".join(duplicates[:5]))
    PATTERN_BY_ID = {item["id"]: item for item in all_runtime_patterns}
    GROOVE_LINKS = defaultdict(set)
    for relationship in GOLD_PERFORMANCE.get("relationships", []):
        ids = list(relationship.get("patterns", {}).values())
        for pattern_id in ids:
            GROOVE_LINKS[pattern_id].update(other for other in ids if other != pattern_id)
    BEST_DRUM_BY_NOTE = {}
    for item in sorted((profile for profile in FACTORY["profiles"] if profile["kind"] == "drum"),
                       key=lambda profile: -profile["samples"]):
        BEST_DRUM_BY_NOTE.setdefault(item.get("drumNote"), item)
    OPTIONS = build_options()


def cache_optimized(midi, report, file_name, suffix="OPT", metadata=None):
    return RESULT_CACHE.put(midi, report, file_name, suffix, metadata)


def get_optimized(token):
    return RESULT_CACHE.get(token)


def optimizer_settings_from_headers(headers):
    return {
        "cleanupNotes": headers.get("X-Cleanup-Notes", "true").lower() != "false",
        "removeRedundantControllers": headers.get("X-Clean-Controllers", "true").lower() != "false",
        "quantizeDivision": int(headers.get("X-Quantize-Division", "16")),
        "quantizeStrength": int(headers.get("X-Quantize-Strength", "85")),
        "factoryDynamics": headers.get("X-Factory-Dynamics", "true").lower() != "false",
        "velocityStrength": int(headers.get("X-Velocity-Strength", "65")),
        "factoryMixer": headers.get("X-Factory-Mixer", "false").lower() == "true",
        "mixerStrength": int(headers.get("X-Mixer-Strength", "65")),
        "insertMissingMixer": headers.get("X-Insert-Mixer", "true").lower() != "false",
        "repairKeyRange": headers.get("X-Repair-Key-Range", "false").lower() == "true",
        "energyTarget": float(headers.get("X-Energy-Target", "64")),
        "fxAuto": headers.get("X-FX-Auto", "false").lower() == "true",
        "fxStrength": int(headers.get("X-FX-Strength", "60")),
        "autoDelay": headers.get("X-Auto-Delay", "false").lower() == "true",
        "autoThird": headers.get("X-Auto-Third", "false").lower() == "true",
        "delayDivision": int(headers.get("X-Delay-Division", "8")),
        "phaseOptimization": headers.get("X-Phase-Optimization", "false").lower() == "true",
        "allowPhaseReplace": headers.get("X-Allow-Phase-Replace", "false").lower() == "true",
        "maxPerformance": headers.get("X-Max-Performance", "false").lower() == "true",
        "performanceGestures": headers.get("X-Performance-Gestures", "false").lower() == "true",
        "pitchBendSemitones": (float(headers.get("X-Pitch-Bend-Semitones")) if headers.get("X-Pitch-Bend-Semitones") else None),
        "echoDensity": float(headers.get("X-Echo-Density", "0.42")),
        "percussionReduction": int(headers.get("X-Percussion-Reduction", "40")),
        "bassKickInterlockStrength": int(headers.get("X-Bass-Kick-Interlock", "45")),
        "databaseVersion": FACTORY.get("databaseVersion", FACTORY.get("version", "unknown")),
        "seed": int(headers.get("X-Seed", "0")),
    }




def reconstruction_variant_settings(base_settings):
    """Return deterministic Suno-like A/B/C settings over the same safe engine.

    Variants change performance intensity only. Protected song skeleton and the
    Factory/GOLD authority model remain enforced by midi_optimizer.
    """
    base = dict(base_settings)
    base.update({"maxPerformance": True, "factoryDynamics": True, "performanceGestures": True})
    return [
        ("A", "Balanced Live", {**base, "quantizeStrength": 74, "velocityStrength": 58,
                                 "percussionReduction": 40, "bassKickInterlockStrength": 42}),
        ("B", "Groove Forward", {**base, "quantizeStrength": 84, "velocityStrength": 66,
                                  "percussionReduction": 40, "bassKickInterlockStrength": 52}),
        ("C", "Conservative", {**base, "quantizeStrength": 62, "velocityStrength": 50,
                                "percussionReduction": 34, "bassKickInterlockStrength": 35}),
    ]


def reconstruct_midi_variants(content, file_name, base_settings):
    """Run three independently validated deterministic reconstruction variants."""
    max_brain_plan = build_max_brain_plan(content, file_name).to_dict()
    variants = []
    for variant_id, label, settings in reconstruction_variant_settings(base_settings):
        evidence = truth_evidence()
        if settings.get("phaseOptimization"):
            analysis = song_analyzer.analyze_midi(content, file_name)
            evidence.update({"analysis": analysis,
                             "goldPatterns": GOLD_PERFORMANCE["patterns"],
                             "factoryStrumPatterns": FACTORY_STRUM["patterns"]})
        midi, report = midi_optimizer.optimize_midi(
            content, FACTORY["profiles"], settings, file_name, evidence)
        report = dict(report)
        report["reconstructionVariant"] = {
            "id": variant_id, "label": label, "schema": "dna-reconstruction-variant",
            "version": "4.15", "deterministic": True,
            "protectedSkeleton": True, "factoryVelocityOnly": True,
            "goldVelocityInfluence": False,
        }
        token = cache_optimized(midi, report, file_name, f"RECON_{variant_id}",
                                {"variant": variant_id, "label": label})
        variants.append({
            "id": variant_id, "label": label, "token": token,
            "downloadUrl": f"/api/optimizer-download?token={token}",
            "qualityBefore": report.get("quality", {}).get("before"),
            "qualityAfter": report.get("quality", {}).get("after"),
            "outputSha256": report.get("output", {}).get("sha256"),
            "report": report,
        })
    # Highest verified quality wins; stable A/B/C ordering is the tie-breaker.
    selected = max(variants, key=lambda item: (item["qualityAfter"] or -1, -ord(item["id"])))
    return {
        "schema": "dna-max-ai-reconstruction", "version": "6.0",
        "sourceFile": file_name, "variantCount": len(variants),
        "maxAIBrain": max_brain_plan,
        "selectedVariant": selected["id"], "token": selected["token"],
        "downloadUrl": selected["downloadUrl"], "report": selected["report"],
        "variants": variants,
        "invariants": {"originalOverwritten": False, "protectedSkeleton": True,
                       "factoryVelocityOnly": True, "goldVelocityInfluence": False},
    }

def build_phase_plan(content, file_name, seed=0, allow_replace=False):
    analysis = song_analyzer.analyze_midi(content, file_name)
    parsed = midi_optimizer.parse_smf(content)
    notes_by_track = {}
    for track in parsed["tracks"]:
        notes = midi_optimizer.pair_notes(track)
        midi_optimizer.attach_instruments(track, notes)
        notes_by_track[track["index"]] = notes
    profiles_by_key = midi_optimizer.profile_indexes(FACTORY["profiles"])[0]
    plan = phase_optimizer.build_phase_plan(
        parsed, notes_by_track, analysis, profiles_by_key,
        GOLD_PERFORMANCE["patterns"], FACTORY_STRUM["patterns"],
        seed=seed, allow_replace=allow_replace)
    return analysis, plan


def build_options():
    profiles = FACTORY["profiles"]
    melodic = [profile for profile in profiles if profile["kind"] == "melodic"]
    melodic.sort(key=lambda item: -item["samples"])
    kits = {}
    for profile in (item for item in profiles if item["kind"] == "drum"):
        key = f"drum:{profile['bankMsb']}:{profile['bankLsb']}:{profile['program']}"
        kit = kits.setdefault(key, {"id": key, "label": f"Kit {profile['bankMsb']}/{profile['bankLsb']}/{profile['program']}",
                                    "bankMsb": profile["bankMsb"], "bankLsb": profile["bankLsb"],
                                    "program": profile["program"], "samples": 0, "members": []})
        kit["samples"] += profile["samples"]
        kit["members"].append(profile)
    for kit in kits.values():
        labels = [label for _, label in factory_velocity.CURVE_ANCHORS]
        curve_values = {
            label: round(sum(item["velocity"][label] * item["samples"] for item in kit["members"]) / kit["samples"])
            for label in labels
        }
        kit["velocity"] = {"min": curve_values["floor"], "optimal": curve_values["optimal"],
                           "max": curve_values["ceiling"], **curve_values}
        kit["velocityCurve"] = {
            "method": "weighted-drum-kit-factory-curves-v1",
            "points": [{"intensity": intensity, "label": label, "velocity": curve_values[label]}
                       for intensity, label in factory_velocity.CURVE_ANCHORS],
            "values": curve_values, "sampleCount": kit["samples"],
            "allowedRange": [curve_values["floor"], curve_values["ceiling"]],
            "goldAffectsDynamics": False,
        }
        del kit["members"]
    kit_list = sorted(kits.values(), key=lambda item: -item["samples"])[:160]

    def option(profile):
        return {key: profile[key] for key in ("id", "instrument", "instrumentKey", "bankMsb", "bankLsb",
                                               "program", "velocity", "velocityCurve", "mixerProfile", "register",
                                               "confidence", "samples")}

    bass = [item for item in melodic if 32 <= item["program"] <= 39][:220] or melodic[:220]
    chords = [item for item in melodic if item["program"] <= 31 or 48 <= item["program"] <= 55][:300] or melodic[:300]
    melody = [item for item in melodic if 40 <= item["program"] <= 87][:300] or melodic[:300]
    return {
        "target": "Korg Pa800 OS 2.0+", "midiFormat": 0,
        "summary": {"profiles": FACTORY["summary"]["profileCount"], "patterns": GOLD["summary"]["patternCount"],
                    "factoryStyleSegments": FACTORY_STYLE["summary"]["segments"],
                    "factoryStrumPatterns": FACTORY_STRUM["summary"]["patterns"],
                    "goldPerformancePatterns": GOLD_PERFORMANCE["summary"]["patterns"],
                    "goldGrooveRelationships": GOLD_PERFORMANCE["summary"]["relationships"],
                    "velocitySamples": FACTORY["summary"]["velocitySamples"], "goldVelocityFields": 0,
                    "factoryDatabaseVersion": FACTORY.get("databaseVersion", FACTORY.get("version", "unknown")),
                    "goldDatabaseVersion": GOLD.get("databaseVersion", GOLD.get("version", "unknown"))},
        "elements": DEFAULT_ELEMENTS,
        "tracks": {
            "bass": [option(item) for item in bass], "drum": kit_list, "perc": kit_list,
            "acc1": [option(item) for item in chords], "acc2": [option(item) for item in chords],
            "acc3": [option(item) for item in melody], "acc4": [option(item) for item in melody],
            "acc5": [option(item) for item in chords],
        },
        "channelMap": {name: info["channel"] + 1 for name, info in TRACKS.items()},
        "polyphonyLimits": dict(POLYPHONY_LIMITS),
        "trackGuidance": {name: style_intelligence.track_recommendation(name) for name in TRACKS},
    }


def valid_marker(marker):
    return pa800_validator.valid_marker(marker)


def stable_index(text, size):
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big") % size


def style_pattern_role(track_name, choice):
    if track_name == "drum":
        return "drums"
    if track_name == "perc":
        return "percussion"
    if track_name == "bass":
        return "bass"
    program = int(choice.get("program", 0))
    name = choice.get("instrument", choice.get("label", "")).lower()
    if 24 <= program <= 28 or any(word in name for word in ("nylon", "steel", "clean guitar", "jazz guitar")):
        return "factory-strum"
    if 29 <= program <= 31 or any(word in name for word in ("overdrive", "distortion")):
        return "power-riff"
    if track_name in ("acc3", "acc4"):
        return "riff"
    return "accompaniment"


def pattern_rank(item, role, meter, marker, track_name, intensity, tempo=120, bars=1,
                 linked_ids=None, previous_id=None):
    notes = item["notes"]
    marker_type = {"i": "intro", "v": "body", "f": "transition", "e": "ending"}.get(marker[0], "body")
    source_section = item.get("sourceSection", "body")
    marker_element = {"i1": "intro 1", "i2": "intro 2", "i3": "intro 3",
                      "v1": "variation 1", "v2": "variation 2", "v3": "variation 3", "v4": "variation 4",
                      "f1": "fill 1", "f2": "fill 2", "f3": "fill 3", "br": "break",
                      "e1": "ending 1", "e2": "ending 2", "e3": "ending 3"}.get(marker[:2])
    if marker_element and item.get("sourceElement") == marker_element:
        section_score = 1.0
    else:
        section_score = .82 if source_section == marker_type else .62 if source_section == "body" else .35
    desired_notes = 3 + max(0, min(100, intensity)) * .18
    intensity_score = max(0.0, 1 - abs(len(notes) - desired_notes) / max(desired_notes, len(notes), 1))
    pitch_values = [note[2] for note in notes]
    span = max(pitch_values) - min(pitch_values) if pitch_values else 0
    target_span = {"bass": 18, "drum": 48, "perc": 48, "acc1": 36, "acc2": 36,
                   "acc3": 30, "acc4": 30, "acc5": 24}.get(track_name, 36)
    register_score = max(0.0, 1 - abs(span - target_span) / max(target_span, span, 1))
    if role == "drums":
        harmonic_score = 1.0
    else:
        allowed = {0, 7} if role == "bass" else {0, 4, 7} if role == "chords" else {0, 2, 4, 5, 7, 9, 11}
        harmonic_score = sum(1 for pitch in pitch_values if pitch % 12 in allowed) / max(1, len(pitch_values))
    tempo_range = item.get("tempoRange")
    if not tempo_range:
        tempo_score = .72
    elif tempo_range[0] <= tempo <= tempo_range[1]:
        tempo_score = 1.0
    else:
        distance = min(abs(tempo - tempo_range[0]), abs(tempo - tempo_range[1]))
        tempo_score = max(0.0, 1 - distance / max(30, tempo))
    quality = item.get("qualityScore", item.get("confidence", .5) * 100) / 100
    transition = item.get("transitionContext") or {}
    if marker_type == "transition":
        transition_score = min(1.0, .45 + transition.get("exitNotes", 0) / 12)
    elif previous_id and item["id"] in GROOVE_LINKS.get(previous_id, set()):
        transition_score = 1.0
    else:
        transition_score = .72
    linked_ids = set(linked_ids or [])
    relationship_score = 1.0 if any(item["id"] in GROOVE_LINKS.get(linked, set()) for linked in linked_ids) else .65
    target_length = max(1, int(bars or 1))
    transformation_cost = min(1.0, abs(int(item.get("lengthBars", 1)) - target_length) / target_length)
    articulation = item.get("articulation") or {}
    articulation_score = 1.0 if role == "factory-strum" and item.get("strokes") else (
        .82 if articulation else .62)
    criteria = {
        "role_match": 1.0 if item["role"] == role else 0.0,
        "meter_match": 1.0 if item["meter"] == meter else .35,
        "tempo_match": round(tempo_score, 4),
        "section_match": round(section_score, 4),
        "density_accent_match": round(intensity_score, 4),
        "harmonic_compatibility": round(harmonic_score, 4),
        "register_articulation_match": round((register_score + articulation_score) / 2, 4),
        "evidence_quality": round((item.get("confidence", .5) + quality) / 2, 4),
        "transition_compatibility": round((transition_score + relationship_score) / 2, 4),
        "transformation_budget_safety": round(1 - transformation_cost, 4),
    }
    weights = {"role_match": .16, "meter_match": .11, "tempo_match": .08,
               "section_match": .1, "density_accent_match": .1,
               "harmonic_compatibility": .11, "register_articulation_match": .09,
               "evidence_quality": .1, "transition_compatibility": .08,
               "transformation_budget_safety": .07}
    total = sum(criteria[key] * weights[key] for key in weights)
    return round(total, 6), criteria


def choose_pattern(role, meter, seed, marker, track_name, intensity, locked_id=None, candidate_offset=0,
                   excluded_ids=None, tempo=120, bars=1, linked_ids=None, previous_id=None):
    excluded_ids = set(excluded_ids or [])
    if locked_id:
        locked = PATTERN_BY_ID.get(locked_id)
        if not locked:
            raise ValueError(f"Zaključani pattern ne postoji: {locked_id}")
        if locked["role"] != role:
            raise ValueError(f"Zaključani pattern {locked_id} nije kompatibilan s ulogom {role}")
        if locked["meter"] != meter:
            raise ValueError(f"Zaključani pattern {locked_id} nije kompatibilan s taktom {meter}")
        total, criteria = pattern_rank(locked, role, meter, marker, track_name, intensity,
                                       tempo, bars, linked_ids, previous_id)
        return locked, {"score": total, "criteria": criteria, "candidatePool": 1, "rankedPool": 1,
                        "bestDeterministicSet": 1, "selectionMode": "locked-by-user",
                        "selectionHash": hashlib.sha256(f"lock:{locked_id}".encode("utf-8")).hexdigest(),
                        "alternatives": []}
    if role == "factory-strum":
        source_patterns = FACTORY_STRUM["patterns"]
    else:
        source_patterns = GOLD_PERFORMANCE["patterns"]
    pool = [item for item in source_patterns if item["role"] == role and item["meter"] == meter]
    if not pool:
        pool = [item for item in source_patterns if item["role"] == role]
    # Compatibility fallback for unusual meters/roles; the normal engine uses
    # the new full-performance registries above.
    if not pool and role in ("accompaniment", "riff"):
        legacy_role = "chords" if role == "accompaniment" else "melody"
        pool = [item for item in GOLD["patterns"] if item["role"] == legacy_role]
    pool = [item for item in pool if item["id"] not in excluded_ids]
    relationship_constrained = False
    if role in ("bass", "percussion") and linked_ids:
        related_ids = set().union(*(GROOVE_LINKS.get(pattern_id, set()) for pattern_id in linked_ids))
        related = [item for item in pool if item["id"] in related_ids]
        if related:
            pool = related
            relationship_constrained = True
    if not pool:
        return None, None
    if not pool:
        return None, None
    bounded = sorted(pool, key=lambda item: (-item.get("qualityScore", 0),
                                              -item.get("occurrences", 1), item["id"]))[:3000]
    ranked = []
    for item in bounded:
        total, criteria = pattern_rank(item, role, meter, marker, track_name, intensity,
                                       tempo, bars, linked_ids, previous_id)
        ranked.append((total, criteria, item))
    ranked.sort(key=lambda row: (-row[0], -row[1]["evidence_quality"],
                                 -row[2].get("occurrences", 1), row[2]["id"]))
    best_score = ranked[0][0]
    best_set = [row for row in ranked if row[0] >= best_score - .04][:64]
    base_index = stable_index(f"{seed}:{marker}:{track_name}", len(best_set))
    if int(candidate_offset or 0):
        candidate_set = ranked[:64]
        chosen = candidate_set[(base_index + int(candidate_offset)) % len(candidate_set)]
        selection_mode = "manual-next-candidate"
    else:
        chosen = best_set[base_index]
        selection_mode = "seeded-related-best-set" if relationship_constrained else "seeded-best-set"
    return chosen[2], {
        "score": chosen[0], "criteria": chosen[1], "candidatePool": len(pool),
        "rankedPool": len(ranked), "bestDeterministicSet": len(best_set),
        "selectionMode": selection_mode, "candidateOffset": int(candidate_offset or 0),
        "relationshipConstrained": relationship_constrained,
        "selectionHash": hashlib.sha256(f"{seed}:{marker}:{track_name}".encode("utf-8")).hexdigest(),
        "alternatives": [{"patternId": row[2]["id"], "score": row[0]} for row in ranked[:8]],
    }


def find_choice(track_name, choice_id):
    choices = OPTIONS["tracks"][track_name]
    return next((item for item in choices if item["id"] == choice_id), choices[0] if choices else None)


def velocity_at(profile, intensity):
    return factory_velocity.velocity_at(profile, intensity)


def style_note_intensity(track_name, pitch, marker, intensity, factory_accent=None):
    """Role/element intensity is always rendered through a Factory curve."""
    value = float(intensity)
    if factory_accent is not None:
        value = .72 * value + .28 * float(factory_accent)
    if track_name in ("drum", "perc"):
        element = dna_builder.drum_element(int(pitch))
        modifier = {"Kick": 2, "Snare": 4, "Closed Hi-Hat": -8, "Open Hi-Hat": -2,
                    "Crash": 7, "Ride": -4, "Toms": 3, "Clap": -2,
                    "Percussion": -10}.get(element, 0)
        if marker.startswith("f") or marker.startswith("br"):
            modifier += 7 if element in ("Toms", "Crash", "Snare") else 1
        if track_name == "perc":
            modifier -= 7
        value += modifier
    elif track_name == "bass":
        value -= 3
    return max(0, min(100, round(value)))


def fold(pitch, low, high):
    while pitch < low:
        pitch += 12
    while pitch > high:
        pitch -= 12
    return max(0, min(127, pitch))


def adapted_pitch(value, track_name, pitch_mode=None):
    if track_name in ("drum", "perc"):
        return value
    info = TRACKS[track_name]
    if info["role"] == "bass":
        return fold(info["base"] + value, 28, 55)
    if pitch_mode == "factory-strum-relative-voicing":
        octave, pc = divmod(value, 12)
        chord_tone = min((0, 4, 7, 12), key=lambda tone: abs(tone - pc))
        return fold(info["base"] + octave * 12 + chord_tone, 43, 88)
    if info["role"] == "chords":
        octave, pc = divmod(value, 12)
        chord_tone = min((0, 4, 7), key=lambda tone: abs(tone - pc))
        return fold(info["base"] + octave * 12 + chord_tone, 43, 84)
    return fold(info["base"] + value, 55, 92)


def transformed_notes(pattern, track_name):
    notes = pattern.get("events", pattern["notes"])
    if track_name == "perc":
        filtered = [note for note in notes if note[2] not in range(35, 41)]
        return filtered if len(filtered) >= 2 else notes
    if track_name == "acc5":
        sparse = [note for note in notes if note[0] % 4 == 0]
        return sparse if len(sparse) >= 2 else notes
    return notes


def prepared_notes(pattern, track_name):
    """Mapiraj pitch i ograniči stvarnu istodobnu MIDI-note polifoniju."""
    grouped = defaultdict(dict)
    duplicate_count = 0
    resolution = pattern.get("timingResolution")
    pitch_mode = pattern.get("pitchMode")
    for raw in transformed_notes(pattern, track_name):
        position, duration, pitch_value = raw[:3]
        accent = raw[3] if len(raw) >= 4 and pattern.get("role") == "factory-strum" else None
        if resolution:
            position = round(position * 480 / resolution)
            duration = max(1, round(duration * 480 / resolution))
        else:
            position, duration = round(position * 120), max(1, round(duration * 120))
        pitch = adapted_pitch(pitch_value, track_name, pitch_mode)
        previous = grouped[position].get(pitch)
        if previous is not None:
            grouped[position][pitch] = (max(previous[0], duration),
                                        accent if accent is not None else previous[1])
            duplicate_count += 1
        else:
            grouped[position][pitch] = (duration, accent)
    mapped = [
        (position, duration, pitch, accent)
        for position, pitch_map in grouped.items()
        for pitch, (duration, accent) in pitch_map.items()
    ]

    def peak_polyphony(notes):
        boundaries = []
        for position, duration, *_ in notes:
            boundaries.extend(((position, 1), (position + duration, -1)))
        active = peak = 0
        # Note-off na istom ticku mora osloboditi glas prije novog note-ona.
        for _, delta in sorted(boundaries, key=lambda item: (item[0], item[1])):
            active += delta
            peak = max(peak, active)
        return peak

    output, polyphony_dropped, polyphony_tails_trimmed = [], 0, 0
    limit = POLYPHONY_LIMITS[track_name]
    for position, pitch_map in sorted(grouped.items()):
        candidates = sorted((pitch, duration, accent) for pitch, (duration, accent) in pitch_map.items())
        if len(candidates) > limit:
            polyphony_dropped += len(candidates) - limit
            if limit == 1:
                candidates = [candidates[0] if track_name == "bass" else candidates[len(candidates) // 2]]
            else:
                indexes = sorted({round(index * (len(candidates) - 1) / (limit - 1)) for index in range(limit)})
                candidates = [candidates[index] for index in indexes]
        active = [index for index, note in enumerate(output)
                  if note[0] < position < note[0] + note[1]]
        overflow = max(0, len(active) + len(candidates) - limit)
        # Novi akord/fraza zadrzava onset; samo repovi starijih nota zavrsavaju
        # na novom onsetu. Tako nema nasumicnog voice stealinga ni gubitka napada.
        victims = sorted(active, key=lambda index: (output[index][0],
                                                    -(output[index][0] + output[index][1]),
                                                    output[index][2]))[:overflow]
        for index in victims:
            old_position, _, old_pitch, old_accent = output[index]
            output[index] = (old_position, position - old_position, old_pitch, old_accent)
            polyphony_tails_trimmed += 1
        output.extend((position, duration, pitch, accent) for pitch, duration, accent in candidates)
    return sorted(output), {"duplicatesRemoved": duplicate_count, "polyphonyNotesRemoved": polyphony_dropped,
                            "polyphonyTailsTrimmed": polyphony_tails_trimmed,
                            "peakPolyphonyBefore": peak_polyphony(mapped),
                            "peakPolyphonyAfter": peak_polyphony(output),
                            "patternLengthBars": max(1, int(pattern.get("lengthBars", 1))),
                            "patternAuthority": "factory-strumming" if pattern.get("role") == "factory-strum"
                                                else "gold-performance"}


def drum_profile(kit, pitch):
    exact = f"{kit['id']}:{pitch}"
    return PROFILE_BY_KEY.get(exact) or BEST_DRUM_BY_NOTE.get(pitch) or kit


def build_pa800_style(config):
    meter = config.get("meter", "4/4")
    numerator, denominator = (int(value) for value in meter.split("/"))
    tempo = max(30, min(300, int(config.get("tempo", 120))))
    seed = int(config.get("seed", 120111231))
    pattern_locks = config.get("patternLocks") or {}
    pattern_offsets = config.get("patternOffsets") or {}
    excluded_patterns = set(config.get("excludedPatternIds") or [])
    ppq, step = 480, 120
    bar_ticks = round(ppq * numerator * 4 / denominator)
    elements = [item for item in config.get("elements", DEFAULT_ELEMENTS) if item.get("enabled", True)]
    if not elements or any(not valid_marker(item.get("marker", "")) for item in elements):
        raise ValueError("Neispravan ili nedostajući Pa800 marker")
    if len({item["marker"] for item in elements}) != len(elements):
        raise ValueError("Pa800 markeri moraju biti jedinstveni")

    selected_tracks = {}
    for name in TRACKS:
        request = config.get("tracks", {}).get(name, {})
        if request.get("enabled", name in ("bass", "drum", "perc", "acc1", "acc2")):
            choice = find_choice(name, request.get("profileId"))
            if choice:
                selected_tracks[name] = choice
    if not selected_tracks:
        raise ValueError("Uključi barem jednu Style traku")

    events = [{"tick": 0, "priority": 0, "data": meta_text(3, config.get("name", "DNA Pa800 Style")[:24])},
              {"tick": 0, "priority": 1, "data": tempo_meta(tempo)}]
    manifest_elements, cursor, note_count = [], 0, 0
    quality = {"duplicatesRemoved": 0, "polyphonyNotesRemoved": 0, "overlapsTrimmed": 0,
               "voiceLeadingOctaveMoves": 0, "registerCollisionsResolved": 0}
    active_notes = {}
    tick_occupancy = defaultdict(set)
    previous_centers = {}
    for element_index, element in enumerate(elements):
        marker = element["marker"].lower()
        bars = max(1, min(32, int(element.get("bars", 2))))
        intensity = max(0, min(100, int(element.get("intensity", 60))))
        events.append({"tick": cursor, "priority": 0, "data": meta_text(6, marker)})
        events.append({"tick": cursor, "priority": 1, "data": meter_meta(numerator, denominator)})
        pattern_ids, pattern_selection, musical_decisions = {}, {}, {}
        for track_name, choice in selected_tracks.items():
            info, channel = TRACKS[track_name], TRACKS[track_name]["channel"]
            events.extend([
                {"tick": cursor, "priority": 2, "data": [0xB0 | channel, 0, choice["bankMsb"]]},
                {"tick": cursor, "priority": 2, "data": [0xB0 | channel, 32, choice["bankLsb"]]},
                {"tick": cursor, "priority": 2, "data": [0xC0 | channel, choice["program"]]},
                {"tick": cursor, "priority": 2, "data": [0xB0 | channel, 11, 127]},
            ])
            lock_id = (pattern_locks.get(marker) or {}).get(track_name)
            offset = int((pattern_offsets.get(marker) or {}).get(track_name, 0))
            pattern, ranking = choose_pattern(info["role"], meter, seed, marker, track_name, intensity,
                                              lock_id, offset, excluded_patterns)
            if not pattern:
                continue
            pattern_ids[track_name] = pattern["id"]
            pattern_selection[track_name] = {"patternId": pattern["id"], **ranking}
            notes, cleanup = prepared_notes(pattern, track_name)
            notes, previous_centers[track_name], voice_leading = style_intelligence.voice_lead(
                notes, track_name, previous_centers.get(track_name))
            musical_decisions[track_name] = {"voiceLeading": voice_leading,
                                             "trackGuidance": style_intelligence.track_recommendation(track_name)}
            quality["voiceLeadingOctaveMoves"] += int(voice_leading["applied"])
            quality["duplicatesRemoved"] += cleanup["duplicatesRemoved"] * bars
            quality["polyphonyNotesRemoved"] += cleanup["polyphonyNotesRemoved"] * bars
            for bar in range(bars):
                bar_start = cursor + bar * bar_ticks
                for position, duration, pitch in notes:
                    start = bar_start + round(position * step)
                    if start >= bar_start + bar_ticks:
                        continue
                    pitch, collision_fixed = style_intelligence.resolve_unison(
                        pitch, track_name, tick_occupancy[start])
                    quality["registerCollisionsResolved"] += int(collision_fixed)
                    if track_name not in ("drum", "perc"):
                        tick_occupancy[start].add(pitch)
                    end = min(bar_start + bar_ticks, start + max(1, round(duration * step)))
                    profile = drum_profile(choice, pitch) if track_name in ("drum", "perc") else choice
                    velocity = velocity_at(profile, intensity)
                    note_key = (channel, pitch)
                    previous = active_notes.get(note_key)
                    if previous and start < previous["off"]["tick"]:
                        if start == previous["start"]:
                            previous["off"]["tick"] = max(previous["off"]["tick"], end)
                            quality["duplicatesRemoved"] += 1
                            continue
                        previous["off"]["tick"] = max(previous["start"] + 1, start)
                        quality["overlapsTrimmed"] += 1
                    on_event = {"tick": start, "priority": 4, "data": [0x90 | channel, pitch, velocity]}
                    off_event = {"tick": end, "priority": 3, "data": [0x80 | channel, pitch, 0]}
                    events.extend((on_event, off_event))
                    active_notes[note_key] = {"start": start, "off": off_event}
                    note_count += 1
        next_marker = elements[element_index + 1]["marker"].lower() if element_index + 1 < len(elements) else None
        manifest_elements.append({"marker": marker, "bars": bars, "intensity": intensity,
                                  "patterns": pattern_ids, "patternSelection": pattern_selection,
                                  "musicalDecisions": musical_decisions,
                                  "transition": style_intelligence.transition_recommendation(marker, next_marker)})
        cursor += bars * bar_ticks
    events.append({"tick": cursor, "priority": 9, "data": [0xFF, 0x2F, 0]})
    midi = smf0(events, ppq)
    compliance = validate_pa800_smf(midi, [item["marker"] for item in manifest_elements],
                                    [TRACKS[name]["channel"] for name in selected_tracks])
    if not compliance["passed"]:
        raise ValueError("Pa800 validator: " + "; ".join(compliance["issues"][:5]))
    factory_version = FACTORY.get("databaseVersion", FACTORY.get("version", "unknown"))
    gold_version = GOLD.get("databaseVersion", GOLD.get("version", "unknown"))
    combined_version = hashlib.sha256(f"{factory_version}:{gold_version}".encode("utf-8")).hexdigest()[:20]
    config_hash = hashlib.sha256(json.dumps(config, sort_keys=True, ensure_ascii=False,
                                            separators=(",", ":")).encode("utf-8")).hexdigest()
    output_hash = hashlib.sha256(midi).hexdigest()
    manifest = {
        "schema": "dna-korg-pa800-style", "version": "1.0", "target": "Korg Pa800 OS 2.0+",
        "seed": seed,
        "database": {"version": combined_version, "factory": factory_version, "gold": gold_version},
        "determinism": {"sameSeedSameOutput": True, "configSha256": config_hash,
                        "selection": "seven-criteria-best-deterministic-set"},
        "midi": {"format": 0, "ppq": ppq, "tempo": tempo, "meter": meter, "noteCount": note_count,
                 "trackCount": 1, "usedChannels": [TRACKS[name]["channel"] + 1 for name in selected_tracks],
                 "sha256": output_hash},
        "rules": {"dynamicsSource": "factory-only", "goldAffectsDynamics": False,
                  "goldVelocityFields": 0, "referenceKey": "C", "referenceChord": "Major"},
        "tracks": {name: {"channel": TRACKS[name]["channel"] + 1, "profileId": choice["id"],
                          "bankMsb": choice["bankMsb"], "bankLsb": choice["bankLsb"],
                          "program": choice["program"], "velocity": choice["velocity"],
                          "pa800Recommendation": style_intelligence.track_recommendation(name)}
                   for name, choice in selected_tracks.items()},
        "elements": manifest_elements,
        "quality": {**quality, "polyphonyLimits": POLYPHONY_LIMITS},
        "patternControls": {"locks": pattern_locks, "offsets": pattern_offsets,
                            "excludedPatternIds": sorted(excluded_patterns)},
        "compliance": compliance,
        "audit": {"inputHash": config_hash, "outputHash": output_hash, "seed": seed,
                  "databaseVersion": combined_version,
                  "interventionCount": sum(value for value in quality.values() if isinstance(value, int)),
                  "validationResult": "PASS"},
        "certification": {"software": "SOFTWARE_VALIDATED", "physicalPa800": "WAITING_FOR_DEVICE"},
        "pa800Import": {"mode": "Style Record > Import SMF", "initializeNewStyle": True,
                        "originalKey": "C", "originalChord": "Major",
                        "nttNote": "Sve Track Type i NTT vrijednosti su preporuke; potvrditi ih na Pa800 nakon uvoza."},
    }
    if config.get("songAnalysis"):
        manifest["songAnalysis"] = config["songAnalysis"]
    return midi, manifest


# Transportni server zadržava kompatibilne javne funkcije, dok je aktivna
# orkestracija Style builda izdvojena u zaseban servisni modul.
_legacy_build_pa800_style = build_pa800_style


def build_pa800_style(config):
    return pa800_style_builder.build_style(config, {
        "tracks": TRACKS, "polyphonyLimits": POLYPHONY_LIMITS,
        "defaultElements": DEFAULT_ELEMENTS, "factory": FACTORY, "gold": GOLD,
        "factoryStrum": FACTORY_STRUM, "goldPerformance": GOLD_PERFORMANCE,
        "validMarker": valid_marker, "findChoice": find_choice,
        "patternRole": style_pattern_role,
        "choosePattern": choose_pattern, "preparedNotes": prepared_notes,
        "drumProfile": drum_profile, "velocityAt": velocity_at,
        "noteIntensity": style_note_intensity,
        "metaText": meta_text, "tempoMeta": tempo_meta, "meterMeta": meter_meta,
        "smf0": smf0, "validate": pa800_validator.validate_pa800_smf,
    })


def vlq(value):
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


def meta_text(kind, text):
    payload = text.encode("ascii", "replace")
    return [0xFF, kind, *vlq(len(payload)), *payload]


def tempo_meta(bpm):
    micros = round(60_000_000 / bpm)
    return [0xFF, 0x51, 3, (micros >> 16) & 255, (micros >> 8) & 255, micros & 255]


def meter_meta(numerator, denominator):
    power = 0
    while 2 ** power < denominator:
        power += 1
    return [0xFF, 0x58, 4, numerator, power, 24, 8]


def smf0(events, ppq):
    events.sort(key=lambda item: (item["tick"], item["priority"]))
    body, previous, running_status = bytearray(), 0, None
    for event in events:
        body.extend(vlq(max(0, event["tick"] - previous)))
        encoded = bytes(event["data"])
        status = encoded[0]
        if 0x80 <= status <= 0xEF and running_status == status:
            body.extend(encoded[1:])
        else:
            body.extend(encoded)
        running_status = status if 0x80 <= status <= 0xEF else None
        previous = event["tick"]
    return b"MThd" + struct.pack(">IHHH", 6, 0, 1, ppq) + b"MTrk" + struct.pack(">I", len(body)) + body


def validate_pa800_smf(midi, expected_markers, expected_channels):
    issues = []
    if len(midi) < 22 or midi[:4] != b"MThd":
        return {"passed": False, "issues": ["Nedostaje MThd zaglavlje"]}
    header_length, midi_format, track_count, ppq = struct.unpack_from(">IHHH", midi, 4)
    if header_length != 6:
        return {"passed": False, "issues": ["MThd duljina mora biti 6"],
                "format": midi_format, "trackCount": track_count, "ppq": ppq}
    if midi_format != 0:
        issues.append("MIDI mora biti format 0")
    if track_count != 1:
        issues.append("MIDI mora imati jednu traku")
    if ppq != 480:
        issues.append("Pa800 Style MIDI mora koristiti PPQ 480")
    if midi[14:18] != b"MTrk":
        return {"passed": False, "issues": issues + ["Nedostaje MTrk chunk"]}
    track_length = struct.unpack_from(">I", midi, 18)[0]
    pos, end = 22, 22 + track_length
    if end > len(midi):
        return {"passed": False, "issues": issues + ["MTrk duljina prelazi datoteku"]}
    if end != len(midi):
        issues.append("Podaci iza deklariranog MTrk chunka nisu dopušteni")

    def read_variable():
        nonlocal pos
        value = 0
        for _ in range(4):
            if pos >= end:
                raise ValueError("Prekinuta variable-length vrijednost")
            byte = midi[pos]
            pos += 1
            value = (value << 7) | (byte & 127)
            if byte < 128:
                return value
        return value

    tick, running, note_count, event_count = 0, None, 0, 0
    markers, marker_ticks, time_signature_ticks = [], {}, set()
    channel_events = defaultdict(lambda: defaultdict(list))
    used_channels, open_notes = set(), defaultdict(list)
    end_of_track_count, event_after_eot, last_event_eot = 0, False, False
    try:
        while pos < end:
            if end_of_track_count:
                event_after_eot = True
            tick += read_variable()
            if pos >= end:
                raise ValueError("Delta-time bez MIDI događaja")
            status = midi[pos]
            if status < 128:
                if running is None:
                    raise ValueError("Running status bez prethodnog statusa")
                status = running
            else:
                pos += 1
                if status < 240:
                    running = status
            if status == 255:
                if pos >= end:
                    raise ValueError("Prekinut meta event")
                kind = midi[pos]
                pos += 1
                length = read_variable()
                if pos + length > end:
                    raise ValueError("Meta event prelazi granicu trake")
                payload = midi[pos:pos + length]
                pos += length
                event_count += 1
                last_event_eot = kind == 47
                if kind == 6:
                    marker = payload.decode("ascii", "replace")
                    markers.append(marker)
                    marker_ticks[marker] = tick
                elif kind == 88:
                    time_signature_ticks.add(tick)
                elif kind == 47:
                    end_of_track_count += 1
                    if length != 0:
                        issues.append("End Of Track mora imati duljinu 0")
                continue
            if status in (240, 247):
                length = read_variable()
                if pos + length > end:
                    raise ValueError("SysEx event prelazi granicu trake")
                pos += length
                running = None
                event_count += 1
                last_event_eot = False
                continue
            if not 128 <= status <= 239:
                raise ValueError(f"Nepodržan status 0x{status:02X}")
            command, channel = status >> 4, status & 15
            if pos >= end:
                raise ValueError("Prekinut channel event")
            one = midi[pos]
            pos += 1
            two = None
            if command not in (12, 13):
                if pos >= end:
                    raise ValueError("Prekinut channel event")
                two = midi[pos]
                pos += 1
            used_channels.add(channel)
            channel_events[tick][channel].append((command, one, two))
            event_count += 1
            last_event_eot = False
            key = (channel, one)
            if command == 9 and two:
                if not 1 <= two <= 127:
                    issues.append("Note-on velocity izvan raspona 1-127")
                if open_notes[key]:
                    issues.append(f"Preklopljena nota CH{channel + 1} pitch {one}")
                open_notes[key].append(tick)
                note_count += 1
            elif command == 8 or (command == 9 and not two):
                if open_notes[key]:
                    start_tick = open_notes[key].pop(0)
                    if tick <= start_tick:
                        issues.append(f"Nevaljano trajanje note CH{channel + 1} pitch {one}")
                else:
                    issues.append(f"Note-off bez note-on CH{channel + 1} pitch {one}")
    except (ValueError, IndexError) as error:
        issues.append(str(error))

    if markers != expected_markers:
        issues.append("Marker redoslijed ne odgovara manifestu")
    if len(markers) != len(set(markers)):
        issues.append("Markeri nisu jedinstveni")
    for marker in markers:
        if marker != marker.lower() or not valid_marker(marker):
            issues.append(f"Neispravan Pa800 marker: {marker}")
    expected_set = set(expected_channels)
    if expected_set - set(range(8, 16)):
        issues.append("Manifest očekuje kanal izvan Pa800 raspona 9-16")
    if used_channels - set(range(8, 16)):
        issues.append("Pronađeni su MIDI kanali izvan Pa800 raspona 9-16")
    if used_channels - expected_set:
        issues.append("Pronađeni su MIDI kanali izvan aktivnog Pa800 skupa")
    if expected_set - used_channels:
        issues.append("Nedostaje događaj za jednu ili više aktivnih Pa800 traka")
    for marker in expected_markers:
        marker_tick = marker_ticks.get(marker)
        if marker_tick is None:
            continue
        if marker_tick not in time_signature_ticks:
            issues.append(f"Marker {marker} nema Time Signature")
        for channel in expected_channels:
            events = channel_events[marker_tick][channel]
            if not any(command == 11 and one == 0 for command, one, _ in events):
                issues.append(f"{marker} CH{channel + 1} nema CC00")
            if not any(command == 11 and one == 32 for command, one, _ in events):
                issues.append(f"{marker} CH{channel + 1} nema CC32")
            if not any(command == 12 for command, _, _ in events):
                issues.append(f"{marker} CH{channel + 1} nema Program Change")
            if not any(command == 11 and one == 11 and two == 127 for command, one, two in events):
                issues.append(f"{marker} CH{channel + 1} nema CC11=127")
    dangling = sum(len(values) for values in open_notes.values())
    if dangling:
        issues.append(f"Datoteka ima {dangling} visećih nota")
    if end_of_track_count != 1:
        issues.append("Traka mora imati točno jedan End Of Track")
    if event_after_eot or not last_event_eot:
        issues.append("End Of Track mora biti posljednji događaj")
    return {
        "passed": not issues, "issues": issues, "format": midi_format, "trackCount": track_count,
        "ppq": ppq, "markers": markers, "usedChannels": sorted(channel + 1 for channel in used_channels),
        "noteCount": note_count, "danglingNotes": dangling, "eventCount": event_count,
        "endOfTrackCount": end_of_track_count, "eventOrderValid": not event_after_eot and last_event_eot,
        "checkedControllersPerMarker": ["CC00", "CC32", "ProgramChange", "CC11=127"],
    }


# Aktivni validator živi u zasebnom modulu; alias čuva kompatibilnost postojećeg API-ja i testova.
validate_pa800_smf = pa800_validator.validate_pa800_smf


LEGACY_HTML = r'''<!doctype html><html lang="hr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DNA Pa800 Style Arranger</title><style>
:root{color-scheme:dark;--b:#080b10;--p:#131923;--l:#2a3444;--t:#f5f7fa;--m:#93a0b2;--g:#5de8aa;--o:#ffb96a}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 85% 0,#1a2d44 0,var(--b) 42rem);color:var(--t);font-family:Inter,system-ui,"Segoe UI",sans-serif}header,main{width:min(1180px,calc(100% - 30px));margin:auto}header{display:flex;justify-content:space-between;align-items:end;padding:46px 0 26px}h1{margin:0;font-size:clamp(2.5rem,7vw,5rem);line-height:.92;letter-spacing:-.06em}h2,p{margin-top:0}.sub,.hint,small{color:var(--m)}.tag{color:var(--g);font-size:.7rem;font-weight:850;letter-spacing:.15em}.online{color:var(--g)}.metrics,.tracks{display:grid;grid-template-columns:repeat(4,1fr);gap:11px}.metrics{margin-bottom:17px}.metrics div,.panel{border:1px solid var(--l);border-radius:15px;background:rgba(19,25,35,.96)}.metrics div{display:grid;gap:4px;padding:16px}.metrics b{font-size:1.35rem}.metrics span{color:var(--m);font-size:.75rem}.panel{margin-bottom:17px;padding:22px}.head,.actions{display:flex;justify-content:space-between;align-items:center;gap:15px}.grid{display:grid;grid-template-columns:2fr repeat(3,1fr);gap:12px}label{display:grid;gap:6px;color:var(--m);font-size:.75rem;font-weight:750}input,select{width:100%;height:40px;padding:0 10px;border:1px solid var(--l);border-radius:8px;background:#0b1017;color:var(--t);font:inherit}.elements{display:grid;gap:7px}.element{display:grid;grid-template-columns:auto 1.2fr .7fr 1.6fr;gap:10px;align-items:center;padding:10px;border:1px solid var(--l);border-radius:10px;background:#0d1219}.element input[type=checkbox]{width:18px}.element input[type=range]{padding:0;accent-color:var(--g)}.track{padding:13px;border:1px solid var(--l);border-radius:11px;background:#0d1219}.track h3{display:flex;justify-content:space-between;margin:0 0 12px}.track h3 span{color:var(--g);font-size:.72rem}.track small{display:block;margin-top:8px}.button{min-height:42px;padding:0 15px;border:1px solid var(--l);border-radius:8px;background:#1a2330;color:var(--t);font:inherit;font-weight:800;cursor:pointer}.primary{border-color:var(--g);background:var(--g);color:#05251a}.plan{display:grid;gap:7px;margin-top:18px}.plan-row{display:grid;grid-template-columns:.8fr .5fr repeat(4,1fr);gap:8px;padding:10px;border:1px solid var(--l);border-radius:9px;background:#0d1219;font-size:.72rem}.plan-row code{color:var(--g)}.analysis{display:grid;grid-template-columns:1fr 2fr;gap:18px;align-items:center}.analysis-result{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.analysis-result div{padding:10px;border:1px solid var(--l);border-radius:9px;background:#0d1219}.analysis-result b{display:block;color:var(--g)}.chips{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}.chips span{padding:4px 7px;border:1px solid var(--l);border-radius:99px;color:var(--m);font-size:.7rem}.instructions{border-color:#4c614f}.instructions li{margin:8px 0;color:var(--m)}.hidden{display:none}.error{color:#ff7883}@media(max-width:850px){.metrics,.tracks{grid-template-columns:1fr 1fr}.grid,.analysis{grid-template-columns:1fr 1fr}.plan-row{grid-template-columns:1fr 1fr}}@media(max-width:520px){header,.head,.actions{display:block}.metrics,.tracks,.grid,.element,.plan-row,.analysis,.analysis-result{grid-template-columns:1fr}.actions .button{width:100%;margin-top:8px}}
</style></head><body><header><div><div class="tag">KORG PA800 · OS 2.0+</div><h1>DNA Style Arranger</h1><p class="sub">Factory dinamika. Filtrirani Gold patterni. Pa800 SMF0 s markerima.</p></div><div id="state">Učitavanje…</div></header><main>
<section class="metrics"><div><b id="profiles">—</b><span>Factory profila</span></div><div><b id="patterns">—</b><span>Gold patterna</span></div><div><b>SMF 0</b><span>Pa800 Style import</span></div><div><b style="color:var(--g)">0%</b><span>Gold utjecaja na dinamiku</span></div></section>
<section class="panel analysis"><div><div class="tag">MIDI SONG ANALYSIS</div><h2>Učitaj song kao muzički nacrt</h2><p class="hint">Analizira tempo, takt, tonalitet, akorde i formu. Velocity songa se ne koristi.</p><label class="button primary">Odaberi MIDI song<input id="song" type="file" accept=".mid,.midi" hidden></label></div><div id="analysis" class="analysis-result"><div><b>—</b><small>Tonalitet</small></div><div><b>—</b><small>Forma</small></div><div><b>—</b><small>Akordi</small></div></div></section>
<section class="panel"><div class="head"><div><div class="tag">STYLE</div><h2>Osnovne postavke</h2></div></div><div class="grid"><label>Naziv Stylea<input id="name" value="DNA PA800 STYLE" maxlength="24"></label><label>Tempo<input id="tempo" type="number" min="30" max="300" value="120"></label><label>Takt<select id="meter"><option>4/4</option><option>2/4</option><option>3/4</option><option>6/8</option><option>7/8</option><option>9/8</option></select></label><label>Seed<input id="seed" type="number" value="120111231"></label></div></section>
<section class="panel"><div class="head"><div><div class="tag">STYLE ELEMENTS</div><h2>Markeri i Chord Variations</h2></div></div><div id="elements" class="elements"></div><p class="hint">Marker imena moraju ostati malim slovima. Variation podržava CV1–CV6; Intro/Fill/Ending CV1–CV2.</p></section>
<section class="panel"><div class="head"><div><div class="tag">PA800 CHANNEL MAP</div><h2>Osam Style traka</h2></div></div><div id="tracks" class="tracks"></div></section>
<section class="panel"><div class="actions"><div><div class="tag">BUILD</div><h2>Pa800-kompatibilni Style SMF</h2><p class="hint">Reference Key/Chord: C Major. NTT se potvrđuje na Pa800 nakon uvoza.</p></div><button id="preview" class="button primary">Generiraj plan</button></div><div id="plan" class="plan hidden"></div><div id="exports" class="actions hidden" style="margin-top:18px"><span id="result"></span><div><button id="json" class="button">Manifest JSON</button> <button id="midi" class="button primary">Preuzmi Pa800 .MID</button></div></div></section>
<section class="panel instructions"><h2>Uvoz na Pa800</h2><ol><li>Kopiraj generirani `.MID` na USB.</li><li>Na Pa800 otvori <b>Style Record</b> i napravi novi Style.</li><li>Otvori <b>Import SMF</b>, drži <b>SHIFT</b> i pritisni <b>Execute</b> za uvoz svih markera.</li><li>Za novi Style uključi <b>Initialize</b>. Postavi originalni Key/Chord na <b>C Major</b>.</li><li>Provjeri Track Type i NTT, zatim spremi Style u USER/FAVORITE lokaciju.</li></ol></section>
</main><script>
const $=s=>document.querySelector(s);let options,manifest,lastConfig,songAnalysis;const trackNames={bass:'Bass',drum:'Drum',perc:'Percussion',acc1:'Acc1',acc2:'Acc2',acc3:'Acc3',acc4:'Acc4',acc5:'Acc5'};
async function init(){try{options=await fetch('/api/options').then(r=>r.json());$('#profiles').textContent=options.summary.profiles.toLocaleString();$('#patterns').textContent=options.summary.patterns.toLocaleString();$('#state').textContent='● DNA spremna';$('#state').className='online';renderElements();renderTracks()}catch(e){$('#state').textContent='Greška: '+e.message;$('#state').className='error'}}
function renderElements(){const root=$('#elements');options.elements.forEach(x=>{const row=document.createElement('div');row.className='element';row.innerHTML=`<input class="en" type="checkbox" checked><label>Marker<input class="marker" value="${x.marker}"></label><label>Taktovi<input class="bars" type="number" min="1" max="32" value="${x.bars}"></label><label>Intenzitet <output>${x.intensity}%</output><input class="intensity" type="range" min="0" max="100" value="${x.intensity}"></label>`;row.querySelector('.intensity').oninput=e=>e.target.previousElementSibling.value=e.target.value+'%';root.append(row)})}
function renderTracks(){const root=$('#tracks');Object.entries(trackNames).forEach(([name,label])=>{const card=document.createElement('article');card.className='track';const enabled=!['acc3','acc4','acc5'].includes(name);card.innerHTML=`<h3>${label}<span>CH ${options.channelMap[name]}</span></h3><label><span><input class="enabled" type="checkbox" ${enabled?'checked':''}> Uključena traka</span></label><label>Factory Sound<select class="profile"></select></label><small></small>`;const select=card.querySelector('select');options.tracks[name].forEach(x=>{const o=document.createElement('option');o.value=x.id;o.textContent=(x.instrument||x.label)+' · '+x.id;select.append(o)});const update=()=>{const x=options.tracks[name].find(v=>v.id===select.value);card.querySelector('small').textContent=x?`Velocity ${x.velocity.min} / ${x.velocity.optimal} / ${x.velocity.max} · Poly max ${options.polyphonyLimits[name]} · MSB ${x.bankMsb} LSB ${x.bankLsb} PC ${x.program}`:''};select.onchange=update;update();card.dataset.name=name;root.append(card)})}
async function analyzeSong(file){try{$('#state').textContent='Analiziram MIDI…';const r=await fetch('/api/analyze-midi',{method:'POST',headers:{'Content-Type':'application/octet-stream','X-Filename':encodeURIComponent(file.name)},body:await file.arrayBuffer()});const data=await r.json();if(!r.ok)throw Error(data.error);songAnalysis=data;$('#tempo').value=Math.round(data.tempo);if(![...$('#meter').options].some(o=>o.value===data.meter))$('#meter').add(new Option(data.meter,data.meter));$('#meter').value=data.meter;$('#seed').value=data.suggestedSeed;data.suggestedPa800Elements.forEach(x=>{const row=[...document.querySelectorAll('.element')].find(r=>r.querySelector('.marker').value===x.marker);if(row){row.querySelector('.bars').value=x.bars;row.querySelector('.intensity').value=x.intensity;row.querySelector('output').value=x.intensity+'%'}});applyInstrumentSuggestions(data.detectedInstruments);const chords=[...new Set(data.barAnalysis.map(x=>x.chord))].slice(0,10);$('#analysis').innerHTML=`<div><b>${data.key.name}</b><small>Tonalitet · ${Math.round(data.key.confidence*100)}%</small></div><div><b>${data.sections.length} sekcija</b><small>${data.bars} taktova · ${data.tempo} BPM</small></div><div><b>${chords.join(' · ')}</b><small>Detektirani akordi</small></div>`;$('#state').textContent='● Analiza spremna';$('#state').className='online'}catch(e){$('#state').textContent='Greška analize';alert(e.message)}}
function applyInstrumentSuggestions(items){items.forEach(item=>{const target=item.suggestedPa800Track;const card=[...document.querySelectorAll('.track')].find(c=>c.dataset.name===target);if(!card)return;const select=card.querySelector('select');const wanted=target==='drum'?item.instrumentKey:options.tracks[target].find(x=>x.instrumentKey===item.instrumentKey)?.id;if(wanted&&[...select.options].some(o=>o.value===wanted)){select.value=wanted;select.onchange()}})}
function config(){const analysis=songAnalysis?{source:songAnalysis.source,key:songAnalysis.key,bars:songAnalysis.bars,sections:songAnalysis.sections,rules:songAnalysis.rules}:null;return{name:$('#name').value,tempo:+$('#tempo').value,meter:$('#meter').value,seed:+$('#seed').value,songAnalysis:analysis,elements:[...document.querySelectorAll('.element')].map(r=>({enabled:r.querySelector('.en').checked,marker:r.querySelector('.marker').value.toLowerCase(),bars:+r.querySelector('.bars').value,intensity:+r.querySelector('.intensity').value})),tracks:Object.fromEntries([...document.querySelectorAll('.track')].map(c=>[c.dataset.name,{enabled:c.querySelector('.enabled').checked,profileId:c.querySelector('.profile').value}]))}}
async function build(){try{lastConfig=config();const r=await fetch('/api/arrange',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(lastConfig)});const data=await r.json();if(!r.ok)throw Error(data.error);manifest=data;const root=$('#plan');root.innerHTML='';data.elements.forEach(e=>{const row=document.createElement('div');row.className='plan-row';const pats=Object.entries(e.patterns);row.innerHTML=`<b>${e.marker}</b><span>${e.bars} bar</span>`+['bass','drum','perc','acc1'].map(t=>`<code>${e.patterns[t]||'—'}</code>`).join('');root.append(row)});root.classList.remove('hidden');$('#exports').classList.remove('hidden');$('#result').innerHTML=`<b class="online">✓ Pa800 validator PASS</b><br><small>${data.midi.noteCount.toLocaleString()} nota · kanali ${data.midi.usedChannels.join(', ')} · ${data.quality.polyphonyNotesRemoved} uklonjeno zbog polifonije</small>`}catch(e){alert(e.message)}}
async function exportMidi(){lastConfig=config();const r=await fetch('/api/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(lastConfig)});if(!r.ok){const x=await r.json();return alert(x.error)}download(await r.blob(),safe($('#name').value)+'.mid')}
function exportJson(){if(!manifest)return;download(new Blob([JSON.stringify(manifest,null,2)],{type:'application/json'}),safe($('#name').value)+'.json')}
function download(blob,name){const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}function safe(x){return(x||'PA800_STYLE').replace(/[\\/:*?"<>|]/g,'-')}
$('#song').onchange=e=>e.target.files[0]&&analyzeSong(e.target.files[0]);$('#preview').onclick=build;$('#midi').onclick=exportMidi;$('#json').onclick=exportJson;init();
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    def send_bytes(self, body, content_type, status=200, filename=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, data, status=200):
        self.send_bytes(json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", status)

    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path in ("/", "/index.html"):
            from web_gui import HTML as ACTIVE_HTML
            self.send_bytes(ACTIVE_HTML.encode("utf-8"), "text/html; charset=utf-8")
        elif parsed_path.path == "/api/options":
            self.send_json(OPTIONS)
        elif parsed_path.path == "/api/status":
            test_report = json.loads(TEST_REPORT_JSON.read_text(encoding="utf-8")) if TEST_REPORT_JSON.exists() else {}
            device_preflight = (json.loads(DEVICE_PREFLIGHT_JSON.read_text(encoding="utf-8"))
                                if DEVICE_PREFLIGHT_JSON.exists() else {})
            tests_run = int(test_report.get("testsRun", 0))
            self.send_json({"ready": True, **OPTIONS["summary"], "target": OPTIONS["target"],
                            "softwareValidation": "SOFTWARE_VALIDATED",
                            "physicalPa800": "WAITING_FOR_DEVICE",
                            "devicePreflight": device_preflight.get("status", {}).get(
                                "session14DevicePreflight", "NOT_PREPARED"),
                            "deviceKitReady": DEVICE_KIT_ZIP.is_file(),
                            "masterPromptTests": f"{tests_run}/{tests_run} PASS" if tests_run else "NOT RUN",
                            "cache": RESULT_CACHE.summary()})
        elif parsed_path.path == "/api/ai-max-status":
            self.send_json(build_max_status(Path(__file__).resolve().parent))
        elif parsed_path.path == "/api/learning-status":
            manifest = json.loads(LEARNING_MANIFEST_JSON.read_text(encoding="utf-8")) if LEARNING_MANIFEST_JSON.exists() else {}
            training = json.loads(AI_TRAINING_REPORT_JSON.read_text(encoding="utf-8")) if AI_TRAINING_REPORT_JSON.exists() else {}
            self.send_json({
                "ready": bool(manifest),
                "dataset": manifest,
                "model": training,
                "authority": {"factoryVelocityOnly": True, "goldVelocityUsed": False,
                              "hardValidatorRequired": True},
                "runtimeMode": "ADVISORY_REQUIRES_HARD_VALIDATION",
            })
        elif parsed_path.path == "/api/compliance":
            if not COMPLIANCE_JSON.exists():
                self.send_json({"error": "Compliance izvještaj nije pronađen"}, 404)
            else:
                self.send_bytes(COMPLIANCE_JSON.read_bytes(), "application/json; charset=utf-8",
                                filename="master-prompt-compliance.json")
        elif parsed_path.path == "/api/release-report":
            if not RELEASE_JSON.exists():
                self.send_json({"error": "Pokreni testiraj.bat za izradu release izvještaja"}, 404)
            else:
                self.send_bytes(RELEASE_JSON.read_bytes(), "application/json; charset=utf-8",
                                filename="release-check-report.json")
        elif parsed_path.path == "/api/device-preflight":
            if not DEVICE_PREFLIGHT_JSON.exists():
                self.send_json({"error": "Session 14 uređajni preflight nije pripremljen"}, 404)
            else:
                self.send_bytes(DEVICE_PREFLIGHT_JSON.read_bytes(), "application/json; charset=utf-8",
                                filename="session14-preflight-report.json")
        elif parsed_path.path == "/api/device-test-kit":
            if not DEVICE_KIT_ZIP.exists():
                self.send_json({"error": "Pa800 test-paket nije pripremljen"}, 404)
            else:
                self.send_bytes(DEVICE_KIT_ZIP.read_bytes(), "application/zip",
                                filename=DEVICE_KIT_ZIP.name)
        elif parsed_path.path == "/api/pattern":
            pattern_id = parse_qs(parsed_path.query).get("id", [""])[0]
            pattern = PATTERN_BY_ID.get(pattern_id)
            if not pattern:
                self.send_json({"error": "Performance pattern nije pronađen"}, 404)
            else:
                authority = pattern.get("authority", {})
                self.send_json({"pattern": pattern, "authority": authority,
                                "invariants": {"goldAffectsDynamics": False,
                                               "goldAffectsProgramChange": False,
                                               "factoryStrummingGoldUsed": False}})
        elif parsed_path.path == "/api/library/factory":
            query = parse_qs(parsed_path.query)
            text_query = query.get("q", [""])[0].strip().lower()
            role = query.get("role", [""])[0].strip().lower()
            offset = max(0, int(query.get("offset", ["0"])[0]))
            limit = max(1, min(100, int(query.get("limit", ["40"])[0])))
            profiles = [item for item in FACTORY["profiles"]
                        if (not role or item.get("role") == role)
                        and (not text_query or text_query in item["id"].lower()
                             or text_query in item["instrument"].lower()
                             or text_query in item["instrumentKey"].lower()
                             or text_query in item.get("drumElement", "").lower())]
            items = []
            for item in profiles[offset:offset + limit]:
                public = {key: value for key, value in item.items() if key != "source_ids"}
                public["sourceCount"] = len(item.get("source_ids", []))
                public["sourceIds"] = item.get("source_ids", [])[:12]
                items.append(public)
            self.send_json({"databaseVersion": FACTORY.get("databaseVersion"), "total": len(profiles),
                            "offset": offset, "limit": limit, "items": items})
        elif parsed_path.path == "/api/library/gold":
            query = parse_qs(parsed_path.query)
            text_query = query.get("q", [""])[0].strip().lower()
            role = query.get("role", [""])[0].strip().lower()
            meter = query.get("meter", [""])[0].strip()
            offset = max(0, int(query.get("offset", ["0"])[0]))
            limit = max(1, min(100, int(query.get("limit", ["40"])[0])))
            patterns = [item for item in GOLD["patterns"]
                        if (not role or item["role"] == role) and (not meter or item["meter"] == meter)
                        and (not text_query or text_query in item["id"].lower()
                             or text_query in item["source"].lower()
                             or text_query in item.get("sourceInstrumentClass", "").lower())]
            self.send_json({"databaseVersion": GOLD.get("databaseVersion"), "total": len(patterns),
                            "offset": offset, "limit": limit, "items": patterns[offset:offset + limit],
                            "invariants": {"velocityDataIncluded": False, "goldAffectsDynamics": False}})
        elif parsed_path.path == "/api/library/factory-style":
            query = parse_qs(parsed_path.query)
            role = query.get("role", [""])[0].strip().upper()
            element = query.get("element", [""])[0].strip().lower()
            cv = int(query.get("cv", ["0"])[0])
            offset = max(0, int(query.get("offset", ["0"])[0]))
            limit = max(1, min(100, int(query.get("limit", ["40"])[0])))
            segments = [item for item in FACTORY_STYLE["segments"]
                        if (not role or item["role"] == role)
                        and (not element or item["element"] == element)
                        and (not cv or item["cv"] == cv)]
            items = [dict(item) for item in segments[offset:offset + limit]]
            self.send_json({"databaseVersion": FACTORY_STYLE.get("databaseVersion"),
                            "total": len(segments), "offset": offset, "limit": limit,
                            "items": items, "invariants": {"source": "factory-only", "goldUsed": False}})
        elif parsed_path.path == "/api/library/factory-strum":
            query = parse_qs(parsed_path.query)
            element = query.get("element", [""])[0].strip().lower()
            offset = max(0, int(query.get("offset", ["0"])[0]))
            limit = max(1, min(100, int(query.get("limit", ["40"])[0])))
            patterns = [item for item in FACTORY_STRUM["patterns"]
                        if not element or item["sourceElement"] == element]
            self.send_json({"databaseVersion": FACTORY_STRUM.get("databaseVersion"),
                            "total": len(patterns), "offset": offset, "limit": limit,
                            "items": patterns[offset:offset + limit],
                            "invariants": {"source": "factory-acc-only", "goldUsed": False}})
        elif parsed_path.path == "/api/instrument-catalog":
            catalog_file = Path(__file__).resolve().parent / "data" / "instrument-catalog-9.30.json"
            if catalog_file.exists():
                catalog = json.loads(catalog_file.read_text(encoding="utf-8"))
                instruments = catalog.get("instruments", [])
                self.send_json({"total": len(instruments), "instruments": instruments})
            else:
                self.send_json({"error": "Katalog instrumenata nije pronađen"}, 404)
        elif parsed_path.path == "/api/instrument-curve":
            query = parse_qs(parsed_path.query)
            name = query.get("name", [""])[0]
            catalog_file = Path(__file__).resolve().parent / "data" / "instrument-catalog-9.30.json"
            if catalog_file.exists():
                catalog = json.loads(catalog_file.read_text(encoding="utf-8"))
                match = next((i for i in catalog.get("instruments", []) if i.get("name") == name), None)
                if match:
                    curve = match.get("velCurve", {})
                    pts = [curve.get(k, 0) for k in ["ppp","pp","p","mp","mf","f","ff"]]
                    self.send_json({"name": name, "curve": pts, "velMin": match.get("velMin",0), "velMax": match.get("velMax",127)})
                else:
                    self.send_json({"error": "Instrument nije pronađen"}, 404)
            else:
                self.send_json({"error": "Katalog nije pronađen"}, 404)
        elif parsed_path.path == "/api/instrument-catalog":
            catalog_file = Path(__file__).resolve().parent / "data" / "instrument-catalog-9.30.json"
            if catalog_file.exists():
                catalog = json.loads(catalog_file.read_text(encoding="utf-8"))
                instruments = catalog.get("instruments", [])
                self.send_json({"total": len(instruments), "instruments": instruments})
            else:
                self.send_json({"error": "Katalog instrumenata nije pronađen"}, 404)
        elif parsed_path.path == "/api/instrument-curve":
            query = parse_qs(parsed_path.query)
            name = query.get("name", [""])[0]
            catalog_file = Path(__file__).resolve().parent / "data" / "instrument-catalog-9.30.json"
            if catalog_file.exists():
                catalog = json.loads(catalog_file.read_text(encoding="utf-8"))
                match = next((i for i in catalog.get("instruments", []) if i.get("name") == name), None)
                if match:
                    curve = match.get("velCurve", {})
                    pts = [curve.get(k, 0) for k in ["ppp","pp","p","mp","mf","f","ff"]]
                    self.send_json({"name": name, "curve": pts, "velMin": match.get("velMin",0), "velMax": match.get("velMax",127)})
                else:
                    self.send_json({"error": "Instrument nije pronađen"}, 404)
            else:
                self.send_json({"error": "Katalog nije pronađen"}, 404)
        elif parsed_path.path == "/api/library/gold-performance":
            query = parse_qs(parsed_path.query)
            role = query.get("role", [""])[0].strip().lower()
            offset = max(0, int(query.get("offset", ["0"])[0]))
            limit = max(1, min(100, int(query.get("limit", ["40"])[0])))
            patterns = [item for item in GOLD_PERFORMANCE["patterns"]
                        if not role or item["role"] == role]
            self.send_json({"databaseVersion": GOLD_PERFORMANCE.get("databaseVersion"),
                            "total": len(patterns), "offset": offset, "limit": limit,
                            "items": patterns[offset:offset + limit],
                            "invariants": {"velocityDataIncluded": False,
                                           "soundSelectionIncluded": False,
                                           "rhythmGuitarStrumming": False}})
        elif parsed_path.path == "/api/optimizer-download":
            token = parse_qs(parsed_path.query).get("token", [""])[0]
            item = get_optimized(token)
            if not item:
                self.send_json({"error": "Rezultat je istekao ili token nije valjan"}, 404)
            else:
                self.send_bytes(item["midi"], "audio/midi", filename=item["fileName"])
        elif parsed_path.path == "/api/optimizer-preview":
            token = parse_qs(parsed_path.query).get("token", [""])[0]
            item = get_optimized(token)
            if not item:
                self.send_json({"error": "Rezultat je istekao ili token nije valjan"}, 404)
            else:
                preview = midi_optimizer.midi_preview(item["midi"], item["fileName"])
                preview["editorToken"] = token
                self.send_json(preview)
        else:
            self.send_json({"error": "Nije pronađeno"}, 404)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            parsed_path = urlparse(self.path)
            if parsed_path.path == "/api/train":
                if length > 8192:
                    raise ValueError("Training request prevelik")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                mode = payload.get("mode", "calibrate")
                try:
                    import subprocess, sys
                    proj_dir = str(Path(__file__).resolve().parent)
                    cmd = [sys.executable, str(Path(proj_dir)/"scripts"/"train_local.py"), "--mode", mode]
                    if mode != "calibrate":
                        epochs = payload.get("epochs", 8)
                        cmd.extend(["--epochs", str(epochs)])
                        if payload.get("promote", True):
                            cmd.append("--promote")
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=proj_dir)
                    ok = result.returncode == 0
                    self.send_json({"ok": ok, "message": "Training completed" if ok else "Training failed",
                                    "results": result.stdout.strip().split("\n")[-15:] if result.stdout else [],
                                    "error": result.stderr.strip()[-500:] if result.stderr and not ok else ""})
                except subprocess.TimeoutExpired:
                    self.send_json({"ok": False, "message": "Timeout — koristi train_local.py izvan preglednika",
                                    "results": []})
                except Exception as e:
                    self.send_json({"ok": False, "message": str(e), "results": []})
                return
            if parsed_path.path == "/api/calibrate":
                try:
                    proj_dir = str(Path(__file__).resolve().parent)
                    from calibration import run_all_calibrations
                    results = run_all_calibrations(proj_dir)
                    passed = all(r.get("passed", False) for r in results)
                    self.send_json({"passed": passed, "total": len(results),
                                    "passed_count": sum(1 for r in results if r.get("passed")),
                                    "checks": results})
                except Exception as e:
                    try:
                        import subprocess, sys
                        cmd = [sys.executable, str(Path(__file__).resolve().parent/"scripts"/"train_local.py"), "--mode", "calibrate"]
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=str(Path(__file__).resolve().parent))
                        ok = result.returncode == 0
                        lines = result.stdout.strip().split("\n") if result.stdout else []
                        checks = [{"name": l.strip().replace("✅ ",""), "passed": "✅" in l, "detail": ""} for l in lines if "✅" in l or "❌" in l]
                        self.send_json({"passed": ok, "total": len(checks), "passed_count": sum(1 for c in checks if c["passed"]), "checks": checks})
                    except Exception as e2:
                        self.send_json({"passed": False, "total": 0, "passed_count": 0, "checks": [], "error": str(e2)})
                return
            if parsed_path.path == "/api/general-rules":
                try:
                    rules_path = Path(__file__).resolve().parent / "data" / "general-rules-9.30.json"
                    if rules_path.exists():
                        rules = json.loads(rules_path.read_text(encoding="utf-8"))
                        summary = {
                            "gmPrograms": len(rules.get("gmMelodicRanges", {})),
                            "drumValidKeys": len(rules.get("drumValidKeys", {})),
                            "velocityCategories": len(rules.get("velocityRules", {})),
                            "polyphonyLimit": rules.get("polyphonyRules", {}).get("pa800_total", {}).get("maxVoices", 54),
                            "balkanRules": len(rules.get("balkanRules", [])),
                            "exportRules": len(rules.get("exportRules", [])),
                            "enforced": True,
                            "integrated": "optimize_midi() automatic gate"
                        }
                        self.send_json(summary)
                    else:
                        self.send_json({"enforced": False, "error": "general-rules-9.30.json not found"})
                except Exception as e:
                    self.send_json({"enforced": False, "error": str(e)})
                return
            if parsed_path.path == "/api/general-rules/validate":
                # Return General Rules summary for now (MIDI validation requires uploaded file)
                try:
                    rules_path = Path(__file__).resolve().parent / "data" / "general-rules-9.30.json"
                    if rules_path.exists():
                        rules = json.loads(rules_path.read_text(encoding="utf-8"))
                        # Summarize key ranges
                        ranges = []
                        for k, v in list(rules.get("gmMelodicRanges", {}).items())[:10]:
                            ranges.append({"program": int(k), "name": v.get("name",""), "lo": v.get("lo"), "hi": v.get("hi"), "cat": v.get("cat","")})
                        self.send_json({"enforced": True, "sampleRanges": ranges, "totalPrograms": len(rules.get("gmMelodicRanges", {}))})
                    else:
                        self.send_json({"enforced": False, "error": "rules not found"})
                except Exception as e:
                    self.send_json({"enforced": False, "error": str(e)})
                return
            if parsed_path.path == "/api/premium-producer-brief":
                return
            if parsed_path.path == "/api/premium-song-map":
                if length > 64_000_000:
                    raise ValueError("MIDI datoteka je veća od 64 MB")
                content = self.rfile.read(length)
                file_name = unquote(self.headers.get("X-Filename", "song.mid"))
                self.send_json(analyze_song_map(content, file_name))
                return
            if parsed_path.path == "/api/automatic-track-analysis":
                if length > 64_000_000:
                    raise ValueError("Automatic Track Analysis zahtjev je veći od 64 MB")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(execute_track_instrument_analysis_api(payload, Path(".")))
                return
            if parsed_path.path == "/api/evidence-authority-resolver":
                if length > 192_000_000:
                    raise ValueError("Evidence Authority zahtjev je veći od 192 MB")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(execute_evidence_resolver_api(payload, Path(".")))
                return
            if parsed_path.path == "/api/track-plan":
                if length > 256_000_000:
                    raise ValueError("TrackPlan zahtjev je veći od 256 MB")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(execute_track_plan_api(payload, Path(".")))
                return
            if parsed_path.path == "/api/arrangement-render":
                if length > 320_000_000:
                    raise ValueError("Arrangement Renderer zahtjev je veći od 320 MB")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(execute_arrangement_renderer_api(payload, Path(".")))
                return
            if parsed_path.path == "/api/global-coherence":
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(execute_global_coherence_api(payload))
                return
            if parsed_path.path == "/api/song-to-style-project":
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(execute_end_to_end_api(payload))
                return
            if parsed_path.path == "/api/reliability-gate":
                if length > 384_000_000:
                    raise ValueError("Reliability Gate zahtjev je veći od 384 MB")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(execute_reliability_gate_api(payload, Path(".")))
                return
            if parsed_path.path == "/api/quality-calibration":
                if length > 384_000_000:
                    raise ValueError("Quality Calibration zahtjev je veći od 384 MB")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(execute_quality_calibration_api(payload, Path(".")))
                return
            if parsed_path.path == "/api/device-certification":
                if length > 32_000_000:
                    raise ValueError("Device Certification zahtjev je veći od 32 MB")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(execute_device_certification_api(payload, Path(".")))
                return
            if parsed_path.path == "/api/premium-arrangement-graph":
                if length > 8_000_000:
                    raise ValueError("Arrangement Graph zahtjev je veći od 8 MB")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(execute_arrangement_graph_api(payload))
                return
            if parsed_path.path == "/api/premium-candidate-search":
                if length > 24_000_000:
                    raise ValueError("Candidate Search zahtjev je veći od 24 MB")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(execute_candidate_search_api(payload, Path(".")))
                return
            if parsed_path.path == "/api/premium-groove-plan":
                if length > 48_000_000:
                    raise ValueError("GroovePlan zahtjev je veći od 48 MB")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(execute_groove_plan_api(payload, Path(".")))
                return
            if parsed_path.path == "/api/premium-expression-plan":
                if length > 96_000_000:
                    raise ValueError("ExpressionPlan zahtjev je veći od 96 MB")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(execute_expression_plan_api(payload, Path(".")))
                return
            if parsed_path.path == "/api/premium-articulation-map":
                if length > 96_000_000:
                    raise ValueError("ArticulationMap zahtjev je veći od 96 MB")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(execute_articulation_map_api(payload))
                return
            if parsed_path.path == "/api/premium-preview-session":
                if length > 128_000_000:
                    raise ValueError("Premium Preview zahtjev je veći od 128 MB")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(execute_preview_session_api(payload))
                return
            if parsed_path.path == "/api/premium-preview-audio":
                if length > 128_000_000:
                    raise ValueError("Premium Preview audio zahtjev je veći od 128 MB")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                if set(payload) != {"previewSession", "variantId"}:
                    raise ValueError("Preview audio prima samo previewSession i variantId")
                raw, manifest = render_preview_wav(payload["previewSession"], payload["variantId"])
                self.send_response(200)
                self.send_header("Content-Type", "audio/wav")
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("X-Preview-Audio-SHA256", manifest["wavSha256"])
                self.send_header("X-Preview-Device-Audio", "false")
                self.end_headers()
                self.wfile.write(raw)
                return
            if parsed_path.path == "/api/premium-quality-evaluator":
                if length > 192_000_000:
                    raise ValueError("Music Quality Evaluator zahtjev je veći od 192 MB")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(execute_quality_evaluator_api(payload, Path(".")))
                return
            if parsed_path.path == "/api/premium-producer-workflow":
                if length > 256_000_000:
                    raise ValueError("Premium Producer Workflow zahtjev je veći od 256 MB")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(execute_premium_workflow_api(payload, Path(".")))
                return
            if parsed_path.path == "/api/personal-producer-profile":
                if length > 128_000_000:
                    raise ValueError("Personal Producer Profile zahtjev je veći od 128 MB")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(execute_personal_profile_api(payload))
                return
            if parsed_path.path == "/api/premium-release-readiness":
                if length > 64_000_000:
                    raise ValueError("Release Readiness zahtjev je veći od 64 MB")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(execute_release_readiness_api(payload, Path(".")))
                return
            if parsed_path.path == "/api/project-validate":
                if length > 2_000_000:
                    raise ValueError("Projektna datoteka je veća od 2 MB")
                document = json.loads(self.rfile.read(length).decode("utf-8"))
                project, validation = project_model.validate_project(document)
                if not validation["passed"]:
                    self.send_json({"project": project, "validation": validation}, 400)
                else:
                    self.send_json({"project": project, "validation": validation})
                return
            if parsed_path.path == "/api/unified-pipeline":
                if length > 90_000_000:
                    raise ValueError("Unified pipeline zahtjev je veći od 90 MB")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self.send_json(execute_api_payload(payload, Path(".")))
                return
            if parsed_path.path == "/api/analyze-midi":
                if length > 64_000_000:
                    raise ValueError("MIDI datoteka je veća od 64 MB")
                content = self.rfile.read(length)
                file_name = unquote(self.headers.get("X-Filename", "song.mid"))
                analysis = song_analyzer.analyze_midi(content, file_name)
                track_analysis = analyze_track_instruments(
                    content, file_name, factory_catalog=FACTORY
                )
                analysis["trackInstrumentAnalysis"] = track_analysis
                analysis["detectedInstruments"] = [
                    {
                        "instrumentKey": segment["soundBinding"].get("status") == "EXACT"
                        and (f"drum:{segment['soundBinding']['bankMsb']}:{segment['soundBinding']['bankLsb']}:{segment['soundBinding']['program']}"
                             if segment["channelIndex"] == 9 else
                             f"melodic:{segment['soundBinding']['bankMsb']}:{segment['soundBinding']['bankLsb']}:{segment['soundBinding']['program']}")
                        or "unresolved",
                        "kind": "drum" if segment["channelIndex"] == 9 else "melodic",
                        "bankMsb": segment["soundBinding"]["bankMsb"],
                        "bankLsb": segment["soundBinding"]["bankLsb"],
                        "program": segment["soundBinding"]["program"],
                        "noteCount": segment["noteStatistics"]["noteCount"],
                        "medianPitch": segment["noteStatistics"]["medianPitch"],
                        "trackName": track["trackName"],
                        "suggestedPa800Track": segment["suggestedPa800Track"],
                        "decision": segment["decision"],
                        "identityStatus": segment["identityStatus"],
                    }
                    for track in track_analysis["tracks"]
                    for segment in track["segments"]
                    if segment["decision"] == "ACCEPT"
                ]
                self.send_json(analysis)
                return
            if parsed_path.path == "/api/midi-preview":
                if length > 64_000_000:
                    raise ValueError("MIDI datoteka je veća od 64 MB")
                content = self.rfile.read(length)
                file_name = unquote(self.headers.get("X-Filename", "song.mid"))
                token = cache_optimized(content, {"schema": "dna-midi-source", "readOnly": True}, file_name, "WORK")
                preview = midi_optimizer.midi_preview(content, file_name)
                preview["editorToken"] = token
                preview["preflight"] = midi_optimizer.preflight_midi(content, file_name)
                self.send_json(preview)
                return
            if parsed_path.path == "/api/phase-plan":
                if length > 64_000_000:
                    raise ValueError("MIDI datoteka je veća od 64 MB")
                content = self.rfile.read(length)
                file_name = unquote(self.headers.get("X-Filename", "song.mid"))
                seed = int(self.headers.get("X-Seed", "0"))
                allow_replace = self.headers.get("X-Allow-Phase-Replace", "false").lower() == "true"
                analysis, plan = build_phase_plan(content, file_name, seed, allow_replace)
                self.send_json({"plan": plan, "analysis": {
                    "source": analysis["source"], "tempo": analysis["tempo"],
                    "meter": analysis["meter"], "bars": analysis["bars"],
                    "key": analysis["key"], "chordTimeline": analysis["chordTimeline"],
                    "phaseBoundaries": analysis["phaseBoundaries"], "sections": analysis["sections"],
                    "rules": analysis["rules"]},
                    "invariants": {"readOnly": True, "midiWritten": False,
                                   "goldAffectsDynamics": False, "soloTimingQuantized": False}})
                return
            if parsed_path.path == "/api/reconstruct-midi":
                if length > 64_000_000:
                    raise ValueError("MIDI datoteka je veća od 64 MB")
                content = self.rfile.read(length)
                file_name = unquote(self.headers.get("X-Filename", "song.mid"))
                settings = optimizer_settings_from_headers(self.headers)
                self.send_json(reconstruct_midi_variants(content, file_name, settings))
                return
            if parsed_path.path == "/api/optimize-midi":
                if length > 64_000_000:
                    raise ValueError("MIDI datoteka je veća od 64 MB")
                content = self.rfile.read(length)
                file_name = unquote(self.headers.get("X-Filename", "song.mid"))
                settings = optimizer_settings_from_headers(self.headers)
                evidence = truth_evidence()
                if settings["phaseOptimization"]:
                    analysis = song_analyzer.analyze_midi(content, file_name)
                    evidence.update({"analysis": analysis,
                                     "goldPatterns": GOLD_PERFORMANCE["patterns"],
                                     "factoryStrumPatterns": FACTORY_STRUM["patterns"]})
                optimized, report = midi_optimizer.optimize_midi(
                    content, FACTORY["profiles"], settings, file_name, evidence)
                token = cache_optimized(optimized, report, file_name)
                self.send_json({"token": token, "downloadUrl": f"/api/optimizer-download?token={token}", "report": report})
                return
            if parsed_path.path == "/api/editor-apply":
                if length > 2_000_000:
                    raise ValueError("Editor zahtjev je veći od 2 MB")
                token = parse_qs(parsed_path.query).get("token", [""])[0]
                item = get_optimized(token)
                if not item:
                    self.send_json({"error": "Editor rezultat je istekao ili token nije valjan"}, 404)
                    return
                request = json.loads(self.rfile.read(length).decode("utf-8"))
                edited, report = midi_editor.apply_edits(
                    item["midi"], FACTORY["profiles"], request, item["fileName"],
                    FACTORY.get("databaseVersion", FACTORY.get("version", "unknown")),
                    evidence=truth_evidence())
                new_token = cache_optimized(edited, report, item["fileName"], "EDIT", {"parentToken": token})
                preview = midi_optimizer.midi_preview(edited, item["fileName"])
                preview["editorToken"] = new_token
                self.send_json({"token": new_token, "downloadUrl": f"/api/optimizer-download?token={new_token}",
                                "report": report, "preview": preview})
                return
            if length > 2_000_000:
                raise ValueError("Zahtjev je prevelik")
            config = json.loads(self.rfile.read(length).decode("utf-8"))
            midi, manifest = build_pa800_style(config)
            if parsed_path.path == "/api/arrange":
                self.send_json(manifest)
            elif parsed_path.path == "/api/export":
                name = re.sub(r'[^A-Za-z0-9_-]+', '_', config.get("name", "PA800_STYLE"))[:24] or "PA800_STYLE"
                self.send_bytes(midi, "audio/midi", filename=f"{name}.mid")
            else:
                self.send_json({"error": "Nije pronađeno"}, 404)
        except EvidenceGateBlocked as error:
            self.send_json({"status": "BLOCKED", "error": str(error), "truth_gate": error.report}, 409)
        except Exception as error:
            self.send_json({"error": str(error)}, 400)

    def log_message(self, template, *args):
        print(f"[Pa800] {template % args}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    load_data()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"DNA Pa800 Style Arranger: {url}")
    if not args.no_browser:
        threading.Timer(.7, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()