#!/usr/bin/env python3
"""Run the Session 26 Premium Preview 2.0 software release gate."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import (  # noqa: E402
    compare_device_audio_capture,
    import_device_audio_capture,
    render_preview_wav,
)
from dna_midi_studio.session26_fixture import build_session26_chain  # noqa: E402


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _update_feature_matrix() -> None:
    path = ROOT / "data" / "premium-feature-matrix.json"
    matrix = json.loads(path.read_text(encoding="utf-8"))
    matrix["softwareBaseline"] = "4.4-alpha"
    for feature in matrix["features"]:
        if feature["session"] == 26:
            feature.update({
                "status": "SOFTWARE_VALIDATED / DEVICE_AUDIO_COMPARISON_ONLY",
                "evidence": "data/session26-test-report.json",
                "blocker": "Session 16 physical evidence remains required for Pa800 certification",
                "limitations": [
                    "Built-in GM/Pa800 profiles are deterministic proxy audio, not a physical device claim",
                    "External renderer is manifest-only and cannot affect MIDI, ranking or validator verdict",
                ],
            })
    matrix["premiumProductStatus"] = "PLANNED"
    _write_json(path, matrix)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session26.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    (midi, song_map, groove, expression, articulations, verdict, controls,
     session, wav_bytes, audio_manifest, capture_metadata) = build_session26_chain()
    repeated_wav, repeated_manifest = render_preview_wav(session, "C")
    capture = import_device_audio_capture(wav_bytes, capture_metadata)
    comparison = compare_device_audio_capture(session, "C", capture, audio_manifest)

    artifacts = ROOT / "artifacts"
    paths = {
        "referenceMidi": artifacts / "session26-reference.mid",
        "songMap": artifacts / "session26-song-map.json",
        "groovePlan": artifacts / "session26-groove-plan.json",
        "expressionPlan": artifacts / "session26-expression-plan.json",
        "controls": artifacts / "session26-preview-controls.json",
        "validatorVerdict": artifacts / "session26-validator-verdict.json",
        "previewSession": artifacts / "session26-preview-session.json",
        "proxyWav": artifacts / "session26-variant-c-proxy.wav",
        "audioManifest": artifacts / "session26-audio-manifest.json",
        "deviceCapture": artifacts / "session26-device-audio-capture.json",
        "audioComparison": artifacts / "session26-audio-comparison.json",
    }
    paths["referenceMidi"].write_bytes(midi.to_bytes())
    paths["proxyWav"].write_bytes(wav_bytes)
    for name, value in (("songMap", song_map), ("groovePlan", groove),
                        ("expressionPlan", expression), ("controls", controls),
                        ("validatorVerdict", verdict), ("previewSession", session),
                        ("audioManifest", audio_manifest), ("deviceCapture", capture),
                        ("audioComparison", comparison)):
        _write_json(paths[name], value)
    for index, plan in enumerate(articulations, start=1):
        path = artifacts / f"session26-articulation-plan-{index}.json"
        paths[f"articulationPlan{index}"] = path
        _write_json(path, plan)

    profile_control = dict(controls)
    profile_control["profileId"] = "GM_PROXY_V1"
    from dna_midi_studio import build_preview_session  # local import keeps release imports concise
    changed_profile = build_preview_session(midi, song_map, groove, expression, articulations,
                                            verdict, profile_control)
    gain_control = dict(controls)
    gain_control["masterGainDb"] = -12.0
    changed_gain = build_preview_session(midi, song_map, groove, expression, articulations,
                                         verdict, gain_control)
    benchmark = {
        "schema": "dna-session26-preview-benchmark", "version": "1.0",
        "date": date.today().isoformat(), "license": "self-authored-test-fixtures",
        "sourceMidiSha256": midi.digest(),
        "validatorIdentityHash": session["validatorIdentity"]["identityHash"],
        "previewSessionHash": session["previewSessionHash"],
        "variantNoteCounts": {item["variantId"]: len(item["notes"]) for item in session["variants"]},
        "variantAudibleCounts": {item["variantId"]: item["audibleNoteCount"] for item in session["variants"]},
        "variantPeaks": {item["variantId"]: item["polyphony"]["globalPeak"] for item in session["variants"]},
        "articulationEventCount": session["audit"]["articulationEventCount"],
        "proxyWavSha256": audio_manifest["wavSha256"],
        "proxyDurationSeconds": audio_manifest["durationSeconds"],
        "deviceComparisonHash": comparison["comparisonHash"],
        "deterministicWav": wav_bytes == repeated_wav,
        "deterministicAudioManifest": audio_manifest == repeated_manifest,
        "profileChangePreservedMidiHash": changed_profile["source"]["midiSha256"] == midi.digest(),
        "profileChangePreservedValidatorIdentity": changed_profile["validatorIdentity"] == session["validatorIdentity"],
        "gainChangePreservedMidiHash": changed_gain["source"]["midiSha256"] == midi.digest(),
        "gainChangePreservedValidatorIdentity": changed_gain["validatorIdentity"] == session["validatorIdentity"],
        "deviceCaptureComparisonOnly": capture["comparisonAllowed"] and not capture["certificationAllowed"],
        "softwareMidiNoteCeiling": 54,
        "passed": all((
            session["audit"]["allVariantsWithinMidiNoteCeiling"],
            wav_bytes == repeated_wav, audio_manifest == repeated_manifest,
            changed_profile["validatorIdentity"] == session["validatorIdentity"],
            changed_gain["validatorIdentity"] == session["validatorIdentity"],
            not capture["certificationAllowed"], not comparison["certificationAllowed"],
            not session["midiMutationAllowed"], not session["finalMidiGenerated"],
        )),
    }
    benchmark["benchmarkHash"] = sha256(_canonical({key: value for key, value in benchmark.items()
                                                     if key != "benchmarkHash"})).hexdigest()
    benchmark_path = ROOT / "data" / "session26-benchmark-report.json"
    _write_json(benchmark_path, benchmark)
    if not benchmark["passed"]:
        raise RuntimeError("Session 26 preview benchmark failed")

    schema_paths = [
        ROOT / "premium/schemas/v2/preview-session-v2.schema.json",
        ROOT / "premium/schemas/v2/audio-render-adapter-v1.schema.json",
        ROOT / "premium/schemas/v2/device-audio-capture-v1.schema.json",
    ]
    contracts = []
    for path in schema_paths:
        value = json.loads(path.read_text(encoding="utf-8"))
        contracts.append({"name": path.name, "$id": value["$id"],
                          "contractVersion": value["x-contract-version"],
                          "sha256": sha256(path.read_bytes()).hexdigest()})
    schema_catalog = {"schema": "dna-session26-schema-catalog", "version": "1.0",
                      "date": date.today().isoformat(), "contracts": contracts,
                      "catalogHash": sha256(_canonical(contracts)).hexdigest()}
    schema_catalog_path = ROOT / "data" / "session26-schema-catalog.json"
    _write_json(schema_catalog_path, schema_catalog)
    _update_feature_matrix()

    report = {
        "schema": "dna-session26-test-report", "version": "1.0",
        "date": date.today().isoformat(), "result": "pass",
        "scope": "synchronized-abc-preview-loop-role-mix-polyphony-loudness-proxy-and-device-audio-separation",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures),
                        "errors": len(result.errors)},
        "benchmark": {"report": str(benchmark_path.relative_to(ROOT)),
                      **{key: benchmark[key] for key in (
                          "variantNoteCounts", "variantAudibleCounts", "variantPeaks",
                          "articulationEventCount", "proxyWavSha256", "proxyDurationSeconds",
                          "deterministicWav", "profileChangePreservedValidatorIdentity",
                          "gainChangePreservedValidatorIdentity", "deviceCaptureComparisonOnly",
                          "benchmarkHash")}},
        "artifacts": {name: str(path.relative_to(ROOT)) for name, path in paths.items()}
                     | {"schemaCatalog": str(schema_catalog_path.relative_to(ROOT))},
        "transports": {"cli": "session26_premium_preview.py",
                       "api": "/api/premium-preview-session",
                       "audioApi": "/api/premium-preview-audio",
                       "guiCard": "PREMIUM PREVIEW 2.0", "apiGuiParity": True},
        "invariants": {
            "synchronizedAbcClock": True, "sectionLoop": True,
            "roleSoloMute": True, "oneClickVerifiedBaseline": True,
            "activeNoteTrackChannelUidSoundBindingVisible": True,
            "fullDurationPolyphonyVisible": True, "softwareMidiNoteCeiling": 54,
            "loudnessMethod": "MIDI_ENERGY_RMS_PROXY", "loudnessAffectsMidi": False,
            "profileAffectsMidi": False, "externalRendererManifestOnly": True,
            "apiClientCannotSupplyFinalValidatorVerdict": True,
            "externalCommandExecution": False, "proxyIsDeviceAudio": False,
            "deviceCaptureComparisonOnly": True, "session16CertAuthorityPreserved": True,
            "readOnly": True, "midiMutationAllowed": False, "finalMidiGenerated": False,
        },
        "status": {
            "session26PremiumPreview": "SOFTWARE_VALIDATED / DEVICE_AUDIO_COMPARISON_ONLY",
            "activeSoftwareBaseline": "4.4-alpha", "aiArrangerAlpha": "SOFTWARE_VALIDATED / ALPHA",
            "productionAudioRenderer": "OPTIONAL_MANIFEST_ONLY",
            "pa800AudioCapture": "COMPARISON_READY / CERTIFICATION_BLOCKED",
            "qualityListeningBenchmark": "PENDING_SESSION27",
            "aiPremiumArranger": "PLANNED", "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data/session26-test-report.json"
    _write_json(report_path, report)

    release_path = ROOT / "data/release-check-report.json"
    if release_path.is_file():
        release = json.loads(release_path.read_text(encoding="utf-8"))
        release.setdefault("premiumReadiness", {}).update({
            "softwareBaseline": "4.4-alpha", "session26": f"{result.testsRun}/{result.testsRun} PASS",
            "premiumPreview2": "SOFTWARE_VALIDATED / DEVICE_AUDIO_COMPARISON_ONLY",
            "aiArranger": "ALPHA", "premiumProduct": "PLANNED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(release_path, release)
    compliance_path = ROOT / "data/master-prompt-compliance.json"
    if compliance_path.is_file():
        compliance = json.loads(compliance_path.read_text(encoding="utf-8"))
        compliance.setdefault("summary", {}).update({
            "session26PremiumPreview": f"{result.testsRun}/{result.testsRun} PASS",
            "activeSoftwareBaseline": "4.4-alpha",
            "previewAudio": "PROXY_AND_COMPARISON_ONLY", "aiArranger": "ALPHA",
            "aiPremiumArranger": "PLANNED", "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(compliance_path, compliance)
    print(f"Session 26 PASS: {result.testsRun}/{result.testsRun}; variants={benchmark['variantNoteCounts']}; peak={max(benchmark['variantPeaks'].values())}/54; {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())