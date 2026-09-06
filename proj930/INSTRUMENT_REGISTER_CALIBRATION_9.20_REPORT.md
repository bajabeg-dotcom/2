# DNA MIDI Studio 9.20 — Instrument / Register Calibration

## Goal
Evidence-based register scoring for regenerated/repaired candidates without hard octave cages.

## Authorities
- Factory: absolute instrument/style register evidence where available.
- GOLD: relative phrase-span/register-motion evidence.
- Original source phrase: primary absolute register anchor for solo/lead material.
- Velocity: FACTORY ONLY; this calibration does not read or author velocity.

## Roles
Bass, rhythm guitar, power-riff/riff, solo/lead, strings, brass, pad, choir, organ, piano and generic accompaniment.
Drums/percussion are explicitly excluded from melodic register scoring because pitch identifies kit elements.

## Safety behavior
- No hard register clamp.
- No automatic octave fold.
- Healthy high-register solo remains valid when supported by the source phrase.
- Unsupported whole-phrase octave relocation receives a lower register score.
- RX/DNC trigger-note extremes are excluded from Factory musical-register statistics.

## Candidate critic integration
CandidatePreferenceBrain VERSION 9.20 adds `register_fit` as a scored dimension. Register fit is backend-neutral and read-only; it only changes candidate ranking.

Weights:
- groove_fit 0.18
- harmonic_fit 0.15
- cross_track_fit 0.20
- repetition_balance 0.10
- density_fit 0.15
- transition_quality 0.10
- safety 0.08
- register_fit 0.10

Total = 1.00.

## Tests executed
Split regression due runtime window:
- Group A: 20/20 PASS
- Group B: 15/15 PASS
- Total: 35/35 PASS
- One existing PyTorch nested-tensor warning; no test failure.

## Physical device status
Not physically certified on Korg Pa800 in this environment. Listening/device validation remains an external release gate.
