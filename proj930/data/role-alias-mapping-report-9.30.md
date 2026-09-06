# DNA MIDI Studio 9.30 — Role Alias Mapping Report

**Verzija:** 9.30.1
**Ukupno profila:** 20

## Alias Mapiranje

### Gold Role → Instrument Aliases

**accompaniment** →
  - piano: weight=35%, evidence=CHORDAL_COMPING_PATTERN
  - organ: weight=15%, evidence=SUSTAIN_CHORD_COMPING
  - pad: weight=15%, evidence=SUSTAIN_HARMONIC_BED
  - accordion: weight=15%, evidence=CHORD_PULSE_PATTERN
  - strings: weight=10%, evidence=SUSTAIN_HARMONIC_SUPPORT
  - choir: weight=10%, evidence=SUSTAIN_VOCAL_TEXTURE

**power-riff** →
  - rhythm_guitar: weight=80%, evidence=STRUM_POWER_CHORD_RIFF
  - brass: weight=15%, evidence=SECTION_STAB_ACCENT
  - mallet: weight=5%, evidence=ARTICULATED_RIFF_PATTERN

**riff** →
  - solo_guitar: weight=28%, evidence=MELODIC_RIFF_SOLO
  - sax: weight=22%, evidence=MELODIC_RIFF_PHRASE
  - synth_lead: weight=13%, evidence=SYNTH_RIFF_PHRASE
  - brass: weight=13%, evidence=BRASS_RIFF_STAB
  - violin: weight=10%, evidence=FOLK_RIFF_VIOLIN
  - clarinet: weight=7%, evidence=FOLK_RIFF_ORNAMENT
  - woodwind: weight=4%, evidence=FOLK_RIFF_MELODIC

**bass** →
  - bass: weight=100%, evidence=DIRECT_MAP

**drums** →
  - drums: weight=100%, evidence=DIRECT_MAP

**percussion** →
  - percussion: weight=100%, evidence=DIRECT_MAP

### Factory Role → Instrument Aliases

**chords** →
  - piano: weight=30%, evidence=VELOCITY_CHORDAL_COMPING
  - rhythm_guitar: weight=20%, evidence=VELOCITY_STRUM_CHORDS
  - organ: weight=15%, evidence=VELOCITY_SUSTAIN_CHORD
  - accordion: weight=15%, evidence=VELOCITY_CHORD_PUMP
  - pad: weight=10%, evidence=VELOCITY_SUSTAIN_BED
  - strings: weight=5%, evidence=VELOCITY_SUSTAIN_ENSEMBLE
  - choir: weight=5%, evidence=VELOCITY_VOCAL_TEXTURE

**melody** →
  - sax: weight=25%, evidence=VELOCITY_MELODIC_PHRASE
  - clarinet: weight=15%, evidence=VELOCITY_FOLK_MELODIC
  - violin: weight=15%, evidence=VELOCITY_LEGATO_MELODIC
  - solo_guitar: weight=15%, evidence=VELOCITY_SOLO_PHRASE
  - synth_lead: weight=15%, evidence=VELOCITY_SYNTH_LEAD
  - woodwind: weight=10%, evidence=VELOCITY_FOLK_WIND
  - brass: weight=5%, evidence=VELOCITY_BRASS_SOLO

**bass** →
  - bass: weight=100%, evidence=DIRECT_MAP

**drums** →
  - drums: weight=90%, evidence=DIRECT_MAP
  - percussion: weight=5%, evidence=VELOCITY_PERC_HIT
  - mallet: weight=5%, evidence=VELOCITY_MALLET_HIT

---

## Profili po instrumentu

### ACCOMPANIMENT

- **Family:** keyboard
- **Subfamily:** generic_comp
- **Arrangement Role:** RHYTHMIC_CHORD
- **PA800 Track:** ACC2 | NTT: Chord/Fixed

#### Alias Sources

- **Velocity:** inherited from Factory `?` role (weight 0%, confidence 0.00)
- **Timing:** inherited from Gold `?` role (weight 0%, confidence 0.00)

#### Velocity Curve

| Level | Value |
|---|---|
| Source | NO_FACTORY_ALIAS |
| Confidence | 0.000 |

#### Timing

- Humanization: ?
- Groove profile: ?
- Base offset: 0
- Swing: 0.00

#### Harmony

- Root weight: 0.40
- Third weight: 0.60
- Passing rate: 8%
- Chromatic rate: 3%

#### How It Plays

> Generic chordal/rhythmic support. velocity inherited from ? role (weight 0%) timing inherited from ? role (weight 0%) follows chord tones (weight 0.52) moderate timing dynamic range ?-? primary articulation: legato (30%), accent (30%), staccato (20%).

#### Confidence

- Overall: 0.000
- Gold samples: 0
- Factory samples: 0
- Flags: LOW_GOLD_SAMPLES, LOW_FACTORY_SAMPLES, WEAK_GOLD_ALIAS, WEAK_FACTORY_ALIAS, NO_ALIAS_DATA

---

### ACCORDION

- **Family:** free_reed
- **Subfamily:** accordion
- **Arrangement Role:** RHYTHMIC_CHORD
- **PA800 Track:** ACC1 | NTT: Chord/Fixed

#### Alias Sources

- **Velocity:** inherited from Factory `chords` role (weight 15%, confidence 0.14)
- **Timing:** inherited from Gold `accompaniment` role (weight 15%, confidence 0.15)

#### Velocity Curve

| Level | Value |
|---|---|
| pp | 30 |
| p | 61 |
| mp | 76 |
| mf | 87 |
| f | 107 |
| ff | 127 |
| fff | 127 |
| accent | 119 |
| ghost | 54 |
| Source | FACTORY_ALIAS(chords) |
| Confidence | 0.144 |

#### Timing

- Humanization: BELLOWS_HUMAN
- Groove profile: PULSE_PHRASE
- Base offset: 1
- Swing: 0.00

#### Harmony

- Root weight: 0.50
- Third weight: 0.70
- Passing rate: 6%
- Chromatic rate: 8%

#### How It Plays

> Melodic and chord-pumping balkan character. velocity inherited from chords role (weight 15%) timing inherited from accompaniment role (weight 15%) follows chord tones (weight 0.62) bellows human timing dynamic range 30-127 primary articulation: legato (50%), accent (40%), staccato (30%).

#### Confidence

- Overall: 0.148
- Gold samples: 3039
- Factory samples: 335
- Flags: WEAK_GOLD_ALIAS, WEAK_FACTORY_ALIAS

---

### BASS

- **Family:** bass
- **Subfamily:** electric_bass
- **Arrangement Role:** BASS
- **PA800 Track:** BASS | NTT: None

#### Alias Sources

- **Velocity:** inherited from Factory `bass` role (weight 100%, confidence 0.46)
- **Timing:** inherited from Gold `bass` role (weight 100%, confidence 0.99)

#### Velocity Curve

| Level | Value |
|---|---|
| pp | 32 |
| p | 82 |
| mp | 94 |
| mf | 105 |
| f | 116 |
| ff | 127 |
| fff | 127 |
| accent | 126 |
| ghost | 59 |
| Source | FACTORY_ALIAS(bass) |
| Confidence | 0.456 |

#### Timing

- Humanization: MODERATE
- Groove profile: GENERIC
- Base offset: 0
- Swing: 0.15

#### Harmony

- Root weight: 0.85
- Third weight: 0.10
- Passing rate: 12%
- Chromatic rate: 5%

#### How It Plays

> Low-frequency harmonic and rhythmic foundation. velocity inherited from bass role (weight 100%) timing inherited from bass role (weight 100%) strongly anchors root (weight 0.85) moderate timing dynamic range 32-127 primary articulation: legato (40%), accent (30%), staccato (20%).

#### Confidence

- Overall: 0.990
- Gold samples: 2866
- Factory samples: 51
- Flags: None

---

### BRASS

- **Family:** brass
- **Subfamily:** section
- **Arrangement Role:** FILL
- **PA800 Track:** ACC5 | NTT: Parallel

#### Alias Sources

- **Velocity:** inherited from Factory `melody` role (weight 5%, confidence 0.04)
- **Timing:** inherited from Gold `power-riff` role (weight 15%, confidence 0.15)

#### Velocity Curve

| Level | Value |
|---|---|
| pp | 40 |
| p | 68 |
| mp | 83 |
| mf | 103 |
| f | 112 |
| ff | 127 |
| fff | 127 |
| accent | 127 |
| ghost | 62 |
| Source | FACTORY_ALIAS(melody) |
| Confidence | 0.040 |

#### Timing

- Humanization: ACCENT_DRIVEN
- Groove profile: STAB_ACCENT
- Base offset: 0
- Swing: 0.15

#### Harmony

- Root weight: 0.55
- Third weight: 0.65
- Passing rate: 8%
- Chromatic rate: 5%

#### How It Plays

> Stab accents and section transition marks. velocity inherited from melody role (weight 5%) timing inherited from power-riff role (weight 15%) follows chord tones (weight 0.60) accent driven timing dynamic range 40-127 primary articulation: accent (60%), staccato (40%), legato (30%).

#### Confidence

- Overall: 0.148
- Gold samples: 4927
- Factory samples: 157
- Flags: WEAK_GOLD_ALIAS, WEAK_FACTORY_ALIAS

---

### CHOIR

- **Family:** vocal
- **Subfamily:** choir
- **Arrangement Role:** HARMONIC_PAD
- **PA800 Track:** ACC5 | NTT: Fixed

#### Alias Sources

- **Velocity:** inherited from Factory `chords` role (weight 5%, confidence 0.05)
- **Timing:** inherited from Gold `accompaniment` role (weight 10%, confidence 0.10)

#### Velocity Curve

| Level | Value |
|---|---|
| pp | 30 |
| p | 61 |
| mp | 76 |
| mf | 82 |
| f | 99 |
| ff | 127 |
| fff | 127 |
| accent | 106 |
| ghost | 54 |
| Source | FACTORY_ALIAS(chords) |
| Confidence | 0.048 |

#### Timing

- Humanization: MINIMAL
- Groove profile: SLOW_ARC
- Base offset: 1
- Swing: 0.00

#### Harmony

- Root weight: 0.50
- Third weight: 0.75
- Passing rate: 2%
- Chromatic rate: 3%

#### How It Plays

> Sustained vocal harmonic texture. velocity inherited from chords role (weight 5%) timing inherited from accompaniment role (weight 10%) follows chord tones (weight 0.65) dynamic range 30-127 primary articulation: legato (90%).

#### Confidence

- Overall: 0.099
- Gold samples: 3039
- Factory samples: 335
- Flags: WEAK_GOLD_ALIAS, WEAK_FACTORY_ALIAS

---

### CLARINET

- **Family:** wind
- **Subfamily:** clarinet_folk
- **Arrangement Role:** COUNTER_MELODY
- **PA800 Track:** ACC2 | NTT: Parallel

#### Alias Sources

- **Velocity:** inherited from Factory `melody` role (weight 15%, confidence 0.12)
- **Timing:** inherited from Gold `riff` role (weight 7%, confidence 0.07)

#### Velocity Curve

| Level | Value |
|---|---|
| pp | 40 |
| p | 68 |
| mp | 83 |
| mf | 98 |
| f | 112 |
| ff | 127 |
| fff | 127 |
| accent | 126 |
| ghost | 62 |
| Source | FACTORY_ALIAS(melody) |
| Confidence | 0.121 |

#### Timing

- Humanization: ORNAMENT_DRIVEN
- Groove profile: FOLK_ORNAMENT
- Base offset: 0
- Swing: 0.15

#### Harmony

- Root weight: 0.30
- Third weight: 0.55
- Passing rate: 20%
- Chromatic rate: 12%

#### How It Plays

> Folk/balkan ornamental melodic voice. velocity inherited from melody role (weight 15%) timing inherited from riff role (weight 7%) ornament driven timing dynamic range 40-127 primary articulation: legato (50%), accent (30%), staccato (20%).

#### Confidence

- Overall: 0.121
- Gold samples: 566
- Factory samples: 157
- Flags: WEAK_GOLD_ALIAS, WEAK_FACTORY_ALIAS

---

### DRUMS

- **Family:** drums
- **Subfamily:** drum_kit
- **Arrangement Role:** DRUM
- **PA800 Track:** DRUM | NTT: None

#### Alias Sources

- **Velocity:** inherited from Factory `drums` role (weight 90%, confidence 0.89)
- **Timing:** inherited from Gold `drums` role (weight 100%, confidence 0.99)

#### Velocity Curve

| Level | Value |
|---|---|
| pp | 67 |
| p | 77 |
| mp | 88 |
| mf | 98 |
| f | 110 |
| ff | 115 |
| fff | 127 |
| accent | 121 |
| ghost | 90 |
| Source | FACTORY_ALIAS(drums) |
| Confidence | 0.891 |

#### Timing

- Humanization: MODERATE
- Groove profile: GENERIC
- Base offset: 42
- Swing: 0.15

#### Harmony

- Root weight: 0.40
- Third weight: 0.60
- Passing rate: 8%
- Chromatic rate: 3%

#### How It Plays

> Primary rhythmic driver and groove keeper. velocity inherited from drums role (weight 90%) timing inherited from drums role (weight 100%) follows chord tones (weight 0.52) moderate timing dynamic range 67-115 primary articulation: staccato (90%), accent (50%), ghost (20%).

#### Confidence

- Overall: 0.990
- Gold samples: 1442
- Factory samples: 1421
- Flags: None

---

### FX

- **Family:** fx
- **Subfamily:** special
- **Arrangement Role:** FX
- **PA800 Track:** ACC5 | NTT: None

#### Alias Sources

- **Velocity:** inherited from Factory `?` role (weight 0%, confidence 0.00)
- **Timing:** inherited from Gold `?` role (weight 0%, confidence 0.00)

#### Velocity Curve

| Level | Value |
|---|---|
| Source | NO_FACTORY_ALIAS |
| Confidence | 0.000 |

#### Timing

- Humanization: ?
- Groove profile: ?
- Base offset: 0
- Swing: 0.00

#### Harmony

- Root weight: 0.10
- Third weight: 0.05
- Passing rate: 8%
- Chromatic rate: 3%

#### How It Plays

> Event/section-driven special effect. velocity inherited from ? role (weight 0%) timing inherited from ? role (weight 0%) moderate timing dynamic range ?-? primary articulation: staccato (50%), accent (30%).

#### Confidence

- Overall: 0.000
- Gold samples: 0
- Factory samples: 0
- Flags: LOW_GOLD_SAMPLES, LOW_FACTORY_SAMPLES, WEAK_GOLD_ALIAS, WEAK_FACTORY_ALIAS, NO_ALIAS_DATA

---

### MALLET

- **Family:** percussion
- **Subfamily:** mallet
- **Arrangement Role:** FILL
- **PA800 Track:** ACC2 | NTT: Chord/Parallel

#### Alias Sources

- **Velocity:** inherited from Factory `drums` role (weight 5%, confidence 0.05)
- **Timing:** inherited from Gold `power-riff` role (weight 5%, confidence 0.05)

#### Velocity Curve

| Level | Value |
|---|---|
| pp | 67 |
| p | 77 |
| mp | 88 |
| mf | 101 |
| f | 110 |
| ff | 115 |
| fff | 127 |
| accent | 127 |
| ghost | 90 |
| Source | FACTORY_ALIAS(drums) |
| Confidence | 0.050 |

#### Timing

- Humanization: TIGHT_HUMAN
- Groove profile: ARTICULATED
- Base offset: 0
- Swing: 0.15

#### Harmony

- Root weight: 0.40
- Third weight: 0.55
- Passing rate: 10%
- Chromatic rate: 3%

#### How It Plays

> Clear-attack arpeggiated or repeated color. velocity inherited from drums role (weight 5%) timing inherited from power-riff role (weight 5%) tight human timing dynamic range 67-115 primary articulation: accent (50%), legato (30%), staccato (30%).

#### Confidence

- Overall: 0.050
- Gold samples: 4927
- Factory samples: 1421
- Flags: WEAK_GOLD_ALIAS, WEAK_FACTORY_ALIAS

---

### ORGAN

- **Family:** keyboard
- **Subfamily:** organ
- **Arrangement Role:** RHYTHMIC_CHORD
- **PA800 Track:** ACC3 | NTT: Fixed

#### Alias Sources

- **Velocity:** inherited from Factory `chords` role (weight 15%, confidence 0.14)
- **Timing:** inherited from Gold `accompaniment` role (weight 15%, confidence 0.15)

#### Velocity Curve

| Level | Value |
|---|---|
| pp | 30 |
| p | 61 |
| mp | 76 |
| mf | 90 |
| f | 107 |
| ff | 127 |
| fff | 127 |
| accent | 116 |
| ghost | 54 |
| Source | FACTORY_ALIAS(chords) |
| Confidence | 0.144 |

#### Timing

- Humanization: MINIMAL
- Groove profile: SUSTAIN_PULSE
- Base offset: 1
- Swing: 0.00

#### Harmony

- Root weight: 0.50
- Third weight: 0.70
- Passing rate: 5%
- Chromatic rate: 3%

#### How It Plays

> Sustained harmonic and rhythmic comping. velocity inherited from chords role (weight 15%) timing inherited from accompaniment role (weight 15%) follows chord tones (weight 0.62) dynamic range 30-127 primary articulation: legato (30%), accent (30%), staccato (20%).

#### Confidence

- Overall: 0.148
- Gold samples: 3039
- Factory samples: 335
- Flags: WEAK_GOLD_ALIAS, WEAK_FACTORY_ALIAS

---

### PAD

- **Family:** synth
- **Subfamily:** pad
- **Arrangement Role:** HARMONIC_PAD
- **PA800 Track:** ACC4 | NTT: Fixed

#### Alias Sources

- **Velocity:** inherited from Factory `chords` role (weight 10%, confidence 0.10)
- **Timing:** inherited from Gold `accompaniment` role (weight 15%, confidence 0.15)

#### Velocity Curve

| Level | Value |
|---|---|
| pp | 30 |
| p | 61 |
| mp | 76 |
| mf | 80 |
| f | 97 |
| ff | 127 |
| fff | 127 |
| accent | 101 |
| ghost | 54 |
| Source | FACTORY_ALIAS(chords) |
| Confidence | 0.096 |

#### Timing

- Humanization: MINIMAL
- Groove profile: PAD_MOVEMENT
- Base offset: 1
- Swing: 0.00

#### Harmony

- Root weight: 0.50
- Third weight: 0.75
- Passing rate: 2%
- Chromatic rate: 3%

#### How It Plays

> Sustained harmonic bed with slow movement. velocity inherited from chords role (weight 10%) timing inherited from accompaniment role (weight 15%) follows chord tones (weight 0.65) dynamic range 30-127 primary articulation: legato (90%).

#### Confidence

- Overall: 0.148
- Gold samples: 3039
- Factory samples: 335
- Flags: WEAK_GOLD_ALIAS, WEAK_FACTORY_ALIAS

---

### PERCUSSION

- **Family:** percussion
- **Subfamily:** hand_perc
- **Arrangement Role:** PERCUSSION
- **PA800 Track:** PERC | NTT: None

#### Alias Sources

- **Velocity:** inherited from Factory `drums` role (weight 5%, confidence 0.05)
- **Timing:** inherited from Gold `percussion` role (weight 100%, confidence 0.80)

#### Velocity Curve

| Level | Value |
|---|---|
| pp | 67 |
| p | 77 |
| mp | 88 |
| mf | 98 |
| f | 110 |
| ff | 115 |
| fff | 127 |
| accent | 121 |
| ghost | 90 |
| Source | FACTORY_ALIAS(drums) |
| Confidence | 0.050 |

#### Timing

- Humanization: INTERLOCK
- Groove profile: INTERLOCK_PATTERN
- Base offset: 43
- Swing: 0.00

#### Harmony

- Root weight: 0.10
- Third weight: 0.05
- Passing rate: 8%
- Chromatic rate: 3%

#### How It Plays

> Interlocking rhythmic color and accent. velocity inherited from drums role (weight 5%) timing inherited from percussion role (weight 100%) interlock timing dynamic range 67-115 primary articulation: staccato (70%), accent (40%), ghost (20%).

#### Confidence

- Overall: 0.803
- Gold samples: 78
- Factory samples: 1421
- Flags: WEAK_FACTORY_ALIAS

---

### PIANO

- **Family:** keyboard
- **Subfamily:** piano
- **Arrangement Role:** RHYTHMIC_CHORD
- **PA800 Track:** ACC2 | NTT: Chord/Fixed

#### Alias Sources

- **Velocity:** inherited from Factory `chords` role (weight 30%, confidence 0.29)
- **Timing:** inherited from Gold `accompaniment` role (weight 35%, confidence 0.35)

#### Velocity Curve

| Level | Value |
|---|---|
| pp | 30 |
| p | 61 |
| mp | 76 |
| mf | 85 |
| f | 107 |
| ff | 127 |
| fff | 127 |
| accent | 121 |
| ghost | 54 |
| Source | FACTORY_ALIAS(chords) |
| Confidence | 0.288 |

#### Timing

- Humanization: SMALL_SPREAD
- Groove profile: COMPING
- Base offset: 1
- Swing: 0.00

#### Harmony

- Root weight: 0.40
- Third weight: 0.80
- Passing rate: 8%
- Chromatic rate: 3%

#### How It Plays

> Chordal comping, voicing, and harmonic support. velocity inherited from chords role (weight 30%) timing inherited from accompaniment role (weight 35%) follows chord tones (weight 0.63) small spread timing dynamic range 30-127 primary articulation: accent (40%), legato (30%), staccato (30%).

#### Confidence

- Overall: 0.346
- Gold samples: 3039
- Factory samples: 335
- Flags: WEAK_GOLD_ALIAS, WEAK_FACTORY_ALIAS

---

### RHYTHM_GUITAR

- **Family:** guitar
- **Subfamily:** rhythm
- **Arrangement Role:** RHYTHMIC_CHORD
- **PA800 Track:** ACC1 | NTT: Chord

#### Alias Sources

- **Velocity:** inherited from Factory `chords` role (weight 20%, confidence 0.19)
- **Timing:** inherited from Gold `power-riff` role (weight 80%, confidence 0.79)

#### Velocity Curve

| Level | Value |
|---|---|
| pp | 30 |
| p | 61 |
| mp | 76 |
| mf | 87 |
| f | 107 |
| ff | 127 |
| fff | 127 |
| accent | 124 |
| ghost | 49 |
| Source | FACTORY_ALIAS(chords) |
| Confidence | 0.192 |

#### Timing

- Humanization: STRUM_SPREAD
- Groove profile: STRUM_PATTERN
- Base offset: -2
- Swing: 0.15

#### Harmony

- Root weight: 0.45
- Third weight: 0.75
- Passing rate: 5%
- Chromatic rate: 3%

#### How It Plays

> Harmonic rhythm with strumming physicality. velocity inherited from chords role (weight 20%) timing inherited from power-riff role (weight 80%) follows chord tones (weight 0.63) strum spread timing dynamic range 30-127 primary articulation: accent (50%), staccato (30%), legato (20%).

#### Confidence

- Overall: 0.792
- Gold samples: 4927
- Factory samples: 335
- Flags: WEAK_FACTORY_ALIAS

---

### SAX

- **Family:** wind
- **Subfamily:** saxophone
- **Arrangement Role:** COUNTER_MELODY
- **PA800 Track:** ACC3 | NTT: Parallel

#### Alias Sources

- **Velocity:** inherited from Factory `melody` role (weight 25%, confidence 0.20)
- **Timing:** inherited from Gold `riff` role (weight 22%, confidence 0.22)

#### Velocity Curve

| Level | Value |
|---|---|
| pp | 40 |
| p | 68 |
| mp | 83 |
| mf | 98 |
| f | 112 |
| ff | 127 |
| fff | 127 |
| accent | 124 |
| ghost | 62 |
| Source | FACTORY_ALIAS(melody) |
| Confidence | 0.201 |

#### Timing

- Humanization: PHRASE_DRIVEN
- Groove profile: BREATH_PHRASE
- Base offset: 0
- Swing: 0.15

#### Harmony

- Root weight: 0.30
- Third weight: 0.55
- Passing rate: 25%
- Chromatic rate: 10%

#### How It Plays

> Phrase-based melodic counterpoint. velocity inherited from melody role (weight 25%) timing inherited from riff role (weight 22%) phrase driven timing dynamic range 40-127 primary articulation: legato (50%), accent (30%), staccato (20%).

#### Confidence

- Overall: 0.218
- Gold samples: 566
- Factory samples: 157
- Flags: WEAK_GOLD_ALIAS, WEAK_FACTORY_ALIAS

---

### SOLO_GUITAR

- **Family:** guitar
- **Subfamily:** solo
- **Arrangement Role:** SOLO
- **PA800 Track:** ACC5 | NTT: Chord

#### Alias Sources

- **Velocity:** inherited from Factory `melody` role (weight 15%, confidence 0.12)
- **Timing:** inherited from Gold `riff` role (weight 28%, confidence 0.28)

#### Velocity Curve

| Level | Value |
|---|---|
| pp | 40 |
| p | 68 |
| mp | 83 |
| mf | 93 |
| f | 112 |
| ff | 127 |
| fff | 127 |
| accent | 126 |
| ghost | 62 |
| Source | FACTORY_ALIAS(melody) |
| Confidence | 0.121 |

#### Timing

- Humanization: EXPRESSIVE
- Groove profile: PHRASE_FLOW
- Base offset: 0
- Swing: 0.15

#### Harmony

- Root weight: 0.30
- Third weight: 0.55
- Passing rate: 22%
- Chromatic rate: 10%

#### How It Plays

> Expressive solo phrase with bends and articulation. velocity inherited from melody role (weight 15%) timing inherited from riff role (weight 28%) expressive timing dynamic range 40-127 primary articulation: legato (60%), accent (40%), bend (25%).

#### Confidence

- Overall: 0.277
- Gold samples: 566
- Factory samples: 157
- Flags: WEAK_GOLD_ALIAS, WEAK_FACTORY_ALIAS

---

### STRINGS

- **Family:** bowed_strings
- **Subfamily:** ensemble
- **Arrangement Role:** HARMONIC_PAD
- **PA800 Track:** ACC4 | NTT: Fixed/Parallel

#### Alias Sources

- **Velocity:** inherited from Factory `chords` role (weight 5%, confidence 0.05)
- **Timing:** inherited from Gold `accompaniment` role (weight 10%, confidence 0.10)

#### Velocity Curve

| Level | Value |
|---|---|
| pp | 30 |
| p | 61 |
| mp | 76 |
| mf | 85 |
| f | 107 |
| ff | 127 |
| fff | 127 |
| accent | 116 |
| ghost | 54 |
| Source | FACTORY_ALIAS(chords) |
| Confidence | 0.048 |

#### Timing

- Humanization: MINIMAL
- Groove profile: SUSTAIN_FLOW
- Base offset: 1
- Swing: 0.00

#### Harmony

- Root weight: 0.50
- Third weight: 0.70
- Passing rate: 5%
- Chromatic rate: 3%

#### How It Plays

> Sustained harmonic and emotional support. velocity inherited from chords role (weight 5%) timing inherited from accompaniment role (weight 10%) follows chord tones (weight 0.62) dynamic range 30-127 primary articulation: legato (80%), accent (30%).

#### Confidence

- Overall: 0.099
- Gold samples: 3039
- Factory samples: 335
- Flags: WEAK_GOLD_ALIAS, WEAK_FACTORY_ALIAS

---

### SYNTH_LEAD

- **Family:** synth
- **Subfamily:** lead
- **Arrangement Role:** MELODY
- **PA800 Track:** ACC3 | NTT: Parallel

#### Alias Sources

- **Velocity:** inherited from Factory `melody` role (weight 15%, confidence 0.12)
- **Timing:** inherited from Gold `riff` role (weight 13%, confidence 0.13)

#### Velocity Curve

| Level | Value |
|---|---|
| pp | 40 |
| p | 68 |
| mp | 83 |
| mf | 98 |
| f | 112 |
| ff | 127 |
| fff | 127 |
| accent | 121 |
| ghost | 62 |
| Source | FACTORY_ALIAS(melody) |
| Confidence | 0.121 |

#### Timing

- Humanization: PHRASE_DRIVEN
- Groove profile: LEAD_PHRASE
- Base offset: 0
- Swing: 0.15

#### Harmony

- Root weight: 0.30
- Third weight: 0.50
- Passing rate: 20%
- Chromatic rate: 8%

#### How It Plays

> Melodic synthesizer phrase. velocity inherited from melody role (weight 15%) timing inherited from riff role (weight 13%) phrase driven timing dynamic range 40-127 primary articulation: legato (40%), accent (30%), staccato (20%).

#### Confidence

- Overall: 0.129
- Gold samples: 566
- Factory samples: 157
- Flags: WEAK_GOLD_ALIAS, WEAK_FACTORY_ALIAS

---

### VIOLIN

- **Family:** bowed_strings
- **Subfamily:** violin_fiddle
- **Arrangement Role:** MELODY
- **PA800 Track:** ACC4 | NTT: Parallel

#### Alias Sources

- **Velocity:** inherited from Factory `melody` role (weight 15%, confidence 0.12)
- **Timing:** inherited from Gold `riff` role (weight 10%, confidence 0.10)

#### Velocity Curve

| Level | Value |
|---|---|
| pp | 40 |
| p | 68 |
| mp | 83 |
| mf | 95 |
| f | 112 |
| ff | 127 |
| fff | 127 |
| accent | 124 |
| ghost | 62 |
| Source | FACTORY_ALIAS(melody) |
| Confidence | 0.121 |

#### Timing

- Humanization: BOW_DRIVEN
- Groove profile: BOW_PHRASE
- Base offset: 0
- Swing: 0.15

#### Harmony

- Root weight: 0.25
- Third weight: 0.50
- Passing rate: 18%
- Chromatic rate: 8%

#### How It Plays

> Legato melodic voice with slides and ornaments. velocity inherited from melody role (weight 15%) timing inherited from riff role (weight 10%) bow driven timing dynamic range 40-127 primary articulation: legato (70%), accent (30%), staccato (15%).

#### Confidence

- Overall: 0.121
- Gold samples: 566
- Factory samples: 157
- Flags: WEAK_GOLD_ALIAS, WEAK_FACTORY_ALIAS

---

### WOODWIND

- **Family:** wind
- **Subfamily:** folk_woodwind
- **Arrangement Role:** COUNTER_MELODY
- **PA800 Track:** ACC3 | NTT: Parallel

#### Alias Sources

- **Velocity:** inherited from Factory `melody` role (weight 10%, confidence 0.08)
- **Timing:** inherited from Gold `riff` role (weight 4%, confidence 0.04)

#### Velocity Curve

| Level | Value |
|---|---|
| pp | 40 |
| p | 68 |
| mp | 83 |
| mf | 98 |
| f | 112 |
| ff | 127 |
| fff | 127 |
| accent | 121 |
| ghost | 62 |
| Source | FACTORY_ALIAS(melody) |
| Confidence | 0.081 |

#### Timing

- Humanization: MODERATE
- Groove profile: GENERIC
- Base offset: 0
- Swing: 0.15

#### Harmony

- Root weight: 0.40
- Third weight: 0.60
- Passing rate: 15%
- Chromatic rate: 3%

#### How It Plays

> Ornamental melodic phrase with breath. velocity inherited from melody role (weight 10%) timing inherited from riff role (weight 4%) follows chord tones (weight 0.52) moderate timing dynamic range 40-127 primary articulation: legato (30%), accent (30%), staccato (20%).

#### Confidence

- Overall: 0.081
- Gold samples: 566
- Factory samples: 157
- Flags: WEAK_GOLD_ALIAS, WEAK_FACTORY_ALIAS

---

## Coverage Summary

| Metric | Before Alias | After Alias |
|---|---|---|
| Gold (timing/articulation) | 15.0% | 90.0% |
| Factory (velocity) | 5.0% | 90.0% |
