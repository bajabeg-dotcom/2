from dna_midi_studio.arranger_lifecycle import evaluate_lifecycle, lifecycle_policy
from dna_midi_studio.midi import Note

def N(s,e,p=48): return Note(0,12,p,s,e,80)

def test_powerchord_mid_section_dropout_is_rejected():
    ppq=96; end=8*4*ppq; notes=[]
    for b in range(4,7):
        s=b*4*ppq; notes += [N(s,s+60,48),N(s,s+60,55)]
    r=evaluate_lifecycle(notes,role='power-riff',section_label='chorus',section_start=0,section_end=end,ppq=ppq)
    assert not r.pass_lifecycle
    assert 'LATE_UNEXPLAINED_ENTRY' in r.reasons or 'SECTION_COVERAGE_TOO_LOW' in r.reasons

def test_powerchord_full_chorus_presence_passes():
    ppq=96; end=8*4*ppq; notes=[]
    for b in range(8):
        base=b*4*ppq
        for q in (0,2*ppq): notes += [N(base+q,base+q+72,48),N(base+q,base+q+72,55)]
    r=evaluate_lifecycle(notes,role='power-riff',section_label='chorus',section_start=0,section_end=end,ppq=ppq)
    assert r.pass_lifecycle, r

def test_foundation_bass_requires_section_continuity():
    p=lifecycle_policy('bass','verse')
    assert p.require_start_anchor and p.require_end_anchor and p.min_coverage>=.8

def test_one_small_syncopated_gap_does_not_fail():
    ppq=96; end=4*4*ppq; notes=[]
    for b in range(4):
        base=b*4*ppq
        for q in (0,ppq,2*ppq,3*ppq): notes.append(N(base+q,base+q+48,48))
    r=evaluate_lifecycle(notes,role='bass',section_label='verse',section_start=0,section_end=end,ppq=ppq)
    assert r.pass_lifecycle
