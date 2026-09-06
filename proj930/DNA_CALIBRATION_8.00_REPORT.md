# DNA Calibration 8.00 — Relationship Grammar

## Source truth
- Source archive: `prism-uploads/DNA.zip`.
- GOLD corpus: **182 MIDI files**.
- Tolerant forensic parse: **182/182**.
- Original MIDI files are never rewritten.
- Invalid/orphan/zero-duration note pairs ignored for calibration only: **7332**.
- Velocity is excluded from GOLD relationship grammar; Factory remains the only velocity authority.

## Terca calibration
- Strong raw-GOLD solo↔terca relations: **73**.
- PLAY / SKIP / HOLD: **{'PLAY': 0.4334, 'SKIP': 0.3442, 'HOLD': 0.2224}**.
- Interval probabilities: **{'-3': 0.2281, '3': 0.2234, '4': 0.1289, '9': 0.1288, '-8': 0.0903, '8': 0.0849, '-4': 0.0584, '-9': 0.0572}**.
- Renderer now accepts chord/scale-valid **±3/±4/±8/±9** instead of forcing only +3/+4.
- Existing terca repair preserves the current upper/lower voicing where harmonically valid.
- Fallback rendering is deterministic and corpus-conditioned.

## Echo calibration
- Automatically high-confidence raw-GOLD echo pairs: **4**.
- Echo data remains conservative; existing validated relationship-sequence model/data remains authoritative where available.

## Recovered asset
- Restored `relationship_sequence_data_v2` from the previously validated 6.01 AI package because the 7.50 package retained the model but omitted its dataset.

## Validation
- Targeted + regression suite: **36/36 PASS**.
- Covers DNA grammar, melodic relationship model/sequence model, Echo/Terca engine, rhythm-guitar polyphony fix, self-refinement, candidate critic, cross-track brain, hierarchical planner and full-song autoregressive regeneration.

## Authority contract
- GOLD: relationship, phrase, PLAY/SKIP/HOLD, voicing evidence.
- Factory: velocity/performance dynamics.
- Source solo: protected melodic authority.
