from dna_midi_studio.full_dna_balance import _range_fit, FullDNABalanceCalibration


def test_range_fit_prefers_target_window():
    assert _range_fit(.5,.38,.88)==1.0
    assert _range_fit(.98,.38,.88)<1.0


def test_pair_rules_are_velocity_free():
    from dna_midi_studio.full_dna_balance import PAIR_RULES
    assert ('bass','drums') in PAIR_RULES
    assert ('brass','solo') in PAIR_RULES
    assert ('echo','solo') in PAIR_RULES
    assert all('velocity' not in str(v).lower() for v in PAIR_RULES.values())


def test_balance_version():
    assert FullDNABalanceCalibration.VERSION=='8.70'
