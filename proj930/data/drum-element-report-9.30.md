# DNA MIDI Studio 9.30 — Drum Element Sub-Profiles

**Verzija:** 9.30.1
**Ukupno elemenata:** 15

## Autoritet Model

| Domena | Autoritet |
|---|---|
| Velocity | FACTORY_DRUM_KIT |
| Timing/Gate | GOLD_PATTERN |
| Interakcija | RULE_BASED |
| Chord Foundation | KICK_BASS_COUPLING |

## Element Pregled

| Element | GM# | Family | Groove Role | Notes | Gate | Sync | Conf |
|---|---|---|---|---|---|---|---|
| closed_hat | 42 | hihat | PULSE | 1053 | 1 | 0.65 | 1.00 |
| snare | 38 | snare | BACKBEAT | 327 | 1 | 0.68 | 0.65 |
| kick | 36 | bass_drum | ANCHOR | 233 | 1 | 0.43 | 0.47 |
| pedal_hat | 44 | hihat | PULSE_ALT | 123 | 1 | 0.45 | 0.25 |
| cowbell | 56 | percussion | PATTERN_ACCENT | 75 | 1 | 0.56 | 0.15 |
| snare_ghost | 40 | snare | GHOST_FILL | 46 | 1 | 0.65 | 0.09 |
| tom_mid | 48 | tom | FILL_VOICE | 43 | 1 | 0.67 | 0.09 |
| open_hat | 46 | hihat | ACCENT | 31 | 1 | 0.87 | 0.06 |
| tom_high | 50 | tom | FILL_VOICE | 27 | 1 | 0.70 | 0.05 |
| ride | 51 | cymbal | SWING_PULSE | 25 | 1 | 0.48 | 0.05 |
| side_stick | 37 | snare | BACKBEAT_ALT | 15 | 1 | 0.33 | 0.03 |
| clap | 39 | percussion | ACCENT | 15 | 2 | 0.00 | 0.03 |
| tom_low | 47 | tom | FILL_VOICE | 11 | 1 | 0.73 | 0.02 |
| crash | 49 | cymbal | SECTION_MARK | 6 | 3 | 0.00 | 0.01 |
| ride_bell | 59 | cymbal | ACCENT_PULSE | 0 | 8 | 0.00 | 0.00 |

---

## CLAP

- **GM Pitch:** 39
- **Family:** percussion
- **Groove Role:** ACCENT

### Velocity

| pp | p | mp | mf | f | ff | floor | optimal |
|---|---|---|---|---|---|---|---|
| 40 | 62 | 80 | 98 | 112 | 127 | 30 | 98 |

### Timing

- Base offset: 0
- Early bias: 0
- Gate typical: 5
- Gate median (Gold): 2
- Syncopation rate: 0.00

### Interakcije


---

## CLOSED_HAT

- **GM Pitch:** 42
- **Family:** hihat
- **Groove Role:** PULSE

### Velocity

| pp | p | mp | mf | f | ff | floor | optimal |
|---|---|---|---|---|---|---|---|
| 30 | 55 | 72 | 85 | 100 | 115 | 25 | 85 |

### Timing

- Base offset: 0
- Early bias: -1
- Gate typical: 3
- Gate median (Gold): 1
- Syncopation rate: 0.65

### Interakcije

- **groovePulse:** Closed hat je osnova groova — 8th ili 16th pulse
  - Rule: `HIHAT_STEADY_PULSE`

---

## COWBELL

- **GM Pitch:** 56
- **Family:** percussion
- **Groove Role:** PATTERN_ACCENT

### Velocity

| pp | p | mp | mf | f | ff | floor | optimal |
|---|---|---|---|---|---|---|---|
| 40 | 60 | 78 | 92 | 108 | 120 | 30 | 92 |

### Timing

- Base offset: 0
- Early bias: 0
- Gate typical: 6
- Gate median (Gold): 1
- Syncopation rate: 0.56

### Interakcije


---

## CRASH

- **GM Pitch:** 49
- **Family:** cymbal
- **Groove Role:** SECTION_MARK

### Velocity

| pp | p | mp | mf | f | ff | floor | optimal |
|---|---|---|---|---|---|---|---|
| 50 | 72 | 88 | 105 | 118 | 127 | 40 | 108 |

### Timing

- Base offset: -1
- Early bias: -2
- Gate typical: 15
- Gate median (Gold): 3
- Syncopation rate: 0.00

### Interakcije

- **sectionMark:** Crash označava početak sekcije — intro/chorus/bridge
  - Rule: `CRASH_ON_SECTION_CHANGE`

---

## KICK

- **GM Pitch:** 36
- **Family:** bass_drum
- **Groove Role:** ANCHOR

### Velocity

| pp | p | mp | mf | f | ff | floor | optimal |
|---|---|---|---|---|---|---|---|
| 40 | 65 | 80 | 95 | 110 | 120 | 30 | 95 |

### Timing

- Base offset: 0
- Early bias: 1
- Gate typical: 8
- Gate median (Gold): 1
- Syncopation rate: 0.43

### Interakcije

- **bassCoupling:** Kick i Bass moraju sinhrono — kick je temporal anchor za bass
  - Rule: `BLOCK_KICK_WITHOUT_BASS_ON_BEAT_1`

---

## OPEN_HAT

- **GM Pitch:** 46
- **Family:** hihat
- **Groove Role:** ACCENT

### Velocity

| pp | p | mp | mf | f | ff | floor | optimal |
|---|---|---|---|---|---|---|---|
| 35 | 58 | 75 | 88 | 105 | 118 | 28 | 88 |

### Timing

- Base offset: 0
- Early bias: 0
- Gate typical: 8
- Gate median (Gold): 1
- Syncopation rate: 0.87

### Interakcije


---

## PEDAL_HAT

- **GM Pitch:** 44
- **Family:** hihat
- **Groove Role:** PULSE_ALT

### Velocity

| pp | p | mp | mf | f | ff | floor | optimal |
|---|---|---|---|---|---|---|---|
| 25 | 48 | 65 | 78 | 92 | 105 | 20 | 75 |

### Timing

- Base offset: 0
- Early bias: 0
- Gate typical: 5
- Gate median (Gold): 1
- Syncopation rate: 0.45

### Interakcije

- **groovePulse:** Closed hat je osnova groova — 8th ili 16th pulse
  - Rule: `HIHAT_STEADY_PULSE`

---

## RIDE

- **GM Pitch:** 51
- **Family:** cymbal
- **Groove Role:** SWING_PULSE

### Velocity

| pp | p | mp | mf | f | ff | floor | optimal |
|---|---|---|---|---|---|---|---|
| 35 | 58 | 74 | 88 | 102 | 115 | 28 | 88 |

### Timing

- Base offset: 0
- Early bias: -1
- Gate typical: 10
- Gate median (Gold): 1
- Syncopation rate: 0.48

### Interakcije

- **hatExclusion:** Ride zamjenjuje closed hat u swing/latin patternima
  - Rule: `MUTUAL_EXCLUSION`

---

## RIDE_BELL

- **GM Pitch:** 59
- **Family:** cymbal
- **Groove Role:** ACCENT_PULSE

### Velocity

| pp | p | mp | mf | f | ff | floor | optimal |
|---|---|---|---|---|---|---|---|
| 40 | 62 | 78 | 92 | 108 | 120 | 32 | 92 |

### Timing

- Base offset: 0
- Early bias: -1
- Gate typical: 8
- Gate median (Gold): 8
- Syncopation rate: 0.00

### Interakcije


---

## SIDE_STICK

- **GM Pitch:** 37
- **Family:** snare
- **Groove Role:** BACKBEAT_ALT

### Velocity

| pp | p | mp | mf | f | ff | floor | optimal |
|---|---|---|---|---|---|---|---|
| 35 | 55 | 72 | 85 | 100 | 115 | 28 | 85 |

### Timing

- Base offset: 0
- Early bias: 1
- Gate typical: 3
- Gate median (Gold): 1
- Syncopation rate: 0.33

### Interakcije


---

## SNARE

- **GM Pitch:** 38
- **Family:** snare
- **Groove Role:** BACKBEAT

### Velocity

| pp | p | mp | mf | f | ff | floor | optimal |
|---|---|---|---|---|---|---|---|
| 35 | 60 | 78 | 98 | 115 | 127 | 25 | 98 |

### Timing

- Base offset: 0
- Early bias: 2
- Gate typical: 6
- Gate median (Gold): 1
- Syncopation rate: 0.68

### Interakcije

- **backbeat:** Snare na 2 i 4 — standardni backbeat
  - Rule: `SNARE_ON_BEATS_2_4`

---

## SNARE_GHOST

- **GM Pitch:** 40
- **Family:** snare
- **Groove Role:** GHOST_FILL

### Velocity

| pp | p | mp | mf | f | ff | floor | optimal |
|---|---|---|---|---|---|---|---|
| 20 | 40 | 55 | 68 | 82 | 95 | 15 | 65 |

### Timing

- Base offset: 0
- Early bias: 0
- Gate typical: 4
- Gate median (Gold): 1
- Syncopation rate: 0.65

### Interakcije


---

## TOM_HIGH

- **GM Pitch:** 50
- **Family:** tom
- **Groove Role:** FILL_VOICE

### Velocity

| pp | p | mp | mf | f | ff | floor | optimal |
|---|---|---|---|---|---|---|---|
| 45 | 68 | 83 | 100 | 114 | 126 | 35 | 100 |

### Timing

- Base offset: 0
- Early bias: 0
- Gate typical: 5
- Gate median (Gold): 1
- Syncopation rate: 0.70

### Interakcije

- **fillRule:** Tomovi se koriste samo u fill kontekstu
  - Rule: `TOMS_ONLY_IN_FILL`

---

## TOM_LOW

- **GM Pitch:** 47
- **Family:** tom
- **Groove Role:** FILL_VOICE

### Velocity

| pp | p | mp | mf | f | ff | floor | optimal |
|---|---|---|---|---|---|---|---|
| 40 | 62 | 78 | 95 | 110 | 122 | 30 | 95 |

### Timing

- Base offset: 0
- Early bias: 0
- Gate typical: 8
- Gate median (Gold): 1
- Syncopation rate: 0.73

### Interakcije

- **fillRule:** Tomovi se koriste samo u fill kontekstu
  - Rule: `TOMS_ONLY_IN_FILL`

---

## TOM_MID

- **GM Pitch:** 48
- **Family:** tom
- **Groove Role:** FILL_VOICE

### Velocity

| pp | p | mp | mf | f | ff | floor | optimal |
|---|---|---|---|---|---|---|---|
| 42 | 65 | 80 | 98 | 112 | 124 | 32 | 98 |

### Timing

- Base offset: 0
- Early bias: 0
- Gate typical: 6
- Gate median (Gold): 1
- Syncopation rate: 0.67

### Interakcije

- **fillRule:** Tomovi se koriste samo u fill kontekstu
  - Rule: `TOMS_ONLY_IN_FILL`

---
