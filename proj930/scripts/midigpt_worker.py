from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_api():
    try:
        from midigpt import Score
        from midigpt.inference import (
            GenerationRequest,
            InferenceConfig,
            InferenceEngine,
            TrackPrompt,
        )
        return Score, InferenceEngine, GenerationRequest, InferenceConfig, TrackPrompt
    except Exception as exc:
        raise RuntimeError(
            "MIDI-GPT is not installed in this Python environment. "
            "Run scripts\\install_midigpt_windows.bat"
        ) from exc


def _track_prompts(payload: dict[str, Any], score, TrackPrompt):
    explicit = payload.get("track_prompts") or []
    if explicit:
        prompts = []
        for spec in explicit:
            bar_attrs = {
                int(k): v for k, v in (spec.get("bar_attributes") or {}).items()
            }
            prompts.append(
                TrackPrompt(
                    id=int(spec["track"]),
                    bars=[int(v) for v in spec.get("bars", [])],
                    ignore=bool(spec.get("ignore", False)),
                    autoregressive=bool(spec.get("autoregressive", False)),
                    attributes=dict(spec.get("attributes") or {}),
                    bar_attributes=bar_attrs,
                    controls=dict(spec.get("controls") or {}),
                )
            )
        return prompts

    target_tracks = set(payload.get("tracks") or range(len(score.tracks)))
    target_bars = [int(v) for v in payload.get("bars", [])]
    return [
        TrackPrompt(
            id=i,
            bars=target_bars if i in target_tracks else [],
            ignore=i not in target_tracks,
        )
        for i in range(len(score.tracks))
    ]


def run_request(payload: dict[str, Any]) -> dict[str, Any]:
    Score, Engine, GenerationRequest, InferenceConfig, TrackPrompt = load_api()

    input_path = Path(payload["input"])
    output_path = Path(payload["output"])
    report_path = Path(payload.get("report") or output_path.with_suffix(".midigpt.json"))

    score = Score.from_midi(str(input_path))
    prompts = _track_prompts(payload, score, TrackPrompt)

    cfg = InferenceConfig(
        temperature=float(payload.get("temperature", 0.95)),
        top_p=float(payload.get("top_p", 0.95)),
        top_k=int(payload.get("top_k", 0)),
        model_dim=int(payload.get("model_dim", 8)),
        bars_per_step=int(payload.get("bars_per_step", 1)),
        tracks_per_step=int(payload.get("tracks_per_step", 1)),
        seed=int(payload.get("seed", -1)),
        mask_mode=str(payload.get("mask_mode", "attention")),
        num_candidates=int(payload.get("num_candidates", 1)),
    )

    piece_controls = {
        "velocity": bool(payload.get("velocity", False)),
        "microtiming": bool(payload.get("microtiming", False)),
    }
    request = GenerationRequest(tracks=prompts, config=cfg, controls=piece_controls)

    model = str(payload.get("model", "yellow_medium"))
    project_root = Path(__file__).resolve().parents[1]
    local_model = project_root / "models" / "midigpt" / f"{model}-final.safetensors"
    if local_model.exists():
        engine = Engine.from_checkpoint(str(local_model))
        model_source = "local"
    else:
        engine = Engine.from_pretrained(model)
        model_source = "huggingface"

    session = engine.session(score, request)
    n_candidates = max(1, int(payload.get("num_candidates", 1)))
    candidate_files = []
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if n_candidates > 1 and hasattr(session, "run_variations"):
        results = session.run_variations()
        for idx, item in enumerate(results):
            candidate = item.get("score") if isinstance(item, dict) else item
            if candidate is None:
                continue
            cpath = output_path if idx == 0 else output_path.with_name(f"{output_path.stem}.candidate_{idx+1}{output_path.suffix}")
            candidate.to_midi(str(cpath))
            candidate_files.append(str(cpath))
        if not candidate_files:
            raise RuntimeError("MIDI-GPT generated no valid candidate scores")
    else:
        result = session.run()
        result.to_midi(str(output_path))
        candidate_files.append(str(output_path))

    rep = {
        "ok": True,
        "backend": "MIDI-GPT",
        "backend_version": "0.3.4-vendored",
        "model": model,
        "model_source": model_source,
        "input": str(input_path),
        "output": str(output_path),
        "track_prompts": payload.get("track_prompts") or [],
        "tracks": payload.get("tracks") or [],
        "bars": payload.get("bars") or [],
        "velocity_enabled": piece_controls["velocity"],
        "microtiming_enabled": piece_controls["microtiming"],
        "num_candidates": n_candidates,
        "candidate_files": candidate_files,
    }
    report_path.write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep))
    return rep


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--request-json")
    ns = ap.parse_args()

    if ns.self_test:
        _, Engine, *_ = load_api()
        print(json.dumps({"ok": True, "backend": "MIDI-GPT", "version": "0.3.4", "imported": True}))
        return 0

    if not ns.request_json:
        ap.error("--request-json is required")
    payload = json.loads(Path(ns.request_json).read_text(encoding="utf-8"))
    run_request(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
