from pathlib import Path
from dna_midi_studio.tempo_dependent_calibration import TempoDependentCalibration,tempo_bucket

ROOT=Path(__file__).resolve().parents[1]

def test_buckets():
    assert tempo_bucket(72)=='slow'
    assert tempo_bucket(105)=='medium'
    assert tempo_bucket(128)=='brisk'
    assert tempo_bucket(145)=='fast'

def test_real_profiles():
    c=TempoDependentCalibration(ROOT)
    assert c.available
    assert c.profile(115,'bass') is not None
    assert c.profile(145,'drums') is not None
    assert c.to_dict()['velocityUsed'] is False

def test_modifiers_change_with_tempo():
    c=TempoDependentCalibration(ROOT)
    slow=c.modifiers(75,'solo'); fast=c.modifiers(150,'solo')
    assert slow['gateScale'] > fast['gateScale']
    assert slow['ornamentRateScale'] > fast['ornamentRateScale']
    assert fast['fillDensityScale'] > slow['fillDensityScale']
    assert slow['velocityUsed'] is False

def test_candidate_fit_velocity_free():
    c=TempoDependentCalibration(ROOT)
    p=c.profile(110,'bass'); assert p
    score,d=c.candidate_fit(bpm=110,role='bass',density=p.density_median,gate96=p.gate96_median,syncopation=p.syncopation_median)
    assert score>.7
    assert d['velocityUsed'] is False
