import json
from pathlib import Path
from dna_midi_studio.dna_relationship_grammar import DnaRelationshipGrammar

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/dna-relationship-grammar-8.00.json'

def test_raw_gold_calibration_covers_entire_dna_gold_archive():
    d=json.loads(DATA.read_text(encoding='utf-8'))
    assert d['source']['midiCount']==182
    assert d['source']['parsedMidiCount']==182
    assert d['source']['failures']==[]
    assert d['policy']['goldVelocityUsed'] is False
    assert d['policy']['velocityAuthority']=='FACTORY_ONLY'

def test_terca_grammar_is_selective_and_contains_thirds_and_sixths():
    d=json.loads(DATA.read_text(encoding='utf-8'))['terca']
    p=d['actionProbabilities']
    assert d['pairCount']>=20
    assert 0.15 < p['SKIP'] < 0.70
    assert p['HOLD']>0.03
    intervals={abs(int(k)) for k in d['intervalProbabilities']}
    assert intervals & {3,4}
    assert intervals & {8,9}

def test_grammar_decisions_are_deterministic_and_velocity_free():
    g=DnaRelationshipGrammar(DATA)
    a=[g.action(kind='terca',index=i,total=24,pitch=60+i%5,start=i*240,variant=1) for i in range(24)]
    b=[g.action(kind='terca',index=i,total=24,pitch=60+i%5,start=i*240,variant=1) for i in range(24)]
    assert a==b
    assert {'PLAY','SKIP'} <= set(a)
    assert g.choose_interval(pitch=64,start=960,index=4,variant=2,candidates=[3,-4,8,-9]) in {3,-4,8,-9}
