# DNA MIDI Studio 9.30 — Instrument Playing Profile Report

**Verzija:** 9.30.0
**Ukupno profila:** 22
**Autoritet:** FACTORY=Velocity, GOLD=Timing/Articulation, PA800=Mapping
**Osnova:** Chord Tracking — svaka funkcija prati Chord

---

## ACCOMPANIMENT

- **Family:** keyboard
- **Subfamily:** generic_comp
- **Arrangement Role:** RHYTHMIC_CHORD
- **Musical Role:** Generic chordal/rhythmic support
- **PA800 Track:** ACC2 | NTT: Chord/Fixed
- **Register:** mid

### Velocity

| Level | Value |
|---|---|
| pp | 15 |
| p | 45 |
| mp | 60 |
| mf | 75 |
| f | 100 |
| ff | 118 |
| fff | 127 |
| accent | 110 |
| ghost | 30 |
| Source | DEFAULT_ESTIMATED |
| Confidence | 0.30 |

### Harmony

- Root weight: 0.40
- Third weight: 0.60
- Fifth weight: 0.55
- Passing rate: 8%
- Chromatic rate: 3%
- Chord change: follow_chord

### Timing

- Humanization: MODERATE
- Base offset: 1
- Groove profile: GENERIC
- Swing: 0.00

### How It Plays

> Generic chordal/rhythmic support. follows chord tones (weight 0.52) moderate timing leans slightly late (offset 1) dynamic range 15-127 primary articulation: legato (30%), accent (30%), staccato (20%) in variations: follow section follow relative to chord pa800 ntt: chord/fixed.

### Confidence

- Overall: 0.99
- Gold samples: 3039
- Factory samples: 0
- Flags: None

---

## ACCORDION

- **Family:** free_reed
- **Subfamily:** accordion
- **Arrangement Role:** RHYTHMIC_CHORD
- **Musical Role:** Melodic and chord-pumping Balkan character
- **PA800 Track:** ACC1 | NTT: Chord/Fixed
- **Register:** mid

### Velocity

| Level | Value |
|---|---|
| pp | 15 |
| p | 45 |
| mp | 60 |
| mf | 75 |
| f | 100 |
| ff | 118 |
| fff | 127 |
| accent | 110 |
| ghost | 30 |
| Source | DEFAULT_ESTIMATED |
| Confidence | 0.30 |

### Harmony

- Root weight: 0.50
- Third weight: 0.70
- Fifth weight: 0.65
- Passing rate: 8%
- Chromatic rate: 8%
- Chord change: follow_chord

### Timing

- Humanization: MINIMAL
- Base offset: 0
- Groove profile: ON_BEAT
- Swing: 0.00

### How It Plays

> Melodic and chord-pumping balkan character. follows chord tones (weight 0.62) applies chromatic approach at 8% dynamic range 15-127 primary articulation: legato (50%), accent (40%), staccato (30%) in variations: follow section follow relative to chord pa800 ntt: chord/fixed.

### Confidence

- Overall: 0.00
- Gold samples: 0
- Factory samples: 0
- Flags: LOW_CONFIDENCE

---

## BASS

- **Family:** bass
- **Subfamily:** electric_bass
- **Arrangement Role:** BASS
- **Musical Role:** Low-frequency harmonic and rhythmic foundation
- **PA800 Track:** BASS | NTT: None
- **Register:** low

### Velocity

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
| Source | FACTORY |
| Confidence | 0.46 |

### Harmony

- Root weight: 0.85
- Third weight: 0.10
- Fifth weight: 0.40
- Passing rate: 12%
- Chromatic rate: 5%
- Chord change: anticipate_root

### Timing

- Humanization: CONTROLLED
- Base offset: 0
- Groove profile: POCKET_DRIVEN
- Swing: 0.15

### How It Plays

> Low-frequency harmonic and rhythmic foundation. strongly anchors root notes (weight 0.85) uses passing tones at rate 12% controlled timing dynamic range 32-127 primary articulation: legato (40%), accent (30%), staccato (20%) in variations: groove with variation on fills: walk or rest interlock with kick root follow relative to chord.

### Confidence

- Overall: 0.99
- Gold samples: 2866
- Factory samples: 51
- Flags: None

---

## BRASS

- **Family:** brass
- **Subfamily:** section
- **Arrangement Role:** FILL
- **Musical Role:** Stab accents and section transition marks
- **PA800 Track:** ACC5 | NTT: Parallel
- **Register:** mid

### Velocity

| Level | Value |
|---|---|
| pp | 15 |
| p | 45 |
| mp | 60 |
| mf | 75 |
| f | 100 |
| ff | 118 |
| fff | 127 |
| accent | 110 |
| ghost | 30 |
| Source | DEFAULT_ESTIMATED |
| Confidence | 0.30 |

### Harmony

- Root weight: 0.55
- Third weight: 0.65
- Fifth weight: 0.60
- Passing rate: 8%
- Chromatic rate: 3%
- Chord change: stab_on_change

### Timing

- Humanization: MINIMAL
- Base offset: 0
- Groove profile: ON_BEAT
- Swing: 0.00

### How It Plays

> Stab accents and section transition marks. follows chord tones (weight 0.60) dynamic range 15-127 primary articulation: accent (60%), staccato (40%), legato (30%) in variations: stab accent on fills: stab fill follow relative to chord pa800 ntt: parallel.

### Confidence

- Overall: 0.00
- Gold samples: 0
- Factory samples: 0
- Flags: LOW_CONFIDENCE

---

## CHOIR

- **Family:** vocal
- **Subfamily:** choir
- **Arrangement Role:** HARMONIC_PAD
- **Musical Role:** Sustained vocal harmonic texture
- **PA800 Track:** ACC5 | NTT: Fixed
- **Register:** mid-high

### Velocity

| Level | Value |
|---|---|
| pp | 15 |
| p | 45 |
| mp | 60 |
| mf | 75 |
| f | 100 |
| ff | 118 |
| fff | 127 |
| accent | 110 |
| ghost | 30 |
| Source | DEFAULT_ESTIMATED |
| Confidence | 0.30 |

### Harmony

- Root weight: 0.50
- Third weight: 0.75
- Fifth weight: 0.70
- Passing rate: 8%
- Chromatic rate: 3%
- Chord change: follow_chord

### Timing

- Humanization: MINIMAL
- Base offset: 0
- Groove profile: ON_BEAT
- Swing: 0.00

### How It Plays

> Sustained vocal harmonic texture. follows chord tones (weight 0.65) dynamic range 15-127 primary articulation: legato (30%), accent (30%), staccato (20%) in variations: follow section follow relative to chord pa800 ntt: fixed.

### Confidence

- Overall: 0.00
- Gold samples: 0
- Factory samples: 0
- Flags: LOW_CONFIDENCE

---

## CLARINET

- **Family:** wind
- **Subfamily:** clarinet_folk
- **Arrangement Role:** COUNTER_MELODY
- **Musical Role:** Folk/Balkan ornamental melodic voice
- **PA800 Track:** ACC2 | NTT: Parallel
- **Register:** mid-high

### Velocity

| Level | Value |
|---|---|
| pp | 15 |
| p | 45 |
| mp | 60 |
| mf | 75 |
| f | 100 |
| ff | 118 |
| fff | 127 |
| accent | 110 |
| ghost | 30 |
| Source | DEFAULT_ESTIMATED |
| Confidence | 0.30 |

### Harmony

- Root weight: 0.30
- Third weight: 0.55
- Fifth weight: 0.45
- Passing rate: 20%
- Chromatic rate: 12%
- Chord change: follow_chord

### Timing

- Humanization: MINIMAL
- Base offset: 0
- Groove profile: ON_BEAT
- Swing: 0.00

### How It Plays

> Folk/balkan ornamental melodic voice. uses passing tones at rate 20% applies chromatic approach at 12% dynamic range 15-127 primary articulation: legato (50%), accent (30%), staccato (20%) in variations: follow section follow relative to chord pa800 ntt: parallel.

### Confidence

- Overall: 0.00
- Gold samples: 0
- Factory samples: 0
- Flags: LOW_CONFIDENCE

---

## DRUMS

- **Family:** drums
- **Subfamily:** drum_kit
- **Arrangement Role:** DRUM
- **Musical Role:** Primary rhythmic driver and groove keeper
- **PA800 Track:** DRUM | NTT: None
- **Register:** percussion

### Velocity

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
| Source | FACTORY |
| Confidence | 0.99 |

### Harmony

- Root weight: 0.40
- Third weight: 0.60
- Fifth weight: 0.55
- Passing rate: 8%
- Chromatic rate: 3%
- Chord change: follow_chord

### Timing

- Humanization: TIGHT_HUMAN
- Base offset: 42
- Groove profile: GROOVE_KEEPER
- Swing: 0.15

### How It Plays

> Primary rhythmic driver and groove keeper. follows chord tones (weight 0.52) tight human timing leans slightly late (offset 42) dynamic range 67-127 primary articulation: staccato (90%), accent (50%), ghost (20%) in variations: density change on fills: fill pattern.

### Confidence

- Overall: 0.99
- Gold samples: 1442
- Factory samples: 1421
- Flags: None

---

## FX

- **Family:** fx
- **Subfamily:** special
- **Arrangement Role:** FX
- **Musical Role:** Event/section-driven special effect
- **PA800 Track:** ACC5 | NTT: None
- **Register:** full

### Velocity

| Level | Value |
|---|---|
| pp | 15 |
| p | 45 |
| mp | 60 |
| mf | 75 |
| f | 100 |
| ff | 118 |
| fff | 127 |
| accent | 110 |
| ghost | 30 |
| Source | DEFAULT_ESTIMATED |
| Confidence | 0.30 |

### Harmony

- Root weight: 0.40
- Third weight: 0.60
- Fifth weight: 0.55
- Passing rate: 8%
- Chromatic rate: 3%
- Chord change: follow_chord

### Timing

- Humanization: MINIMAL
- Base offset: 0
- Groove profile: ON_BEAT
- Swing: 0.00

### How It Plays

> Event/section-driven special effect. follows chord tones (weight 0.52) dynamic range 15-127 primary articulation: legato (30%), accent (30%), staccato (20%) in variations: follow section follow relative to chord.

### Confidence

- Overall: 0.00
- Gold samples: 0
- Factory samples: 0
- Flags: LOW_CONFIDENCE

---

## MALLET

- **Family:** percussion
- **Subfamily:** mallet
- **Arrangement Role:** FILL
- **Musical Role:** Clear-attack arpeggiated or repeated color
- **PA800 Track:** ACC2 | NTT: Chord/Parallel
- **Register:** mid-high

### Velocity

| Level | Value |
|---|---|
| pp | 15 |
| p | 45 |
| mp | 60 |
| mf | 75 |
| f | 100 |
| ff | 118 |
| fff | 127 |
| accent | 110 |
| ghost | 30 |
| Source | DEFAULT_ESTIMATED |
| Confidence | 0.30 |

### Harmony

- Root weight: 0.40
- Third weight: 0.60
- Fifth weight: 0.55
- Passing rate: 8%
- Chromatic rate: 3%
- Chord change: follow_chord

### Timing

- Humanization: MINIMAL
- Base offset: 0
- Groove profile: ON_BEAT
- Swing: 0.00

### How It Plays

> Clear-attack arpeggiated or repeated color. follows chord tones (weight 0.52) dynamic range 15-127 primary articulation: legato (30%), accent (30%), staccato (20%) in variations: follow section follow relative to chord pa800 ntt: chord/parallel.

### Confidence

- Overall: 0.00
- Gold samples: 0
- Factory samples: 0
- Flags: LOW_CONFIDENCE

---

## ORGAN

- **Family:** keyboard
- **Subfamily:** organ
- **Arrangement Role:** RHYTHMIC_CHORD
- **Musical Role:** Sustained harmonic and rhythmic comping
- **PA800 Track:** ACC3 | NTT: Fixed
- **Register:** mid

### Velocity

| Level | Value |
|---|---|
| pp | 15 |
| p | 45 |
| mp | 60 |
| mf | 75 |
| f | 100 |
| ff | 118 |
| fff | 127 |
| accent | 110 |
| ghost | 30 |
| Source | DEFAULT_ESTIMATED |
| Confidence | 0.30 |

### Harmony

- Root weight: 0.50
- Third weight: 0.70
- Fifth weight: 0.65
- Passing rate: 5%
- Chromatic rate: 3%
- Chord change: follow_chord

### Timing

- Humanization: MINIMAL
- Base offset: 0
- Groove profile: ON_BEAT
- Swing: 0.00

### How It Plays

> Sustained harmonic and rhythmic comping. follows chord tones (weight 0.62) dynamic range 15-127 primary articulation: legato (30%), accent (30%), staccato (20%) in variations: follow section follow relative to chord pa800 ntt: fixed.

### Confidence

- Overall: 0.00
- Gold samples: 0
- Factory samples: 0
- Flags: LOW_CONFIDENCE

---

## PAD

- **Family:** synth
- **Subfamily:** pad
- **Arrangement Role:** HARMONIC_PAD
- **Musical Role:** Sustained harmonic bed with slow movement
- **PA800 Track:** ACC4 | NTT: Fixed
- **Register:** mid

### Velocity

| Level | Value |
|---|---|
| pp | 15 |
| p | 45 |
| mp | 60 |
| mf | 75 |
| f | 100 |
| ff | 118 |
| fff | 127 |
| accent | 110 |
| ghost | 30 |
| Source | DEFAULT_ESTIMATED |
| Confidence | 0.30 |

### Harmony

- Root weight: 0.50
- Third weight: 0.75
- Fifth weight: 0.70
- Passing rate: 2%
- Chromatic rate: 3%
- Chord change: sustain_through

### Timing

- Humanization: MINIMAL
- Base offset: 0
- Groove profile: ON_BEAT
- Swing: 0.00

### How It Plays

> Sustained harmonic bed with slow movement. follows chord tones (weight 0.65) dynamic range 15-127 primary articulation: legato (30%), accent (30%), staccato (20%) in variations: follow section follow relative to chord pa800 ntt: fixed.

### Confidence

- Overall: 0.00
- Gold samples: 0
- Factory samples: 0
- Flags: LOW_CONFIDENCE

---

## PERCUSSION

- **Family:** percussion
- **Subfamily:** hand_perc
- **Arrangement Role:** PERCUSSION
- **Musical Role:** Interlocking rhythmic color and accent
- **PA800 Track:** PERC | NTT: None
- **Register:** percussion

### Velocity

| Level | Value |
|---|---|
| pp | 15 |
| p | 45 |
| mp | 60 |
| mf | 75 |
| f | 100 |
| ff | 118 |
| fff | 127 |
| accent | 110 |
| ghost | 30 |
| Source | DEFAULT_ESTIMATED |
| Confidence | 0.30 |

### Harmony

- Root weight: 0.40
- Third weight: 0.60
- Fifth weight: 0.55
- Passing rate: 8%
- Chromatic rate: 3%
- Chord change: follow_chord

### Timing

- Humanization: INTERLOCK
- Base offset: 43
- Groove profile: GENERIC
- Swing: 0.00

### How It Plays

> Interlocking rhythmic color and accent. follows chord tones (weight 0.52) interlock timing leans slightly late (offset 43) dynamic range 15-127 primary articulation: legato (30%), accent (30%), staccato (20%) in variations: follow section follow relative to chord.

### Confidence

- Overall: 0.58
- Gold samples: 78
- Factory samples: 0
- Flags: None

---

## PIANO

- **Family:** keyboard
- **Subfamily:** piano
- **Arrangement Role:** RHYTHMIC_CHORD
- **Musical Role:** Chordal comping, voicing, and harmonic support
- **PA800 Track:** ACC2 | NTT: Chord/Fixed
- **Register:** mid

### Velocity

| Level | Value |
|---|---|
| pp | 25 |
| p | 50 |
| mp | 65 |
| mf | 75 |
| f | 100 |
| ff | 118 |
| fff | 127 |
| accent | 110 |
| ghost | 30 |
| Source | DEFAULT_ESTIMATED |
| Confidence | 0.30 |

### Harmony

- Root weight: 0.40
- Third weight: 0.80
- Fifth weight: 0.70
- Passing rate: 8%
- Chromatic rate: 3%
- Chord change: voice_lead_minimal

### Timing

- Humanization: MINIMAL
- Base offset: 0
- Groove profile: ON_BEAT
- Swing: 0.00

### How It Plays

> Chordal comping, voicing, and harmonic support. follows chord tones (weight 0.63) dynamic range 25-127 primary articulation: accent (40%), legato (30%), staccato (30%) in variations: follow section register avoid with bass voicing relative to chord pa800 ntt: chord/fixed.

### Confidence

- Overall: 0.00
- Gold samples: 0
- Factory samples: 0
- Flags: LOW_CONFIDENCE

---

## POWER-RIFF

- **Family:** unknown
- **Subfamily:** unknown
- **Arrangement Role:** RHYTHMIC_CHORD
- **Musical Role:** Undefined musical role
- **PA800 Track:** ACC5 | NTT: Chord
- **Register:** mid

### Velocity

| Level | Value |
|---|---|
| pp | 15 |
| p | 45 |
| mp | 60 |
| mf | 75 |
| f | 100 |
| ff | 118 |
| fff | 127 |
| accent | 110 |
| ghost | 30 |
| Source | DEFAULT_ESTIMATED |
| Confidence | 0.30 |

### Harmony

- Root weight: 0.40
- Third weight: 0.60
- Fifth weight: 0.55
- Passing rate: 8%
- Chromatic rate: 3%
- Chord change: follow_chord

### Timing

- Humanization: MODERATE
- Base offset: 0
- Groove profile: GENERIC
- Swing: 0.15

### How It Plays

> Undefined musical role. follows chord tones (weight 0.52) moderate timing dynamic range 15-127 primary articulation: legato (30%), accent (30%), staccato (20%) in variations: follow section follow relative to chord pa800 ntt: chord.

### Confidence

- Overall: 0.99
- Gold samples: 4927
- Factory samples: 0
- Flags: None

---

## RHYTHM_GUITAR

- **Family:** guitar
- **Subfamily:** rhythm
- **Arrangement Role:** RHYTHMIC_CHORD
- **Musical Role:** Harmonic rhythm with strumming physicality
- **PA800 Track:** ACC1 | NTT: Chord
- **Register:** mid

### Velocity

| Level | Value |
|---|---|
| pp | 35 |
| p | 55 |
| mp | 65 |
| mf | 78 |
| f | 100 |
| ff | 115 |
| fff | 127 |
| accent | 110 |
| ghost | 35 |
| Source | DEFAULT_ESTIMATED |
| Confidence | 0.30 |

### Harmony

- Root weight: 0.45
- Third weight: 0.75
- Fifth weight: 0.70
- Passing rate: 5%
- Chromatic rate: 3%
- Chord change: strum_chord_change

### Timing

- Humanization: MINIMAL
- Base offset: 0
- Groove profile: ON_BEAT
- Swing: 0.00

### How It Plays

> Harmonic rhythm with strumming physicality. follows chord tones (weight 0.63) dynamic range 35-127 primary articulation: accent (50%), staccato (30%), legato (20%) in variations: pattern change register avoid with bass strum voicing relative to chord pa800 ntt: chord guitar mode: norm/finger/pick.

### Confidence

- Overall: 0.00
- Gold samples: 0
- Factory samples: 0
- Flags: LOW_CONFIDENCE

---

## RIFF

- **Family:** unknown
- **Subfamily:** unknown
- **Arrangement Role:** FILL
- **Musical Role:** Undefined musical role
- **PA800 Track:** ACC5 | NTT: Chord
- **Register:** mid

### Velocity

| Level | Value |
|---|---|
| pp | 15 |
| p | 45 |
| mp | 60 |
| mf | 75 |
| f | 100 |
| ff | 118 |
| fff | 127 |
| accent | 110 |
| ghost | 30 |
| Source | DEFAULT_ESTIMATED |
| Confidence | 0.30 |

### Harmony

- Root weight: 0.40
- Third weight: 0.60
- Fifth weight: 0.55
- Passing rate: 8%
- Chromatic rate: 3%
- Chord change: follow_chord

### Timing

- Humanization: MODERATE
- Base offset: 0
- Groove profile: GENERIC
- Swing: 0.15

### How It Plays

> Undefined musical role. follows chord tones (weight 0.52) moderate timing dynamic range 15-127 primary articulation: legato (30%), accent (30%), staccato (20%) in variations: follow section follow relative to chord pa800 ntt: chord.

### Confidence

- Overall: 0.99
- Gold samples: 566
- Factory samples: 0
- Flags: None

---

## SAX

- **Family:** wind
- **Subfamily:** saxophone
- **Arrangement Role:** COUNTER_MELODY
- **Musical Role:** Phrase-based melodic counterpoint
- **PA800 Track:** ACC3 | NTT: Parallel
- **Register:** mid

### Velocity

| Level | Value |
|---|---|
| pp | 15 |
| p | 45 |
| mp | 60 |
| mf | 75 |
| f | 100 |
| ff | 118 |
| fff | 127 |
| accent | 110 |
| ghost | 30 |
| Source | DEFAULT_ESTIMATED |
| Confidence | 0.30 |

### Harmony

- Root weight: 0.30
- Third weight: 0.55
- Fifth weight: 0.45
- Passing rate: 25%
- Chromatic rate: 10%
- Chord change: follow_chord

### Timing

- Humanization: MINIMAL
- Base offset: 0
- Groove profile: ON_BEAT
- Swing: 0.00

### How It Plays

> Phrase-based melodic counterpoint. uses passing tones at rate 25% applies chromatic approach at 10% dynamic range 15-127 primary articulation: legato (50%), accent (30%), staccato (20%) in variations: phrase counter on fills: phrase ending counter melody relative to chord pa800 ntt: parallel.

### Confidence

- Overall: 0.00
- Gold samples: 0
- Factory samples: 0
- Flags: LOW_CONFIDENCE

---

## SOLO_GUITAR

- **Family:** guitar
- **Subfamily:** solo
- **Arrangement Role:** SOLO
- **Musical Role:** Expressive solo phrase with bends and articulation
- **PA800 Track:** ACC5 | NTT: Chord
- **Register:** mid-high

### Velocity

| Level | Value |
|---|---|
| pp | 15 |
| p | 45 |
| mp | 60 |
| mf | 75 |
| f | 100 |
| ff | 118 |
| fff | 127 |
| accent | 110 |
| ghost | 30 |
| Source | DEFAULT_ESTIMATED |
| Confidence | 0.30 |

### Harmony

- Root weight: 0.30
- Third weight: 0.55
- Fifth weight: 0.45
- Passing rate: 22%
- Chromatic rate: 10%
- Chord change: follow_chord

### Timing

- Humanization: MINIMAL
- Base offset: 0
- Groove profile: ON_BEAT
- Swing: 0.00

### How It Plays

> Expressive solo phrase with bends and articulation. uses passing tones at rate 22% applies chromatic approach at 10% dynamic range 15-127 primary articulation: legato (60%), accent (40%), bend (25%) in variations: follow section follow relative to chord pa800 ntt: chord.

### Confidence

- Overall: 0.00
- Gold samples: 0
- Factory samples: 0
- Flags: LOW_CONFIDENCE

---

## STRINGS

- **Family:** bowed_strings
- **Subfamily:** ensemble
- **Arrangement Role:** HARMONIC_PAD
- **Musical Role:** Sustained harmonic and emotional support
- **PA800 Track:** ACC4 | NTT: Fixed/Parallel
- **Register:** mid-high

### Velocity

| Level | Value |
|---|---|
| pp | 15 |
| p | 45 |
| mp | 60 |
| mf | 75 |
| f | 100 |
| ff | 118 |
| fff | 127 |
| accent | 110 |
| ghost | 30 |
| Source | DEFAULT_ESTIMATED |
| Confidence | 0.30 |

### Harmony

- Root weight: 0.50
- Third weight: 0.70
- Fifth weight: 0.65
- Passing rate: 5%
- Chromatic rate: 3%
- Chord change: smooth_voice_lead

### Timing

- Humanization: MINIMAL
- Base offset: 0
- Groove profile: ON_BEAT
- Swing: 0.00

### How It Plays

> Sustained harmonic and emotional support. follows chord tones (weight 0.62) dynamic range 15-127 primary articulation: legato (80%), accent (30%) in variations: sustain with movement on fills: sustain or crest follow relative to chord pa800 ntt: fixed/parallel.

### Confidence

- Overall: 0.00
- Gold samples: 0
- Factory samples: 0
- Flags: LOW_CONFIDENCE

---

## SYNTH_LEAD

- **Family:** synth
- **Subfamily:** lead
- **Arrangement Role:** MELODY
- **Musical Role:** Melodic synthesizer phrase
- **PA800 Track:** ACC3 | NTT: Parallel
- **Register:** mid-high

### Velocity

| Level | Value |
|---|---|
| pp | 15 |
| p | 45 |
| mp | 60 |
| mf | 75 |
| f | 100 |
| ff | 118 |
| fff | 127 |
| accent | 110 |
| ghost | 30 |
| Source | DEFAULT_ESTIMATED |
| Confidence | 0.30 |

### Harmony

- Root weight: 0.40
- Third weight: 0.60
- Fifth weight: 0.55
- Passing rate: 8%
- Chromatic rate: 3%
- Chord change: follow_chord

### Timing

- Humanization: MINIMAL
- Base offset: 0
- Groove profile: ON_BEAT
- Swing: 0.00

### How It Plays

> Melodic synthesizer phrase. follows chord tones (weight 0.52) dynamic range 15-127 primary articulation: legato (30%), accent (30%), staccato (20%) in variations: follow section follow relative to chord pa800 ntt: parallel.

### Confidence

- Overall: 0.00
- Gold samples: 0
- Factory samples: 0
- Flags: LOW_CONFIDENCE

---

## VIOLIN

- **Family:** bowed_strings
- **Subfamily:** violin_fiddle
- **Arrangement Role:** MELODY
- **Musical Role:** Legato melodic voice with slides and ornaments
- **PA800 Track:** ACC4 | NTT: Parallel
- **Register:** high

### Velocity

| Level | Value |
|---|---|
| pp | 15 |
| p | 45 |
| mp | 60 |
| mf | 75 |
| f | 100 |
| ff | 118 |
| fff | 127 |
| accent | 110 |
| ghost | 30 |
| Source | DEFAULT_ESTIMATED |
| Confidence | 0.30 |

### Harmony

- Root weight: 0.25
- Third weight: 0.50
- Fifth weight: 0.40
- Passing rate: 18%
- Chromatic rate: 8%
- Chord change: follow_chord

### Timing

- Humanization: MINIMAL
- Base offset: 0
- Groove profile: ON_BEAT
- Swing: 0.00

### How It Plays

> Legato melodic voice with slides and ornaments. uses passing tones at rate 18% applies chromatic approach at 8% dynamic range 15-127 primary articulation: legato (70%), accent (30%), staccato (15%) in variations: follow section follow relative to chord pa800 ntt: parallel.

### Confidence

- Overall: 0.00
- Gold samples: 0
- Factory samples: 0
- Flags: LOW_CONFIDENCE

---

## WOODWIND

- **Family:** wind
- **Subfamily:** folk_woodwind
- **Arrangement Role:** COUNTER_MELODY
- **Musical Role:** Ornamental melodic phrase with breath
- **PA800 Track:** ACC3 | NTT: Parallel
- **Register:** mid-high

### Velocity

| Level | Value |
|---|---|
| pp | 15 |
| p | 45 |
| mp | 60 |
| mf | 75 |
| f | 100 |
| ff | 118 |
| fff | 127 |
| accent | 110 |
| ghost | 30 |
| Source | DEFAULT_ESTIMATED |
| Confidence | 0.30 |

### Harmony

- Root weight: 0.40
- Third weight: 0.60
- Fifth weight: 0.55
- Passing rate: 8%
- Chromatic rate: 3%
- Chord change: follow_chord

### Timing

- Humanization: MINIMAL
- Base offset: 0
- Groove profile: ON_BEAT
- Swing: 0.00

### How It Plays

> Ornamental melodic phrase with breath. follows chord tones (weight 0.52) dynamic range 15-127 primary articulation: legato (30%), accent (30%), staccato (20%) in variations: follow section follow relative to chord pa800 ntt: parallel.

### Confidence

- Overall: 0.00
- Gold samples: 0
- Factory samples: 0
- Flags: LOW_CONFIDENCE

---
