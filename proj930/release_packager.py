#!/usr/bin/env python3
"""Build one deterministic portable Windows ZIP and its checksum."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import shutil
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
ZIP_NAME = "DNA-MIDI-Studio-Pa800-Windows-6.03-PRE-SALE-RC.zip"
FIXED_TIME = (2026, 9, 3, 0, 0, 0)
ROOT_FILES = {
    "README.md", "WINDOWS_RELEASE.md", "MASTER_PROMPT_COMPLIANCE.md", "ZAVRSNE_SESIJE.md",
    "VIZIJA_PROJEKTA.md", "ULTRA_PLAN.md", "AI_PREMIUM_ARRANGER_PLAN.md",
    "APP_AUDIT.md", "DNA_CORPUS_AUDIT.md", "PRE_SALE_RELEASE_REPORT.md",
    "THIRD_PARTY_NOTICES.md", "SALE_HANDOFF_CHECKLIST.md",
    "SESSION_1_CHECKPOINT.md", "POKRENI.txt", "main.pdf",
    "requirements-lock.txt", "pokreni.bat", "izgradi-dna.bat", "testiraj.bat", "install.bat", "run.bat",
    "dna_builder.py", "factory_velocity.py", "factory_style_registry.py", "factory_strumming.py",
    "gold_performance_registry.py", "gold_schema.py", "midi_integrity.py", "midi_optimizer.py",
    "midi_editor.py", "song_analyzer.py", "style_intelligence.py", "pa800_style_builder.py",
    "pa800_validator.py", "project_model.py", "result_cache.py", "special_track_engine.py",
    "performance_engine.py", "performance_gesture_engine.py",
    "phase_optimizer.py", "web_gui.py", "server.py", "corpus_forensics.py", "test_master_prompt.py",
    "release_check.py", "recovery_release_check.py", "release_packager.py", "premium_config.py",
    *(f"session{number}_release_check.py" for number in range(2, 16)),
    "session17_release_check.py", "session18_release_check.py", "session19_release_check.py",
    "session20_release_check.py", "session20_producer_brief.py",
    "session21_release_check.py", "session21_arrangement_graph.py",
    "session22_release_check.py", "session22_candidate_search.py",
    "session23_release_check.py", "session23_groove_plan.py",
    "session24_release_check.py", "session24_expression_plan.py",
    "session25_release_check.py", "session25_articulation_map.py",
    "session26_release_check.py", "session26_premium_preview.py",
    "session27_release_check.py", "session27_quality_evaluator.py",
    "session28_release_check.py", "session28_premium_workflow.py",
    "session29_release_check.py", "session29_personal_profile.py",
    "session30_release_check.py", "session30_release_readiness.py",
    "session31_release_check.py", "session31_track_analysis.py",
    "session31b_release_check.py", "session31b_evidence_resolver.py",
    "session32_release_check.py", "session32_track_plan.py",
    "session33_release_check.py", "session33_arrangement_renderer.py",
    "session34_release_check.py",
    "session35_release_check.py", "session35_end_to_end_arranger.py",
    "session36_release_check.py", "session36_reliability_gate.py",
    "session37_release_check.py", "session37_quality_calibration.py",
    "session38_release_check.py", "session38_device_lab.py",
    "session2_reconstruct.py", "session3_reconstruct.py", "session4_reconstruct.py",
    "session5_enhance.py", "session6_rx.py", "session7_dnc.py", "session8_agent_runtime.py",
    "session9_pipeline.py", "session10_transaction.py", "session11_verify.py",
    "session14_device_check.py", "SESSION14_DEVICE_CHECKLIST.md",
}
FULL_REGISTRIES = {
    "factory-velocity-profiles.json", "gold-patterns.json", "factory-style-segments.json",
    "factory-strumming.json", "gold-performance-patterns.json",
}


def package_files(root: Path = ROOT) -> list[Path]:
    files = [root / name for name in ROOT_FILES]
    files += [path for path in (root / "src").rglob("*.py")]
    files += [path for path in (root / "tests").rglob("test_*.py")]
    files += [path for path in (root / "premium").rglob("*") if path.is_file()]
    files += [root / "agents" / "agent-team.json"]
    files += [path for path in (root / "data").glob("*.json")
              if path.name not in {"release-package-manifest.json", "session13-test-report.json"}]
    files += [path for path in (root / "artifacts").rglob("*")
              if path.is_file() and not path.name.endswith((".lock", ".tmp"))]
    files += [root / "prism-uploads" / "DNA.zip"]
    missing = [path for path in files if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing release files: " + ", ".join(str(path.relative_to(root)) for path in missing))
    return sorted(set(files), key=lambda path: path.relative_to(root).as_posix())


def _packaged_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    if path.suffix.lower() == ".bat":
        return raw.decode("ascii").replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii")
    return raw


def content_manifest(files: list[Path], root: Path = ROOT) -> dict:
    entries = []
    for path in files:
        raw = _packaged_bytes(path)
        entries.append({"path": path.relative_to(root).as_posix(), "size": len(raw),
                        "sha256": sha256(raw).hexdigest()})
    content_hash = sha256(json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"schema": "dna-windows-release-manifest", "version": "6.03-pre-sale-rc", "date": "2026-09-05",
            "platform": ["Windows 10 x64", "Windows 11 x64"],
            "python": ["3.11", "3.12", "3.13", "3.14"], "thirdPartyDependencies": [],
            "entryPoints": ["pokreni.bat", "izgradi-dna.bat", "testiraj.bat"],
            "authoritativeSourceArchive": "prism-uploads/DNA.zip",
            "files": entries, "contentHash": content_hash,
            "certification": {"software": "SOFTWARE_VALIDATED_DEVICE_INTAKE_PREVIEW",
                              "allowedProductName": "AI PREMIUM ARRANGER PREVIEW",
                              "softwarePreviewMidi": "ALLOWED_AFTER_VERIFIER",
                              "finalCertifiedMidiExport": "BLOCKED",
                              "physicalPa800": "WAITING_FOR_DEVICE"}}


def build_release(root: Path = ROOT, dist: Path = DIST) -> tuple[Path, Path, dict]:
    files = package_files(root)
    manifest = content_manifest(files, root)
    manifest_bytes = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    dist.mkdir(parents=True, exist_ok=True)
    for old in dist.glob("DNA-MIDI-Studio-Pa800-Windows-*.zip*"):
        old.unlink()
    zip_path = dist / ZIP_NAME
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(relative, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, _packaged_bytes(path))
        info = zipfile.ZipInfo("data/release-package-manifest.json", FIXED_TIME)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        archive.writestr(info, manifest_bytes)
    checksum = sha256(zip_path.read_bytes()).hexdigest()
    checksum_path = zip_path.with_suffix(zip_path.suffix + ".sha256")
    checksum_path.write_text(f"{checksum}  {zip_path.name}\n", encoding="ascii")
    (root / "data" / "release-package-manifest.json").write_bytes(manifest_bytes)
    return zip_path, checksum_path, manifest


if __name__ == "__main__":
    path, checksum, manifest = build_release()
    print(f"Release ZIP: {path} ({len(manifest['files'])} files)")
    print(f"Checksum: {checksum}")
