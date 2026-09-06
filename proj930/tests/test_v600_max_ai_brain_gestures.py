from dna_midi_studio.midi import Note
from dna_midi_studio.performance_gesture_brain import bass_gestures, guitar_gestures


def test_bass_slide_candidate_is_phrase_aware():
    ppq=480
    notes=[
        Note(0,0,40,0,420,82),
        Note(0,0,42,430,800,86),
        Note(0,0,47,810,1260,94),
    ]
    out=bass_gestures(notes,ppq)
    assert out
    assert all(g.technique=='slide' for g in out)
    assert any(g.interval in (2,5) for g in out)


def test_guitar_slide_only_connected_motion():
    ppq=480
    notes=[Note(0,1,60,0,200,80),Note(0,1,62,205,420,82),Note(0,1,70,900,1100,88)]
    out=guitar_gestures(notes,ppq)
    assert len(out)==1
    assert out[0].target_pitch==62
