# Rhythm Guitar Polyphony Fix 7.41

Root cause: role_first_song_optimizer._rhythm_guitar() converted simultaneous chord attacks into generic alternating strums. On DNC/clean rhythm-guitar sounds this reduced exact onset polyphony to one Note On at a time and created a mono/arpeggio-like perception.

Fix:
- safe repair preserves exact chord onset clusters;
- safe repair may repair gate continuity only;
- pitch and velocity multisets remain invariant;
- inter-string timing/strum offsets are reserved for Factory/GOLD evidence-backed strumming engines;
- no generic alternating-strum synthesis in safe repair.

Real VALJA validation: representative 3- and 4-note chord tracks preserve their original exact-onset polyphony after repair.
