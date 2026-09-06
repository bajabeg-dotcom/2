from pathlib import Path
from dna_midi_studio.bass_drum_dna_calibration import BassDrumDNACalibration

ROOT=Path(__file__).resolve().parents[1]

def test_gold_bass_drum_calibration_is_present_and_velocity_free():
    c=BassDrumDNACalibration(ROOT)
    assert c.available
    assert c.to_dict()['velocityUsed'] is False
    b=c.role_profile('bass'); d=c.role_profile('drums')
    assert b and b.pattern_count >= 2800
    assert d and d.pattern_count >= 1400
    assert 3 <= b.density_median <= 5
    assert 10 <= d.density_median <= 18


def test_shared_source_relationship_prior_is_strong():
    c=BassDrumDNACalibration(ROOT)
    assert c.raw['relationships']['sharedSourceDrumBassPairs'] >= 4000
    assert c.raw['relationships']['uniqueSourceHashes'] >= 160
    assert c.shared_groove_confidence() > .95


def test_drum_element_prior_is_normalized():
    c=BassDrumDNACalibration(ROOT)
    p=c.drum_element_prior()
    assert p['kick'] > 0 and p['snare'] > 0 and p['closed-hat'] > 0
    assert abs(sum(p.values())-1.0) < 1e-5

def test_gold_gate_and_element_priors_are_non_velocity_features():
    c=BassDrumDNACalibration(ROOT)
    b=c.role_profile('bass'); d=c.role_profile('drums')
    assert b.gate_median > 0 and d.gate_median > 0
    prior=c.drum_element_prior()
    assert prior['closed-hat'] > prior['crash']
    assert c.raw['rules']['velocityUsed'] is False
