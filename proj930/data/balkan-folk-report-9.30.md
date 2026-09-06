# DNA MIDI Studio 9.30 — Balkan/Folk Specialization Report

**Schema:** dna-balkan-folk-profiles
**Version:** 9.30.0

## Autoriteti

- **velocity**: FACTORY
- **timing**: GOLD_PATTERN
- **ornaments**: RULE_BASED
- **meterAccent**: BALKAN_METRIC
- **chordFoundation**: MANDATORY

## Balkanski Metri

### Sedminka (7/8)

- **Grupiranje:** 2+2+3
- **Alternativna grupiranja:** 3+2+2, 2+3+2
- **PPQ po taktu:** 168
- **Tempo raspon:** 100–200 BPM
- **Patterna u Gold bazi:** 628
- **Plesni stilovi:** Leskoto, Makedonsko oro, Račanik, Balkan folk
- **Distribucija po rolama:** {'drums': 119, 'power-riff': 266, 'riff': 33, 'bass': 210}
- **Prosječna gustina:** 9.2

**Akcent pattern:**

| 1 | 1.00 | ██████████ |
| 2 | 0.50 | █████░░░░░ |
| 3 | 0.30 | ███░░░░░░░ |
| 4 | 0.50 | █████░░░░░ |
| 5 | 0.60 | ██████░░░░ |
| 6 | 0.40 | ████░░░░░░ |
| 7 | 0.40 | ████░░░░░░ |

### Devetina (9/8)

- **Grupiranje:** 2+2+5
- **Alternativna grupiranja:** 2+2+2+3, 2+3+2+2, 3+2+2+2
- **PPQ po taktu:** 216
- **Tempo raspon:** 80–160 BPM
- **Patterna u Gold bazi:** 94
- **Plesni stilovi:** Aksak, Devetinka, Balkan folk 9/8
- **Distribucija po rolama:** {'drums': 24, 'power-riff': 31, 'bass': 39}
- **Prosječna gustina:** 13.25

**Akcent pattern:**

| 1 | 1.00 | ██████████ |
| 2 | 0.50 | █████░░░░░ |
| 3 | 0.30 | ███░░░░░░░ |
| 4 | 0.50 | █████░░░░░ |
| 5 | 0.60 | ██████░░░░ |
| 6 | 0.40 | ████░░░░░░ |
| 7 | 0.40 | ████░░░░░░ |
| 8 | 0.30 | ███░░░░░░░ |
| 9 | 0.30 | ███░░░░░░░ |

### Šestčetvrtina (6/4)

- **Grupiranje:** 3+3
- **Alternativna grupiranja:** 
- **PPQ po taktu:** 144
- **Tempo raspon:** 60–120 BPM
- **Patterna u Gold bazi:** 40
- **Plesni stilovi:** Balkan folk 6/4
- **Distribucija po rolama:** {'drums': 11, 'power-riff': 7, 'accompaniment': 9, 'bass': 9, 'riff': 4}
- **Prosječna gustina:** 17.79

**Akcent pattern:**

| 1 | 1.00 | ██████████ |
| 2 | 0.50 | █████░░░░░ |
| 3 | 0.30 | ███░░░░░░░ |
| 4 | 0.60 | ██████░░░░ |
| 5 | 0.40 | ████░░░░░░ |
| 6 | 0.30 | ███░░░░░░░ |

## Folk Instrumenti

### Harmonika (Button Accordion)

- **GM Patch:** 22
- **Familija:** keyboard
- **Primarna rola:** chords
- **Velocity autoritet:** FACTORY
- **Timing autoritet:** GOLD_PATTERN
- **Humanizacija:** BELLOW_PHRASE
- **Chord obavezno:** MANDATORY
- **Raspon:** 48–84

**Ornamenti:**

| Ornament | Vjerovatnost | Interval | Timing offset |
|----------|-------------|----------|---------------|
| mordent | 15% | 2 | -3 |
| turn | 8% | 2 | -5 |
| glissando | 5% | — | 0 |

### Klarinet (Clarinet)

- **GM Patch:** 72
- **Familija:** wind
- **Primarna rola:** melody
- **Velocity autoritet:** FACTORY
- **Timing autoritet:** GOLD_PATTERN
- **Humanizacija:** BREATH_PHRASE
- **Chord obavezno:** MANDATORY
- **Raspon:** 55–91

**Ornamenti:**

| Ornament | Vjerovatnost | Interval | Timing offset |
|----------|-------------|----------|---------------|
| mordent | 25% | 2 | -2 |
| trill | 12% | 2 | — |
| appoggiatura | 20% | 3 | -4 |
| glissando | 8% | — | 0 |
| shake | 5% | 2 | — |

### Violina (Violin)

- **GM Patch:** 41
- **Familija:** strings
- **Primarna rola:** melody
- **Velocity autoritet:** FACTORY
- **Timing autoritet:** GOLD_PATTERN
- **Humanizacija:** BOW_PHRASE
- **Chord obavezno:** MANDATORY
- **Raspon:** 55–96

**Ornamenti:**

| Ornament | Vjerovatnost | Interval | Timing offset |
|----------|-------------|----------|---------------|
| mordent | 20% | 2 | -2 |
| trill | 18% | 2 | — |
| appoggiatura | 22% | 3 | -3 |
| glissando | 15% | — | 0 |
| grace_note | 10% | 2 | -2 |

### Frula (Folk Flute/Recorder)

- **GM Patch:** 75
- **Familija:** wind
- **Primarna rola:** melody
- **Velocity autoritet:** FACTORY
- **Timing autoritet:** GOLD_PATTERN
- **Humanizacija:** BREATH_PHRASE
- **Chord obavezno:** MANDATORY
- **Raspon:** 60–84

**Ornamenti:**

| Ornament | Vjerovatnost | Interval | Timing offset |
|----------|-------------|----------|---------------|
| mordent | 30% | 2 | -1 |
| trill | 15% | 2 | — |
| appoggiatura | 18% | 2 | -3 |
| flutter | 8% | — | — |

### Tambura (Tamburitza)

- **GM Patch:** 25
- **Familija:** strings
- **Primarna rola:** chords
- **Velocity autoritet:** FACTORY
- **Timing autoritet:** GOLD_PATTERN
- **Humanizacija:** PLECTRUM_PHRASE
- **Chord obavezno:** MANDATORY
- **Raspon:** 48–77

**Ornamenti:**

| Ornament | Vjerovatnost | Interval | Timing offset |
|----------|-------------|----------|---------------|
| mordent | 10% | 2 | -2 |
| appoggiatura | 12% | 2 | -2 |

### Gusle (Folk Fiddle)

- **GM Patch:** 111
- **Familija:** strings
- **Primarna rola:** melody
- **Velocity autoritet:** FACTORY
- **Timing autoritet:** GOLD_PATTERN
- **Humanizacija:** BOW_FREE
- **Chord obavezno:** MANDATORY
- **Raspon:** 55–77

**Ornamenti:**

| Ornament | Vjerovatnost | Interval | Timing offset |
|----------|-------------|----------|---------------|
| glissando | 25% | — | 0 |
| mordent | 15% | 1 | -2 |
| vibrato_wide | 20% | — | — |

## Determinizam i Hard Limits

### BLOCK pravila
- FACTORY velocity se NIKAD ne zamjenjuje — samo skalira (0.7–1.0)
- Chord foundation je OBAVEZAN za sve folk instrumente
- Ornament interval mora biti dijatonski (vezan za skalu)
- Timing offset NIKAD ne prekoračuje ±6 PPQ

### CLAMP pravila
- Velocity scale: CLAMP(0.7, 1.0)
- Timing offset: CLAMP(-6, +6) PPQ
- Ornament probability: CLAMP(0, 1.0)
- Vibrato depth: CLAMP(0, 20) cents
