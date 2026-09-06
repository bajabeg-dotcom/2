# DNA MIDI Studio 9.10 — Tempo-Dependent Calibration

Status: SOFTWARE-VALIDATED TEMPO CALIBRATION

## Purpose
The same symbolic pattern must not be judged identically at 75 BPM and 150 BPM. Version 9.10 adds corpus-derived tempo buckets and role-specific GOLD/Factory priors.

## Tempo buckets
- slow: <90 BPM
- medium: 90–119 BPM
- brisk: 120–139 BPM
- fast: >=140 BPM

GOLD coverage in the current performance registry: slow 1,844 patterns, medium 4,937, brisk 2,651, fast 3,486.
Factory coverage: slow 5,123 segments, medium 11,084, brisk 6,204, fast 4,511.

## Behavior
- Candidate critic evaluates density, gate, syncopation and tempo fit using the role-specific bucket.
- Generator/refinement guidance exposes bounded tempo modifiers for gate, strum spread, ornament rate, echo delay, fill density and bass pickup.
- The calibration layer is read-only: it never mutates notes or velocities directly.
- Velocity is excluded from every tempo profile and remains Factory-only.

## Safety
Tempo calibration cannot override region scope, protected events, Factory velocity authority, 8.31 terca eligibility, or rhythm-guitar chord/gate protections.

## Tests
28/28 PASS across tempo, Balkan meter, Factory style-family, candidate critic, full-song regeneration, rhythm-guitar, solo ornament and echo regression groups.

Known limitation: modifier guidance is intentionally bounded and evidence-based; it does not force creative regeneration when the backend is unavailable or the region is not eligible.
