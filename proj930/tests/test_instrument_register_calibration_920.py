from pathlib import Path
from types import SimpleNamespace
from dna_midi_studio.instrument_register_calibration import InstrumentRegisterCalibration

ROOT=Path(__file__).resolve().parents[1]
def notes(ps): return [SimpleNamespace(pitch=p) for p in ps]

def test_profiles_are_evidence_backed_and_velocity_free():
    c=InstrumentRegisterCalibration(ROOT); d=c.to_dict()
    assert d['version']=='9.20' and d['velocityUsed'] is False
    assert c.profile('bass').factory_segments > 100
    assert c.profile('rhythm-guitar').factory_segments > 100
    assert c.profile('solo').gold_patterns > 100

def test_solo_high_register_is_not_hard_clamped():
    c=InstrumentRegisterCalibration(ROOT)
    src=notes([76,79,81,83,84,88]); out=notes([76,79,81,84,88,91])
    score,detail=c.candidate_fit(role='solo',source_notes=src,candidate_notes=out)
    assert score > .65
    assert detail['hardClamp'] is False and detail['octaveFold'] is False

def test_unsupported_octave_relocation_scores_worse():
    c=InstrumentRegisterCalibration(ROOT)
    src=notes([60,64,67,69]); good=notes([60,64,67,71]); bad=notes([96,100,103,107])
    gs,_=c.candidate_fit(role='solo',source_notes=src,candidate_notes=good)
    bs,_=c.candidate_fit(role='solo',source_notes=src,candidate_notes=bad)
    assert gs > bs

def test_drum_pitch_is_not_register_scored():
    c=InstrumentRegisterCalibration(ROOT)
    score,d=c.candidate_fit(role='drums',source_notes=notes([36,38,42]),candidate_notes=notes([36,38,42]))
    assert score == 1.0 and d['reason']=='PITCH_IS_ELEMENT_IDENTITY'
