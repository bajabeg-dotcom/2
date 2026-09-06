from pathlib import Path
from dna_midi_studio.cross_track_brain import CrossTrackBrain
from dna_midi_studio.midi import MidiFile


def _fixture(root: Path) -> Path:
    candidates=list((root/'artifacts').rglob('*.mid'))+list((root/'tests'/'fixtures').rglob('*.mid'))+list((root/'tests').rglob('*.mid'))
    assert candidates
    return candidates[0]


def test_cross_track_context_excludes_velocity():
    root=Path(__file__).resolve().parents[1]
    p=_fixture(root)
    raw=p.read_bytes(); m=MidiFile.from_bytes(raw)
    ns=m.notes(); assert ns
    n=ns[0]
    brain=CrossTrackBrain(root)
    c=brain.analyze(raw,track_index=n.track,channel=n.channel,role='bass',start_tick=n.start,end_tick=max(n.end,n.start+m.ppq*4),source=p.name)
    assert c.velocity_used is False
    assert 1 <= c.suggested_density_level <= 9
    assert 0.7 <= c.suggested_temperature <= 1.1
    assert c.attention_mode.startswith('MUSEFORMER_')


def test_cross_track_controls_are_deterministic():
    root=Path(__file__).resolve().parents[1]
    p=_fixture(root); raw=p.read_bytes(); m=MidiFile.from_bytes(raw); n=m.notes()[0]
    b=CrossTrackBrain(root)
    kw=dict(track_index=n.track,channel=n.channel,role='drums',start_tick=n.start,end_tick=max(n.end,n.start+m.ppq*4),source=p.name)
    a=b.as_generation_controls(raw,**kw); c=b.as_generation_controls(raw,**kw)
    assert a==c
    assert a['velocityUsed'] is False
