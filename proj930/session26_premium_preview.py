#!/usr/bin/env python3
"""CLI for Session 26 synchronized Premium Preview and audio comparison."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import (  # noqa: E402
    MidiFile,
    build_preview_session,
    compare_device_audio_capture,
    import_device_audio_capture,
    render_preview_wav,
)


def _json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: str, value) -> None:
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build validation-neutral A/B/C previews; never writes final MIDI")
    sub = parser.add_subparsers(dest="action", required=True)
    plan = sub.add_parser("plan", help="Build PreviewSession 2.0")
    plan.add_argument("midi")
    plan.add_argument("song_map")
    plan.add_argument("output")
    plan.add_argument("--groove-plan")
    plan.add_argument("--expression-plan")
    plan.add_argument("--articulation-plan", action="append", default=[])
    plan.add_argument("--validator-verdict")
    plan.add_argument("--controls")

    render = sub.add_parser("render", help="Render deterministic built-in proxy WAV")
    render.add_argument("preview_session")
    render.add_argument("variant", choices=("A", "B", "C"))
    render.add_argument("wav_output")
    render.add_argument("manifest_output")

    capture = sub.add_parser("capture", help="Import Pa800 WAV for comparison only")
    capture.add_argument("wav")
    capture.add_argument("metadata")
    capture.add_argument("output")

    compare = sub.add_parser("compare", help="Compare proxy manifest and Pa800 capture")
    compare.add_argument("preview_session")
    compare.add_argument("variant", choices=("A", "B", "C"))
    compare.add_argument("capture")
    compare.add_argument("proxy_manifest")
    compare.add_argument("output")
    args = parser.parse_args()

    if args.action == "plan":
        session = build_preview_session(
            MidiFile.read(args.midi), _json(args.song_map),
            _json(args.groove_plan) if args.groove_plan else None,
            _json(args.expression_plan) if args.expression_plan else None,
            [_json(path) for path in args.articulation_plan],
            _json(args.validator_verdict) if args.validator_verdict else None,
            _json(args.controls) if args.controls else None,
        )
        _write(args.output, session)
        print(f"PreviewSession {session['previewSessionHash']} -> {args.output}")
    elif args.action == "render":
        raw, manifest = render_preview_wav(_json(args.preview_session), args.variant)
        Path(args.wav_output).write_bytes(raw)
        _write(args.manifest_output, manifest)
        print(f"Proxy WAV {manifest['wavSha256']} -> {args.wav_output}")
    elif args.action == "capture":
        value = import_device_audio_capture(Path(args.wav).read_bytes(), _json(args.metadata))
        _write(args.output, value)
        print(f"Comparison capture {value['captureHash']} -> {args.output}")
    else:
        value = compare_device_audio_capture(_json(args.preview_session), args.variant,
                                             _json(args.capture), _json(args.proxy_manifest))
        _write(args.output, value)
        print(f"Audio comparison {value['comparisonHash']} -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())