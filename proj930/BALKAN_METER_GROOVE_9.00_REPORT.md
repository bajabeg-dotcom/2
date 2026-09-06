# DNA MIDI Studio 9.00 — Balkan Meter / Groove Calibration

## Purpose
Evidence-driven meter calibration from GOLD performance patterns. No velocity data is consumed; Factory remains the only velocity authority.

## Direct GOLD coverage
- 4/4: 8,057 patterns
- 2/4: 3,846 patterns
- 7/8: 628 patterns
- 9/8: 94 patterns
- 1/4 and 6/4 are retained as registry evidence but are not promoted as primary Balkan calibration families.
- 6/8: insufficient direct GOLD coverage in the current registry; uses a conservative low-confidence fallback and is never reported as learned.

## Behavior
- Builds per-meter GOLD profiles for density, median gate and syncopation.
- Candidate critic blends meter fit into groove and density ranking.
- Odd meters no longer inherit a universal 4/4 score prior.
- Unknown/low-evidence meters remain conservative and close to neutral.
- Velocity is excluded from all profiles and scoring.

## Safety
- Read-only calibration; does not mutate MIDI.
- Does not change meter, tempo, harmony, form or velocity.
- Existing 8.80 KEEP/REPAIR conservatism remains intact.

## Verification
Targeted 9.00 + 8.80/full-song regression: 13/13 PASS.
