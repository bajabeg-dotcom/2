# DNA MIDI Studio 8.31 — Terca Eligibility + Rhythm Guitar Safety Fix

## Fixed

### Terca eligibility
- Terca is no longer a generic second-solo transformation.
- Auto-promotion to TERCA requires an explicit harmony-layer identity (`terca`, `third`, `2nd voice`, `second voice`, `harmony solo`, etc.).
- Vocal/lyric source evidence blocks THIRD/TERCA generation.
- Lyrics elsewhere in a song do not automatically block instrumental solos; lyric events must align with the source-note region, or the source track must have an explicit vocal name hint.
- Existing explicitly identified terca tracks remain supported and DNA PLAY/SKIP/HOLD grammar remains available.

### Rhythm guitar
- 7.41 chord-onset polyphony preservation remains mandatory.
- 8.31 removes broad gate normalization from healthy chordal rhythm guitar.
- Only pathological micro-gates (< ~4.5% quarter-note) may be repaired in the safe role-first pass.
- Normal chord gate, onset, pitch and velocity are preserved.
- Deliberate strum offsets/articulation remain owned by Factory/GOLD evidence-driven strumming, not the generic safe repair pass.

## Verification
Targeted and wider regression set: 28/28 PASS.

## Authority
- GOLD: relationship/performance grammar only.
- Factory: velocity/performance/strumming execution authority.
- Vocal lead: protected from automatic terca generation.
