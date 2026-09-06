# DNA MIDI Studio 7.50 — Hierarchical Song Planner

Status: PASS.

Implemented:
- SongMap 2.0 driven global section plan;
- normalized section energy curve;
- role lifecycle across sections (entry, exit, active, silence, density, polyphony);
- transition intents: establish / continue / build / lift / release / resolve;
- low-confidence and ending sections are conservative destructive-regeneration zones;
- full-song REGENERATE consults the global plan before invoking MIDI-GPT/DNA backends;
- read-only planner; velocity is never read for planning;
- Factory-only velocity authority unchanged.

Tests:
- 19/19 hierarchical + 7.41/7.40/7.30/7.20/7.10/router targeted regressions PASS;
- 2/2 full-song autoregressive regressions PASS, including catastrophic drum regeneration with Factory velocity.
