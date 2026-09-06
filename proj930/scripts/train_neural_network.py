#!/usr/bin/env python3
"""Compatibility entry point for the canonical local neural trainer.

The old 9.02 implementation duplicated training and promotion logic and could
emit a misleading calibration report. Keep the historical command name, but
route it through scripts/train_local.py so both Windows launchers use the same
finite-metric, dataset-hash, model-byte and fail-closed gates.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from train_local import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
