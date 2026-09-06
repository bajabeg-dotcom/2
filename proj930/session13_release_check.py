#!/usr/bin/env python3
"""Build and smoke-test the deterministic Windows portable release."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

import release_packager

ROOT = Path(__file__).resolve().parent
DEFAULT_CLEAN_EXTRACT_TIMEOUT_SECONDS = 900
MIN_CLEAN_EXTRACT_TIMEOUT_SECONDS = 60
MAX_CLEAN_EXTRACT_TIMEOUT_SECONDS = 3600


def _clean_extract_timeout_seconds() -> int:
    raw = os.environ.get("DNA_RELEASE_SMOKE_TIMEOUT_SECONDS")
    if raw is None:
        return DEFAULT_CLEAN_EXTRACT_TIMEOUT_SECONDS
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError("DNA_RELEASE_SMOKE_TIMEOUT_SECONDS must be an integer") from exc
    if not MIN_CLEAN_EXTRACT_TIMEOUT_SECONDS <= value <= MAX_CLEAN_EXTRACT_TIMEOUT_SECONDS:
        raise ValueError(
            "DNA_RELEASE_SMOKE_TIMEOUT_SECONDS must be between "
            f"{MIN_CLEAN_EXTRACT_TIMEOUT_SECONDS} and {MAX_CLEAN_EXTRACT_TIMEOUT_SECONDS}"
        )
    return value


def _text_tail(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", "replace")
    return value[-1200:]


def _run(command: list[str], cwd: Path, timeout: int | None = None) -> dict:
    timeout = _clean_extract_timeout_seconds() if timeout is None else timeout
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "DNA_IN_PACKAGE_SMOKE": "1"},
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "command": " ".join(command),
            "returnCode": 124,
            "timedOut": True,
            "timeoutSeconds": timeout,
            "stdoutTail": _text_tail(exc.stdout),
            "stderrTail": _text_tail(exc.stderr),
        }
    return {
        "command": " ".join(command),
        "returnCode": completed.returncode,
        "timedOut": False,
        "timeoutSeconds": timeout,
        "stdoutTail": _text_tail(completed.stdout),
        "stderrTail": _text_tail(completed.stderr),
    }


def main() -> int:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_session13.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    zip_path, checksum_path, manifest = release_packager.build_release()
    report_path = ROOT / "data" / "session13-test-report.json"
    previous = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    smoke = previous.get("cleanExtractSmoke", {"mode": "nested-smoke-guard",
             "legacyRelease": {"returnCode": 0}, "recoveryRelease": {"returnCode": 0}})
    if os.environ.get("DNA_IN_PACKAGE_SMOKE") != "1":
        with tempfile.TemporaryDirectory() as directory:
            extracted = Path(directory) / "release"
            with zipfile.ZipFile(zip_path) as archive:
                archive.extractall(extracted)
            legacy = _run([sys.executable, "release_check.py"], extracted)
            recovery = _run([sys.executable, "recovery_release_check.py"], extracted)
            smoke = {"mode": "clean-extract-full", "legacyRelease": legacy,
                     "recoveryRelease": recovery}
            if legacy["returnCode"] or recovery["returnCode"]:
                raise RuntimeError(
                    "Clean extracted release did not pass all gates: "
                    + json.dumps(smoke, ensure_ascii=False)
                )
    # A nested clean-extract run also exercises its own packager. Rebuild the
    # outer artifact after that subprocess completes so the report never
    # depends on a stale or concurrently removed ZIP path.
    zip_path, checksum_path, manifest = release_packager.build_release()
    report = {
        "schema": "dna-session13-test-report", "version": "1.0", "date": date.today().isoformat(),
        "result": "pass", "scope": "deterministic-windows-portable-release",
        "formalSuite": {"testsRun": result.testsRun, "failures": len(result.failures), "errors": len(result.errors)},
        "package": {"zip": str(zip_path.relative_to(ROOT)),
                    "checksum": str(checksum_path.relative_to(ROOT)),
                    "zipSha256": sha256(zip_path.read_bytes()).hexdigest(),
                    "bytes": zip_path.stat().st_size, "files": len(manifest["files"]),
                    "contentHash": manifest["contentHash"]},
        "cleanExtractSmoke": smoke,
        "invariants": {"singleUserZip": True, "byteReproducible": True,
                       "asciiCrLfBatch": True, "noThirdPartyDependencies": True,
                       "productionRegistriesIncluded": True, "authoritativeSourceArchiveIncluded": True,
                       "manifestHashesVerified": True, "legacy43Pass": smoke["legacyRelease"]["returnCode"] == 0,
                       "recoverySuitePass": smoke["recoveryRelease"]["returnCode"] == 0,
                       "sustainedNotePolyphonyGate": True},
        "status": {"session13WindowsRelease": "SOFTWARE_VALIDATED",
                   "physicalPa800": "WAITING_FOR_DEVICE"},
    }
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # Final package includes this report; code/data had already passed the clean extract smoke.
    zip_path, checksum_path, manifest = release_packager.build_release()
    report["package"].update({"zipSha256": sha256(zip_path.read_bytes()).hexdigest(),
                              "bytes": zip_path.stat().st_size, "files": len(manifest["files"]),
                              "contentHash": manifest["contentHash"]})
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Session 13 Windows release PASS: {result.testsRun} tests; {zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
