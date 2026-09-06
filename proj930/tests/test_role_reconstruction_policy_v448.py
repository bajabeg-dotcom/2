from dna_midi_studio.midi import Note
from dna_midi_studio.role_reconstruction_policy import assess_role
PPQ=480

def N(p,s,d=120,v=90,tr=0,ch=0): return Note(tr,ch,p,s,s+d,v)

def test_robotic_block_guitar_requests_reconstruction():
    notes=[]
    for i,t in enumerate(range(0,PPQ*8,PPQ//2)):
        notes += [N(48,t,45,85),N(52,t,45,85),N(55,t,45,85)]
    d=assess_role(notes,PPQ,'rhythm-guitar',evidence_strength=.9)
    assert d.action in {'REPAIR','REPLACE'}
    assert 'ROBOTIC_REPEATED_CHORD_SHAPE' in d.reasons
    assert 'BLOCK_CHORD_NOT_STRUMMED' in d.reasons

def test_power_riff_is_scored_independently():
    notes=[]
    for t in range(0,PPQ*8,PPQ): notes += [N(40,t,120),N(47,t,120),N(52,t,120)]
    d=assess_role(notes,PPQ,'power-riff',evidence_strength=.9)
    assert d.role=='power-riff'
    assert 'WEAK_POWER_VOICING_EVIDENCE' not in d.reasons

def test_solo_never_auto_replaced_by_generic_defect_score():
    notes=[N(p,i*240,200) for i,p in enumerate([60,84,61,85,62,86,63,87]*6)]
    d=assess_role(notes,PPQ,'solo',evidence_strength=1.0)
    assert d.action != 'REPLACE'
    assert 'SOLO_CONTINUITY_LARGE_LEAPS' in d.reasons

def test_echo_requires_source_and_strum_cannot_be_echo():
    tgt=[N(60,120),N(62,360)]
    d=assess_role(tgt,PPQ,'echo',evidence_strength=1.0)
    assert d.action=='MANUAL_REVIEW'
    assert 'ECHO_WITHOUT_CONFIRMED_SOLO_SOURCE' in d.reasons
    src=[N(p,i*240,180) for i,p in enumerate([60,62,64,65,67,65,64,62])]
    strum=[]
    for t in range(120,PPQ*4,PPQ//2): strum += [N(48,t,80),N(52,t+8,80),N(55,t+16,80)]
    d2=assess_role(strum,PPQ,'echo',evidence_strength=1.0,solo_source=src)
    assert d2.action=='MANUAL_REVIEW'
    assert 'STRUMMING_VETO' in d2.reasons

def test_terca_requires_confirmed_solo_source():
    d=assess_role([N(64,0)],PPQ,'third')
    assert d.action=='MANUAL_REVIEW'
