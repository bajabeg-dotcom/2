# DNA MIDI Studio 7.03 — Generative Backend Router

## Goal
Turn KEEP / REPAIR / REGENERATE into real backend policies rather than labels.

## Routing
- KEEP: preserve material; no generator call.
- REPAIR: constrained MIDI-GPT remix/infill when installed; otherwise the already-applied role-first safe repair remains authoritative.
- REGENERATE: MIDI-GPT 0.3.4 and the existing DNA neural replacement engine both produce candidates. A backend-neutral symbolic critic ranks all valid candidates.

## Hard rules
- MIDI-GPT request always sets velocity=false and microtiming=false.
- DNA neural candidates retain their Factory velocity proof metadata.
- Solo / terca / echo remain protected from blind full regeneration.
- All generated candidates must parse as MIDI before entering ranking.
- Full-song protected-event and outside-authorized-region verification still runs after selection.

## Why this matters
The project no longer assumes that one model is always best. GitHub generation backends are treated as interchangeable proposal engines under the DNA/Factory/GOLD verifier and critic layer.

## Verification added after integration
- MIDI-GPT candidates are rejected when notes outside the authorized track/channel/tick window change.
- Protected meta/SysEx/Bank/Program/RPN/NRPN events must remain identical.
- Accepted MIDI-GPT symbolic output is re-rendered through the existing FactoryVelocityProvider before ranking/commit.
- Targeted regression suite: 10/10 PASS.
