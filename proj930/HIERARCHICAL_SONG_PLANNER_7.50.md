# Hierarchical Song Planner 7.50

Read-only global planning layer before generation.

- uses SongMap 2.0 section boundaries, role segments, note density and polyphony;
- never reads velocity;
- creates normalized section energy curve;
- tracks role entry / exit / silence / density lifecycle;
- emits transition intent: establish / continue / build / lift / release / resolve;
- low-confidence or ending sections are conservative regeneration zones;
- full-song REGENERATE is now gated by this plan before any backend is called;
- Factory remains the sole velocity authority.
