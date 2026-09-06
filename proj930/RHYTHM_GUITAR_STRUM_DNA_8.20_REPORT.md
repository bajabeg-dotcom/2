# DNA MIDI Studio 8.20 — Rhythm Guitar / Strum DNA Calibration

## Authority contract
- GOLD: accompaniment intent only — density, gate, syncopation, section/transition character.
- Factory: authoritative strum execution — stroke direction, inter-string spread, playable voicing, Factory velocity/performance.
- GOLD velocity is never consumed by this calibration layer.

## Corpus evidence
- Factory strumming patterns: 2,919
- GOLD accompaniment performance patterns: 3,039
- Main Factory meters: 4/4 (2,378), 3/4 (363), 2/4 (102), 6/8 (55), 6/4 (21)
- GOLD accompaniment is primarily body/transition evidence and is used only as a selector prior.

## Implemented
- Added `RhythmGuitarDnaCalibrator`.
- Builds section+meter GOLD intent profiles for density, median gate, syncopation, starts-with-rest and ends-with-space behavior.
- Scores compatible Factory strum candidates against GOLD intent while preserving Factory as the physical execution authority.
- Explicitly rewards polyphonic chord attacks and penalizes effectively mono-like strokes.
- Preserves 7.41 rule: generic safe repair cannot stagger a valid block chord into an invented arpeggio.
- No synthetic Guitar Mode control notes are introduced by this calibration layer.

## Tests
- New 8.20 calibration tests: 3/3 PASS.
- Combined regression set: 28/28 PASS.
- Includes rhythm-guitar polyphony, role-first optimizer, self-refinement, candidate critic, cross-track, symbolic foundation, hierarchical planner, full-song regeneration, bass/drum DNA and terca/echo DNA tests.

## Known boundary
GOLD does not directly authorize physical Down/Up string execution. It selects the musical intent; Factory evidence remains required for the actual strum pattern and playable voicing.
