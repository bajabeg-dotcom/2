# DNA MIDI Studio 7.01 — MIDI-GPT 0.3.4 Integration

## Source selected
Vendored source: `Metacreation-Lab/MIDI-GPT`, tagged source package `0.3.4`.
License: MIT. Original license is retained in `third_party/MIDI-GPT-0.3.4/LICENSE`.

## Why 0.3.4
The bundled 0.3.4 source provides production implementations for:
- MIDI `Score.from_midi()` / `Score.to_midi()` round-trip
- autoregressive generation
- bar-level infill
- multi-track context
- attribute conditioning
- grammar constrained decoding
- pitch masks
- rhythm masks
- remix schedules (preserve onset schedule while varying pitch/full note values)
- multi-candidate generation via `SamplingSession.run_variations()`
- replay scoring (`score_from_tokens`)
- pretrained checkpoint loading from `Metacreation/MIDI-GPT`
- safetensors checkpoints
- training/preprocess pipeline and unit/integration tests

## DNA Studio policy
MIDI-GPT is a generative backend, not the final authority.

DNA Studio still owns:
1. full-song understanding and section/role planning,
2. KEEP / REPAIR / REGENERATE authorization,
3. Factory-only velocity policy,
4. GOLD/evidence arranger logic,
5. Korg Pa800 bank/program/RX/DNC mapping,
6. final independent verification.

Piece-level MIDI-GPT controls default to:
- `velocity = false`
- `microtiming = false`

This prevents the external model from overriding Factory velocity or introducing unapproved microtiming.

## Files changed
- `third_party/MIDI-GPT-0.3.4/` — exact reviewed source tree
- `scripts/install_midigpt_windows.bat` — installs bundled 0.3.4 source into isolated `.venv-midigpt`
- `scripts/midigpt_worker.py` — advanced JSON worker
- `src/dna_midi_studio/external_midigpt.py` — typed backend bridge
- `tests/test_external_midigpt_bridge.py` — bridge regression tests

## New controls exposed to DNA Conductor
Per-track:
- target bars
- autoregressive mode
- attributes / per-bar attributes
- pitch masks
- rhythm masks
- remix amount/mode

Per-generation:
- temperature
- top-p / top-k
- model dimension
- bars/tracks per step
- seed
- number of candidates
- mask mode
- velocity enable/disable
- microtiming enable/disable

## Verification in this integration session
- Python compilation: PASS
- DNA bridge tests: 4/4 PASS
- vendored source and MIT LICENSE present: PASS
- `num_candidates > 1` routes to official `run_variations()`: PASS by code audit

## External dependency still required
Pretrained model weights are not contained in the GitHub source ZIP. On first model use,
`InferenceEngine.from_pretrained("yellow_medium")` downloads the official checkpoint from
`Metacreation/MIDI-GPT` on Hugging Face and caches it locally.

## Next integration task
Connect FullSongAutoregressiveEngine decisions directly to `MidiGPTTrackControl`:
- REPAIR -> remix / constrained infill
- REGENERATE -> full infill or AR generation
- KEEP -> context only
Then rank generated candidates using DNA global coherence + role fit + harmonic fit + Pa800 verifier.
