# DNA MIDI Studio 9.30 — RX/DNC Articulation Calibration

## Goal
Calibrate articulation handling so regeneration preserves real expressive evidence and never invents Pa800 RX/DNC triggers without an exact confirmed sound map.

## Implemented
- Added `RxDncArticulationCalibration` (read-only, velocity-free candidate critic).
- Existing pitch-bend, channel aftertouch, CC1, CC2, CC11 and CC64 evidence is measured and expected to survive regeneration.
- Melodic roles compare neighbor/grace/trill context and short-gate articulation against the source phrase.
- Guitar/riff roles preserve source mute/staccato character instead of flattening it.
- Exact sound is resolved from Bank MSB/LSB + Program when present and checked against Factory device evidence.
- Most exact device profiles remain hardware-pending for trigger/playable maps; therefore this module never emits keyswitch, SC1/SC2, Y+/Y-, aftertouch-trigger or RX noise events by itself.
- Candidate critic adds `articulation_fit` and `WEAK_ARTICULATION_FIT` diagnostics.
- Velocity is excluded. Factory remains sole final velocity authority.

## Safety policy
1. Semantic articulation evidence may influence ranking.
2. Existing expressive MIDI events are preserved as evidence.
3. Device trigger insertion requires an exact confirmed sound profile/map.
4. Unknown RX/DNC behavior is never guessed.
5. No bank/program/protected-controller mutation is introduced by this calibration layer.

## Regression
- Group A: 16/16 PASS
- Group B: 14/14 PASS
- Total: 30/30 PASS
- One existing PyTorch nested-tensor warning, no test failure.

## Status
Software calibration complete. Physical Pa800 validation is still required before claiming exact hardware articulation behavior for hardware-pending sounds.
