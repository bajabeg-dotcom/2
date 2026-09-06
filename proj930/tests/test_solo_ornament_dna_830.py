from pathlib import Path

from dna_midi_studio.solo_ornament_dna import SoloOrnamentDNACalibration

ROOT = Path(__file__).resolve().parents[1]


def test_raw_gold_ornament_calibration_available_and_velocity_free():
    dna = SoloOrnamentDNACalibration(ROOT)
    assert dna.available
    payload = dna.to_dict()
    assert payload["velocityUsed"] is False
    assert payload["source"]["parsedMidiCount"] == 182
    assert payload["source"]["midiCount"] == 182
    assert payload["ornaments"]["grace"]["events"] > 1000
    assert payload["ornaments"]["trill"]["events"] > 1000


def test_interval_selection_is_deterministic_and_idiomatic():
    dna = SoloOrnamentDNACalibration(ROOT)
    a = dna.choose_interval("grace", index=7, pitch=67, start=3840, variant=1)
    b = dna.choose_interval("grace", index=7, pitch=67, start=3840, variant=1)
    assert a == b
    assert a is not None and 1 <= abs(a) <= 4
    t = dna.choose_interval("trill", index=4, pitch=69, start=1920, variant=2)
    assert t is not None and 1 <= abs(t) <= 3


def test_placement_and_duration_are_bounded():
    dna = SoloOrnamentDNACalibration(ROOT)
    ppq = 480
    for kind in ("grace", "trill", "slide"):
        score = dna.placement_score(kind, index=5, total=24, gap_ticks=80, ppq=ppq)
        assert 0.0 <= score <= 1.0
    assert 12 <= dna.note_duration_ticks("grace", ppq, 60) <= round(ppq * .22)
    assert 12 <= dna.note_duration_ticks("trill", ppq, 60) <= round(ppq * .22)


def test_corpus_rate_gate_does_not_ornament_every_eligible_note():
    dna = SoloOrnamentDNACalibration(ROOT)
    total = 160
    placed = {}
    for kind in ("grace", "trill", "slide"):
        hits = sum(
            dna.should_place(
                kind,
                index=i,
                total=total,
                pitch=60 + (i % 12),
                start=i * 120,
                gap_ticks=90,
                ppq=480,
                variant=1,
            )
            for i in range(total)
        )
        placed[kind] = hits
        assert hits < total // 4
    assert placed["grace"] >= placed["trill"] >= placed["slide"]


def test_candidate_fit_is_bounded_and_velocity_independent():
    from dna_midi_studio.midi import Note
    dna = SoloOrnamentDNACalibration(ROOT)
    notes_a = [Note(0, 0, 60 + (i % 5), i * 120, i * 120 + 90, 30 + (i % 80)) for i in range(40)]
    notes_b = [Note(n.track, n.channel, n.pitch, n.start, n.end, 127 if n.velocity != 127 else 1) for n in notes_a]
    a = dna.candidate_fit(notes_a, 480)
    b = dna.candidate_fit(notes_b, 480)
    assert 0.0 <= a <= 1.0
    assert a == b
