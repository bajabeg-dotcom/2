# DNA MIDI Studio 9.30 — Deterministic Humanization Report

**Schema:** dna-deterministic-humanization
**Version:** 9.30.0
**Ukupno instrumenata:** 26

## Autoriteti

- **velocity**: FACTORY_SCALED
- **timing**: GOLD_PROFILE
- **gate**: HUMANIZATION_PROFILE
- **chord**: MANDATORY
- **determinism**: SHA256_POSITION_SEED

## Hard Limits (BLOCK/CLAMP)

- **velocityScale**: 🔒 CLAMP(0.5, 1.2)
- **timingOffsetPPQ**: 🔒 CLAMP(-8, 8)
- **gateScale**: 🔒 CLAMP(0.3, 2.0)
- **velocityOverride**: 🚫 BLOCK — FACTORY_is_sole_authority
- **randomGeneration**: 🚫 BLOCK — deterministic_only
- **chordTracking**: 🚫 BLOCK — mandatory_for_all_instruments
- **maxOrnamentPPQ**: 🔒 CLAMP(-6, 6)

## Humanizacioni Tipovi

| Tip | Opis | Timing profil | Velocity profil |
|-----|------|---------------|-----------------|
| PHRASE_DRIVEN | Frazna humanizacija — prirodni kraj i početak fraze | phrase_end_late | phrase_arc |
| BREATH_PHRASE | Dah-fraza — timing kod promjene daha | breath_point_late | breath_cresc_dim |
| BOW_PHRASE | Gudalo-fraza — timing kod promjene gudala | bow_change_micro | bow_pressure_arc |
| BOW_FREE | Slobodno gudalo — rubato sa širokim vibratom | rubato_free | rubato_swell |
| BELLOW_PHRASE | Meh-fraza — dinamika mijeha harmonike | bellow_change | bellow_cresc_dim |
| PLECTRUM_PHRASE | Trzalka-fraza — timing kod promjene trzalka | pick_alternating | pick_accent |
| STANDARD | Standardna humanizacija — blagi micro-timing | standard_micro | standard_arc |
| DRUM_GROOVE | Bubanj-groove — element-specific timing | element_groove | element_accent |

## Instrument → Humanizacija Mapa

| Instrument | Tip | Groove profil | Folk |
|-----------|-----|--------------|------|
| accompaniment | STANDARD | standard_micro |  |
| accordion | BELLOW_PHRASE | bellow_change |  |
| bass | STANDARD | standard_micro |  |
| brass | STANDARD | standard_micro |  |
| choir | STANDARD | standard_micro |  |
| clarinet | BREATH_PHRASE | breath_point_late |  |
| drums | DRUM_GROOVE | element_groove |  |
| frula | BREATH_PHRASE | BREATH_PHRASE | ✅ |
| fx | STANDARD | standard_micro |  |
| gusle | BOW_FREE | BOW_FREE_RUBATO | ✅ |
| harmonika | BELLOW_PHRASE | BELLOW_SUSTAIN | ✅ |
| klarinet | BREATH_PHRASE | BREATH_PHRASE | ✅ |
| mallet | STANDARD | standard_micro |  |
| organ | STANDARD | standard_micro |  |
| pad | STANDARD | standard_micro |  |
| percussion | DRUM_GROOVE | element_groove |  |
| piano | STANDARD | standard_micro |  |
| rhythm_guitar | STANDARD | standard_micro |  |
| sax | PHRASE_DRIVEN | phrase_end_late |  |
| solo_guitar | STANDARD | standard_micro |  |
| strings | STANDARD | standard_micro |  |
| synth_lead | STANDARD | standard_micro |  |
| tambura | PLECTRUM_PHRASE | PLECTRUM_PHRASE | ✅ |
| violin | BOW_PHRASE | bow_change_micro |  |
| violina | BOW_PHRASE | BOW_PHRASE | ✅ |
| woodwind | STANDARD | standard_micro |  |

## Determinizam

- **Seed:** SHA-256(instrument + position + chord_root + bar + section)
- **Isti ulaz = isti izlaz** — nema random() nigdje
- **Micro-variation:** ±1 PPQ iz seeda (deterministički)
- **Velocity varijacija:** ±5% iz seeda (deterministički)
- **Chord tracking:** obavezni za sve instrumente

## Test: Determinizam Verifikacija

```
# Isti ulaz poziva 3 puta = isti izlaz
  sax: vel=89, offset=1, gate=0.95 — determinističan=✅
  violin: vel=91, offset=-1, gate=0.95 — determinističan=✅
  harmonika: vel=101, offset=0, gate=0.85 — determinističan=✅
  drums: vel=94, offset=0, gate=0.85 — determinističan=✅
```
