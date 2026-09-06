from dataclasses import asdict
from pathlib import Path

from dna_midi_studio.external_midigpt import (
    MidiGPTBackend,
    MidiGPTRequest,
    MidiGPTTrackControl,
)


def test_request_defaults():
    r = MidiGPTRequest((0,), (0, 1, 2, 3))
    assert r.model == "yellow_medium"
    assert r.top_p == 0.95
    assert r.velocity is False
    assert r.microtiming is False


def test_advanced_controls_serialize():
    c = MidiGPTTrackControl(
        track=1,
        bars=(4, 5),
        controls={
            "pitch_mask": {"scale": "minor", "root": 2},
            "rhythm_mask": {"grid": {"unit": "eighth", "strength": 0.8}},
            "remix": {"amount": 0.4, "mode": "pitch"},
        },
    )
    r = MidiGPTRequest(track_prompts=(c,), num_candidates=3, top_k=32)
    d = asdict(r)
    assert d["track_prompts"][0]["controls"]["remix"]["amount"] == 0.4
    assert d["num_candidates"] == 3
    assert d["top_k"] == 32


def test_backend_reports_not_installed(tmp_path: Path):
    b = MidiGPTBackend(tmp_path)
    assert not b.available()
    assert not b.vendored()
    assert b.install_hint().endswith("install_midigpt_windows.bat")


def test_backend_detects_vendored_source(tmp_path: Path):
    vendor = tmp_path / "third_party" / "MIDI-GPT-0.3.4"
    vendor.mkdir(parents=True)
    (vendor / "pyproject.toml").write_text("[project]\nname='midigpt'\n", encoding="utf-8")
    (vendor / "LICENSE").write_text("MIT", encoding="utf-8")
    b = MidiGPTBackend(tmp_path)
    assert b.vendored()
