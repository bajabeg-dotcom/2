from dna_midi_studio.midi import Note
from dna_midi_studio.role_first_song_optimizer import _rhythm_guitar


def test_block_chord_onsets_remain_polyphonic():
    ppq=480
    notes=[]
    for s in (0,480,960,1440):
        for p in (48,55,60):
            notes.append(Note(0,11,p,s,s+160,90,0,0,None,None,None))
    out, changed, reasons = _rhythm_guitar(notes, ppq)
    before={}
    after={}
    for n in notes: before[n.start]=before.get(n.start,0)+1
    for n in out: after[n.start]=after.get(n.start,0)+1
    assert before == after
    assert max(after.values()) == 3
    assert 'CHORD_ONSET_POLYPHONY_PRESERVED' in reasons
    assert 'FACTORY_STRUM_OFFSETS_ONLY' in reasons


def test_pitch_velocity_multiset_preserved():
    ppq=480
    notes=[Note(0,11,p,0,100,70+i,0,0,None,None,None) for i,p in enumerate((48,52,55,60))]
    notes += [Note(0,11,p,480,580,80+i,0,0,None,None,None) for i,p in enumerate((50,53,57,62))]
    out, *_ = _rhythm_guitar(notes, ppq)
    assert sorted((n.pitch,n.velocity) for n in out) == sorted((n.pitch,n.velocity) for n in notes)
    assert sorted(n.start for n in out) == sorted(n.start for n in notes)

def test_healthy_chord_gates_are_not_normalized_anymore():
    ppq=480
    notes=[]
    for s in (0,480,960):
        for p in (48,52,55):
            notes.append(Note(0,11,p,s,s+150,90,0,0,None,None,None))
    out, changed, reasons = _rhythm_guitar(notes, ppq)
    assert changed == 0
    assert [(n.start,n.end,n.pitch) for n in out] == sorted((n.start,n.end,n.pitch) for n in notes)
    assert 'HEALTHY_GATE_PRESERVED' in reasons
