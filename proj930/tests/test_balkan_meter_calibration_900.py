from pathlib import Path
from dna_midi_studio.balkan_meter_calibration import BalkanMeterCalibration

ROOT=Path(__file__).resolve().parents[1]

def test_direct_gold_meter_coverage_and_velocity_free():
    c=BalkanMeterCalibration(ROOT)
    d=c.to_dict()
    assert d['velocityUsed'] is False
    assert d['profiles']['4/4']['patterns'] > 8000
    assert d['profiles']['2/4']['patterns'] > 3800
    assert d['profiles']['7/8']['patterns'] > 600
    assert d['profiles']['9/8']['patterns'] > 90

def test_7_8_is_direct_learned_not_4_4_alias():
    c=BalkanMeterCalibration(ROOT)
    p=c.profile('7/8'); q=c.profile('4/4')
    assert p.learned and p.patterns >= 600
    assert (p.density_median,p.gate_median,p.sync_median)!=(q.density_median,q.gate_median,q.sync_median)

def test_6_8_is_factory_backed_learned_in_901():
    c=BalkanMeterCalibration(ROOT)
    p=c.profile('6/8')
    assert p.learned
    assert p.patterns >= 48
    assert p.confidence >= .5

def test_matching_7_8_profile_beats_mismatched_candidate():
    c=BalkanMeterCalibration(ROOT); p=c.profile('7/8')
    good,_=c.candidate_fit(meter='7/8',density=p.density_median,gate96=p.gate_median,syncopation=p.sync_median)
    bad,_=c.candidate_fit(meter='7/8',density=p.density_median*4+20,gate96=p.gate_median*4+50,syncopation=min(1,p.sync_median+.7))
    assert good > bad
