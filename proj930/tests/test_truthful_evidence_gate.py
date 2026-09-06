from pathlib import Path

from truthful_evidence_gate import EvidenceGateBlocked, TruthEvidenceGate, build_truth_report


ROOT = Path(__file__).resolve().parents[1]


def test_current_checkout_is_blocked_by_content_evidence_not_path_presence():
    report = build_truth_report(ROOT)
    assert report["status"] == "BLOCKED"
    assert report["can_transform"] is False
    assert report["can_export"] is False
    assert report["source_counts"] == {
        "factory_archive_members": 3211,
        "gold_archive_members": 182,
        "expected_full_source_inputs": 3393,
    }
    assert report["domains"]["learning"]["status"] == "BLOCKED"
    assert report["domains"]["full_corpus"]["status"] == "PENDING"
    assert report["role_matrix"]["piano"]["exportable"] is False
    assert report["role_matrix"]["choir"]["gold"] == "PROXY"


def test_blocked_gate_cannot_be_used_as_a_transform_override():
    report = build_truth_report(ROOT)
    gate = TruthEvidenceGate(ROOT)
    try:
        gate.assert_transform_allowed({"gate": report}, {})
    except EvidenceGateBlocked:
        pass
    else:
        raise AssertionError("a BLOCKED gate must not authorize a transform")


def test_missing_gate_is_not_a_legacy_default():
    gate = TruthEvidenceGate(ROOT)
    try:
        gate.assert_transform_allowed(None, {})
    except EvidenceGateBlocked as exc:
        assert "no signed evidence gate" in str(exc)
    else:
        raise AssertionError("missing gate must be rejected")
