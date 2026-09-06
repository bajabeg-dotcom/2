from pathlib import Path
from dna_midi_studio.factory_style_family_calibration import FactoryStyleFamilyCalibration
from dna_midi_studio.balkan_meter_calibration import BalkanMeterCalibration
ROOT=Path(__file__).resolve().parents[1]

def test_factory_families_are_real_and_velocity_free():
    c=FactoryStyleFamilyCalibration(ROOT); d=c.to_dict()
    assert d['velocityUsed'] is False and d['authority']['goldUsed'] is False
    for fam in ('6/8','rock','techno_dance','ballad','beat'):
        p=d['profiles'][fam]
        assert p['learned'] and p['segments'] >= 48 and p['styles'] >= 1

def test_factory_6_8_replaces_old_fallback():
    c=BalkanMeterCalibration(ROOT); p=c.profile('6/8')
    assert p.learned and p.patterns >= 48 and p.confidence >= .5

def test_matching_family_beats_bad_candidate():
    c=FactoryStyleFamilyCalibration(ROOT); p=c.profile('rock')
    good,_=c.candidate_fit(family='rock',density=p.density_median,gate96=p.gate96_median,tempo=p.tempo_median)
    bad,_=c.candidate_fit(family='rock',density=p.density_median*5+20,gate96=p.gate96_median*5+50,tempo=p.tempo_median+80)
    assert good>bad
