from pathlib import Path
from dna_midi_studio.dna_relationship_grammar import DnaRelationshipGrammar

ROOT=Path(__file__).resolve().parents[1]

def test_echo_dna_available_and_velocity_free():
    g=DnaRelationshipGrammar(ROOT/'data'/'dna-relationship-grammar-8.00.json')
    assert g.echo_available
    assert g.echo.get('velocityUsed') is False
    assert g.echo.get('pairCount',0) >= 1

def test_echo_action_is_selective_and_deterministic():
    g=DnaRelationshipGrammar(ROOT/'data'/'dna-relationship-grammar-8.00.json')
    a=[g.action(kind='echo',index=i,total=64,pitch=60+(i%5),start=i*120,variant=1) for i in range(64)]
    b=[g.action(kind='echo',index=i,total=64,pitch=60+(i%5),start=i*120,variant=1) for i in range(64)]
    assert a==b
    assert 'SKIP' in a and 'PLAY' in a
    assert sum(x=='PLAY' for x in a) < 48

def test_echo_delay_comes_from_gold_prior():
    g=DnaRelationshipGrammar(ROOT/'data'/'dna-relationship-grammar-8.00.json')
    assert 0.10 <= g.echo_delay_qn(0) <= g.echo_delay_qn(1) <= g.echo_delay_qn(2) <= 1.5
