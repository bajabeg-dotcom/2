# DNA MIDI Studio – Suno-like Symbolic Brain 6.10

## What changed
- Added `symbolic_language.py`: deterministic REMI+/FIGARO-inspired multi-track token stream with sections/chords/roles. Velocity is excluded.
- Added `suno_like_brain.py`: hierarchical whole-song conductor with section intent, GOLD/Factory corpus memory, multi-candidate retrieval, global critic and bounded retry loop.
- Added `SunoLikeConductor.neural_replace_region(...)`: real A/B/C MIDI generation using the existing neural replacement stack.
- Restored neural assets accidentally missing from 6.03 by carrying forward the 6.01 FULL-AI-BRAIN-GUI checkpoints/data: DNA reconstruction Transformer v2, relationship models, song-context model, event decoder, autoregressive event decoder, phrase planner, 4-bar multibar decoder, section arranger, transition-fill model and learning normalization datasets.
- Added `suno_brain_cli.py` and tests `test_suno_like_brain_v610.py`.

## Production reasoning loop
1. Understand the whole MIDI: tempo, meter, key, chords, phrases, sections and time-scoped track roles.
2. Encode a transformer-ready symbolic language across all tracks.
3. Build a section-level energy/density/novelty/transition plan.
4. Retrieve GOLD/Factory evidence candidates for weak or absent rhythm-core regions.
5. Where requested, create actual neural A/B/C candidates using retrieval + Transformer infill + event/autoregressive/multibar decoders.
6. Score candidates with song context, phrase context, section intent and transition intent.
7. Run a global critic and retry weak roles instead of committing the first locally-good answer.
8. Keep Factory as exclusive velocity authority and preserve protected non-target events.
9. Require MIDI reparse + final Pa800 validator before commit/export.

## Verification performed
- New Suno-like brain tests: 4/4 pass.
- MAX orchestrator regression tests: 3/3 pass.
- Previously broken neural inpainting/track-replacement/multibar tests were rerun after restoring checkpoint assets and the observed cases passed until the combined command reached its execution timeout.
- Direct live smoke generation on the Session 19 benchmark produced three real bass replacement MIDI variants A/B/C, each with 8 notes, through `PERFORMANCE_DNA_V1`, with Factory-only velocity authority.

## Important boundary
This is a Suno-like symbolic arranging architecture, not Suno's proprietary model or audio engine. It reasons over MIDI/song structure and generates/reconstructs MIDI material under DNA/Factory/GOLD/Pa800 constraints.
