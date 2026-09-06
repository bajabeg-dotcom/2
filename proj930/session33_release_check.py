#!/usr/bin/env python3
"""Run the Session 33 deterministic Arrangement Renderer release gate."""

from __future__ import annotations

import base64
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from time import perf_counter
import unittest
import statistics


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import (  # noqa: E402
    execute_arrangement_renderer_api,
    execute_arrangement_renderer_batch,
    execute_arrangement_renderer_gui,
    publish_rendered_arrangement,
    render_arrangement,
)
from dna_midi_studio.session33_fixture import build_session33_chain  # noqa: E402


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _update_feature_matrix() -> None:
    path = ROOT / "data/premium-feature-matrix.json"
    matrix = json.loads(path.read_text(encoding="utf-8"))
    matrix["softwareBaseline"] = "4.9.3-renderer-foundation"
    matrix["features"] = [item for item in matrix["features"]
                          if item.get("id") != "deterministic-arrangement-renderer"]
    matrix["features"].append({
        "session": "33", "id": "deterministic-arrangement-renderer", "priority": "P0",
        "status": "SOFTWARE_VALIDATED / ARRANGER PREVIEW MIDI",
        "evidence": "data/session33-test-report.json",
        "blocker": "Global coherence, human listening and physical Pa800 certification remain open",
        "limitations": [
            "Device-unconfirmed expression and articulation events are excluded from production rendering",
            "CC11=127 remains the Pa800 Style initialization contract; Factory CC7 and velocity remain exact-evidence only",
            "Software-validated preview MIDI is allowed, but final certified export and the non-Preview product name remain blocked",
        ],
    })
    matrix["premiumProductStatus"] = "PREVIEW_RENDERER_FOUNDATION"
    _write_json(path, matrix)


def _cli_parity(fixture: dict, expected_hash: str) -> bool:
    with tempfile.TemporaryDirectory() as raw:
        directory = Path(raw)
        source = directory / "source.mid"
        documents = directory / "documents.json"
        ledger = directory / "ledger.json"
        plan = directory / "track-plan.json"
        output = directory / "out"
        source.write_bytes(fixture["sourceBytes"])
        _write_json(documents, fixture["documents"])
        _write_json(ledger, fixture["ledger"])
        _write_json(plan, fixture["trackPlan"])
        completed = subprocess.run(
            [sys.executable, str(ROOT / "session33_arrangement_renderer.py"),
             str(source), str(documents), str(ledger), str(plan),
             "--output-dir", str(output)],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        outputs = list(output.glob("*.mid"))
        return (completed.returncode == 0 and len(outputs) == 1
                and sha256(outputs[0].read_bytes()).hexdigest() == expected_hash)


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session33.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    if result.testsRun != 160:
        raise RuntimeError(f"Session 33 expected 160 tests, got {result.testsRun}")

    fixture = build_session33_chain(ROOT)
    render_samples = []
    repeated_results = []
    for _ in range(3):
        start = perf_counter()
        repeated_results.append(render_arrangement(
            fixture["sourceBytes"], fixture["trackPlan"], fixture["documents"],
            fixture["ledger"], ROOT,
        ))
        render_samples.append(perf_counter() - start)
    render_seconds = statistics.median(render_samples)
    deterministic = all(
        repeated_midi == fixture["renderedMidi"]
        and repeated_manifest == fixture["renderManifest"]
        for repeated_midi, repeated_manifest in repeated_results
    )
    if not deterministic:
        raise RuntimeError("Session 33 renderer is not deterministic")

    payload = {
        "midiBase64": base64.b64encode(fixture["sourceBytes"]).decode("ascii"),
        "documents": fixture["documents"], "evidenceLedger": fixture["ledger"],
        "trackPlan": fixture["trackPlan"],
    }
    api = execute_arrangement_renderer_api(payload, ROOT)
    gui = execute_arrangement_renderer_gui(payload, ROOT)
    batch = execute_arrangement_renderer_batch([payload], ROOT)[0]
    expected_hash = fixture["renderManifest"]["midi"]["outputSha256"]
    transport_hashes = {
        "direct": expected_hash,
        "api": api["renderManifest"]["midi"]["outputSha256"],
        "gui": gui["renderManifest"]["midi"]["outputSha256"],
        "batch": batch["result"]["renderManifest"]["midi"]["outputSha256"],
    }
    cli_parity = _cli_parity(fixture, expected_hash)
    transport_parity = len(set(transport_hashes.values())) == 1 and cli_parity

    publish_dir = ROOT / "artifacts/session33-publish"
    publish_result = publish_rendered_arrangement(
        fixture["sourceBytes"], fixture["renderedMidi"], fixture["renderManifest"],
        publish_dir, "session33-arranger-preview.mid",
    )
    if publish_result["status"] not in {"COMMITTED", "RESUMED"}:
        raise RuntimeError("Session 33 atomic publication did not commit or safely resume")

    paths = {
        "sourceMidi": ROOT / "artifacts/session33-source.mid",
        "trackPlan": ROOT / "artifacts/session33-track-plan.json",
        "evidenceLedger": ROOT / "artifacts/session33-evidence-ledger.json",
        "renderManifest": ROOT / "artifacts/session33-render-manifest.json",
        "verification": ROOT / "artifacts/session33-render-verification.json",
        "renderedMidi": Path(publish_result["output_path"]),
        "publishedManifest": Path(publish_result["manifest_path"]),
        "atomicJournal": Path(publish_result["journal_path"]),
    }
    paths["sourceMidi"].write_bytes(fixture["sourceBytes"])
    _write_json(paths["trackPlan"], fixture["trackPlan"])
    _write_json(paths["evidenceLedger"], fixture["ledger"])
    _write_json(paths["renderManifest"], fixture["renderManifest"])
    _write_json(paths["verification"], fixture["verification"])

    manifest = fixture["renderManifest"]
    benchmark = {
        "schema": "dna-session33-renderer-benchmark", "version": "1.0",
        "date": date.today().isoformat(), "license": "self-authored-test-fixtures",
        "sourceMidiSha256": sha256(fixture["sourceBytes"]).hexdigest(),
        "trackPlanHash": fixture["trackPlan"]["trackPlanHash"],
        "renderManifestHash": manifest["renderManifestHash"],
        "outputMidiSha256": expected_hash,
        "renderedMidiBytes": len(fixture["renderedMidi"]),
        "renderedFragments": manifest["audit"]["renderedFragments"],
        "renderedNotes": manifest["midi"]["noteCount"],
        "markers": manifest["midi"]["markerCount"],
        "usedChannels": manifest["midi"]["usedChannels"],
        "globalPeakConcurrentMidiNotes": manifest["midi"]["globalPeakConcurrentMidiNotes"],
        "softwareMidiNoteCeiling": manifest["midi"]["softwareMidiNoteCeiling"],
        "channelPolyphonyNotesRemoved": manifest["audit"]["channelPolyphonyNotesRemoved"],
        "channelPolyphonyTailsTrimmed": manifest["audit"]["channelPolyphonyTailsTrimmed"],
        "deviceUnconfirmedLayersExcluded": manifest["audit"]["deviceUnconfirmedLayersExcluded"],
        "transportHashes": transport_hashes, "transportParity": transport_parity,
        "independentVerifierPassed": fixture["verification"]["passed"],
        "pa800HardValidatorPassed": fixture["verification"]["checks"]["pa800HardValidator"],
        "deterministic": deterministic, "renderSeconds": round(render_seconds, 6),
        "renderSamplesSeconds": [round(value, 6) for value in render_samples],
        "atomicPublication": publish_result["status"],
        "sourceMidiMutated": manifest["safety"]["sourceMidiMutated"],
        "goldAffectsDynamics": manifest["safety"]["goldAffectsDynamics"],
        "finalCertifiedMidiExportAllowed": manifest["safety"]["finalCertifiedMidiExportAllowed"],
    }
    checks = {
        "fragmentCount": benchmark["renderedFragments"] == 52,
        "noteCount": benchmark["renderedNotes"] == 1400,
        "markerCount": benchmark["markers"] == 10,
        "channels": benchmark["usedChannels"] == [9, 10, 11, 12, 13, 14, 15],
        "peak": benchmark["globalPeakConcurrentMidiNotes"] == 14,
        "ceiling": benchmark["softwareMidiNoteCeiling"] == 54,
        "deviceLayersExcluded": benchmark["deviceUnconfirmedLayersExcluded"] == {
            "ARTICULATION_EVENT": 11, "EXPRESSION_EVENT": 83},
        "transportParity": benchmark["transportParity"],
        "independentVerifier": benchmark["independentVerifierPassed"],
        "pa800Validator": benchmark["pa800HardValidatorPassed"],
        "deterministic": benchmark["deterministic"],
        "medianRenderUnderTwoSeconds": render_seconds < 2.0,
        "atomicCommitOrExactResume": benchmark["atomicPublication"] in {"COMMITTED", "RESUMED"},
        "sourceImmutable": not benchmark["sourceMidiMutated"],
        "goldDynamicsZero": not benchmark["goldAffectsDynamics"],
        "certifiedExportBlocked": not benchmark["finalCertifiedMidiExportAllowed"],
    }
    benchmark["checks"] = checks
    benchmark["passed"] = all(checks.values())
    benchmark["benchmarkHash"] = sha256(_canonical(benchmark)).hexdigest()
    benchmark_path = ROOT / "data/session33-benchmark-report.json"
    _write_json(benchmark_path, benchmark)
    if not benchmark["passed"]:
        failed = ", ".join(name for name, passed in checks.items() if not passed)
        raise RuntimeError(f"Session 33 benchmark failed: {failed}")

    schema_paths = [
        ROOT / "premium/schemas/v2/rendered-fragment-v1.schema.json",
        ROOT / "premium/schemas/v2/render-manifest-v2.schema.json",
        ROOT / "premium/schemas/v2/renderer-verification-v1.schema.json",
    ]
    contracts = []
    for path in schema_paths:
        value = json.loads(path.read_text(encoding="utf-8"))
        contracts.append({"name": path.name, "$id": value["$id"],
                          "contractVersion": value["x-contract-version"],
                          "sha256": sha256(path.read_bytes()).hexdigest()})
    schema_catalog = {
        "schema": "dna-session33-schema-catalog", "version": "1.0",
        "date": date.today().isoformat(), "contracts": contracts,
        "catalogHash": sha256(_canonical(contracts)).hexdigest(),
    }
    schema_path = ROOT / "data/session33-schema-catalog.json"
    _write_json(schema_path, schema_catalog)
    _update_feature_matrix()

    report = {
        "schema": "dna-session33-test-report", "version": "1.0",
        "date": date.today().isoformat(), "result": "pass",
        "scope": "deterministic-evidence-driven-pa800-arrangement-renderer",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures),
                        "errors": len(result.errors)},
        "benchmark": {"report": str(benchmark_path.relative_to(ROOT)), **{
            key: benchmark[key] for key in (
                "outputMidiSha256", "renderManifestHash", "renderedMidiBytes",
                "renderedFragments", "renderedNotes", "markers", "usedChannels",
                "globalPeakConcurrentMidiNotes", "channelPolyphonyNotesRemoved",
                "channelPolyphonyTailsTrimmed", "deviceUnconfirmedLayersExcluded",
                "transportHashes", "transportParity", "renderSeconds", "benchmarkHash",
            )}},
        "artifacts": {name: str(path.relative_to(ROOT)) for name, path in paths.items()} | {
            "schemaCatalog": str(schema_path.relative_to(ROOT)),
        },
        "transports": {"cli": "session33_arrangement_renderer.py",
                       "api": "/api/arrangement-render",
                       "guiAdapter": "execute_arrangement_renderer_gui",
                       "batchIsolation": True, "byteIdentical": transport_parity},
        "invariants": manifest["safety"],
        "status": {
            "session33ArrangementRenderer": "SOFTWARE_VALIDATED / ARRANGER PREVIEW MIDI",
            "activeSoftwareBaseline": "4.9.3-renderer-foundation",
            "softwarePreviewMidi": "ALLOWED_AFTER_INDEPENDENT_VERIFIER",
            "globalCoherence": "NEXT", "finalCertifiedMidiExport": "BLOCKED",
            "humanListeningEvidence": "0/2 VERIFIED", "physicalPa800": "WAITING_FOR_DEVICE",
        },
    }
    report_path = ROOT / "data/session33-test-report.json"
    _write_json(report_path, report)

    recovery_path = ROOT / "data/recovery-release-report.json"
    recovery_total = None
    if recovery_path.is_file():
        recovery = json.loads(recovery_path.read_text(encoding="utf-8"))
        if recovery.get("result") == "pass":
            recovery_total = recovery.get("tests", {}).get("run")
    release_path = ROOT / "data/release-check-report.json"
    if release_path.is_file():
        release = json.loads(release_path.read_text(encoding="utf-8"))
        release.setdefault("premiumReadiness", {}).update({
            "softwareBaseline": "4.9.3-renderer-foundation",
            "session33": f"{result.testsRun}/{result.testsRun} PASS",
            "arrangementRenderer": "SOFTWARE_VALIDATED_PREVIEW_MIDI",
            "softwarePreviewMidi": "ALLOWED_AFTER_INDEPENDENT_VERIFIER",
            "finalCertifiedMidiExport": "BLOCKED", "globalCoherence": "NEXT",
            "premiumProduct": "PREVIEW_ONLY", "physicalPa800": "WAITING_FOR_DEVICE",
            **({"recoveryPremiumRenderer": f"{recovery_total}/{recovery_total} PASS"}
               if recovery_total else {}),
        })
        _write_json(release_path, release)
    compliance_path = ROOT / "data/master-prompt-compliance.json"
    if compliance_path.is_file():
        compliance = json.loads(compliance_path.read_text(encoding="utf-8"))
        compliance.setdefault("summary", {}).update({
            "session33ArrangementRenderer": f"{result.testsRun}/{result.testsRun} PASS",
            "activeSoftwareBaseline": "4.9.3-renderer-foundation",
            "arrangementRenderer": "SOFTWARE_VALIDATED_PREVIEW_MIDI",
            "globalCoherence": "NEXT",
            **({"recoveryPremiumRenderer": f"{recovery_total}/{recovery_total} PASS"}
               if recovery_total else {}),
        })
        evidence = compliance.setdefault("evidence", [])
        for relative in (
            "data/session33-test-report.json", "data/session33-benchmark-report.json",
            "data/session33-schema-catalog.json", "artifacts/session33-render-manifest.json",
            "artifacts/session33-render-verification.json",
            "artifacts/session33-publish/session33-arranger-preview_OPT.mid",
        ):
            if relative not in evidence:
                evidence.append(relative)
        _write_json(compliance_path, compliance)
    print(
        f"Session 33 PASS: {result.testsRun}/{result.testsRun}; "
        f"fragments={benchmark['renderedFragments']}; notes={benchmark['renderedNotes']}; "
        f"peak={benchmark['globalPeakConcurrentMidiNotes']}/54; {report_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())