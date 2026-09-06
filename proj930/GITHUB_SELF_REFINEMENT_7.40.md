# DNA MIDI Studio 7.40 — Self-Refinement Loop

## Goal
Turn the 7.30 preference critic into an active retry loop:

`Generate -> Critic -> Diagnose -> Refine controls -> Regenerate -> Re-score -> Stop/accept`

## Implemented
- `SelfRefinementPolicy` converts critic reasons into bounded generation-control changes.
- Maximum 2 refinement rounds.
- Stops immediately for `BALANCED_CANDIDATE` or safety failure.
- Stops when a retry improves the best score by <= 0.005.
- Retry never edits notes directly.
- Retry can adjust only generation intent:
  - temperature
  - top-p
  - candidate count
  - REPAIR remix amount
  - reserved bounded density delta
- Every refined MIDI-GPT candidate still passes:
  - authorized-region scope gate
  - protected event gate
  - Factory-only velocity rendering
  - 7.30 preference critic
- Refined candidates retain provenance in `facts.refinementRound` and `facts.refinementReasons`.

## Diagnostic mapping
- weak groove/cross-track -> lower randomness, stronger constrained remix, more candidates
- weak harmony -> lower randomness, more candidates
- weak repetition balance -> slightly higher diversity
- weak transition -> slightly tighter sampling and stronger REPAIR remix
- weak density -> broaden candidate search rather than blindly inserting/deleting notes
- weak safety -> stop retrying

## Invariants
- Velocity is never used as a refinement target.
- No mutation can bypass Factory velocity authority.
- No retry can bypass the region/protected-event verifier.
- Backend identity gets no preference bonus.

## Validation
Targeted 7.40 + 7.30 + 7.20 + 7.10 + router regression set: 14/14 PASS.
