from pathlib import Path
from types import SimpleNamespace

from dna_midi_studio.generative_backend_router import GenerativeBackendRouter


def test_bar_conversion_is_zero_based(tmp_path: Path):
    r = GenerativeBackendRouter(tmp_path, SimpleNamespace())
    assert r._bar_indexes(1, 4) == (0, 1, 2, 3)
    assert r._bar_indexes(5, 5) == (4,)


def test_keep_never_calls_backend(tmp_path: Path):
    r = GenerativeBackendRouter(tmp_path, SimpleNamespace())
    out = r.generate(b"x", track_index=0, channel=9, start_bar=1, end_bar=1,
                     start_tick=0, end_tick=480, role="bass", action="KEEP")
    assert out["status"] == "KEEP"
    assert out["candidates"] == []


def test_backend_status_is_truthful(tmp_path: Path):
    r = GenerativeBackendRouter(tmp_path, SimpleNamespace())
    st = r.backend_status()
    assert st["midigptInstalled"] is False
    assert st["dnaNeuralCheckpoint"] is False

from dna_midi_studio.generative_backend_router import _scope_safe
from dna_midi_studio.midi import MidiFile, MidiTrack, MidiEvent, Note


def _tiny_midi():
    # Minimal type-1 MIDI with one melodic channel; use project writer for deterministic bytes.
    tr = MidiTrack([])
    m = MidiFile(format_type=1, ppq=480, tracks=[tr])
    return m


def test_scope_gate_rejects_outside_change():
    # Reuse a real benchmark to avoid constructing malformed MIDI internals.
    root = Path(__file__).resolve().parents[1]
    p = root / "tests" / "fixtures" / "ai_learning" / "input" / "pa800_benchmark.mid"
    if not p.exists():
        return
    before = MidiFile.from_bytes(p.read_bytes())
    notes = before.notes()
    n = notes[0]
    changed = before.replace_notes(track_index=n.track, channel=n.channel, start_tick=n.start, end_tick=n.end+1,
                                   new_notes=[Note(n.track,n.channel,n.pitch,n.start,n.end+2,n.velocity)])
    ok,_ = _scope_safe(before, changed, track=99, channel=15, start=0, end=1)
    assert ok is False
