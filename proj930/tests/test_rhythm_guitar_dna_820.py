from pathlib import Path
from dna_midi_studio.rhythm_guitar_dna import RhythmGuitarDnaCalibrator
from dna_midi_studio.guitar_reconstruction import FactoryStrumPattern, FactoryStrumStroke

ROOT=Path(__file__).resolve().parents[1]

def _pat(pid, chord_size=3, gate=24, spread=3):
    strings=tuple(range(chord_size)); tones=tuple(i%3 for i in range(chord_size)); offs=tuple(round(i*spread/max(1,chord_size-1)) for i in range(chord_size))
    return FactoryStrumPattern(pid,'131.200.173','body','4/4',384,(FactoryStrumStroke(0,'down',strings,tones,offs,gate),),.8,('001.001.001',))

def test_gold_intent_uses_no_velocity():
    c=RhythmGuitarDnaCalibrator(ROOT/'data'); x=c.intent(meter='4/4',section='body')
    assert x.support>0 and x.density>0
    assert 'velocity' not in x.__dict__

def test_polyphonic_factory_pattern_scores_better_than_mono_like():
    c=RhythmGuitarDnaCalibrator(ROOT/'data')
    a,_=c.score_factory_pattern(_pat('001.001.001',3),meter='4/4',section='body')
    b,_=c.score_factory_pattern(_pat('001.001.002',1),meter='4/4',section='body')
    assert a>b

def test_score_reports_velocity_unused():
    c=RhythmGuitarDnaCalibrator(ROOT/'data')
    _,d=c.score_factory_pattern(_pat('001.001.003',4),meter='4/4',section='body')
    assert d['velocityUsed'] is False
    assert d['factoryMetrics']['medianChordSize']>=3
