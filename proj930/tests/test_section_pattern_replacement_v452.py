from pathlib import Path
import json
from dna_midi_studio.midi import Note
from dna_midi_studio.section_pattern_replacement import SectionPatternEvidenceGate

ROOT=Path(__file__).resolve().parents[1]

def _bad_guitar():
    out=[]
    # mechanical repeated block chords, uniform gate, low dynamic diversity
    for i in range(24):
        s=i*48
        for p in (60,64,67): out.append(Note(0,0,p,s,s+8,90))
    return out

def test_gold_never_provides_velocity_authority():
    g=SectionPatternEvidenceGate(ROOT/'data')
    assert g.gold['rules']['velocityDataIncluded'] is False

def test_bad_guitar_can_only_replace_with_factory_strum_and_section_match():
    g=SectionPatternEvidenceGate(ROOT/'data')
    d=g.decide(notes=_bad_guitar(),ppq=96,role='rhythm-guitar',section_label='verse',section_confidence=.95,
               meter='4/4',bpm=110,start_tick=0,end_tick=1152,role_confidence=.95)
    if d.replacement_allowed:
        assert d.candidate is not None and d.candidate.source=='FACTORY_STRUM'
        assert 'SECTION_MISMATCH' not in d.candidate.reasons
        assert d.candidate_margin>=8

def test_low_section_confidence_blocks_destructive_replace():
    g=SectionPatternEvidenceGate(ROOT/'data')
    d=g.decide(notes=_bad_guitar(),ppq=96,role='rhythm-guitar',section_label='verse',section_confidence=.6,
               meter='4/4',bpm=110,start_tick=0,end_tick=1152,role_confidence=.95)
    assert not d.replacement_allowed
    assert 'SECTION_CONFIDENCE_BELOW_REPLACEMENT_THRESHOLD' in d.reasons

def test_solo_echo_terca_not_generic_replacement_roles():
    g=SectionPatternEvidenceGate(ROOT/'data')
    for role in ('solo','echo','terca'):
        d=g.decide(notes=_bad_guitar(),ppq=96,role=role,section_label='chorus',section_confidence=.99,
                   meter='4/4',bpm=110,start_tick=0,end_tick=1152,role_confidence=.99)
        assert not d.replacement_allowed

def test_replacement_decision_schema_exposes_margin_and_authority():
    g=SectionPatternEvidenceGate(ROOT/'data')
    d=g.decide(notes=_bad_guitar(),ppq=96,role='rhythm-guitar',section_label='chorus',section_confidence=.95,
               meter='4/4',bpm=110,start_tick=0,end_tick=1152,role_confidence=.95).to_dict()
    assert 'candidate_margin' in d
    assert d['policy']['velocityAuthority']=='FACTORY_ONLY'
    assert d['policy']['candidateMarginMinimum']==8.0
