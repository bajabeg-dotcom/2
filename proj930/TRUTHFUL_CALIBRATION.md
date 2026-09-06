# Truthful full calibration

`truthful_evidence_gate.py` is the single precondition for mutation, learning
promotion, calibration, and certification. It validates source bytes and
SHA-256 hashes, corpus membership, direct versus derived/proxy roles, NPZ
manifests, promoted model artifacts, and the production runtime.

Run the full preflight with:

```bash
python full_calibration.py --output reports/truthful_full_calibration_15.00.json
```

The command is fail-closed. A blocked run writes a diagnostic report and
processes zero MIDI inputs. It never changes source MIDI or emits a PASS claim.
When the gate eventually becomes PASS, the authorized branch enumerates every
`.mid`/`.midi` member in `Split Factory Styles.zip` and `Gold DNA.zip`, counts
empty/parse/error inputs in the denominator, and records input/output hashes
for every attempted transformation.

## Current result in this checkout

- authoritative Factory archive: **3,211** MIDI members;
- authoritative Gold archive: **182** MIDI members;
- full source denominator: **3,393** inputs;
- current execution: **BLOCKED**, **0** transformations authorized;
- Factory has only family/direct raw role evidence plus derived mappings;
- Gold has derived role classifications and proxy roles (`choir`, `echo`,
  `percussion`), not direct evidence for every target role;
- drum evidence/runtime does not cover all required elements/context counts;
- the promoted neural model reports are absent even though legacy artifacts
  claim `exists: true`;
- `src/dna_midi_studio` and the `mido` dependency used by the legacy
  certification engine are unavailable;
- the previous corpus report used 1,113 extracted files, not the authoritative
  3,393-member source denominator.

`reference_authority_pipeline.py` now reports `PATH_ONLY`: path/hash coverage
is not semantic authority and cannot authorize an export. Legacy `PASS` and
`FULL/NO BYPASS` reports remain historical, non-authoritative artifacts.
