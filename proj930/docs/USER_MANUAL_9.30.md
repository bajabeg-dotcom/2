# DNA MIDI Studio Pa800 — Korisnički Priručnik v9.30

## Sadržaj
1. [Uvod](#uvod)
2. [Brzi Start](#brzi-start)
3. [Katalog Instrumenata](#katalog-instrumenata)
4. [Factory Velocity Profili](#factory-velocity-profili)
5. [Factory Stilovi](#factory-stilovi)
6. [Trening Neuralnih Modela](#trening-neuralnih-modela)
7. [Kalibracija](#kalibracija)
8. [General Rules 9.30 — Hard Export Pravila](#general-rules-930--hard-export-pravila)
9. [Pa800 Kompatibilnost](#pa800-kompatibilnost)

---

## Uvod

DNA MIDI Studio je profesionalni alat za optimizaciju i izgradnju stilova
za Korg Pa800 (OS 2.0+). Koristi Factory kalibraciju (1964 profila),
Gold referentne uzorke (12918 patterna), i neuralne modele za
DNA rekonstrukciju i relacijsku analizu.

**Ključna invarianta:** Factory = jedini autoritet za velocity.
Gold nikad ne sadrži velocity podatke. Kalibracija je READ-ONLY
(nikad ne mutira MIDI).

---

## Brzi Start

```bash
# Pokreni GUI server
python server.py

# Pokreni trening (core model)
python scripts/train_local.py --mode core --epochs 8

# Pokreni trening (relationship model)
python scripts/train_local.py --mode relationship --epochs 12

# Pokreni trening (oba + kalibracija)
python scripts/train_local.py --mode all --promote

# Izgradi katalog instrumenata
python scripts/build_instrument_catalog.py

# Kalibracijski gate
python scripts/train_local.py --mode calibrate
```

---

## Katalog Instrumenata

Katalog sadrži **19 uloga** sa potpunim velocity profilima:

| Uloga | Model Muzičara | Factory Profila | VelMin | VelMax | VelP50 | Autoritet |
|-------|----------------|------------------|--------|--------|--------|-----------|
| drums | bubnjar | 1180 | 1 | 127 | 93 | FACTORY_ONLY |
| chords | akordeonist | 329 | 1 | 127 | 85 | FACTORY_ONLY |
| melody | solista | 154 | 1 | 127 | 93 | FACTORY_ONLY |
| bass | basista | 50 | 1 | 127 | 104 | FACTORY_ONLY |
| accompaniment | aranžer | - | - | - | - | FACTORY_ONLY |
| piano | pijanista | - | - | - | - | FACTORY_ONLY |
| accordion | harmonikaš | - | - | - | - | FACTORY_ONLY |
| brass | duhački | - | - | - | - | FACTORY_ONLY |
| strings | gudači | - | - | - | - | FACTORY_ONLY |
| organ | orguljaš | - | - | - | - | FACTORY_ONLY |
| rhythm-guitar | ritam gitarista | - | - | - | - | FACTORY_ONLY |
| pad | pad/strings | - | - | - | - | FACTORY_ONLY |
| choir | hor | - | - | - | - | FACTORY_ONLY |
| percussion | perkusionist | - | - | - | - | FACTORY_ONLY |
| sax | saksofonista | - | - | - | - | FACTORY_ONLY |
| solo | solista | - | - | - | - | FACTORY_ONLY |
| woodwind | drveni duvač | - | - | - | - | FACTORY_ONLY |
| power-riff | power-chord gitarista | - | - | - | - | FACTORY_ONLY |
| riff | rif majstor | - | - | - | - | FACTORY_ONLY |

> Tačne VelMin/VelMax vrijednosti za svaki profil su u
> `data/instrument-catalog-9.30.json`

### Pa800 Instrumenti (Factory)

| Instrument | Profila | Uloga | GM Program | VelMin | VelMax | P50 |
|-----------|---------|-------|------------|--------|--------|-----|
| DRUMS CV1 | 782 | drums | var | 1-127 | 29-127 | 93 |
| ACC1 CV1 | 85 | chords | 0 (Piano) | 1-98 | 68-127 | 85 |
| ACC2 CV1 | 79 | chords | 25 (Steel Guitar) | 1-127 | 78-127 | 84 |
| ACC3 CV1 | 98 | chords/melody | var | 1-119 | 60-127 | 80-93 |
| ACC4 CV1 | 79 | chords/melody/bass | var | 1-113 | 72-127 | 87-96 |
| ACC5 CV1 | 58 | chords/melody | var | 1-115 | 55-127 | 86-98 |
| BASS CV1 | 48 | bass | 33 (Finger Bass) | 1-113 | 92-127 | 104 |
| PERC CV1 | 45 | melody/chords | var | 1-105 | 98-127 | 80-83 |
| DRUMS CV2 | 28 | drums | var | 1-127 | 47-127 | 82 |
| BASS CV2 | 2 | bass | var | 1-40 | 120-127 | 108-110 |

### 7-Točkasti Velocity Krivulja

Svaki Factory profil ima 7-točkastu velocity krivulju:

```
ppp (pianississimo)  → VelMin   (najtiše moguće)
pp  (pianissimo)     → P05      (5. percentil)
p   (piano)           → P05↗P33  
mp  (mezzo-piano)     → P05↗P67
mf  (mezzo-forte)     → P50      (medijana)
f   (forte)           → P95      (95. percentil)
ff  (fortissimo)      → VelMax   (najglasnije moguće)
```

**Primjer: BASS CV1**
```
ppp=1  pp=77  p=85  mp=96  mf=104  f=120  ff=127
```

**Primjer: DRUMS CV1**
```
ppp=1  pp=68  p=75  mp=85  mf=93  f=111  ff=127
```

**Primjer: ACC1 CV1 (chords)**
```
ppp=1  pp=57  p=65  mp=74  mf=85  f=105  ff=127
```

---

## Factory Velocity Profili

### Struktura profila

Svaki Factory profil sadrži:

```json
{
  "profileId": "698.771.685",
  "instrument": "PERC CV1",
  "role": "melody",
  "soundBinding": [120, 0, 64],
  "mode": "HELD_OUT_EXACT",
  "sourceCount": 651,
  "trainSegments": 984,
  "holdoutSegments": 281,
  "velocityEnvelope": {
    "min": 2,
    "max": 127,
    "p05": 44,
    "p50": 80,
    "p95": 120,
    "sampleCount": 68914,
    "authority": "FACTORY_ONLY"
  },
  "registerEnvelope": {
    "pitchLow": {"p50": 30.0},
    "pitchHigh": {"p50": 57.0},
    "pitchMedian": {"p50": 42.0},
    "densityPerBar": {"p50": 6.81},
    "gateMedianQn": {"p50": 0.42}
  },
  "confidence": 1.0
}
```

### Velocity Envelope — Šta znači

| Polje | Značenje |
|-------|----------|
| `min` | Apsolutni minimum velocity u svim segmentima za ovaj profil |
| `max` | Apsolutni maksimum velocity |
| `p05` | 5. percentil — ispod ovog je samo 5% nota (tiša granica) |
| `p50` | Medijana — polovina nota je iznad, polovina ispod |
| `p95` | 95. percentil — iznad ovog je samo 5% nota (glasnija granica) |
| `sampleCount` | Ukupan broj nota analiziran za ovaj profil |
| `authority` | UVIJEK `FACTORY_ONLY` — jedini izvor velocity podataka |

### Važna pravila

1. **Nikad ne mutiraj velocity** u kalibracionom procesu
2. **Gold patterni** ne sadrže velocity podatke (zabranjeno po šemi)
3. **Factory** je jedini autoritet — sva velocity znanje dolazi odatle
4. **Role Fallback** koristi se kad specifični GM program nije pokriven
5. **Hardware Pending** — svi 1964 profili čekaju fizičku Pa800 validaciju

---

## Factory Stilovi

### Elementi Stilova

| Element | Broj Segmenata | Opis |
|---------|----------------|------|
| variation 4 | 3447 | Najkompleksnija varijacija |
| variation 3 | 3204 | Treća varijacija |
| variation 2 | 2778 | Druga varijacija |
| intro 1 | 3025 | Prvi intro |
| fill 2 | 2122 | Fill druga varijacija |
| BASS | 4200 | Bas segmenti |
| DRUMS | 4165 | Bubanj segmenti |
| ACC1 | 3701 | Akordeon 1 |
| ACC2 | 3707 | Akordeon 2 |
| ACC3 | 3380 | Akordeon 3 |
| ending 1 | 2397 | Prvi ending |
| fill 1 | 1839 | Fill prva varijacija |
| break | 1391 | Break segment |
| ending 2 | 1746 | Drugi ending |
| intro 2 | 1630 | Drugi intro |
| PERC | 3429 | Perkusioni |
| ACC4 | 2427 | Akordeon 4 |
| ACC5 | 1913 | Akordeon 5 |

### Chord Variations (CV)

| CV | Segmenata | Opis |
|----|-----------|------|
| CV1 | 16400 | Glavna varijacija |
| CV2 | 8182 | Druga varijacija |
| CV3 | 1794 | Treća varijacija |
| CV4 | 404 | Četvrta varijacija |
| CV5 | 107 | Peta varijacija |
| CV6 | 35 | Šesta varijacija (maksimalna) |

### Stil Familije (kalibrirane)

| Familija | Segmenata | Stilova | Konfidencija |
|----------|-----------|---------|-------------|
| 6/8 | 628 | 5 | 0.70 |
| rock | 447 | 4 | 0.50 |
| techno_dance | 2051 | 20 | 1.00 |
| ballad | 2743 | 26 | 1.00 |
| beat | 1938 | 24 | 1.00 |

### Metar Distribucija

| Metar | Fajlova u valja.zip | Pa800 Režim |
|-------|---------------------|-------------|
| 4/4 | 152 | Standard |
| 7/8 | 9 | Balkan (aktivira terca) |
| 9/8 | 1 | Balkan (aktivira terca) |
| 6/8 | 1 | Waltz/Lendler |
| 3/4 | - | Valcer |
| 2/4 | - | Polka |

---

## Trening Neuralnih Modela

### Lokalni Trening (na vašem računaru)

```bash
# Core DNA Reconstructor
python scripts/train_local.py --mode core --epochs 8

# Relationship Sequence Transformer
python scripts/train_local.py --mode relationship --epochs 12

# Oba modela + kalibracioni gate
python scripts/train_local.py --mode all --promote

# Samo kalibracioni gate (bez treniranja)
python scripts/train_local.py --mode calibrate
```

### Parametri Treniranja

| Parametar | Default | Opis |
|-----------|---------|------|
| `--epochs` | 12 | Broj epoha za core model |
| `--batch` | 64 | Batch size za core |
| `--lr` | 3e-4 | Learning rate za core |
| `--patience` | 3 | Early stopping patience |
| `--relationship-epochs` | 18 | Epoha za relationship model |
| `--relationship-batch` | 8 | Batch za relationship |
| `--relationship-lr` | 4e-4 | LR za relationship |
| `--relationship-patience` | 5 | Early stopping za relationship |
| `--device` | auto | cpu/cuda/auto |
| `--promote` | false | Promoviraj model u produkciju nakon treninga |

### Šta se dešava tokom treniranja

1. **Core model** uči od 15,837 redova Factory/Gold podataka
2. **Relationship model** uči od 697 relacijskih sekvenci
3. Oba modela poštuju **velocity authority** (Factory = jedini)
4. Nakon svake epohe — validacija na holdout skupu
5. Early stopping ako se loss ne poboljšava `patience` epoha
6. Na kraju — kalibracioni gate provjera

### Rezultati Treniranja

Nakon treninga, rezultati se snimaju u:
- `models/dna-reconstructor-v2/training_report.json`
- `models/relationship-sequence-v2/relationship_sequence_training_report.json`
- `artifacts/neural_training_run_9.02.json`

### Važno: Velocity Invarianta

Tokom treniranja, sistem automatski provjerava:
- ✅ Gold velocity NIJE korištena u ulaznim podacima
- ✅ Model nema velocity output head
- ✅ Relationship dataset nema velocity feature
- ❌ Ako bilo koja provjera padne — trening se PREKIDA

---

## Kalibracija

### Kalibracioni Gate

Gate provjerava da su svi potrebni fajlovi prisutni:

```bash
python scripts/train_local.py --mode calibrate
```

Provjerava:
1. `learning_data/dataset_manifest.json` — postoji
2. `relationship_sequence_data_v2/relationship_sequence_manifest_v2.json` — postoji
3. `models/dna-reconstructor-v2/training_report.json` — postoji
4. `models/relationship-sequence-v2/relationship_sequence_training_report.json` — postoji
5. Relationship manifest `velocityFeature=False` i `velocityTarget=False`
6. Ukupan status: `SOFTWARE_CALIBRATED_WAITING_FOR_LISTENING_DEVICE_GATE`

### Tempo Bucket Kalibracija

| Bucket | BPM Raspon | Opis |
|--------|-----------|------|
| slow | 0-79 | Lagane pjesme, balade |
| medium | 80-119 | Srednji tempo, pop-folk |
| brisk | 120-159 | Brži tempo, rock |
| fast | 160-300 | Brze pjesme, dance |

---

## Pa800 Kompatibilnost

### General Rules 9.30 — Hard Export Pravila

Svaki MIDI export iz DNA MIDI Studio automatski provjerava i korigira
hard limite po realnom instrumentu i Pa800 hardveru. Ova pravila su
**ENFORCED** — ne prijedlozi, ne upozorenja, već HARD CLAMP/BLOCK.

#### Ključna Pravila

| Pravilo | Akcija | Opis |
|---------|--------|------|
| Key Range per GM Program | **CLAMP** | Npr. bas gitara E1–G3, truba E3–A#5, klavir A0–C8 |
| Drum Kanal (9) Valid Keys | **BLOCK** | Samo 61 validan ključ (27–87) na Pa800 GM drum mapi |
| Velocity Min/Max | **CLAMP** | Npr. mesni limeni instrumenti min 20, gudači min 1 |
| Polyphony Limit | **WARN** | Pa800 max 54 istovremenih glasova |
| Note Pair Matching | **AUTO** | Klampirani note-on automatski klampira odgovarajući note-off |

#### Primjeri Hard Limita

```
Bass Guitar (GM 34): E1 (28) — G3 (55)  ← ispod E1 = CLAMP na E1
Trumpet (GM 56):     E3 (52) — A#5 (82)  ← iznad A#5 = CLAMP na A#5
Acoustic Piano (GM 0): A0 (21) — C8 (108) ← puni raspon
Drum Kanal 9:        Keys 27–87 samo       ← van = UKLONJENO
```

#### Validacija na 163 Valja MIDI fajla

- **32 fajla** čista (0 kršenja)
- **131 fajla** korigirana (key clamped, drum blocked, velocity clamped)
- **Najčešće kršenje:** note ispod instrument range-a (bass, brass)
- **445 drum ključeva** blokirano u jednom fajlu (Pitaju me pitaju)

#### Skripta za Validaciju

```bash
# Validiraj jedan MIDI fajl
python scripts/general_rules_validator.py song.mid

# Validiraj direktorij i sačuvaj korigirane
python scripts/general_rules_validator.py ./midi --output ./corrected --report report.json
```

#### Integracija u Optimizer

General Rules Gate je automatski ugrađen u `optimize_midi()`:
```python
result_data, report = midi_optimizer.optimize_midi(data, profiles, options={...})
# report['generalRules'] sadrži sve kršenja i korigiranja
# report['invariants']['generalRulesEnforced'] = True
```

### MIDI Format
- **Format 1** (više trakova) — Pa800 svira bez problema
- **Format 0** (jedna traka) — potrebno za Style Creator import
- PPQN: 120, 192, 480 — sve Pa800-kompatibilne

### Kanal Mapiranje

| Kanal | Pa800 Uloga | Factory Profil |
|-------|-------------|----------------|
| 0-8 | Melodijski (piano, gitar, bas itd.) | melody/chords role |
| 9 | Bubanj kanal 1 | drums CV1 |
| 10 | Bubanj kanal 2 | drums CV2 |
| 11-15 | Efekti, synth, perkusioni | var |

### Hardware Status

⚠️ Svi 1964 Factory profila su **HARDWARE_PENDING** — fizička Pa800
validacija je potrebna za konačnu potvrdu. Softver kalibracija je kompletna.

---

*DNA MIDI Studio Pa800 v9.30 — General Rules + Full Factory/Gold Calibration + Neural Models*
