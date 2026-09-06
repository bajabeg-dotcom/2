# DNA MIDI Studio 6.20 — Full-Song Autoregressive Reconstruction

## What changed

6.20 turns the 6.10 Suno-like conductor into a bounded whole-song reconstruction loop.
It analyzes the entire MIDI, builds a role/section map, partitions owned tracks into musical
regions, and assigns **KEEP / REPAIR / REGENERATE** decisions.

### Execution hierarchy

1. Whole-song understanding: bars, sections, meter, role ownership.
2. Evidence scoring from GOLD + Factory pattern memory.
3. Conservative role-first repair for timing/gate defects while preserving pitch and velocity.
4. Bounded regeneration only for high-priority, sufficiently supported accompaniment regions.
5. A/B/C neural/evidence candidate generation via the restored 6.01 neural stack.
6. Candidate ranking from context, phrase, orchestration and continuity scores.
7. Factory-only velocity proof for every accepted generated region.
8. Independent final checks outside authorized regeneration windows.

### Protected behavior

- Solo, terca/third and echo are never blindly regenerated.
- Healthy regions are preserved.
- Source file is never overwritten.
- Meta, SysEx, Bank Select and Program Change are protected.
- Generated notes require Factory velocity profiles.

### Current generators

The shipped TrackReplacementEngine provides strongest generative coverage for drums and bass,
plus evidence/performance-DNA paths for rhythm guitar, power-riff and accompaniment. Unsupported
roles are explicitly declined rather than reported as generated.

## Main API

```python
from dna_midi_studio.suno_like_brain import reconstruct_full_song_autoregressive
result = reconstruct_full_song_autoregressive(raw, project_root=ROOT, source="song.mid")
out_bytes = result["midiBytes"]
report = result["report"]
```
