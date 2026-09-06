# DNA MIDI Studio 7.10 — GitHub Symbolic Foundation

## Vendored upstream code
- MidiTok (MIT): `third_party/miditok/` — official source package, including REMI implementation.
- Microsoft Muzic / MuseCoco objective MIDI attribute extractor (MIT): `third_party/muzic_musecoco/`.

## Integration
`src/dna_midi_studio/symbolic_foundation.py` provides one canonical front door:
1. Validate/use vendored MidiTok REMI+ semantics when its dependencies (`symusic`, `tokenizers`, etc.) are available.
2. Preserve DNA's section/chord/role enriched deterministic token stream as the canonical fallback.
3. Extract MuseCoco-style objective planning attributes: instrumentation, density, polyphony, pitch/register and rhythmic onset statistics.
4. Velocity is excluded from both token planning and attributes. Factory remains the sole velocity authority.

## Why this layer exists
The generator should receive a structured musical intent before REPAIR/REGENERATE. This prevents MIDI-GPT or DNA neural backends from being asked to improvise without knowing the song's global instrumentation/density context.

## Generator connection
`GenerativeBackendRouter` now converts the symbolic foundation's objective track density into MIDI-GPT `note_density` conditioning (0..9) before generation. This is planning-only; velocity remains excluded and is still rendered by Factory after candidate acceptance.
