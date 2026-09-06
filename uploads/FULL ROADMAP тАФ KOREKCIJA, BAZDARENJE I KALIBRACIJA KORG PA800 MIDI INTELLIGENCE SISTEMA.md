# FULL ROADMAP
## KOREKCIJA → BAZDARENJE → KALIBRACIJA → VALIDACIJA → FINALNA CERTIFIKACIJA

### PROJEKAT
**DNA MIDI Studio / X10 KORG PA800 MIDI Intelligence Engine**

### GLAVNI CILJ

Dovesti kompletan sistem u stanje **REPRODUCIBLE / DETERMINISTIC / MUSICAL / KORG-ACCURATE / CERTIFIABLE**, tako da sistem ne samo tehnički obrađuje MIDI, nego proizvodi rezultate koji se ponašaju muzički ispravno na **Korg Pa800**, uz strogo odvajanje:

- FACTORY → referentna osnova prvenstveno za **VELOCITY / DYNAMICS / RANGE / INSTRUMENTAL BEHAVIOUR**
- GOLD → referentna osnova za **MUSICAL PLAYING LOGIC**, uključujući timing, trills, articulation, expression, groove, phrase behaviour, humanization i druge muzičke obrasce
- ENGINE → odlučuje šta, gdje, kada i kako se primjenjuje
- KORG PA800 CONSTRAINT LAYER → garantuje da je rezultat kompatibilan sa stvarnim Pa800 ponašanjem
- VALIDATION → mora dokazati da je rezultat bolji, a ne samo drugačiji

============================================================
# 0. GLAVNO PRAVILO PROJEKTA
============================================================

NE OPTIMIZIRATI NASLIJEPO.

NE MIJENJATI PARAMETAR SAMO ZATO ŠTO JE PROMJENA TEHNIČKI MOGUĆA.

SVAKA TRANSFORMACIJA MORA IMATI:

1. SOURCE EVIDENCE
2. MUSICAL PURPOSE
3. TARGET PROFILE
4. CONSTRAINTS
5. TRANSFORMATION RULE
6. BEFORE METRIC
7. AFTER METRIC
8. PASS/FAIL CRITERIA
9. REGRESSION CHECK
10. EXPLANATION ZAŠTO JE PROMJENA IZVRŠENA

Ako transformacija ne može biti opravdana, NE PRIMJENJIVATI JE.

============================================================
# 1. BASELINE FREEZE
============================================================

Prije bilo kakve nove kalibracije napraviti potpuni BASELINE FREEZE.

Zamrznuti:

- source corpus
- Factory corpus
- Gold corpus
- database schema
- profile registry
- instrument registry
- MIDI mappings
- Korg mappings
- velocity rules
- timing rules
- articulation rules
- expression rules
- groove rules
- humanization rules
- arrangement rules
- exporter behaviour
- importer behaviour
- random seeds
- deterministic ordering
- hashes
- test results

Napraviti:

### BASELINE MANIFEST

Za svaki ključni artefakt evidentirati:

- filename
- path
- version
- SHA256
- number of files
- number of notes
- number of tracks
- number of channels
- number of CC events
- tempo events
- program changes
- bank select
- markers
- SysEx/Korg events
- duration
- PPQ
- test status

Baseline mora biti reproducibilan.

Ako isti input + isti config + isti seed daje drugačiji rezultat:

**FAIL**

============================================================
# 2. CORPUS INTEGRITY AUDIT
============================================================

Provjeriti kompletan corpus.

## FACTORY

Provjeriti:

- sve Factory MIDI datoteke
- validnost
- duplikate
- hashove
- missing files
- corrupted MIDI
- broj note-on događaja
- CC7
- CC11
- velocity distribuciju
- pitch distribution
- duration distribution
- channel distribution
- instrument distribution
- tempo distribution

Posebno izdvojiti:

- Drum
- Bass
- Accompaniment
- Guitar
- Piano
- Strings
- Brass
- Woodwind
- Synth
- Solo instruments
- FX

## GOLD

Isto provjeriti za GOLD.

Ali GOLD NE koristiti kao univerzalni velocity authority.

GOLD je prvenstveno:

**PLAYING LOGIC REFERENCE**

============================================================
# 3. SOURCE AUTHORITY MATRIX
============================================================

Napraviti centralnu tabelu:

| PARAMETAR | FACTORY | GOLD | ENGINE |
|---|---|---|---|
| Velocity baseline | PRIMARY | SECONDARY | APPLY |
| Velocity curve | PRIMARY | VALIDATION | APPLY |
| Velocity range | PRIMARY | VALIDATION | APPLY |
| Dynamics | PRIMARY | SECONDARY | APPLY |
| Timing | SECONDARY | PRIMARY | APPLY |
| Microtiming | SECONDARY | PRIMARY | APPLY |
| Groove | SECONDARY | PRIMARY | APPLY |
| Trills | NO | PRIMARY | APPLY |
| Rolls | NO | PRIMARY | APPLY |
| Ornamentation | NO | PRIMARY | APPLY |
| Expression | SECONDARY | PRIMARY | APPLY |
| Articulation | REFERENCE | PRIMARY | APPLY |
| Phrase logic | REFERENCE | PRIMARY | APPLY |
| Humanization | NO | PRIMARY | APPLY |
| Arrangement behaviour | REFERENCE | PRIMARY | APPLY |
| Korg constraints | PRIMARY | PRIMARY | APPLY |

NIKADA ne dozvoliti da slučajna funkcija promijeni source authority.

============================================================
# 4. INSTRUMENT PROFILE RECONSTRUCTION
============================================================

Za SVAKI instrument napraviti kompletan PROFILE.

Minimalna struktura:

### IDENTITY
- instrument_name
- family
- subtype
- GM program
- Korg program
- CC0
- CC32
- Program Change
- bank
- sound_type
- RX/DNC status

### RANGE

- absolute_low
- absolute_high
- practical_low
- practical_high
- preferred_register
- danger_register
- transition_zones

### VELOCITY

- min
- max
- median
- mean
- p10
- p25
- p50
- p75
- p90
- p95
- p99
- soft_zone
- normal_zone
- accent_zone
- max_accent
- family_curve
- phrase_curve
- drum_element_curve

### TIMING

- attack_offset
- release_offset
- anticipation
- delay
- humanization_sigma
- microtiming envelope

### EXPRESSION

- CC11 range
- CC11 baseline
- phrase envelope
- swell behaviour
- fade behaviour

### ARTICULATION

- staccato
- legato
- accent
- slide
- trill
- grace
- roll
- repeated-note logic

### GROOVE

- swing
- straightness
- syncopation
- displacement
- phrase timing

### HUMANIZATION

- velocity randomness
- timing randomness
- duration randomness
- repetition avoidance
- pattern variation

### ARRANGEMENT ROLE

- bass
- chord
- accompaniment
- melody
- solo
- pad
- percussion
- fill
- intro
- ending

============================================================
# 5. FACTORY VELOCITY CALIBRATION
============================================================

FACTORY koristiti prvenstveno za određivanje:

- prirodnog velocity raspona
- osnovne krive
- family behaviour
- instrument class behaviour
- drum-element behaviour
- accent behaviour
- dynamic ceiling
- dynamic floor
- inter-note velocity relation

NE koristiti sirovu velocity vrijednost iz originalnog korisničkog MIDI-a kao authority.

Za svaki instrument generisati:

### VELOCITY CURVE

Input:

- instrument family
- role
- phrase position
- note position
- pitch register
- articulation
- intensity
- accent state
- rhythmic density

Output:

**target velocity**

Range mora biti Korg-realistic.

============================================================
# 6. DRUM VELOCITY CALIBRATION
============================================================

Drumovi se NE tretiraju kao jedan instrument.

Napraviti profile za:

- Kick
- Snare
- Rim
- Clap
- Closed HH
- Open HH
- Pedal HH
- Ride
- Crash
- Tom Low
- Tom Mid
- Tom High
- Percussion
- Shaker
- Tambourine
- Conga
- Bongo
- Latin percussion
- FX percussion

Za svaki element:

- minimum
- normal
- accent
- ghost
- fill
- transition
- phrase-end
- syncopated-hit range

Posebno zaštititi:

### KICK
Ne smije biti uniforman.

### SNARE
Razlikovati:

- main hit
- ghost
- accent
- fill

### HI-HAT
Velocity mora imati muzički pattern, ne random noise.

============================================================
# 7. GOLD PLAYING-LOGIC CALIBRATION
============================================================

GOLD koristiti za rekonstrukciju:

- timing
- phrase behaviour
- trills
- grace notes
- rolls
- repeated-note behaviour
- articulation
- humanization
- expression
- CC11 envelopes
- groove
- anticipation
- delayed notes
- note-length behaviour
- phrase endings
- fills
- transitions

Iz Gold corpusa izvući:

### PATTERN DNA

Za svaki pattern čuvati:

- notes
- intervals
- rhythm
- onset spacing
- duration
- velocity relation
- articulation
- phrase position
- harmonic role
- register
- repetition structure

============================================================
# 8. TRILL ENGINE
============================================================

Trill engine NE smije biti obični note duplicator.

Mora razumjeti:

- start note
- upper note
- interval
- speed
- subdivision
- phrase position
- instrument family
- register
- intensity
- duration
- ending behaviour

Trill profil mora imati:

- min duration
- max duration
- rate
- velocity envelope
- acceleration/deceleration
- final resolution
- ornament probability

Gold određuje playing behaviour.

Factory određuje velocity constraints.

============================================================
# 9. TIMING ENGINE
============================================================

Timing engine mora raditi sa:

### MACRO TIMING

- beat
- bar
- phrase
- section

### MICRO TIMING

- per-note offset
- anticipation
- delay
- swing
- push
- drag

Timing ne smije biti random.

Koristiti:

- deterministic seed
- instrument profile
- phrase state
- groove state
- intensity

Svaka promjena timing-a mora ostati unutar sigurnog musical window-a.

============================================================
# 10. EXPRESSION ENGINE
============================================================

CC11 ne smije biti generisan kao slučajna krivulja.

Napraviti profile za:

- sustained instruments
- strings
- brass
- solo
- pads
- guitars
- winds

Expression mora zavisiti od:

- phrase
- note density
- articulation
- register
- intensity
- section

Provjeriti:

- max CC11
- min CC11
- continuity
- jumps
- clipping
- redundant events
- event density

============================================================
# 11. CC7 / MIX ENGINE
============================================================

CC7 mora ostati pod kontrolom master mixer policy-ja.

Posebno validirati:

- CC7
- CC10
- CC11
- CC91
- CC93

Za projekat mora postojati eksplicitna politika:

**CC7 DEFAULT = 110**

Osim kada profil eksplicitno zahtijeva drugačije.

Ne dozvoliti slučajnu promjenu miks odnosa kroz hidden transforms.

============================================================
# 12. KORG PA800 CONSTRAINT ENGINE
============================================================

Sve rezultate provjeriti kroz Korg constraint layer.

Provjeriti:

- CC0
- CC32
- Program Change
- channels
- drum channel
- GM compatibility
- Korg sound mapping
- RX/DNC mapping
- velocity limits
- note range
- controller legality
- SysEx
- markers
- SMF0 structure
- track ordering

Exporter mora imati strict mode.

Ako je bilo koja Korg-specific komponenta invalidna:

**EXPORT FAIL**

============================================================
# 13. MIDI STRUCTURAL VALIDATION
============================================================

Svaki input i output proći kroz:

### STRUCTURE CHECK

- valid MIDI header
- format
- PPQ
- tracks
- delta times
- events
- running status
- note pairing
- tempo
- meta events
- controllers
- program changes
- sysex

### NOTE CHECK

- orphan note-off
- orphan note-on
- overlapping notes
- zero-duration notes
- impossible duration
- out-of-range notes

### CONTROLLER CHECK

- invalid CC
- duplicate controller spam
- abnormal CC density
- illegal values

============================================================
# 14. MUSICAL VALIDATION
============================================================

Ne koristiti samo tehničke testove.

Napraviti musical scoring:

### HARMONY
0–100

### GROOVE
0–100

### DYNAMICS
0–100

### ARTICULATION
0–100

### EXPRESSION
0–100

### HUMANIZATION
0–100

### ARRANGEMENT
0–100

### KORG COMPATIBILITY
0–100

### OVERALL MUSICAL QUALITY
0–100

Rezultat mora imati:

**BEFORE → AFTER → DELTA**

Ako se technical metrics poprave, a musical metrics padnu:

**FAIL**

============================================================
# 15. REGRESSION CORPUS
============================================================

Napraviti stalni regression corpus.

Obavezno uključiti:

- simple MIDI
- dense MIDI
- Balkan folk
- turbo folk
- sevdah
- kafana
- ballad
- dance
- rock
- acoustic
- sparse arrangement
- full arrangement
- difficult drum MIDI
- dense bass MIDI
- guitar patterns
- solo phrases
- ornament-heavy MIDI

Svaki release mora proći isti corpus.

============================================================
# 16. A/B LISTENING VALIDATION
============================================================

Za svaki build generisati:

### ORIGINAL
### OPTIMIZED
### GOLD-ASSISTED
### FACTORY-CALIBRATED
### FINAL

Ocjenjivati:

- groove
- naturalness
- dynamics
- articulation
- phrase quality
- instrument realism
- drum realism
- bass realism
- musicality
- Korg playback behaviour

Ne koristiti samo automatski score.

Human listening mora biti zaseban validation layer.

============================================================
# 17. PARAMETER SWEEP
============================================================

Za svaki važan parametar pronaći:

- SAFE MIN
- OPTIMAL
- SAFE MAX
- FAILURE ZONE

Posebno:

- velocity intensity
- timing shift
- humanization
- expression depth
- trill rate
- articulation probability
- groove amount
- accent strength
- variation amount

Rezultat mora biti calibration table.

============================================================
# 18. SENSITIVITY ANALYSIS
============================================================

Provjeriti koji parametri imaju najveći uticaj.

Mjeriti:

- one-variable-at-a-time
- pair interactions
- family interactions
- role interactions
- phrase interactions

Identifikovati:

### HIGH IMPACT
### MEDIUM IMPACT
### LOW IMPACT
### DANGEROUS

Parametri sa visokim rizikom moraju imati hard constraints.

============================================================
# 19. CONFLICT RESOLUTION ENGINE
============================================================

Kada se Factory i Gold ne slažu:

NE birati slučajno.

Koristiti authority matrix.

Primjer:

Factory kaže:

velocity = 72–98

Gold kaže:

phrase behaviour = soft → loud → soft

Final:

Gold određuje dynamics shape.

Factory određuje legal velocity envelope.

Dakle:

**GOLD SHAPE + FACTORY RANGE + ENGINE CONSTRAINT**

============================================================
# 20. CONFIDENCE ENGINE
============================================================

Svaka transformacija mora imati confidence.

Primjer:

### HIGH
Corpus evidence > strong

### MEDIUM
Limited evidence

### LOW
Heuristic

### UNKNOWN
No evidence

Policy:

HIGH → APPLY

MEDIUM → APPLY WITH LIMITS

LOW → OPTIONAL / SHADOW

UNKNOWN → DO NOT APPLY AUTOMATICALLY

============================================================
# 21. SHADOW MODE
============================================================

Novi intelligence modeli prvo rade u SHADOW MODE.

Engine:

- analizira
- predlaže transformaciju
- NE mijenja output

Sistem računa:

- predicted improvement
- confidence
- conflicts
- possible regressions

Tek nakon PASS:

**TRANSFORM AUTHORIZED**

============================================================
# 22. CALIBRATION LOOP
============================================================

Glavna petlja:

INPUT

↓

ANALYZE

↓

CLASSIFY

↓

PROFILE

↓

FACTORY CONSTRAINTS

↓

GOLD PLAYING LOGIC

↓

TRANSFORM

↓

KORG CONSTRAINT

↓

VALIDATE

↓

MUSICAL SCORE

↓

REGRESSION

↓

COMPARE

↓

CALIBRATE

↓

FREEZE

↓

NEXT LAYER

NIKADA ne preskakati validation korak.

============================================================
# 23. VERSIONED CALIBRATION
============================================================

Svaki calibration build dobija version:

Example:

8.70
8.71
8.72
8.80
8.81
8.82

Svaka verzija mora sadržavati:

- config hash
- corpus hash
- engine hash
- profile hash
- seed
- metrics
- PASS/FAIL
- changed parameters
- regression result

============================================================
# 24. FULL CORPUS LISTENING CALIBRATION
============================================================

Najvažniji završni korak.

Pokrenuti cijeli validated corpus.

Za svaki file sačuvati:

- source
- optimized
- transformations
- instrument profiles
- confidence
- before metrics
- after metrics
- delta
- warnings
- failures

Zatim agregirati:

- family-level score
- instrument-level score
- genre-level score
- complexity-level score
- overall score

============================================================
# 25. FAILURE ANALYSIS
============================================================

Svaki FAIL automatski klasificirati:

### TYPE A
Structural

### TYPE B
Korg compatibility

### TYPE C
Velocity

### TYPE D
Timing

### TYPE E
Expression

### TYPE F
Articulation

### TYPE G
Groove

### TYPE H
Arrangement

### TYPE I
Regression

### TYPE J
Musical degradation

Za svaki FAIL:

- reproduce
- isolate
- identify cause
- patch
- rerun
- regression test

============================================================
# 26. HARD GATES
============================================================

Build ne smije biti RELEASE READY ako postoji:

- corrupted MIDI
- invalid mapping
- broken note pairing
- broken Korg metadata
- unexpected channel changes
- uncontrolled velocity
- clipping
- invalid CC
- regression
- non-deterministic output
- unexplained transformation
- musical degradation iznad thresholda

============================================================
# 27. CERTIFICATION MATRIX
============================================================

Final certification mora imati:

### CODE
PASS

### DATABASE
PASS

### FACTORY
PASS

### GOLD
PASS

### PROFILES
PASS

### VELOCITY
PASS

### TIMING
PASS

### TRILLS
PASS

### ARTICULATION
PASS

### EXPRESSION
PASS

### GROOVE
PASS

### HUMANIZATION
PASS

### KORG MAPPING
PASS

### EXPORT
PASS

### REGRESSION
PASS

### FULL CORPUS
PASS

### LISTENING
PASS

============================================================
# 28. FINAL GOLDEN FREEZE
============================================================

Kada svi gates prođu:

FREEZE:

- Factory DB
- Gold DB
- profile DB
- mappings
- calibration constants
- scoring thresholds
- exporter rules
- transformer rules
- seeds
- regression corpus

Generisati:

### GOLDEN BUILD MANIFEST

Sa:

- versions
- hashes
- corpus statistics
- test counts
- PASS rates
- calibration tables
- known limitations

============================================================
# 29. FINAL RELEASE RULE
============================================================

FINAL RELEASE mora zadovoljiti:

### TECHNICAL
100% critical tests PASS

### KORG
100% critical compatibility PASS

### DETERMINISM
100% reproducible

### REGRESSION
0 unexplained regressions

### MUSICAL
No statistically significant degradation

### FACTORY VELOCITY
Validated

### GOLD PLAYING LOGIC
Validated

### FULL CORPUS
Validated

### HUMAN LISTENING
Validated

============================================================
# 30. AGENT EXECUTION ORDER
============================================================

Agent mora raditi ISKLJUČIVO ovim redoslijedom:

PHASE 0
BASELINE FREEZE

↓

PHASE 1
CORPUS INTEGRITY

↓

PHASE 2
FACTORY AUDIT

↓

PHASE 3
GOLD AUDIT

↓

PHASE 4
SOURCE AUTHORITY MATRIX

↓

PHASE 5
INSTRUMENT PROFILE RECONSTRUCTION

↓

PHASE 6
FACTORY VELOCITY CALIBRATION

↓

PHASE 7
DRUM VELOCITY CALIBRATION

↓

PHASE 8
GOLD PLAYING-LOGIC CALIBRATION

↓

PHASE 9
TRILL / ARTICULATION

↓

PHASE 10
TIMING / GROOVE

↓

PHASE 11
EXPRESSION / CC

↓

PHASE 12
HUMANIZATION

↓

PHASE 13
KORG CONSTRAINT ENGINE

↓

PHASE 14
MUSICAL VALIDATION

↓

PHASE 15
REGRESSION

↓

PHASE 16
PARAMETER SWEEP

↓

PHASE 17
SENSITIVITY ANALYSIS

↓

PHASE 18
SHADOW MODE

↓

PHASE 19
TRANSFORM AUTHORIZATION

↓

PHASE 20
FULL CORPUS CALIBRATION

↓

PHASE 21
LISTENING VALIDATION

↓

PHASE 22
FAILURE ANALYSIS

↓

PHASE 23
FINAL REGRESSION

↓

PHASE 24
GOLDEN FREEZE

↓

PHASE 25
FINAL CERTIFICATION

============================================================
# 31. AGENT REPORTING FORMAT
============================================================

Nakon svake faze agent MORA prijaviti:

## STATUS
PASS / FAIL / BLOCKED

## EVIDENCE
Šta je analizirano.

## CHANGES
Šta je promijenjeno.

## METRICS
Before / After.

## REGRESSION
PASS / FAIL.

## CONFIDENCE
HIGH / MEDIUM / LOW.

## REMAINING ISSUES
Šta još nije riješeno.

## NEXT GATE
Koji je sljedeći korak.

Agent NE SMIJE napisati:

"izgleda dobro"

"vjerovatno radi"

"kalibracija je dobra"

bez konkretnih dokaza.

============================================================
# 32. ABSOLUTE PROJECT POLICY
============================================================

FACTORY ≠ GOLD.

FACTORY = VELOCITY / DYNAMICS / RANGE REFERENCE.

GOLD = PLAYING LOGIC REFERENCE.

ENGINE = INTELLIGENCE / TRANSFORMATION.

KORG = FINAL CONSTRAINT.

VALIDATION = AUTHORITY.

LISTENING = FINAL MUSICAL TRUTH.

============================================================
# 33. ZAVRŠNI CILJ
============================================================

Konačni sistem mora moći uzeti:

**bilo koji validni MIDI**

i automatski:

1. prepoznati instrumente
2. prepoznati njihove role
3. izgraditi instrument context
4. primijeniti Factory velocity intelligence
5. primijeniti Gold playing intelligence
6. poštovati Korg PA800 constraints
7. prilagoditi timing
8. prilagoditi groove
9. prilagoditi expression
10. dodati/korigovati articulation
11. obraditi trills/ornaments gdje je opravdano
12. kontrolisati drums po elementima
13. očuvati harmoniju
14. očuvati strukturu
15. izbjeći destruktivne transformacije
16. generisati deterministic output
17. validirati output
18. izračunati Before/After score
19. odbiti rezultat ako degradira kvalitet
20. proizvesti finalni Korg Pa800-compatible MIDI

FINALNA FORMULA SISTEMA:

**FACTORY DNA**
→ Velocity / Dynamics / Range

+

**GOLD DNA**
→ Playing / Timing / Groove / Articulation / Expression / Humanization

+

**KORG PA800 CONSTRAINTS**
→ Compatibility / Mapping / Limits

+

**INTELLIGENCE ENGINE**
→ Context-aware Transformation

+

**VALIDATION ENGINE**
→ Technical + Musical Verification

=

# FINAL KORG PA800 MIDI INTELLIGENCE ENGINE

Sistem se smatra završenim TEK kada svi critical gates imaju dokazani PASS i kada full-corpus rezultati potvrde da transformacije daju konzistentno ili mjerljivo bolje rezultate bez regresije.