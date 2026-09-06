# DNA MIDI Studio 8.40 — Echo / Answer DNA Calibration

## Scope
- GOLD relationship grammar drives echo PLAY / SKIP / HOLD selection.
- GOLD median delay and duration ratio drive echo timing instead of a fixed generic delay table.
- Echo remains a separate relationship layer and never becomes recursive into the next source onset.
- Long source-note tails may overlap an echo attack when the echo still ends before the next source onset.
- Velocity remains Factory-only; GOLD echo grammar has `velocityUsed=false`.

## Evidence
The current DNA relationship grammar contains 4 strong raw-GOLD echo pairs covering 2,258 source notes / 1,825 target notes:
- PLAY 561 (24.84%)
- SKIP 930 (41.19%)
- HOLD 767 (33.97%)
- GOLD median delay: 0.4505 quarter notes
- GOLD median duration ratio: 1.0 before conservative renderer scaling

Phrase priors strongly reduce automatic echo at phrase starts and permit more answers in body/cadence regions.

## Tests
Focused + DNA regression: 38 PASS.

## Safety
- No velocity learned from GOLD.
- Source solo is protected.
- Echo candidate may not cross the next source onset.
- Existing 8.31 terca eligibility and rhythm-guitar safety rules remain unchanged.
