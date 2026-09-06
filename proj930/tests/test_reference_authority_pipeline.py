from pathlib import Path

from reference_authority_pipeline import REFERENCE_DOMAINS, build_reference_plan


ROOT = Path(__file__).resolve().parents[1]


def test_all_reference_domains_are_explicit_and_consumed():
    plan = build_reference_plan(ROOT)
    assert plan["policy"]["fallbacks"] == "FORBIDDEN"
    assert set(plan["domains"]) == set(REFERENCE_DOMAINS)
    assert all(domain["consumers"] for domain in plan["domains"].values())


def test_reference_plan_is_complete_for_current_snapshot():
    plan = build_reference_plan(ROOT)
    assert plan["coverage"]["status"] == "PATH_ONLY"
    assert plan["coverage"]["path_coverage_only"] is True
    assert plan["policy"]["path_coverage_pass_is_not_export_authority"] is True
    assert plan["coverage"]["ratio"] == 1.0
    assert not plan["coverage"]["missing"]


def test_reference_files_are_hashed():
    plan = build_reference_plan(ROOT)
    assert plan["referenced_files"]
    assert all(len(digest) == 64 for digest in plan["referenced_files"].values())
