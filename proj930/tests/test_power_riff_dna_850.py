from pathlib import Path
from dna_midi_studio.power_riff_dna import PowerRiffDNACalibration
from dna_midi_studio.role_first_song_optimizer import _power_riff
from dna_midi_studio.midi import Note

ROOT=Path(__file__).resolve().parents[1]

def n(p,s,e,v=90): return Note(0,12,p,s,e,v)

def test_gold_power_riff_corpus_loaded_velocity_free():
    d=PowerRiffDNACalibration(ROOT)
    assert len(d.patterns) > 4000
    p=d.profile(meter='4/4',section='body')
    assert p and p.pattern_count > 100
    fit,detail=d.candidate_fit([n(48,0,96),n(55,0,96),n(60,0,96),n(48,192,288),n(55,192,288)],96)
    assert detail['velocityUsed'] is False

def test_power_voicing_scores_above_mono_like():
    d=PowerRiffDNACalibration(ROOT)
    good=[n(48,0,48),n(55,0,48),n(60,0,48),n(48,96,144),n(55,96,144),n(60,96,144)]*4
    mono=[n(48,i*48,i*48+24) for i in range(12)]
    sg,_=d.candidate_fit(good,96); sm,_=d.candidate_fit(mono,96)
    assert sg > sm

def test_safe_repair_preserves_healthy_staccato():
    src=[n(48,0,24),n(55,0,24),n(48,48,72),n(55,48,72)]
    out,changed,reasons=_power_riff(src,96)
    assert changed==0
    assert [(x.start,x.end,x.pitch) for x in out]==[(x.start,x.end,x.pitch) for x in src]
    assert 'HEALTHY_STACCATO_PRESERVED' in reasons

def test_safe_repair_only_repairs_micro_gate():
    src=[n(48,0,2),n(55,0,2),n(48,48,72),n(55,48,72)]
    out,changed,_=_power_riff(src,96)
    assert changed==2
    assert out[0].end>2 and out[1].end>2
    assert out[2].end==72 and out[3].end==72
