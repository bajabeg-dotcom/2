from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio.symbolic_foundation import SymbolicFoundation, extract_musecoco_style_attributes


def _fixture():
    for p in (ROOT / "artifacts").rglob("*.mid"):
        return p.read_bytes()
    raise RuntimeError("no MIDI fixture")


def test_symbolic_foundation_velocity_blind_and_vendored():
    raw = _fixture()
    f = SymbolicFoundation(ROOT)
    r = f.analyze(raw, "fixture.mid")
    assert r.attributes.velocity_used is False
    assert r.facts["velocityUsed"] is False
    assert r.facts["musecocoVendored"] is True
    assert r.sequence.tokens[0] == "BOS"
    assert r.sequence.tokens[-1] == "EOS"
    assert not any(t.startswith("VEL_") or t.startswith("VELOCITY_") for t in r.sequence.tokens)


def test_objective_attributes_are_nonempty():
    a = extract_musecoco_style_attributes(_fixture(), "fixture.mid")
    assert a.bars >= 1
    assert a.note_count > 0
    assert len(a.tracks) > 0
    assert a.density_class in {"sparse", "medium", "dense", "very-dense"}
    assert a.polyphony_class in {"monophonic", "light-polyphonic", "polyphonic", "thick"}


def test_generation_intent_has_factory_velocity_authority():
    intent = SymbolicFoundation(ROOT).generation_intent(_fixture(), "fixture.mid")
    assert intent["velocityAuthority"] == "FACTORY_ONLY"
    assert intent["velocityUsedInPlanning"] is False
    assert intent["tracks"]
