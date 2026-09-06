# DNA MIDI Studio 8.60 — Accompaniment / Strings / Brass / Pad DNA Calibration

## Scope
Evidence-driven calibration for accompaniment-family roles without inventing unsupported separate GOLD corpora.

## Authority split
- GOLD: non-velocity arrangement intent only (density, gate, syncopation, section/transition character, chord attack/polyphony evidence).
- Factory: sole velocity and Pa800 performance authority.
- Role behavior policies: projection constraints for pad, strings, brass, choir, organ and piano.

## Evidence
`data/gold-performance-patterns.json` contains 3,039 accepted `accompaniment` performance patterns. The registry does not contain comparably supported separate `strings`, `brass`, or `pad` role corpora, therefore 8.60 explicitly records those as conservative projections from accompaniment evidence rather than falsely claiming independent learning.

## Implemented
- `src/dna_midi_studio/accompaniment_dna.py`
- section/meter/tempo-aware GOLD accompaniment profile selection
- candidate scoring by density, gate, chord polyphony and syncopation
- role projections:
  - PAD: sparse, sustained, low syncopation
  - STRINGS: sustained/common-tone oriented
  - BRASS: shorter, sparser, more attack-oriented
  - CHOIR/ORGAN/PIANO: conservative role-specific projections
- CandidatePreferenceBrain integration for accompaniment-family roles
- velocity-independent scoring proof

## Safety
This layer scores/selects candidates; it does not fabricate new accompaniment tracks by itself. Existing note content, harmony and protected MIDI events remain governed by the existing reconstruction/safety pipeline.

## Tests
Focused + regression suite: 32/32 PASS.
One existing PyTorch nested-tensor warning remains non-fatal.

## Status
SOFTWARE_VALIDATED for this calibration layer. Physical Pa800 listening remains an external device gate.
