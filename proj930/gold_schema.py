#!/usr/bin/env python3
"""Rekurzivna zabrana actionable velocity/bank/program podataka u GOLD runtimeu."""

from __future__ import annotations

import re


FORBIDDEN_NORMALIZED_KEYS = frozenset({
    "velocity", "velocities", "velocitycurve", "velocitytable",
    "bank", "bankmsb", "banklsb", "bankselect",
    "program", "programchange", "instrumentkey", "instrumentprofileid",
})


def normalize_key(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def forbidden_paths(value, path="patterns"):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if normalize_key(key) in FORBIDDEN_NORMALIZED_KEYS:
                found.append(child_path)
            found.extend(forbidden_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(forbidden_paths(child, f"{path}[{index}]"))
    return found


def validate_patterns(patterns):
    paths = forbidden_paths(patterns)
    return {
        "passed": not paths,
        "forbiddenPaths": paths,
        "checkedPatterns": len(patterns) if isinstance(patterns, list) else 0,
        "goldAffectsVelocity": False,
        "goldAffectsBankSelect": False,
        "goldAffectsProgramChange": False,
    }


def assert_valid_patterns(patterns):
    result = validate_patterns(patterns)
    if not result["passed"]:
        preview = ", ".join(result["forbiddenPaths"][:8])
        raise ValueError("GOLD runtime schema sadrži zabranjene actionable podatke: " + preview)
    return result