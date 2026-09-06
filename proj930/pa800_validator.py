#!/usr/bin/env python3
"""Backward-compatible wrapper for the packaged Pa800 validator.

Production code must import :mod:`dna_midi_studio.pa800_validator`.
This top-level module exists only for legacy scripts/tests in portable checkouts.
"""
import sys
from pathlib import Path
_BOOTSTRAP_ROOT = Path(__file__).resolve().parent
_BOOTSTRAP_SRC = _BOOTSTRAP_ROOT / "src"
if _BOOTSTRAP_SRC.is_dir() and str(_BOOTSTRAP_SRC) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_SRC))
from dna_midi_studio.pa800_validator import *  # noqa: F401,F403
