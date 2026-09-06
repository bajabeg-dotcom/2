# DNA MIDI Studio 8.80 — Full Corpus / Listening Calibration

## Scope
Corpus-level calibration of the conservative role-first repair path using the canonical VALJA reconstructed corpus. No new instruments are synthesized in this pass. Pitch and velocity invariants remain locked; Factory remains the only velocity authority.

## Corpus
- Canonical VALJA folder processed: 164 MIDI files
- Parse/processing errors: 0
- Audit artifacts:
  - `calibration/corpus_880_audit.json` (pre-calibration baseline)
  - `calibration/corpus_880_postcal_final.json` (post-calibration)

## Main finding
The pre-8.80 safe repair path was over-editing otherwise valid articulation, especially bass gates and short muted/chordal rhythm-guitar gates.

### Before → after
| Role | Before changed notes | Before rate | After changed notes | After rate |
|---|---:|---:|---:|---:|
| Bass | 46,749 / 91,882 | 50.88% | 4,860 / 91,882 | 5.29% |
| Rhythm guitar | 22,794 / 317,853 | 7.17% | 1,813 / 317,853 | 0.57% |
| Power-riff | 2,645 / 11,545 | 22.91% | 0 / 11,545 | 0.00% |
| Solo | 4,415 / 396,325 | 1.11% | 4,415 / 396,325 | 1.11% |
| Echo | 0 / 12,371 | 0.00% | 0 / 12,371 | 0.00% |

## 8.80 policy changes
1. Bass safe repair is now pathological-gate-only. Healthy pocket/gate is preserved.
2. Chordal/polyphonic rhythm guitar is fully gate-preserved in the safe pass, including deliberate short mute/staccato chords.
3. Rolled/arpeggiated rhythm guitar is also pathological-gate-only; normal articulation is preserved.
4. Power-riff 23–29 tick mute/staccato gates are treated as valid corpus evidence, not damage. Only near-zero corruption remains eligible for safe repair.
5. Terca/echo relationship roles remain protected from generic safe transforms.
6. No GOLD velocity authority is introduced; velocity remains Factory-only.

## Validation
Targeted + cross-version regression suite: 29/29 PASS.
Full-song catastrophic drum regeneration still passes and retains Factory velocity proof.

## Status
SOFTWARE_CALIBRATED / WAITING_FOR_DEVICE LISTENING VALIDATION.
Physical Korg Pa800 listening remains the external acceptance gate.
