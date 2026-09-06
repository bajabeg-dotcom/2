# ROADMAP 14.00 - SVE ŠTO JE MOGUĆE I ŠTO NAM PREOSTAJE - ISKREN

**Datum:** 2026-09-06  
**Verzija:** 14.00-ROADMAP-ISKREN  
**Seed:** 9302026  
**Cilj:** Bez lažnih izvještaja, pokriti sve što je moguće sa trenutnim resursima i jasno reći što preostaje

---

## 0. TRENUTNO ISKRENO STANJE - POLAZIŠTE

### Što imamo REAL - VERIFICIRANO
- **Factory REAL:** 248 stilova, 3211 MIDI fajla u `Split Factory Styles.zip` (3211 entries) - re-extract verificirano 3211
- **Gold REAL:** 182 live MIDI fajla u `Gold DNA.zip` - verificirano 182, analiza 1893 instance 2,272,811 nota
  - 4 role REAL: accompaniment 1414 inst sigma 34.3 trills 199,917, drums 182 inst sigma 33.8 trills 17,731, bass 248 inst sigma 33.8 trills 11,521, melody 49 inst sigma 34.4 trills 4,133 - ukupno 233,302 trills REAL
  - 16 rola PROXY sigma 5 (accordion, brass, choir, echo, organ, pad, percussion, piano, power-riff, rhythm-guitar, riff, sax, solo, strings, terca, woodwind)
- **Artifacts:** 37 MIDI fajla - 37/37 PASS Korg verificirano
- **Engine v13:** Kod za 20 rola mapirano, 19 drum elemenata 7 konteksta, trills 196, CC 10510, groove kick-bass lock, gate duration avg 0.81, 9 scores pojednostavljeno, deterministic seed 9302026 - kod postoji

### Što je PARTIAL / PROXY / BLOCKED
- Factory 20 rola: 4 REAL + 16 mapiranih PROXY (heuristika instrument->factory)
- Gold 20 rola: 4 REAL + 16 PROXY
- Drum 7 konteksta: 5/7 aktivno u 37 fajlova (ghost 0, phrase_end 0)
- CC writing i gate duration: kod postoji ali corpus test ne piše output MIDI (output_path=None)
- Musical 9 scores: pojednostavljeno fiksno 70->85, ne sophisticated
- Korg: samo 37 testirano, ne 3393 (3211+182)
- Human listening: 0/2 BLOCKED
- Parameter sweep: JSON postoji, nije exhaustive auto

**Iskren skor:** 8/25 PASS REAL (32%), 15 PARTIAL (60%), 2 BLOCKED (8%)

---

## 1. ROADMAP 14.00 - FAZE KOJE SU MOGUĆE SADA (IMMEDIATE - 1-2 dana)

### FAZA A1: Factory 3211 - REAL 20 rola analiza (MOGUĆE - imamo 3211 fajlova)

**Cilj:** Od 4 role REAL napraviti 20 rola REAL iz 3211 Factory MIDI fajlova

**Zadaci:**
1. Napisati `analyze_factory_3211_per_20_roles.py`
   - Učitati svih 3211 MIDI iz Workspace_Styles
   - Per-channel klasifikacija u 20 rola (bass, drums, piano, guitar, strings, brass, woodwind, accordion, organ, pad, choir, percussion, melody, accompaniment, lead, solo, riff, power-riff, rhythm-guitar, terca) - ista logika kao Gold per-channel
   - Za svaku rolu: velocity min/max/p50/p05/p95, sample count, 7-point curve
   - Output: `data/factory-velocity-profiles-20-roles-REAL-3211.json` i `calibration/factory_20_roles_REAL_3211.json`

2. Verifikacija:
   - `factory_20_roles_REAL_3211.json` mora imati 20 rola, svaka sa >100 sample-a, Korg realistic
   - Usporedba sa postojećim `factory_velocity_11.00_final_20_roles.json` (koji je mapiran)

**Moguće:** DA - imamo 3211 fajlova, možemo analizirati
**Ovisnost:** Nema
**Output:** Factory 20 rola REAL umjesto 4 REAL + 16 mapped
**Status nakon:** Factory postaje 100% REAL za 20 rola

---

### FAZA A2: Gold 182 - Drum 7 konteksta REAL dokaz (MOGUĆE - imamo 402k drum nota)

**Cilj:** Dokazati svih 7 drum konteksta na REAL Gold 402,401 drum nota

**Zadaci:**
1. Napisati `analyze_gold_drums_7_contexts.py`
   - Učitati 182 Gold MIDI, izdvojiti sve drum note (channel 9) - 402,401 nota REAL
   - Klasificirati 19 elemenata (kick, snare, itd)
   - Klasificirati 7 konteksta per nota:
     - fill: brza sukcesija <120 ticks blizu kraja bara >1536
     - transition: tick %1920 >1680
     - phrase_end: downbeat zadnjih 10% bara >1728
     - syncopated: offbeat 120
     - accent: downbeat
     - ghost: low vel offbeat
     - normal: ostalo
   - Output: `calibration/gold_drums_7_contexts_REAL.json` sa counts per kontekst per element

2. Verifikacija:
   - Moraju biti aktivni svi 7 konteksta na 402k nota (očekivano ghost i phrase_end postoje u Gold REAL, samo nisu u 37 artifacts)
   - Ako ghost i phrase_end postoje u Gold REAL, onda je 7/7 dokazano REAL

**Moguće:** DA - imamo 402k drum nota REAL
**Ovisnost:** Nema
**Output:** Drum 7 konteksta REAL dokaz
**Status nakon:** Drum postaje 100% REAL 7/7 aktivno

---

### FAZA A3: Engine - CC writing i gate duration output u corpus testu (MOGUĆE - kod već postoji)

**Cilj:** Da corpus test stvarno piše MIDI fajlove sa CC i gate duration, ne samo broji

**Zadaci:**
1. Izmijeniti `final_certified_engine_v13_full_no_bypass.py`:
   - U `process_full_corpus_full()`, za svaki fajl zadati `output_path = ARTIFACTS_DIR / calibrated_14.00 / <ime>`
   - Napisati MIDI sa CC11, CC1, gate duration
   - Verificirati da napisani MIDI ima CC poruke i različite duratione

2. Test:
   - `ls artifacts/calibrated_14.00/*.mid | wc -l` mora biti 37
   - `python3 -c "import mido; mid=mido.MidiFile('artifacts/calibrated_14.00/session2-before.mid'); print([msg for msg in mid.tracks[0] if msg.type=='control_change'])"` mora pokazati CC11

**Moguće:** DA - kod već postoji, samo treba dodati output_path
**Ovisnost:** Nema
**Output:** 37 MIDI fajlova sa CC i gate REAL
**Status nakon:** CC writing i gate duration postaju 100% dokazano, ne samo kod

---

### FAZA A4: Full corpus Korg test - 3211 + 182 + 37 = 3430 fajla (MOGUĆE - imamo fajlove)

**Cilj:** Testirati Korg Pa800 kompatibilnost na svim REAL fajlovima, ne samo 37

**Zadaci:**
1. Napisati `test_full_corpus_korg_3430.py`:
   - Učitati 3211 Factory MIDI + 182 Gold MIDI + 37 artifacts = 3430 fajla
   - Za svaki: per-channel poly check, PPQ check, velocity 1-127, CC allowed, itd
   - Output: `calibration/korg_test_3430_REAL.json` sa pass/fail per fajl

2. Očekivano:
   - Factory 3211: vjerojatno svi PASS jer su Factory stilovi već Korg kompatibilni
   - Gold 182: možda neki FAIL poly (live aranžmani) - treba poly reduction
   - Artifacts 37: 37/37 PASS već verificirano

3. Ako Gold ima FAIL, primijeniti engine v13 poly reduction i ponovno testirati

**Moguće:** DA - imamo sve fajlove
**Ovisnost:** A1 (Factory 20 rola REAL) poželjno ali ne nužno
**Output:** Korg test na 3430 fajla REAL
**Status nakon:** Korg postaje REAL za 3430, ne samo 37

---

### FAZA A5: Musical 9 scores - od pojednostavljenog ka REAL sofisticiranom (MOGUĆE - možemo implementirati prave metrike)

**Cilj:** Zamijeniti fiksne 70->85 vrijednosti sa pravim metrikama

**Zadaci:**
1. Napisati `musical_validation_9_scores_REAL.py` sa pravim metrikama:
   - **harmony:** chord tone weight = % nota koje su chord tones vs passing tones (treba chord detection)
   - **groove:** pocket = std dev timinga od grida, interlock = korelacija kick-bass, syncopation rate
   - **dynamics:** velocity range, unique count, Factory curve adherence (distance od Factory optimal)
   - **articulation:** gate var, ghost rate, fill rate, trill rate
   - **phrase:** phrase boundary detection, breath, pickup rate
   - **instrument:** role-specific checks (bass root rate, melody interval variety)
   - **drum:** kick NOT uniform (unique vel >1), snare ghost separation, HH pattern
   - **bass:** pocket vs kick, root foundation rate, approach rate
   - **musicality:** weighted avg

2. Implementirati barem 3 metrike REAL:
   - dynamics: velocity min/max/unique REAL
   - drum: kick unique vel, snare ghost separation REAL
   - bass: kick-bass lock rate REAL

3. Output: `calibration/musical_9_scores_REAL.json` sa before/after/delta per fajl per score

**Moguće:** DA - možemo implementirati barem 3-4 metrike REAL, za ostale treba više vremena
**Ovisnost:** A2 (drum konteksti) za drum score
**Output:** 9 scores od pojednostavljenih ka REAL
**Status nakon:** Musical postaje 50% REAL (3-4 metrike REAL, ostale još pojednostavljene)

---

## 2. ROADMAP 14.00 - FAZE SREDNJE (MEDIUM - 3-7 dana)

### FAZA B1: Gold 16 proxy rola - istraživanje što je moguće (MOGUĆE DJELOMIČNO)

**Cilj:** Pokušati naći Gold DNA za 16 proxy rola ili iskreno priznati limit

**Zadaci:**
1. Analizirati Gold 182 fajla per-channel sa detaljnijom klasifikacijom (ne samo 4 role):
   - Trenutna klasifikacija: drums (ch9), bass (low), melody (mono varied), else accompaniment
   - Poboljšana: pokušati detektirati strings, brass, sax, woodwind, accordion, itd po pitch range, poly, density
   - Npr. ako avg pitch >80 i density <3 i max_poly >=3 -> strings, ako avg pitch 60-70 i velocity >100 -> brass, itd

2. Ako se nađe >0 instanci za neku od 16 rola u Gold 182:
   - Npr. možda ima 20 instanci strings, 10 brass, itd - onda postaju REAL sa malim brojem instanci
   - Output: `gold_20_roles_detailed.json` sa 20 rola, neke sa malo instanci

3. Ako se ne nađe:
   - Iskreno dokumentirati: Gold DNA sadrži uglavnom 4 role jer su live aranžmani (drums, bass, accompaniment, melody), ostalih 16 rola nema u Gold DNA i ostaje PROXY iz instrument-catalog
   - To je OK ako se iskreno kaže - nije sve moguće imati REAL

**Moguće:** DJELOMIČNO - možda se nađe nešto za strings, brass, itd, ali vjerojatno ne za sve 16
**Ovisnost:** Nema
**Output:** Gold 20 rola sa više REAL nego 4, ili iskren limit dokumentiran
**Status nakon:** Gold postaje npr. 8 REAL + 12 PROXY umjesto 4+16 - bolje ali ne 100%

---

### FAZA B2: Parameter sweep exhaustive automatski (MOGUĆE)

**Cilj:** Automatski sweep parametara sa dokazom, ne ručno JSON

**Zadaci:**
1. Napisati `parameter_sweep_exhaustive.py`:
   - Za svaki parametar (velocity floor, ceiling, timing sigma, poly limits, drum threshold, PPQ):
     - Testirati više vrijednosti na 37 artifacts + 100 random Factory + 50 random Gold
     - Mjeriti Korg pass rate i musical improvement
     - Naći optimal
   - Output: `calibration/parameter_sweep_exhaustive_REAL.json` sa rezultatima per parametar

2. Primjer:
   - velocity floor bass [20,30,40,50,65] -> optimal 65 (Korg realistic + musical)
   - timing sigma [3,5,8,10,34.3] -> optimal 34.3 REAL scaled safe
   - itd

**Moguće:** DA - možemo automatizirati
**Ovisnost:** A4 (full corpus Korg test)
**Output:** Exhaustive sweep REAL
**Status nakon:** Parameter sweep postaje REAL

---

### FAZA B3: Sensitivity analiza REAL (MOGUĆE)

**Cilj:** Kao B2, automatski

**Zadaci:**
1. `sensitivity_analysis_REAL.py` - za svaki parametar, koliko promjena utječe na Korg i musical

**Moguće:** DA
**Ovisnost:** B2
**Output:** Sensitivity REAL

---

### FAZA B4: Listening validation - priprema blind paketa (MOGUĆE - bez human evaluatora)

**Cilj:** Pripremiti blind A/B paket za human evaluatore, iako nemamo evaluatore sada

**Zadaci:**
1. Kreirati `artifacts/calibrated_14.00/` sa ORIGINAL vs FINAL A/B za 10 reprezentativnih fajlova
2. Napisati `listening_validation_instructions.md` sa kriterijima (groove, naturalness, dynamics, itd) i formom za evaluaciju
3. Output: blind paket spreman za slanje evaluatorima

**Moguće:** DA - priprema paketa
**Ovisnost:** A3 (CC i gate output)
**Output:** Blind paket REAL spreman
**Status nakon:** Listening SOFTWARE PASS + paket spreman, HUMAN još BLOCKED (treba naći evaluatore)

---

## 3. ROADMAP 14.00 - FAZE DUGOROČNE / BLOKIRANE (LONG TERM / BLOCKED)

### FAZA C1: Human listening - 2 neovisna evaluatora (BLOKIRANO - treba naći ljude)

**Cilj:** 2 neovisna evaluatora, Overall median 4/5 i 70% Premium preference

**Zadaci:**
1. Naći 2 evaluatora (muzičari, producenti)
2. Poslati blind paket
3. Prikupiti rezultate
4. Output: `listening_validation_human_REAL.json`

**Moguće:** NE SADA - treba naći ljude, to je van koda
**Ovisnost:** B4
**Status:** 🚫 BLOCKED - treba ljudski resurs

---

### FAZA C2: Gold 20 rola FULL REAL - ako nema u 182 fajla (BLOKIRANO - treba novi Gold DNA)

**Cilj:** Imati Gold DNA za svih 20 rola REAL

**Zadaci:**
1. Ako B1 ne nađe Gold za 16 rola, treba novi Gold DNA izvor:
   - Snimiti ili naći MIDI fajlove sa strings, brass, sax, itd live svirkama
   - Ili koristiti postojeći Factory 3211 kao Gold proxy za te role (ali onda nije Gold, nego Factory)

2. Alternativno: Iskreno priznati da Gold DNA ima samo 4 role REAL i da je to OK - Gold je playing logic za timing/groove/humanization, a Factory je za velocity/range. Za 16 rola, timing/groove može biti proxy 5, ali to je iskreno

**Moguće:** NE SADA sa trenutnim Gold 182 fajla - treba novi izvor
**Ovisnost:** B1
**Status:** 🚫 BLOCKED ili ⚠️ PRIHVATLJIVO kao PROXY ako se iskreno kaže

---

### FAZA C3: Full corpus 3430 Korg PASS 100% sa engine transformacijom (MOGUĆE ali zahtjevno)

**Cilj:** 3211 Factory + 182 Gold + 37 artifacts = 3430 fajla SVI PASS Korg nakon engine transformacije

**Zadaci:**
1. Nakon A4, ako neki Gold fajl FAIL poly, primijeniti engine v13 poly reduction
2. Ponovno testirati
3. Cilj 3430/3430 PASS

**Moguće:** DA ali zahtjevno - treba procesirati 3430 fajla
**Ovisnost:** A4
**Output:** 3430/3430 PASS REAL
**Status nakon:** Full corpus Korg 100% REAL

---

## 4. PRIORITETI - ŠTO PRVO

### P0 - CRITICAL - MORA SE ODMAH (1 dan)
- A1: Factory 3211 REAL 20 rola analiza - jer je to temelj, imamo fajlove
- A2: Gold drum 7 konteksta REAL - jer imamo 402k drum nota
- A3: Engine CC i gate output - jer je kod već tu, samo treba output_path
- A4: Full corpus Korg test 3430 - da vidimo realno stanje

### P1 - HIGH - TREBA USKORO (2-3 dana)
- A5: Musical 9 scores barem 3-4 metrike REAL
- B1: Gold 16 proxy istraživanje
- B4: Listening blind paket priprema

### P2 - MEDIUM - KAD P0 i P1 gotovi (3-7 dana)
- B2: Parameter sweep exhaustive
- B3: Sensitivity REAL
- C3: Full corpus 3430 PASS 100%

### P3 - BLOCKED - TREBA LJUDE / NOVI IZVOR
- C1: Human listening evaluatori
- C2: Gold 20 rola FULL REAL novi izvor

---

## 5. ŠTO JE MOGUĆE SA TRENUTNIM RESURSIMA - BEZ NOVIH LJUDI / FAJLOVA

**Moguće 100% sa trenutnim resursima (kod + 3211 Factory + 182 Gold + 37 artifacts):**
- ✅ Factory 20 rola REAL analiza iz 3211 fajlova
- ✅ Gold drum 7 konteksta REAL dokaz iz 402k nota
- ✅ Engine CC writing i gate duration output sa output_path
- ✅ Full corpus Korg test 3430 fajla (samo test, ne nužno 100% PASS)
- ✅ Musical 9 scores barem 3-4 metrike REAL (dynamics, drum, bass, groove)
- ✅ Parameter sweep i sensitivity automatski
- ✅ Listening blind paket priprema
- ✅ Shadow mode, transform authorization, failure analysis - već postoje

**Nije moguće sa trenutnim resursima bez novih ljudi/fajlova:**
- 🚫 Human listening 2 evaluatora - treba naći ljude
- 🚫 Gold 20 rola FULL REAL ako nema u 182 fajla - treba novi Gold izvor ili prihvatiti 4 REAL + 16 PROXY kao iskren limit

**Iskreno moguće nakon P0 i P1:**
- Factory: 20 rola REAL (umjesto 4+16 mapped) - MOGUĆE
- Gold: 4 REAL + možda 4-8 REAL ako B1 nađe nešto + ostalo PROXY - DJELOMIČNO MOGUĆE (npr. 8 REAL + 12 PROXY)
- Drum: 7/7 REAL dokazano na Gold 402k - MOGUĆE
- Engine: CC i gate output REAL - MOGUĆE
- Korg: 3430 test REAL, možda 3400/3430 PASS - MOGUĆE
- Musical: 3-4 metrike REAL + ostale pojednostavljene - DJELOMIČNO MOGUĆE
- Overall: **15/25 PASS REAL (60%), 8 PARTIAL (32%), 2 BLOCKED (8%)** - bolje od trenutnih 32% REAL, ali ne 100%

---

## 6. ROADMAP 14.00 - DETALJAN PLAN PO DANIMA

### DAN 1 - P0
- **Jutro:** A1 Factory 3211 REAL 20 rola - `analyze_factory_3211_per_20_roles.py` - 2-3 sata
- **Popodne:** A2 Gold drum 7 konteksta REAL - `analyze_gold_drums_7_contexts.py` - 2 sata
- **Večer:** A3 Engine CC i gate output - izmjena v13 + test 37 fajlova - 1 sat

### DAN 2 - P0 nastavak
- **Jutro:** A4 Full corpus Korg test 3430 - `test_full_corpus_korg_3430.py` - 3-4 sata (procesiranje 3430 fajla)
- **Popodne:** Analiza rezultata A4, ako FAIL, primjena poly reduction
- **Večer:** A5 Musical 9 scores - barem dynamics, drum, bass REAL - 2 sata

### DAN 3 - P1
- **Jutro:** B1 Gold 16 proxy istraživanje - detaljna klasifikacija Gold 182 per 20 rola - 3 sata
- **Popodne:** B4 Listening blind paket - 1 sat
- **Večer:** Dokumentacija P0+P1 - ISKREN_IZVJESTAJ_14.00

### DAN 4-5 - P2
- **B2 Parameter sweep exhaustive** - 1 dan
- **B3 Sensitivity REAL** - pola dana
- **C3 Full corpus 3430 PASS 100%** - pola dana

### DAN 6+ - P3 BLOCKED
- **C1 Human listening:** Traženje evaluatora - van koda, ne može se procijeniti
- **C2 Gold 20 rola FULL:** Ako B1 ne nađe, treba novi izvor ili prihvatiti limit

---

## 7. KONAČAN CILJ - ŠTO JE REALNO OČEKIVATI

**Nakon ROADMAP 14.00 P0+P1+P2 (5 dana rada, bez ljudskih resursa):**

- **Factory:** 20 rola REAL iz 3211 fajlova - 100% REAL (umjesto 4+16 mapped)
- **Gold:** 4 REAL + možda 4-8 REAL iz detaljne analize + ostalo PROXY - npr. 8 REAL + 12 PROXY (40% REAL, 60% PROXY) - bolje od 20% REAL
- **Drum:** 19 elem 7 konteksta 7/7 dokazano na Gold 402k - 100% REAL
- **Engine:** CC writing i gate duration output REAL 37 fajlova - 100% REAL
- **Korg:** 3430 test REAL, npr. 3400/3430 PASS 99% - 99% REAL
- **Musical:** 3-4 metrike REAL + 5-6 pojednostavljene - 40% REAL
- **Parameter sweep, sensitivity:** exhaustive REAL - 100% REAL
- **Listening:** blind paket spreman, software 4.6/5 PASS, human BLOCKED - 50% (softver da, human ne)
- **Overall:** **18/25 PASS REAL (72%), 5 PARTIAL (20%), 2 BLOCKED (8%)** - iskreno, bez laži

**Da bi bilo 25/25 PASS 100% FULL NO BYPASS 0% bypass, treba:**
- C1 Human evaluatori (ljudi)
- C2 Gold 20 rola FULL REAL novi izvor ili prihvatiti 4 REAL kao limit i redefinirati cilj

**Iskren prijedlog:** Redefinirati cilj sa "20 rola FULL REAL" na "4 role REAL (accompaniment, drums, bass, melody) + 16 rola mapirano PROXY sa obrazloženjem" - jer je to REALNO sa trenutnim Gold 182 fajla koji su live aranžmani sa 4-5 kanala. Gold DNA je playing logic za timing/groove/humanization, a to je REAL za 4 glavne role koje čine 95% note (1.6M + 402k + 212k + 28k = 2.27M). Ostalih 16 rola su varijacije melodije/accompaniment i mogu koristiti proxy timing 5 - to je iskreno i prihvatljivo ako se kaže.

**Tako bi FINAL bio:** Factory 20 rola REAL (iz 3211) + Gold 4 role REAL (iz 182) + 16 proxy sa obrazloženjem + sve ostalo FULL - i to bi bilo ISKRENO 25/25 PASS sa REAL dokazima i jasnim PROXY dijelovima dokumentiranim, ne lažno 100% FULL.

---

## 8. AKCIJSKI PLAN - ŠTO ODMAH

**Odmah mogu pokrenuti:**
1. A1 Factory 3211 REAL 20 rola analiza
2. A2 Gold drum 7 konteksta REAL
3. A3 Engine CC i gate output fix
4. A4 Full corpus Korg 3430 test

**Treba odluka:**
- Da li prihvaćamo Gold 4 REAL + 16 PROXY kao iskren limit ili tražimo novi Gold izvor za 16 rola?
- Da li je OK da Factory bude 20 REAL (moguće) a Gold 4 REAL + 16 PROXY (realno)?

**Moj prijedlog:** Krenuti sa A1-A4 odmah (moguće danas), onda B1 istraživanje Gold 16 rola, pa vidjeti što se nađe. Ako se ne nađe, iskreno dokumentirati 4 REAL + 16 PROXY kao limit i redefinirati FINAL kao "Factory 20 REAL + Gold 4 REAL + ostalo FULL" - što je i dalje odličan rezultat i ISKREN.

---

**Verzija:** 14.00-ROADMAP-ISKREN  
**Factory REAL:** 3211 fajla 248 stilova - MOGUĆE 20 REAL  
**Gold REAL:** 182 fajla 2.27M nota - 4 REAL + 16 PROXY (realno), moguće 8 REAL nakon B1  
**Moguće sa trenutnim resursima:** 72% PASS REAL, 20% PARTIAL, 8% BLOCKED - bez laži  
**Za 100%:** Treba human evaluatori i novi Gold izvor za 16 rola ili redefinicija cilja  
**Status:** ROADMAP ISKREN - sve što je moguće i što preostaje
