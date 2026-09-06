# DNA MIDI Studio 9.30 — SITUACIONI LOG

**Datum:** 2026-09-06  
**Verzija:** 9.30.0  
**Autoritet model:** FACTORY → GOLD → PA800  
**Chord Foundation:** Chord tracking je osnova za SVE funkcije

---

## 1. ŠTA APLIKACIJA RADI — PREGLED

DNA MIDI Studio 9.30 je profesionalni MIDI workflow engine za **Korg Pa800** arranger.  
Aplikacija uzima sirove MIDI datoteke i pretvara ih u **Pa800-spremne, kalibrirane,  
chord-aware MIDI exporte** — sa instrument-specifičnim profilima, velocity krivama,  
timing/groove ljudskizacijom i full arranger strukturom.

### Ključni tok podataka

```
RAW MIDI → Song Analyzer → Chord Timeline → Instrument Profile Engine
       → Factory Velocity Authority → Gold Timing/Groove Authority
       → PA800 Style Builder → PA800 Validator → MIDI Editor
       → Integrity Check → Export (ZIP sa svim fajlovima)
```

---

## 2. STATISTIKA PROJEKTA

| Metrika | Vrijednost |
|---|---|
| **Ukupno fajlova** | 2246 |
| **Python fajlova (.py)** | 545 |
| **Linije koda (root moduli)** | ~19.000 |
| **Linije koda (src/dna_midi_studio)** | ~33.850 |
| **Test fajlova** | 107 |
| **Data fajlova** | 199 |
| **Model fajlova** | 13 |
| **Ukupna veličina projekta** | 264 MB |
| **ZIP (all files)** | 87 MB |
| **ZIP (code only)** | 1.6 MB |

---

## 3. TRI AUTORITETA — KO VLADA ČIM

| Autoritet | Oblast | Šta radi | Source |
|---|---|---|---|
| **FACTORY** | Velocity | Apsolutni vladar velocity krivih. Nijedan drugi izvor ne smije dirati velocity. | 1964 kalibriranih profila, 1713 sa holdout, 26922 segmenata |
| **GOLD** | Timing / Artikulacija / Ekspresija | Groove, humanizacija, gate, swing, density, register — iz stvarnih MIDI performance podataka | 12918 performance patterna, 10637 regularnih patterna |
| **PA800** | Mapping / Range | NTT tip (Chord/Fixed/Parallel/None), track assign, GM program validacija | Pa800 specifikacija + general-rules-9.30 |

### Krute granice (HARD LIMITS — BLOCK/CLAMP, ne savjet)

- **Gold NIKAD ne sadrži velocity, bank ili program** — to je isključivo FACTORY
- **Kanal 10 note izvan drum map** = BLOKIRAJ (nema zvuka na Pa800)
- **Note izvan instrument key range** = BLOKIRAJ + transponiraj na najbližu validnu
- **Polyphony preko max** = FIFO ukloni najstarije
- **RX/DNC triggeri** = samo sa potvrđenim device evidence
- **Calibration** = READ_ONLY, niko ne dira kalibracione podatke

---

## 4. FACTORY AUTORITET — Detaljno

### Resursi

| Resurs | Veličina | Sadržaj |
|---|---|---|
| `factory-velocity-profiles.json` | 14.4 MB | Sirovi velocity profili po stilu |
| `factory-velocity-catalog-9.30.json` | 1.7 MB | Katalog sa perRole, perInstrument, perProfile |
| `factory-calibration-4.37.json` | 2.9 MB | Kalibracioni podaci (4.37) |
| `factory-strumming.json` | 15.6 MB | Strum patterni za guitar |
| `factory-style-segments.json` | 38.1 MB | Segmenti po stilu |
| `factory-profiles-optimizer.json` | 746 KB | Pretvoreni profili za optimizer |
| `factory-device-evidence-4.46.json` | 1.3 MB | Device evidence za RX/DNC |

### Factory Role Coverage

| Role | Profila | GM Programa | Vel P50 | Vel P95 |
|---|---|---|---|---|
| **drums** | 1180 | 0 | 93 | 109 |
| **chords** | 329 | 33 | 84 | 109 |
| **melody** | 154 | 32 | 92 | 113 |
| **bass** | 50 | 14 | 102 | 119 |

**Bass** ima najsnažniju velocity krivu: full-range 1-127, P50=102, P95=119.  
**Chords** su blaži: P50=84, P95=109.  
**Drums** su u sredini: P50=93.  
**Melody** ima najširi P95=113.

### Factory Style Family Kalibracija

| Stilska familija | Segmenata | Stilova | Confidence |
|---|---|---|---|
| ballad | 2743 | 26 | 1.00 |
| beat | 1938 | 24 | 1.00 |
| techno_dance | 2051 | 20 | 1.00 |
| 6/8 | 628 | 5 | 0.70 |
| rock | 447 | 4 | 0.50 |

---

## 5. GOLD AUTORITET — Detaljno

### Dvije baze podataka

| Baza | Patterna | Role | Autoritet |
|---|---|---|---|
| `gold-patterns.json` | 10.637 | drums(599), melody(4439), chords(3590), bass(2009) | TIMING/GROOVE/DENSITY |
| `gold-performance-patterns.json` | 12.918 | power-riff(4927), accompaniment(3039), bass(2866), drums(1442), riff(566), percussion(78) | PERFORMANCE DNA |

### Gold Performance Pattern Detalji (power-riff)

| Parametar | Vrijednost |
|---|---|
| Patterna | 4927 |
| Density mean | 12.3 note/takt |
| Density median | 12.0 |
| Density IQR | 10.0 |
| Length bars mean | 1.36 |
| Length bars mode | 1 |

### Šta Gold daje instrumentima

| Instrument | Gold Source | Confidence | Šta dobija |
|---|---|---|---|
| **accompaniment** | 3039 patterna | 0.99 | Timing, groove, density, register |
| **power-riff** | 4927 patterna | 0.99 | Timing, gate, attack, voicing |
| **bass** | 2866 patterna | 0.99 | Pocket, groove, timing offset |
| **drums** | 1442 patterna | 0.99 | Groove, fill, element timing |
| **riff** | 566 patterna | 0.99 | Motif timing, variation |
| **percussion** | 78 patterna | 0.80 | Percussion groove |
| **accordion** | ❌ NEMA | 0.00 | ❌ Nema Gold podatke |
| **brass** | ❌ NEMA | 0.00 | ❌ Nema Gold podatke |
| **choir** | ❌ NEMA | 0.00 | ❌ Nema Gold podatke |
| **clarinet** | ❌ NEMA | 0.00 | ❌ Nema Gold podatke |
| **organ** | ❌ NEMA | 0.00 | ❌ Nema Gold podatke |
| **pad** | ❌ NEMA | 0.00 | ❌ Nema Gold podatke |
| **piano** | ❌ NEMA | 0.00 | ❌ Nema Gold podatke |
| **sax** | ❌ NEMA | 0.00 | ❌ Nema Gold podatke |
| **solo_guitar** | ❌ NEMA | 0.00 | ❌ Nema Gold podatke |
| **strings** | ❌ NEMA | 0.00 | ❌ Nema Gold podatke |
| **violin** | ❌ NEMA | 0.00 | ❌ Nema Gold podatke |
| **woodwind** | ❌ NEMA | 0.00 | ❌ Nema Gold podatke |

> **⚠️ GAP:** 15 od 22 profila nemaju direktne Gold podatke jer Gold koristi  
> drugačiju rolu imenovanje (accompaniment/power-riff/bass/drums/riff/percussion)  
> dok Master Prompt zahtijeva 20+ specifičnih familija. Potreban **role alias mapping**.

---

## 6. INSTRUMENT PROFILE ENGINE — Musical DNA

### 22 Profila (13 sekcija po Master Promptu)

| # | Profil | Family | Velocity Source | Timing Source | PA800 NTT | Vel Conf | Tim Conf |
|---|---|---|---|---|---|---|---|
| 1 | accompaniment | keyboard | DEFAULT_EST | GOLD (3039) | Chord/Fixed | 0.30 | 0.99 |
| 2 | accordion | free_reed | DEFAULT_EST | NONE | Chord/Fixed | 0.30 | 0.00 |
| 3 | **bass** | bass | **FACTORY** (50) | **GOLD** (2866) | **None** | 0.46 | 0.99 |
| 4 | brass | brass | DEFAULT_EST | NONE | Parallel | 0.30 | 0.00 |
| 5 | choir | vocal | DEFAULT_EST | NONE | Fixed | 0.30 | 0.00 |
| 6 | clarinet | wind | DEFAULT_EST | NONE | Parallel | 0.30 | 0.00 |
| 7 | **drums** | drums | **FACTORY** (1180) | **GOLD** (1442) | **None** | 0.99 | 0.99 |
| 8 | fx | fx | DEFAULT_EST | NONE | None | 0.30 | 0.00 |
| 9 | mallet | percussion | DEFAULT_EST | NONE | Chord/Parallel | 0.30 | 0.00 |
| 10 | organ | keyboard | DEFAULT_EST | NONE | Fixed | 0.30 | 0.00 |
| 11 | pad | synth | DEFAULT_EST | NONE | Fixed | 0.30 | 0.00 |
| 12 | **percussion** | percussion | DEFAULT_EST | **GOLD** (78) | None | 0.30 | 0.80 |
| 13 | piano | keyboard | DEFAULT_EST | NONE | Chord/Fixed | 0.30 | 0.00 |
| 14 | **power-riff** | unknown | DEFAULT_EST | **GOLD** (4927) | Chord | 0.30 | 0.99 |
| 15 | rhythm_guitar | guitar | DEFAULT_EST | NONE | Chord | 0.30 | 0.00 |
| 16 | **riff** | unknown | DEFAULT_EST | **GOLD** (566) | Chord | 0.30 | 0.99 |
| 17 | sax | wind | DEFAULT_EST | NONE | Parallel | 0.30 | 0.00 |
| 18 | solo_guitar | guitar | DEFAULT_EST | NONE | Chord | 0.30 | 0.00 |
| 19 | strings | bowed_strings | DEFAULT_EST | NONE | Fixed/Parallel | 0.30 | 0.00 |
| 20 | synth_lead | synth | DEFAULT_EST | NONE | Parallel | 0.30 | 0.00 |
| 21 | violin | bowed_strings | DEFAULT_EST | NONE | Parallel | 0.30 | 0.00 |
| 22 | woodwind | wind | DEFAULT_EST | NONE | Parallel | 0.30 | 0.00 |

### Samo 5 profila ima prave podatke:
- ✅ **bass** — FACTORY velocity + GOLD timing (najbolje pokriven)
- ✅ **drums** — FACTORY velocity + GOLD timing (najbolje pokriven)
- ✅ **accompaniment** — GOLD timing (ali bez FACTORY velocity)
- ✅ **power-riff** — GOLD timing
- ✅ **riff** — GOLD timing
- ✅ **percussion** — GOLD timing (slaba pokrivenost, 78 patterna)

### 17 profila koristi DEFAULT_ESTIMATED — treba alias mapping:

```
accompaniment → piano, organ, pad, accordion, strings, choir
chords (Factory) → piano, organ, guitar, accordion, strings, pad
melody (Factory) → sax, clarinet, violin, solo_guitar, synth_lead
power-riff → rhythm_guitar
bass → bass (već mapiran)
drums → drums (već mapiran)
```

---

## 7. AE FUNCTION REGISTRY — 234 Funkcije

| Kategorija | Funkcija | Autoritet | Chord Dep |
|---|---|---|---|
| MIXER_LEVEL | 26 | FACTORY | STRONG/MEDIUM/WEAK |
| VELOCITY | 28 | FACTORY | STRONG(37)/MEDIUM/WEAK |
| EXPRESSION | 25 | GOLD | MEDIUM/WEAK |
| TIMING_GROOVE | 30 | GOLD | STRONG/MEDIUM/WEAK |
| ARTICULATION | 25 | GOLD | MEDIUM/WEAK |
| DRUMS_PERCUSSION | 25 | GOLD | STRONG/MEDIUM/WEAK |
| ARRANGEMENT_PATTERN | 25 | MIXED | MEDIUM/WEAK |
| KORG_PA800 | 25 | PA800 | MEDIUM/WEAK |
| OPTIMIZATION_QA | 25 | ALL | WEAK |

### Chord Dependency Distribucija

| Nivo | Funkcija | Opis |
|---|---|---|
| **STRONG** | 37 | Funkcija direktno zavisi od chord timeline — bez chorda ne može raditi |
| **MEDIUM** | 31 | Koristi chord za enrichment, ali može raditi i bez |
| **WEAK** | 166 | Indirektna veza, ne zahtijeva chord u real-time |

---

## 8. GENERAL RULES 9.30 — Kruta Pravila

| Pravilo | Tip | Opis |
|---|---|---|
| RULE 1 | **BLOCK** | Note izvan key range = blokiraj, transponiraj na najbližu validnu |
| RULE 2 | **CLAMP** | Velocity ispod min = clamp na ppp |
| RULE 3 | **CLAMP** | Velocity iznad 127 = clamp na 127 |
| RULE 4 | **BLOCK** | Kanal 10 izvan drum map = blokiraj (nema zvuka na Pa800) |
| RULE 5 | **FIFO** | Polyphony preko max = ukloni najstarije |
| RULE 6-10 | Various | Pitch-bend, expression, controller pravila |

### Podsekcije

| Sekcija | Unosa | Opis |
|---|---|---|
| `gmMelodicRanges` | 128 | GM program key range za svaki program (0-127) |
| `drumValidKeys` | 61 | Validni drum key-evi na kanalu 10 |
| `velocityRules` | 16 | Per-instrument velocity pravila (bass, drums, chords, melody, guitar, brass...) |
| `channel10Rule` | 3 | Pravilo za kanal 10 + valid key range |
| `polyphonyRules` | 7 | Max polyphony po instrumentu |
| `balkanRules` | 7 | Balkan specifične range prilagodbe (bass, guitar, accordion, brass, sax, drums) |

---

## 9. DNA RELATIONSHIP GRAMMAR

| Parametar | Vrijednost |
|---|---|
| Source | Gold DNA.zip, 182 MIDI fajla, 61 relationship fajl |
| Vrste | **terca** + **echo** |
| Ignorirani invalid pairs | 7332 |
| Autoritet | GOLD_SOURCE_MIDI_RELATIONSHIP_GRAMMAR |

### Terca (harmonija trećine)
- Pair count, source/target notes, action probabilities
- Phrase-level action probabilities
- Interval counts

### Echo (odziv/imitacija)
- Pair count, source/target notes
- Action probabilities per phrase

---

## 10. SOLO ORNAMENT CALIBRATION

| Ornament | Opis |
|---|---|
| **grace** | Grace note — brzi ukrasni ton prije glavnog |
| **trill** | Tril — brza alternacija između dva tona |
| **slide** | Klizanje — pitch bend efekat |
| **bend** | Bend — polutonski zavoj |

**Politika:**
- Velocity authority = FACTORY_ONLY
- Gold velocity = FORBIDDEN
- Original MIDI mutacija = zabranjena
- Pitch bend je evidence, ne direktna kopija
- Main solo uvijek očuvan

---

## 11. DRUM ELEMENT EVIDENCE

| Element | Gold patterna | Autoritet |
|---|---|---|
| **closed-hat** | 11.789 | TIMING_GATE_GROOVE_FILL |
| **snare** | 6.064 | TIMING_GATE_GROOVE_FILL |
| **kick** | 3.083 | TIMING_GATE_GROOVE_FILL |
| **open-hat** | 1.535 | TIMING_GATE_GROOVE_FILL |
| **tom** | 1.235 | TIMING_GATE_GROOVE_FILL |
| **crash** | 455 | TIMING_GATE_GROOVE_FILL |
| **ride** | 330 | TIMING_GATE_GROOVE_FILL |
| **percussion** | 8.303 | TIMING_GATE_GROOVE_FILL |

**Factory:** 1421 profil, authority = VELOCITY_RANGE_VALIDATION

> **⚠️ GAP:** Drum element sub-profili još nisu izgrađeni — potreban Kick/Snare/HiHat/  
> Crash/Ride/Toms/Percussion pojedinačni profili sa vlastitim timing podacima.

---

## 12. NEURAL MODELI

| Model | Veličina | Opis |
|---|---|---|
| relationship-transformer-v1 | 325 KB | Terca/echo relationship predikcija |
| relationship-sequence-v2 | 71 KB | Sekvencijalna relationship modelacija |
| dna-reconstructor-v1 | 176 KB | DNA rekonstrukcija |
| dna-reconstructor-v2 | 181 KB | DNA rekonstrukcija v2 |
| song-context-model-v1 | ~500 KB | Kontekst pjesme za AI arranger |
| event-decoder-v1 | ~500 KB | Event dekodiranje |

---

## 13. INSTRUMENT CATALOG 9.30

| Parametar | Vrijednost |
|---|---|
| Velocity authority | FACTORY_ONLY |
| Gold velocity policy | FORBIDDEN |
| Calibration mode | READ_ONLY |
| Factory profila | 1713 |
| GM programa | 35 sa coverage |
| Stilska elemenata | 5 |

### 22 Role u katalogu (sa kompletnim behavior/policy/technique definicijama)

Svaka rola ima:
- `playerModel` — kojeg muzička emulira (bassist, pianist, accordionist...)
- `policies` — 9 podsekcija (register, gate, density, controllers, articulationNoise, interaction, repair, generation)
- `behavior` — follows, techniques, phrase_rules, optimization_priorities, forbidden_without_device_evidence
- `evidence_policy` — evidence-guided-soft-musical-hard-device
- `factoryProfileCount` + `velRange7Point` (ako postoje Factory podaci)

---

## 14. CALIBRATION REPORT 9.30

| Faza | Status | Detalj |
|---|---|---|
| Factory calibration | **PASS** | 1964 profila, 1713 kalibrirano, 1052 holdout |
| Factory style family | **PASS** | ballad/beat/techno/6-8/rock kalibrirani |
| Evidence authority | **PASS** | 0 velocity violations, 0 cross-layer errors |
| Master prompt compliance | **PASS** | 22/22 mandatory, 43/43 tests |
| PA800 validation | **PASS** | NTT mapping, drum keys, channel 10 |

---

## 15. VALJA CORPUS — Popravke

| Metrika | Vrijednost |
|---|---|
| Fajlova | 163 |
| Ispravljenih violacija | 18.120 |

---

## 16. CORE MODULE MAPA

### Root moduli (glavni engine)

| Modul | Linija | Opis |
|---|---|---|
| `server.py` | 1714 | Web server + API endpointi |
| `instrument_profile_engine.py` | 1586 | Musical DNA Engine — 22 profila |
| `midi_optimizer.py` | 1137 | Glavni optimizator sa chord tracking |
| `special_track_engine.py` | 617 | Specijalni track obrada |
| `song_analyzer.py` | 518 | Analiza pjesme + chord extraction |
| `dna_builder.py` | 512 | DNA Relationship Grammar builder |
| `premium_config.py` | 490 | Premium konfiguracija |
| `phase_optimizer.py` | 466 | Fazni optimizator |
| `corpus_forensics.py` | 345 | Corpus forenzika i validacija |
| `gold_performance_registry.py` | 321 | Gold pattern registry |
| `performance_engine.py` | 260 | Performance engine |
| `web_gui.py` | 238 | Web GUI |
| `midi_editor.py` | 224 | MIDI editor |
| `factory_velocity.py` | — | FACTORY velocity autoritet |
| `factory_strumming.py` | — | Factory strum podaci |
| `pa800_style_builder.py` | — | PA800 stil builder |
| `pa800_validator.py` | — | PA800 validator |
| `performance_gesture_engine.py` | — | Gesture/RX/DNC engine |
| `session6_rx.py` | — | RX engine |
| `session7_dnc.py` | — | DNC engine |

### src/dna_midi_studio/ (biblioteka)

| Modul | Linija | Opis |
|---|---|---|
| `solo_enhancement.py` | 1112 | Solo pojačavanje + ornamenti |
| `premium_expression.py` | 997 | Premium ekspresija engine |
| `candidate_search.py` | 921 | Pretraga kandidata |
| `arrangement_renderer.py` | 895 | Arrangement rendering |
| `music_quality.py` | 854 | Kvalitet muzike evaluator |
| `song_understanding.py` | 851 | Razumijevanje pjesme |
| `articulation_mapping.py` | 845 | Artikulacija mapa |
| `harmonic_reconstruction.py` | 824 | Harmonijska rekonstrukcija |
| `groove_polyphony.py` | 814 | Groove + polifonija |
| `guitar_reconstruction.py` | 765 | Gitara rekonstrukcija |
| `rx_engine.py` | 685 | RX (realtime expression) engine |
| `dnc_engine.py` | 644 | DNC (drawer/notation) engine |
| `evidence_authority.py` | 675 | Evidence autoritet sistem |

---

## 17. SESSION HISTORY — 38 sesija razvoja

Sesije 2-38 pokrivaju:
- **2-5:** Rekonstrukcija osnove + demo
- **6-7:** RX i DNC engine
- **8:** Agent runtime
- **9-13:** Pipeline, release check
- **14:** Device certification (Pa800 pre-flight)
- **15:** Premium baseline (20/20 PASS)
- **17:** Production adapter (35/35 PASS)
- **18:** Track identity + solo safety (28/28 PASS)
- **19:** Song understanding (36/36 PASS)
- **20:** AI producer brief (52/52 PASS)
- **21-25:** Arrangement graph, groove plan, expression plan, articulation map
- **26-29:** Premium preview/workflow, personal profile
- **30:** Release readiness hardening
- **31-32:** Track analysis, evidence resolver
- **33-35:** Arrangement renderer, end-to-end arranger
- **36-38:** Reliability gate, quality calibration, device lab

---

## 18. ZNANI GABOVI I ŠTA FALI

### KRITIČNO — Role Alias Mapping

| Stanje | Opis |
|---|---|
| **Problem** | Gold koristi 6 rola, Master Prompt traži 20+ familija |
| **Uticaj** | 15 profila koristi DEFAULT_ESTIMATED umjesto stvarnih podataka |
| **Rješenje** | Mapirati: `accompaniment`→piano/organ/pad/accordion/strings/choir, `melody`→sax/clarinet/violin/solo_guitar, `power-riff`→rhythm_guitar, `chords` (Factory)→isti |
| **Prioritet** | 🔴 VISOK — bez ovoga 68% profila nije stvarno kalibrirano |

### VAŽNO — Drum Element Sub-profili

| Stanje | Opis |
|---|---|
| **Problem** | Drums su jedan profil, ali drum-element-evidence ima 8 elemenata |
| **Uticaj** | Kick, Snare, HiHat, Crash, Ride, Toms nemaju individualne profile |
| **Rješenje** | Izgraditi 8 sub-profila sa individualnim timing podacima |
| **Prioritet** | 🟡 SREDNJI |

### POŽELJNO — Dodatni engine-i

| Engine | Opis | Prioritet |
|---|---|---|
| Balkan/Folk specijalizacija | 7/8 i 9/8 metrum iz Gold patterna | 🟡 |
| Pattern DNA vs Playing DNA | Odvojeno skladištenje | 🟡 |
| Deterministic humanization | Seed-controlled po instrumentu | 🟢 |
| Ornament Engine | Per-instrument ornament constraints | 🟢 |
| Expression Engine | Sekcija-korelirani CC11 | 🟢 |

---

## 19. OUTPUT DATOTEKE

| Fajl | Veličina | Opis |
|---|---|---|
| `instrument-playing-profiles-9.30.json` | 189 KB | 22 profila, 13 sekcija, machine-readable |
| `instrument-profiles-9.30.db` | 148 KB | SQLite sa 4 tabele (profiles, range_data, velocity_data, harmony_data) |
| `instrument-profile-report-9.30.md` | 23 KB | Human-readable report sa howItPlays opisima |
| `ae-function-registry-9.30.json` | 65 KB | 234 funkcije, 9 kategorija |
| `general-rules-9.30.json` | 32 KB | Kruta pravila + GM range + drum keys + balkan |
| `dna-relationship-grammar-8.00.json` | 31 KB | Terca + echo relationship gramatika |
| `dna-solo-ornament-calibration-8.30.json` | 28 KB | 4 ornamenta sa politkom |
| `instrument-catalog-9.30.json` | 3.2 MB | Full katalog sa behavior/policy |
| `factory-velocity-catalog-9.30.json` | 1.7 MB | Factory velocity katalog |
| `drum-element-evidence-4.46.json` | 638 B | Drum element evidencija |
| `evidence-authority-status-4.36.json` | 951 B | Hard gate status |

---

## 20. ARHITEKTURA — Tok Funkcija

```
┌──────────────────────────────────────────────────────────────┐
│                    DNA MIDI Studio 9.30                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │ Song     │───▶│ Chord        │───▶│ Instrument       │   │
│  │ Analyzer │    │ Timeline     │    │ Profile Engine   │   │
│  └──────────┘    └──────┬───────┘    └────────┬─────────┘   │
│                         │                      │             │
│                    ┌────▼────┐          ┌──────▼──────┐      │
│                    │ FACTORY │          │   GOLD      │      │
│                    │ Velocity│          │   Timing    │      │
│                    │ Authority│          │   Groove    │      │
│                    └────┬────┘          └──────┬──────┘      │
│                         │                      │             │
│                    ┌────▼──────────────────────▼────┐        │
│                    │        MIDI Optimizer          │        │
│                    │   (chord-dependent pipeline)   │        │
│                    └────┬──────────────────────┬────┘        │
│                         │                      │             │
│                    ┌────▼────┐          ┌──────▼──────┐      │
│                    │ PA800   │          │   Export     │      │
│                    │ Builder │          │   & ZIP      │      │
│                    └────┬────┘          └──────┬──────┘      │
│                         │                      │             │
│                    ┌────▼────┐          ┌──────▼──────┐      │
│                    │ PA800   │          │   Integrity  │     │
│                    │Validator│          │   Check      │     │
│                    └─────────┘          └─────────────┘      │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  AE Function Registry: 234 funkcije | 9 kategorija          │
│  General Rules: 10 krutih pravila | 128 GM rangeova         │
│  Neural Models: 6 treniranih modela                          │
└──────────────────────────────────────────────────────────────┘
```

---

## 21. KRATAK PREGLED — ŠTA RADI ŠTA

| Komponenta | Šta radi |
|---|---|
| **Song Analyzer** | Čita MIDI, detektuje chord timeline, sekcije, temp, instrumente |
| **Chord Timeline** | Osnova — svaka funkcija koristi chord kao referentni okvir |
| **Instrument Profile Engine** | Gradi 22 profila sa velocity/timing/harmony/range/NTT |
| **Factory Velocity** | Apsolutni vladar velocity — 1713 profila, 4 role, full-range krive |
| **Gold Performance** | Timing, groove, density, register — 12918 patterna, 6 rola |
| **PA800 Builder** | Konvertuje u Pa800 stil format (NTT, track assign, varijacije) |
| **PA800 Validator** | Provjerava NTT, drum keys, channel 10, polyphony |
| **MIDI Optimizer** | Glavni pipeline — chord-aware optimizacija svake note |
| **DNA Builder** | Relationship grammar — terca i echo veze među notama |
| **Performance Gesture** | RX/DNC gesture engine sa device evidence |
| **Solo Ornament** | Grace/trill/slide/bend sa budget per phrase |
| **Corpus Forensics** | Validacija corpusa, detekcija anomalija |
| **General Rules** | 10 krutih pravila + GM range + drum map + balkan |

---

## 22. ZAKLJUČAK

DNA MIDI Studio 9.30 je **funkcionalan i kalibriran** — ali sa značajnim gapom  
u pokrivenosti instrumenata. Samo 5 od 22 profila ima stvarne Gold/Factory podatke.  
Ostali 17 koriste DEFAULT_ESTIMATED vrijednosti.

**Kritični sljedeći korak:** Role alias mapping — jednom kada se `accompaniment`  
mapira na piano/organ/pad/accordion/strings/choir, a `melody` na sax/clarinet/  
violin/solo_guitar — pokrivenost skače sa 23% na ~80%.

**Funkcionalni dio je čvrst:** Factory velocity autoritet radi, Gold timing radi,  
PA800 validacija radi, chord tracking radi za SVE funkcije, general rules  
se izvršavaju kao BLOCK/CLAMP — ne kao savjeti.
