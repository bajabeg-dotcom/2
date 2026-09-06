# DNA MIDI Studio 8.10 — Bass + Drum DNA Calibration

## Scope
This checkpoint calibrates bass/drum musical behavior from GOLD DNA while preserving Factory-only velocity authority.

## GOLD evidence used
- 2,866 bass performance patterns.
- 1,442 drum performance patterns.
- 4,206 shared-source drum↔bass groove relationships from 168 unique source hashes.
- GOLD drum element counts: closed-hat 11,789; percussion 8,303; snare 6,064; kick 3,083; open-hat 1,535; tom 1,235; crash 455; ride 330.
- 70 explicit transition drum patterns in the performance registry.

## Learned priors
Bass:
- density q25/median/q75 = 3 / 4 / 5
- median gate q25/median/q75 = 23 / 33.5 / 38 (96-tick performance grid)
- syncopation q25/median/q75 = 0 / 0 / 0.3333

Drums:
- density q25/median/q75 = 8 / 14 / 19
- median gate q25/median/q75 = 12 / 23 / 24 (96-tick performance grid)
- syncopation q25/median/q75 = 0 / 0.1111 / 0.3947

## Runtime wiring
`BassDrumDNACalibration` is read-only and loads `data/dna-bass-drum-calibration-8.10.json`.

CandidatePreferenceBrain now:
1. blends song-local density intent with GOLD bass/drum density priors;
2. compares bass note gate against GOLD bass gate behavior;
3. compares drum element distribution against GOLD kick/snare/hat/tom/cymbal/percussion evidence;
4. strengthens cross-track ranking only when actual local groove also fits, using the 4,206 shared-source drum+bass pairs as relationship evidence.

No backend gets a bonus by identity. No GOLD velocity values are used.

## Authority
- GOLD: timing, gate, groove, density, kick↔bass relationship, fill/transition behavior.
- Factory: velocity and PA800 kit/performance behavior.
- `velocityUsed=false` for this calibration layer.

## Tests
Combined regression run: 34 PASS, 0 FAIL.
Includes DNA relationship grammar, melodic relationship learning, rhythm-guitar polyphony, self-refinement, cross-track brain, hierarchical planner, generative router, and full-song autoregressive regeneration.
