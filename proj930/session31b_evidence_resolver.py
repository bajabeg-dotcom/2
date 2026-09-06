#!/usr/bin/env python3
"""CLI for Evidence Authority Resolver 3.0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from dna_midi_studio import build_evidence_ledger  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve Factory/GOLD/analysis/expression/articulation evidence without rendering MIDI"
    )
    parser.add_argument("input", help="JSON object containing a documents field or the documents object itself")
    parser.add_argument("--output", required=True, help="Output EvidenceLedger JSON")
    parser.add_argument("--variant", default="C", help="Selected A/B/C/D variant (default C)")
    args = parser.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    documents = payload.get("documents", payload)
    ledger = build_evidence_ledger(documents, ROOT, selected_variant_id=args.variant)
    Path(args.output).write_text(
        json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    coverage = ledger["coverage"]
    print(
        f"Evidence resolver PASS: {coverage['totalSubjects']} subjects; "
        f"{coverage['decisionCounts']['ALLOW']} allow; "
        f"{coverage['manualActionCount']} manual/block; {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())