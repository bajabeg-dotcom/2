#!/usr/bin/env python3
"""Run Session 17 production-registry adapter release gate."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import dna_builder  # noqa: E402
from dna_midi_studio import (  # noqa: E402
    ChordCell,
    GuitarConfig,
    MidiEvent,
    MidiFile,
    MidiTrack,
    ProductionAdapter,
    execute_pipeline,
)


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _isolated_factory_guitar_segment(adapter: ProductionAdapter) -> tuple[MidiFile, dict]:
    segment = next(
        item for item in adapter.documents["factorySegments"]["segments"]
        if item["source"].endswith("Italian Fox/Italian Fox_Var1.mid")
        and item["trackIndex"] == 3
        and item["role"] == "ACC1"
    )
    evidence = segment["soundEvidence"]
    channel = int(evidence["channel"]) - 1
    events = [
        MidiEvent(0, 0, "channel", 0xB0 | channel, bytes((0, int(evidence["bankMsb"])))),
        MidiEvent(0, 1, "channel", 0xB0 | channel, bytes((32, int(evidence["bankLsb"])))),
        MidiEvent(0, 2, "channel", 0xC0 | channel, bytes((int(evidence["program"]),))),
    ]
    order = 3
    for tick, duration, pitch, velocity in segment["notes"]:
        events.append(MidiEvent(int(tick), order, "channel", 0x90 | channel,
                                bytes((int(pitch), int(velocity)))))
        order += 1
        events.append(MidiEvent(int(tick) + int(duration), order, "channel", 0x80 | channel,
                                bytes((int(pitch), 0))))
        order += 1
    return MidiFile(1, int(segment["ppq"]), [MidiTrack(events)]), segment


def _update_feature_matrix() -> None:
    path = ROOT / "data" / "premium-feature-matrix.json"
    matrix = json.loads(path.read_text(encoding="utf-8"))
    matrix["softwareBaseline"] = "3.19"
    for feature in matrix["features"]:
        if feature["session"] == 17:
            feature.update({
                "status": "FOUNDATION_VALIDATED / PRODUCTION_PARTIAL",
                "evidence": "data/session17-test-report.json",
                "limitations": [
                    "solo production adapter is Factory-expression-only",
                    "RX/DNC and Guitar Mode controls require confirmed Pa800 maps",
                ],
            })
    matrix["premiumProductStatus"] = "PLANNED"
    _write_json(path, matrix)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(
        str(ROOT / "tests"), pattern="test_session17.py"
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    adapter = ProductionAdapter(ROOT)
    catalog = adapter.catalog()
    catalog_path = ROOT / "data" / "session17-production-registry-catalog.json"
    _write_json(catalog_path, catalog)

    midi, segment = _isolated_factory_guitar_segment(adapter)
    end_tick = max(int(segment["tickRange"][1]), midi.ppq * 4)
    config = GuitarConfig(
        track_index=0,
        channel=int(segment["soundEvidence"]["channel"]) - 1,
        section="body",
        start_tick=0,
        end_tick=end_tick,
        seed=171717,
        intensity=58,
        profile_id=segment["factoryProfileIds"][0],
        meter=segment["meter"],
        enable_controls=False,
    )
    pipeline_config = {
        "version": "1.0",
        "stages": [{
            "engine": "guitar",
            "production": {"version": "1.0", "maxPatterns": 8},
            "config": dict(config.__dict__),
            "context": {"chords": [{
                "start_tick": 0, "end_tick": end_tick,
                "root_pc": 0, "quality": "major", "confidence": 1.0,
            }]},
        }],
        "previewProfile": "pa800-gm",
        "previewNoteLimit": 25000,
    }
    rendered = execute_pipeline(midi.to_bytes(), pipeline_config, ROOT)
    stage = rendered.manifest["stages"][0]
    if stage["decision"] != "REPLACE" or not stage["stageDiff"]["changed"]:
        raise RuntimeError("Session 17 reference Factory segment was not rendered")

    artifacts = ROOT / "artifacts"
    before_path = artifacts / "session17-factory-segment-before.mid"
    after_path = artifacts / "session17-factory-segment-after.mid"
    manifest_path = artifacts / "session17-production-adapter-manifest.json"
    before_path.write_bytes(midi.to_bytes())
    after_path.write_bytes(rendered.midi)
    _write_json(manifest_path, rendered.manifest)

    factory_files, gold_files = dna_builder.read_nested_archive(
        ROOT / "prism-uploads" / "DNA.zip"
    )
    all_sources = {**dict(factory_files), **dict(gold_files)}
    corpus_names = [
        "Workspace_Styles/Acoustic Bld/Acoustic Bld_3_4_Var1.mid",
        "Workspace_Styles/Analog Beat 2/Analog Beat 2_Intro2.mid",
        "Workspace_Styles/Italian Fox/Italian Fox_Var1.mid",
        "Gold DNA/EVO DZEPA-KNINDZA UZIVO.MID",
        "Gold DNA/GORA SE DRMALA RODIO SE MIS-KALESISKI DIJ UZIVO.MID",
        "Gold DNA/GRMEC I UNA-GR,DRVAR UZIVO.MID",
    ]
    corpus = []
    for name in corpus_names:
        raw = all_sources[name]
        item = {"source": name, "bytes": len(raw), "sha256": sha256(raw).hexdigest()}
        try:
            parsed = MidiFile.from_bytes(raw)
            item.update({"parse": "pass", "format": parsed.format_type,
                         "ppq": parsed.ppq, "tracks": len(parsed.tracks),
                         "notes": len(parsed.notes())})
        except Exception as exc:
            item.update({"parse": "source-has-invalid-note-pairing",
                         "error": str(exc),
                         "safeUse": "validated Factory registry segment only"})
        corpus.append(item)
    corpus_manifest = {
        "schema": "dna-session17-real-corpus-manifest",
        "version": "1.0",
        "date": date.today().isoformat(),
        "sources": corpus,
        "rules": {
            "sourceArchive": "prism-uploads/DNA.zip",
            "malformedSourceNeverBypassesParser": True,
            "goldSongRoleGuessing": False,
            "factoryRegistryEvidenceRequired": True,
        },
    }
    corpus_path = ROOT / "data" / "session17-real-corpus-manifest.json"
    _write_json(corpus_path, corpus_manifest)
    _update_feature_matrix()

    report = {
        "schema": "dna-session17-test-report",
        "version": "1.0",
        "date": date.today().isoformat(),
        "result": "pass",
        "scope": "production-registry-adapter-and-sound-binding-gate",
        "formalSuite": {
            "testsRun": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
        },
        "registries": catalog,
        "referenceRender": {
            "sourceSegmentId": segment["id"],
            "source": segment["source"],
            "sourceTrackIndex": segment["trackIndex"],
            "sourceRole": segment["role"],
            "factoryProfileId": config.profile_id,
            "beforeMidi": str(before_path.relative_to(ROOT)),
            "afterMidi": str(after_path.relative_to(ROOT)),
            "manifest": str(manifest_path.relative_to(ROOT)),
            "inputHash": rendered.manifest["inputHash"],
            "outputHash": rendered.manifest["outputHash"],
            "decision": stage["decision"],
        },
        "realCorpus": {
            "manifest": str(corpus_path.relative_to(ROOT)),
            "factorySources": 3,
            "goldSongs": 3,
        },
        "invariants": {
            "trackLocalSoundBindingBeforeEveryProductionStage": True,
            "midWindowBankProgramChangeBlocked": True,
            "sharedChannelRequiresApproval": True,
            "stageDiffAndRollbackRecorded": True,
            "transportParity": True,
            "goldAffectsVelocity": False,
            "goldAffectsBankSelect": False,
            "goldAffectsProgramChange": False,
            "goldControlsRhythmGuitar": False,
            "originalSoloMutationAllowed": False,
            "unconfirmedRxDncTriggers": False,
        },
        "status": {
            "session17ProductionAdapter": "FOUNDATION_VALIDATED / PRODUCTION_PARTIAL",
            "productionDrumPercussion": "ADAPTER_VALIDATED",
            "productionBassPowerRiff": "ADAPTER_VALIDATED",
            "productionFactoryGuitar": "ADAPTER_VALIDATED",
            "productionSolo": "FACTORY_EXPRESSION_ONLY",
            "productionRx": "DEVICE_BLOCKED_MISSING_CONFIRMED_MAP",
            "productionDnc": "DEVICE_BLOCKED_MISSING_CONFIRMED_MAP",
            "physicalPa800": "WAITING_FOR_DEVICE",
            "aiPremiumArranger": "PLANNED",
        },
    }
    report_path = ROOT / "data" / "session17-test-report.json"
    _write_json(report_path, report)

    release_path = ROOT / "data" / "release-check-report.json"
    if release_path.is_file():
        release = json.loads(release_path.read_text(encoding="utf-8"))
        release.setdefault("premiumReadiness", {}).update({
            "softwareBaseline": "3.19",
            "session17": f"{result.testsRun}/{result.testsRun} PASS",
            "productionAdapter": "FOUNDATION_VALIDATED / PRODUCTION_PARTIAL",
            "premiumProduct": "PLANNED",
            "physicalPa800": "WAITING_FOR_DEVICE",
        })
        _write_json(release_path, release)

    compliance_path = ROOT / "data" / "master-prompt-compliance.json"
    if compliance_path.is_file():
        compliance = json.loads(compliance_path.read_text(encoding="utf-8"))
        compliance.setdefault("summary", {}).update({
            "session17ProductionAdapter": f"{result.testsRun}/{result.testsRun} PASS",
            "productionAdapterStatus": "FOUNDATION_VALIDATED / PRODUCTION_PARTIAL",
            "aiPremiumArranger": "PLANNED",
        })
        compliance.setdefault("invariants", {}).update({
            "productionSoundBindingGate": True,
            "productionStageRollback": True,
            "goldGuitarAuthority": False,
            "unconfirmedProductionArticulationsBlocked": True,
        })
        evidence = compliance.setdefault("evidence", [])
        for item in (
            "data/session17-test-report.json",
            "data/session17-production-registry-catalog.json",
            "data/session17-real-corpus-manifest.json",
            "artifacts/session17-production-adapter-manifest.json",
        ):
            if item not in evidence:
                evidence.append(item)
        _write_json(compliance_path, compliance)

    print(f"Session 17 Production Adapter PASS: {result.testsRun} tests; {report_path}")
    print("Production status: FOUNDATION_VALIDATED / PRODUCTION_PARTIAL")
    print("AI Premium Arranger status: PLANNED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())