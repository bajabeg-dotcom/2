# DNA MIDI Studio 8.50 — Power-Riff / Riff DNA Calibration

## Implemented

- GOLD non-velocity calibration for `power-riff` and `riff` roles.
- Candidate fit uses density, median gate, chord-size, root+fifth/octave voicing and source-proof confidence.
- Candidate Preference Brain blends GOLD riff fit into repetition/groove/cross-track ranking.
- Safe role-first repair no longer forces every power-riff note to ~0.28 quarter-note minimum gate.
- Healthy staccato/mute riff gates are preserved; only pathological micro-gates are repaired.
- GOLD velocity is never read by this calibration. Factory remains sole velocity authority.

## Corpus

- 4,927 GOLD `power-riff` performance patterns.
- 566 GOLD `riff` performance patterns.
- Total riff-family patterns: 5,493.

## Tests

Targeted + regression set: **38/38 PASS**.
Warnings are PyTorch transformer implementation warnings only; no test failures.

## Safety

- No pitch rewriting in safe repair.
- No generic strum transform.
- No velocity authority outside Factory.
- Existing healthy staccato/mute articulation remains unchanged.
