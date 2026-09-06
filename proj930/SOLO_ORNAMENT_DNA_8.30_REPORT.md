# DNA MIDI Studio 8.30 — SOLO / ORNAMENT DNA CALIBRATION

Status: SOFTWARE VALIDATED (targeted regression); physical Pa800 listening remains external.

## Raw GOLD evidence
- Source MIDI files parsed: 182 / 182
- Melodic notes analyzed: ~319k
- Grace evidence: 10,541 events (~3.2987 / 100 notes)
- Trill evidence: 5,352 events (~1.6748 / 100 notes)
- Slide-context evidence: 684 events (~0.2140 / 100 notes)
- Pitch-bend evidence: 1,203 events (~0.3765 / 100 notes)
- Velocity used by this calibration: NO

## Implemented
1. Raw GOLD placement priors by phrase position (start/body/cadence).
2. Deterministic GOLD interval selection for grace/trill.
3. GOLD duration priors for generated ornament notes.
4. Corpus-rate gating so a long solo is not ornamented at every eligible gap.
5. Small phrase/fixture compatibility: evidence coverage remains available when the phrase is too short for statistically useful rate sampling.
6. Candidate critic blends GOLD ornament-density fit into melodic solo preference ranking.
7. Factory remains the only velocity authority.
8. Existing pitch-bend is treated as performance evidence to preserve; 8.30 does not synthesize arbitrary pitch-wheel curves.

## Safety carried forward
- 8.31 terca eligibility rules remain active: no automatic terca on vocal/lyrics accompaniment and no auto-third on arbitrary second solos.
- 7.41/8.20 rhythm-guitar polyphony/gate protections remain active.
- Original solo notes are immutable in the Session-5 augmentation path.

## Regression
74 / 74 PASS on combined 8.30, 8.31, 8.20, 8.10, 8.00, 7.50, 7.40, 7.30, 7.20, 7.10 and full-song targeted tests.
One PyTorch nested-tensor warning is non-fatal.
