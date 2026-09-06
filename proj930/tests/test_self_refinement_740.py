from dna_midi_studio.self_refinement import SelfRefinementPolicy


def test_balanced_candidate_stops():
    p=SelfRefinementPolicy().plan(["BALANCED_CANDIDATE"],round_index=1,action="REGENERATE")
    assert p.stop is True


def test_groove_failure_tightens_sampling_and_expands_search():
    p=SelfRefinementPolicy().plan(["WEAK_GROOVE_FIT","WEAK_CROSS_TRACK_FIT"],round_index=1,action="REPAIR")
    assert p.stop is False
    assert p.temperature_delta < 0
    assert p.top_p_delta < 0
    assert p.remix_amount_delta > 0
    assert p.candidate_multiplier >= 2


def test_repetition_failure_increases_creativity_bounded():
    p=SelfRefinementPolicy().plan(["WEAK_REPETITION_BALANCE"],round_index=1,action="REGENERATE")
    assert 0 < p.temperature_delta <= 0.12
    assert p.top_p_delta > 0


def test_safety_failure_stops():
    p=SelfRefinementPolicy().plan(["WEAK_SAFETY"],round_index=1,action="REGENERATE")
    assert p.stop is True
