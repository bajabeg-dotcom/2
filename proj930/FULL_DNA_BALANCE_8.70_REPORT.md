# DNA MIDI Studio 8.70 — Full DNA Balance / Cross-Role Calibration

## Status
SOFTWARE VALIDATED for the implemented 8.70 scope. Physical Pa800 listening remains an external gate.

## Purpose
8.70 combines the previously calibrated role DNA layers at candidate-ranking time. It does **not** add missing instruments and it does **not** write velocity. It evaluates whether a candidate leaves musically appropriate space for roles already present in the song.

## Cross-role rules
- Bass ↔ drums: pocket/onset relationship, not lock-to-every-kick.
- Rhythm guitar ↔ pad/strings: active-space balance; excessive sustained masking is penalized.
- Brass ↔ solo/lead: call-response preference; excessive simultaneous attacks are penalized.
- Terca ↔ lead: supportive partial overlap, never blanket doubling.
- Echo ↔ lead: answer-space preference; dense simultaneous copying is penalized.

## Safety
- Read-only scorer: no MIDI mutation.
- Existing roles only: no orchestration is invented by this layer.
- Velocity is not read as evidence and is never authored here.
- Factory remains the sole velocity authority.
- Existing 8.31 terca eligibility and rhythm-guitar gate/polyphony protections remain active.

## Integration
`FullDNABalanceCalibration` is integrated into `CandidatePreferenceBrain` 8.70. Its score contributes to `cross_track_fit`; detected conflicts add `WEAK_CROSS_ROLE_BALANCE` to critic reasons.

## Validation
Executed regression set: **23/23 PASS**.
Coverage included 8.70 balance, candidate critic, power-riff DNA, accompaniment DNA, solo ornament DNA, terca eligibility, rhythm-guitar DNA, and full-song autoregressive regeneration with Factory velocity proof.

## Known limitation
The current balance layer is symbolic/onset/active-space based. Final audible masking still needs listening on the target Pa800 sound set because oscillator/envelope behavior can make two symbolically similar arrangements sound different.
