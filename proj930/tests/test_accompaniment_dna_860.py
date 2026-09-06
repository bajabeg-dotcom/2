from pathlib import Path
from dna_midi_studio.accompaniment_dna import AccompanimentDNACalibration
from dna_midi_studio.midi import Note
ROOT=Path(__file__).resolve().parents[1]

def test_gold_accompaniment_loaded_and_velocity_free():
    d=AccompanimentDNACalibration(ROOT)
    assert len(d.patterns) >= 3000
    p=d.profile('accompaniment')
    assert p and p.pattern_count>0

def test_role_projections_are_distinct_and_sensible():
    d=AccompanimentDNACalibration(ROOT)
    a=d.profile('accompaniment'); pad=d.profile('pad'); br=d.profile('brass'); st=d.profile('strings')
    assert pad.density_median < a.density_median
    assert pad.gate_median > a.gate_median
    assert st.gate_median > br.gate_median

def test_candidate_fit_never_uses_velocity():
    d=AccompanimentDNACalibration(ROOT)
    notes=[Note(track=0,channel=0,pitch=60,velocity=10,start=i*480,end=i*480+1440) for i in range(4)]
    score,detail=d.candidate_fit(notes,480,role='pad')
    assert 0<=score<=1 and detail['velocityUsed'] is False

def test_velocity_changes_do_not_change_fit():
    d=AccompanimentDNACalibration(ROOT)
    a=[Note(track=0,channel=0,pitch=60,velocity=10,start=i*240,end=i*240+200) for i in range(8)]
    b=[Note(track=0,channel=0,pitch=60,velocity=120,start=i*240,end=i*240+200) for i in range(8)]
    assert d.candidate_fit(a,480,role='accompaniment')[0] == d.candidate_fit(b,480,role='accompaniment')[0]
