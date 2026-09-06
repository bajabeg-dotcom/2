from dna_midi_studio.midi import Note
from dna_midi_studio.role_first_song_optimizer import _bass, _rhythm_guitar

def N(p,s,e,ch=8): return Note(0,ch,p,s,e,90,0,0,None,None,None)

def test_healthy_bass_gate_is_preserved():
    notes=[N(40,0,180),N(43,240,430),N(45,480,700),N(47,720,900)]
    out,changed,reasons=_bass(notes,480)
    assert changed==0
    assert [(x.start,x.end) for x in out]==[(x.start,x.end) for x in notes]
    assert 'HEALTHY_POCKET_PRESERVED' in reasons

def test_broken_micro_bass_gate_is_repaired_only_where_needed():
    notes=[N(40,0,8),N(43,240,430),N(45,480,700),N(47,720,900)]
    out,changed,_=_bass(notes,480)
    assert changed==1
    assert out[0].end>8 and out[1].end==430

def test_healthy_rolled_guitar_is_not_normalized():
    notes=[N(60,0,100,11),N(64,55,150,11),N(67,110,205,11),N(72,165,260,11)]
    out,changed,reasons=_rhythm_guitar(notes,480)
    assert changed==0
    assert [(x.start,x.end) for x in out]==[(x.start,x.end) for x in notes]
    assert 'HEALTHY_GATE_PRESERVED' in reasons

def test_short_chordal_guitar_mute_gate_is_preserved():
    notes=[]
    for s in (0,120,240,360):
        for p in (48,55,60): notes.append(N(p,s,s+16,11))
    out,changed,reasons=_rhythm_guitar(notes,480)
    assert changed==0
    assert all((b.end-b.start)==16 for b in out)
    assert 'CHORD_GATE_FULLY_PRESERVED' in reasons
