# Plan do AI Premium Arrangera

Datum plana: 3. rujna 2026.
Izvorna polazna verzija: DNA MIDI Studio 3.16
Aktivni software baseline: DNA MIDI Studio 4.11.1 Device Certification Intake Foundation
Trenutačni dokaz: legacy 43/43 PASS, objedinjeni recovery + uređajni preflight + Premium/Renderer/Coherence/Workflow/Reliability/Quality/Device Intake sigurnosni paket 2900/2900 PASS
Trenutačna granica: zaključani quality i uređajni evidence intake rade fail-closed, ali ljudski listening je 0/2, produkcijski expression/articulation capture nije dostavljen, a fizički Korg Pa800 ostaje `WAITING_FOR_DEVICE`

## 1. Što znači AI Premium Arranger

AI Premium Arranger nije chatbot koji iz slobodnog teksta neposredno piše MIDI. To je profesionalni produkcijski sustav u kojem AI razumije namjeru korisnika, analizira pjesmu, predlaže globalni aranžmanski plan i objašnjava alternative, dok deterministički engine proizvodi MIDI i neovisni verifier odlučuje smije li rezultat biti objavljen.

Konačni proizvod mora omogućiti da korisnik:

1. učita MIDI song ili započne prazan projekt;
2. napiše cilj običnim jezikom, primjerice „napravi življi pop-folk Style, sa suzdržanom strofom i punim refrenom”;
3. dobije provjerenu analizu tonaliteta, akorda, forme, uloga, registara, gustoće i polifonije;
4. pregleda AI Producer Brief i ispravi svaku pretpostavku;
5. dobije dvije do četiri koherentne aranžmanske varijante;
6. zaključa željene sekcije, zvukove, trake ili patterne i regenerira samo ostatak;
7. presluša A/B preview i vidi zašto je svaki pattern odabran;
8. uređuje note i prijelaze bez gubitka sigurnosnih pravila;
9. izveze ponovljiv, auditiran i uređajno validiran rezultat;
10. nakon fizičkog testa koristi certificirani Pa800 profil.

### Premium obećanje

Rezultat mora biti glazbeno povezan kroz cijeli Style, a ne zbir lokalno dobrih patterna. Intro mora najaviti identitet Stylea, Variation 1–4 moraju stvarati kontrolirani rast energije, Fill mora voditi prema sljedećoj sekciji, a Ending mora zvučati kao zaključak istog aranžmana.

## 2. Nepovrediva pravila

Ova pravila ostaju iznad AI preporuke, korisničkog preseta i Premium funkcije:

1. Factory MIDI ostaje jedini autoritet za velocity i potvrđene mixer granice.
2. GOLD daje ritam, relativne tonove, gate, fraziranje i odnose, ali nikada velocity, Bank Select ili Program Change.
3. Originalne solo note čuvaju onset, trajanje, pitch i velocity osim kada korisnik izričito napravi ručnu edit operaciju.
4. AI ne piše finalne MIDI bajtove i ne može preskočiti validator.
5. Isti ulaz, konfiguracija, registry verzija i seed daju iste MIDI bajtove.
6. Svaka automatska intervencija ima izvor, razlog, confidence, budget i mogućnost povratka.
7. Nepotvrđen RX, DNC ili Guitar Mode trigger nikada se ne nagađa.
8. Neispravan ili neprovjeren rezultat ne dobiva download finalnog MIDI-ja.
9. Originalna datoteka nikada se ne prepisuje.
10. Cloud ostaje opcionalan, metadata-only po defaultu i ne smije biti uvjet za osnovni rad.

## 3. Ciljna arhitektura

```text
Korisnička namjera / MIDI song
              |
              v
       AI Producer Brief
  strukturirani cilj i ograničenja
              |
              v
          Song Map 2.0
 akordi + forma + uloge + napetost
              |
              v
       Arrangement Graph
 globalni plan svih Style elemenata
              |
              v
 Candidate Search + Constraint Solver
 Factory/GOLD dokaz, veze i budgeti
              |
              v
    Deterministički MIDI Engine
              |
              v
 Independent Verifier + Device Profile
              |
              v
 MIDI + manifest + audit + A/B preview
```

### Obavezni podatkovni ugovori

- `ProducerBrief` — žanr, namjera, energija, gustoća, obavezne i zabranjene uloge, zaključani elementi te tolerancija promjene.
- `SongMap` — tempo/takt, tonalitet, akordi, fraze, sekcije, kadence, gustoće, registri, polifonija i confidence svakog zaključka.
- `SoundBinding` — stabilni track identitet, točan CC00/CC32/Program, uloga, playable raspon, articulation mapa i Factory profil.
- `ArrangementGraph` — odnos Intro/Variation/Fill/Ending elemenata, ciljna energija i prijelazne obaveze.
- `CandidateSet` — rangirani patterni, deset ili više kriterija, razlozi, transformacije, rizici i alternative.
- `TrackPlan` — odluka `KEEP`, `REPAIR`, `REPLACE` ili `MANUAL_REVIEW` za svaku traku i sekciju.
- `RenderManifest` — svi ulazni hashovi, seed, registry verzije, odabiri, intervencije, output hash i validator rezultat.
- `EvaluationReport` — tehničke metrike, glazbene metrike, A/B ocjena i otvorene manual-review stavke.
- `DeviceProfile` — kanali, marker ugovor, polifonijski limiti, procijenjeni voice cost, zvučne i articulation mape te status fizičke potvrde.

## 4. Prioriteti proizvoda

### P0 — obavezno za naziv AI Premium Arranger

- fizički potvrđen Pa800 import profil;
- produkcijska integracija svih Session 2–7 enginea;
- tekstualna namjera prevedena u strogo validiran `ProducerBrief`;
- globalni Arrangement Graph umjesto neovisnog biranja svakog elementa;
- najmanje dvije determinističke A/B varijante;
- zaključavanje i parcijalna regeneracija;
- potpuna zaštita solo traka i sound mappinga;
- full-duration polifonijski i procijenjeni voice-cost budget;
- audio/MIDI preview koji je jasno odvojen od uređajnog certifikata;
- explainable izbor, audit, undo/redo i crash recovery;
- slijepi listening benchmark i release quality gate.

### P1 — Premium 1.x nadogradnja

- osobni profil korisnika iz eksplicitno prihvaćenih odluka;
- biblioteka aranžmanskih recepata i song-to-style predložaka;
- napredni batch workflow;
- dodatni potvrđeni Pa-series DeviceProfileovi;
- usporedba više mikseva i orchestration varijanti.

### P2 — kasniji prošireni opseg

- audio-reference analiza bez automatskog obećanja točne transkripcije;
- stem ili audio render putem vanjskog synth/sampler sloja;
- suradnički cloud projekti;
- izravni proprietarni Style format samo ako postoji legalan i tehnički potvrđen ugovor.

P2 ne smije odgoditi P0. Prva Premium verzija ostaje MIDI-first i Pa800-first.

## 5. Razvojni roadmap

Svaka sesija mora završiti stvarnim artefaktom, automatiziranim pozitivnim i negativnim testovima, ažuriranim manifestom te jasno navedenim preostalim ograničenjem.

### Sesija 15 — Baseline Freeze i Premium specifikacija — ZAVRŠENO

**Cilj:** zaključati postojeći 3.16 rezultat kao nepromjenjivi regresijski baseline.

**Isporuke:**

- hash vault za svih pet produkcijskih registryja, 43/43 i 289/289 izvještaje te referentne MIDI artefakte;
- verzionirana shema svih devet ciljnih podatkovnih ugovora;
- popis P0/P1/P2 funkcija i status `IMPLEMENTED`, `FOUNDATION_VALIDATED`, `PLANNED` ili `DEVICE_BLOCKED`;
- referentni skup od najmanje 20 legalno raspoloživih MIDI songova različitih formi i gustoća;
- definirana referentna Windows konfiguracija za mjerenje brzine i memorije.

**Gate:** nijedan postojeći MIDI hash ili invariant ne mijenja se bez eksplicitne migracije i obrazloženja.

**Rezultat:** 20/20 PASS. Devet schema ugovora, feature matrica, plan-only `PremiumConfig`, referentni Pa800 Style i immutable baseline od 24 datoteke imaju zajednički ID `premium-3.17-98a6d52a09ccc789`. Premium proizvod ostaje `PLANNED`.

### Sesija 16 — Pa800 Mapping Lab i fizička certifikacija

**Cilj:** zamijeniti pretpostavke stvarnim uređajnim dokazom.

**Isporuke:**

- izvršen Session 14 USB import, SHIFT + Execute, marker/CV, Track Type i NTT test;
- save/reload i polifonijski listening rezultat s audio/slikovnim dokazom;
- verzionirani Pa800 `DeviceProfile` s potvrđenim Bank/Program mapama;
- zasebne `CONFIRMED`, `UNSUPPORTED` i `UNKNOWN` RX/DNC/Guitar Mode stavke;
- mjerenje prihvatljivog voice stealinga za ključne višeslojne Soundove;
- popis korekcija koje se vraćaju u engine i regresijski korpus.

**Gate:** `PA800_DEVICE_CERTIFIED` smije se dodijeliti samo potpisanom rezultatu s ispravnim hashovima. Ako uređaj pokaže grešku, status je `DEVICE_TEST_FAILED`, ne parcijalni certifikat.

### Sesija 17 — Production Adapter za Session 2–7 enginee — ZAVRŠENO PARCIJALNO

**Cilj:** ukloniti oznaku `PRODUCTION_BLOCKED` tamo gdje produkcijski registry i GUI/API dokaz stvarno postoje.

**Isporuke:**

- jedan zajednički production adapter za drum, percussion, bass, power/riff, guitar, solo, RX i DNC;
- eksplicitno odbijanje izmišljene produkcijske GOLD ornament/relationship sheme: solo ostaje Factory-expression-only;
- produkcijski Factory strumming adapter bez GOLD gitarskog autoriteta;
- track-local `SoundBinding` prije svake promjene;
- stvarni song E2E kroz GUI, API, CLI i batch s jednakim output hashom;
- per-stage diff i rollback.

**Gate:** svaki modul prolazi najmanje tri stvarna songa, uključujući negativni sound mismatch i shared-channel solo slučaj.

**Rezultat:** 35/35 PASS. Produkcijski adapter provjerava fizički `trackUid`, vremenski CC00/CC32/Program SoundBinding i shared-channel vlasništvo prije svakog stagea. Drum/percussion, bass/power-riff/riff i Factory strumming dobili su stvarne produkcijske pretvorbe; solo dobiva samo exact Factory CC11 uz pipeline-wide zaštitu originalnih nota. CLI, web, API, GUI i batch daju isti rezultat, a blokirani stage čuva izvorne bajtove. Tri stvarna GOLD songa dokazuju sigurno odbijanje role guessing-a. Sesija ostaje `FOUNDATION_VALIDATED / PRODUCTION_PARTIAL` jer potvrđena GOLD ornament shema, RX/DNC mape, Guitar Mode kontrole i fizički Pa800 još nedostaju. Dokazi su `data/session17-test-report.json`, `data/session17-production-registry-catalog.json`, `data/session17-real-corpus-manifest.json` i `artifacts/session17-production-adapter-manifest.json`.

### Sesija 18 — Track Identity, Solo Safety i Mapping 2.0 — ZAVRŠENO

**Cilj:** trajno ukloniti klasu grešaka pogrešnog track/channel mapiranja.

**Isporuke:**

- stabilni `trackUid` neovisan o 0-based/1-based prikazu;
- jasno odvojeni `trackIndex`, `trackNumber`, `channelIndex` i `channelNumber`;
- vremenski scoped Bank/Program state po fizičkoj traci, ne samo po kanalu;
- detekcija SMF0 spajanja i shared-channel konflikta;
- fingerprint originalnih solo nota prije i poslije svakog stagea;
- Delay/Echo allocator koji bira prvi potpuno slobodan track, nikad ne otvara 17. traku i nikad ne koristi zauzeti shared channel bez odobrenja;
- GUI upozorenje koje pokazuje izvorni i ciljni track, kanal i SoundBinding.

**Gate:** property testovi generiraju format 0/1, prazne trake, dijeljene kanale, promjene programa usred pjesme i graničnih 16 traka bez pogrešnog mapiranja ili promjene originalnog sola.

**Rezultat:** 28/28 PASS. Implementirani su stabilni source `trackUid`, vremenski SoundBinding v2, zasebni Track/Channel indeksi i brojevi, SMF0/shared-channel detekcija, odobrenje konflikta, potpuno slobodan Delay track allocator te fingerprint izvornog sola koji se provjerava nakon svakog pipeline stagea. Dokazi su `data/session18-test-report.json`, `data/session18-schema-catalog.json` i `artifacts/session18-mapping-manifest.json`. Premium proizvod i dalje je `PLANNED`.

### Sesija 19 — Song Understanding 2.0 — ZAVRŠENO U FOUNDATION OPSEGU

**Cilj:** izgraditi pouzdan glazbeni model pjesme prije aranžiranja.

**Isporuke:**

- beat/downbeat i frazna analiza uz promjenjiv tempo i takt;
- akordi na pola takta, suspenzije, slash akordi, modalne posudbe i neharmonske note;
- kadence, pickup, break, build-up, drop i završne fraze;
- uloge po vremenskim segmentima umjesto jedne uloge za cijelu traku;
- uncertainty mapa: svaka nejasna ćelija dobiva confidence i razlog;
- interaktivna korekcija akorda i sekcija koja ne mijenja izvorni MIDI;
- labeled benchmark i regression fixtures.

**Gate:** ciljani chord weighted-F1 najmanje 0,85 i section-boundary F1 najmanje 0,80 na zaključanom internom korpusu; niski confidence mora voditi u `MANUAL_REVIEW`.

**Rezultat:** 36/36 PASS. Implementirani su strogi `SongMap 2.0`, zaseban read-only correction overlay, promjenjivi tempo/takt, beat/downbeat mreža, akordi na pola takta, sus/slash/seventh kvalitete, kadence, frazni signali, vremenski scoped uloge, full-duration polifonija i explainable uncertainty. Zaključani self-authored benchmark obuhvaća 20 songova i 320 half-bar ćelija te postiže chord weighted-F1 1,000 i section-boundary F1 1,000. Test s 25.000 nota prolazi cilj od 10 sekundi. Dokazi su `data/session19-test-report.json`, `data/session19-labeled-benchmark.json`, `data/session19-benchmark-report.json`, `data/session19-schema-catalog.json` i `artifacts/session19-song-map.json`. Status ostaje `FOUNDATION_VALIDATED / PRODUCTION_CALIBRATION_PENDING` dok se ne proširi ljudski označeni žanrovski korpus.

### Sesija 20 — AI Producer Brief — ZAVRŠENO

**Cilj:** pretvoriti slobodni korisnički opis u sigurnu, provjerljivu konfiguraciju.

**Isporuke:**

- lokalni rule-based parser za osnovne namjere i opcionalni AI adapter za složeniji jezik;
- JSON Schema validacija `ProducerBriefa`;
- kontrolirani rječnik žanra, energije, gustoće, sinkopacije, prostora, prijelaza i solo tretmana;
- prikaz „AI je razumio” prije generiranja;
- eksplicitna korisnička potvrda konfliktnih zahtjeva;
- prompt-injection i nepoznato-polje zaštita;
- offline fallback koji daje funkcionalno jednak core bez mreže.

**Gate:** AI izlaz ne može sadržavati MIDI bajtove, putanju za pisanje, zaobilaženje validatora ni izravni Bank/Program autoritet.

**Rezultat:** 52/52 PASS. Implementirani su strogi `ProducerBrief 2.0`, deterministički lokalni parser za hrvatske, engleske i miješane opise, kontrolirani rječnik namjere, blokirajući konfliktni gate i eksplicitno odobrenje razrješenja. Zaključani self-authored korpus ima 30 namjera i 62 očekivana polja uz field accuracy 1,000 i conflict accuracy 1,000. Lokalni CLI, API i Home GUI vraćaju isti brief; opcionalni AI adapter je default-off, traži pristanak, prima samo metadata payload, ne može nadjačati eksplicitna lokalna polja i na mrežnu ili schema grešku vraća se na lokalni rezultat. Prompt injection, MIDI writer/output path, validator bypass, Bank/Program autoritet, GOLD dinamika i automatska promjena originalnog sola strogo su blokirani. Dokazi su `data/session20-test-report.json`, `data/session20-intent-corpus.json`, `data/session20-benchmark-report.json`, `data/session20-schema-catalog.json` i `artifacts/session20-producer-brief.json`. Status je `SOFTWARE_VALIDATED`; Premium proizvod i dalje je `PLANNED`.

### Sesija 21 — Arrangement Graph i globalni planner — ZAVRŠENO

**Cilj:** planirati cijeli Style kao jednu glazbenu cjelinu.

**Isporuke:**

- graf veza Intro → Variation → Fill → Variation → Ending;
- ciljna krivulja energije i gustoće kroz V1–V4;
- motivski identitet koji se prenosi između elemenata bez doslovnog kopiranja;
- prijelazne obaveze: pickup, crash, bass approach, harmonic anticipation i ending cadence;
- zajednički register i polyphony budget za svih osam Pa800 traka;
- globalni transformation budget;
- plan s više kandidata prije mutacije.

**Gate:** planner ne smije odabrati lokalno bolji pattern ako ruši prijelaz, registar, harmoniju, polifoniju ili identitet cijelog Stylea.

**Rezultat:** 62/62 PASS. Implementirani su strogi `ArrangementGraph 2.0`, svih deset Pa800 čvorova, devet usmjerenih prijelaza, kontrolirani rast V1–V4, zajednička motivska obitelj, eksplicitni Fill targeti, harmony context, software-safe register plan, full-duration MIDI-note polyphony budget i globalni transformation budget. Planner daje dvije do četiri determinističke read-only plan-varijante prije pattern searcha; zaključani elementi ostaju jednaki u svakoj varijanti. Niski SongMap confidence, unresolved evidence, nedostajući verse/chorus ili source peak iznad 54 nota blokiraju Candidate Search kroz `MANUAL_REVIEW`. Zaključani benchmark nad 20 songova proizvodi 200 čvorova, 180 rubova i 40 planova uz rate 1,000 za rast energije, transition targete, determinizam i lock zaštitu. Lokalni CLI, API i Home GUI koriste isti planner. MIDI mutacija, candidate pattern selection, GOLD dinamika i promjena originalnog sola ostaju zabranjeni. Dokazi su `data/session21-test-report.json`, `data/session21-benchmark-report.json`, `data/session21-schema-catalog.json`, `artifacts/session21-arrangement-graph.json` i `artifacts/session21-locked-four-plan-graph.json`. Status je `SOFTWARE_VALIDATED`; Premium proizvod i dalje je `PLANNED`.

### Sesija 22 — Premium Candidate Search i Variation Engine — ZAVRŠENO

**Cilj:** dobiti različite, ali koherentne profesionalne varijante.

**Isporuke:**

- dvostupanjski retrieval: brzo filtriranje pa detaljno rangiranje;
- hard constrainti prije scorea;
- relationship-aware drum/bass i Factory-only guitar odabir;
- diversity penalty protiv gotovo identičnih V1–V4;
- stabilni A/B/C kandidati iz istog seeda i variant ID-a;
- lock, exclude, next candidate i parcijalna regeneracija;
- audit svih odbijenih kandidata i razloga.

**Gate:** ponovno generiranje otključanog elementa ne mijenja zaključane elemente ni njihove bajtove.

**Rezultat:** 68/68 PASS. `CandidateSet 2.0` veže točan `graphHash`, `songMapHash`, seed, plan-varijantu i hashove produkcijskih GOLD performance/Factory strumming registryja. Dvostupanjski retrieval radi nad 15.837 patterna, zatim prije scorea provodi hard gate za ulogu, takt, relativni pitch-mode, dokaz, registar, full-duration polifoniju i transformation budget. Svaki preživjeli kandidat ima 14 objašnjivih kriterija; gitara je isključivo Factory, drum–bass odnosi su eksplicitno povezani, a GOLD nema velocity, Bank/Program ni guitar autoritet. Stabilne A/B/C/D varijante imaju diversity penalty, user lock, exclude, next-candidate i parcijalnu regeneraciju s fragment hash dokazom da ostali markeri nisu promijenjeni. Benchmark od 20 songova daje 15/15 spremnih CandidateSetova i 5/5 očekivanih sigurnosnih blokada za neriješeni `MANUAL_REVIEW`; obrađeno je 775 zahtjeva, 2.325 selekcija, 13.022 detaljno auditirana odbijanja i 118 relationship odabira, uz sve stope 1,000. CLI, API i Home GUI koriste isti engine. CandidateSet ostaje read-only: finalni MIDI još se ne renderira. Dokazi su `data/session22-test-report.json`, `data/session22-benchmark-report.json`, `data/session22-schema-catalog.json`, `artifacts/session22-candidate-set.json` i `artifacts/session22-partial-regeneration.json`. Status je `SOFTWARE_VALIDATED / AI ARRANGER ALPHA`; AI Premium proizvod i fizički Pa800 ostaju nedovršeni.

### Sesija 23 — Groove, Humanization i polifonija — ZAVRŠENO U SOFTWARE OPSEGU

**Cilj:** poboljšati osjećaj izvedbe bez narušavanja Factory dinamike i uređajnih limita.

**Isporuke:**

- groove template iz timing odnosa, nikad iz GOLD velocityja;
- kontrolirana microtiming i gate varijacija po ulozi;
- očuvanje namjernog laid-back ili ahead-of-beat odnosa;
- full-duration peak mjerenje po traci, kanalu, sekciji i globalno;
- procijenjeni oscillator/voice cost iz potvrđenog DeviceProfilea;
- prioritet voice stealinga: ukrasni i pomoćni sloj prije osnovnog ritma, basa ili glavne melodije;
- stres test dugih sustain repova, pedale i gustih fillova.

**Gate:** nijedan automatski stage ne smije prijeći MIDI-note limit; uređajni voice-cost overflow blokira izvoz ili traži potvrđen simplification plan.

**Rezultat:** 70/70 PASS. `GroovePlan 2.0` pretvara odabrane produkcijske patterne u 4.497 read-only timing događaja i 107 groove-templateova. Role-specific granice čuvaju ahead/laid-back smjer, a gate varijacija ostaje odvojena od dinamike. Full-duration sweep mjeri peak za svaku logičku traku, kanal, marker i A/B/C varijantu; produkcijski maksimum je 18/54. Stress korpus potvrđuje duge sustain repove, sustain prozor, guste fillove, uklanjanje ukrasnog sloja prije core ritma, support thinning do 54 note te blokadu nerješivog core ili locked overflowa. GOLD daje samo timing/gate odnose, Factory dinamika se ne mijenja, a SoundBinding, originalni solo i zaključani fragmenti ostaju zaštićeni. Pa800 oscillator/voice cost ostaje `UNCONFIRMED` i izračunava se samo kada postoji hashiran `PA800_DEVICE_CERTIFIED` profil s mjerenim role-cost modelom. CLI, API i Home GUI koriste isti engine. GroovePlan još ne piše finalni MIDI. Dokazi su `data/session23-test-report.json`, `data/session23-benchmark-report.json`, `data/session23-schema-catalog.json`, `artifacts/session23-groove-plan.json` i `artifacts/session23-polyphony-stress.json`. Status je `SOFTWARE_VALIDATED / AI ARRANGER ALPHA`; fizički Pa800 i Premium proizvod ostaju nedovršeni.

### Sesija 24 — Premium Solo i Expression Director — ZAVRŠENO U SOFTWARE PREVIEW OPSEGU

**Cilj:** dodati glazbenu ekspresiju bez oštećenja glavne melodije.

**Isporuke:**

- phrase-aware grace, trill, slide i turnaround samo uz dokaz i slobodan prostor;
- tension/release CC11 krivulja unutar Factory granica;
- dijatonska terca s kontrolom registra, harmonije i collisiona;
- nerekurzivni Delay/Echo s jasnim routingom i per-layer budgetom;
- pravila kada je profesionalnije ne dodati ništa;
- A/B solo preview i vizualni sloj svih generiranih nota;
- jedan klik za uklanjanje samo AI expression sloja.

**Gate:** fingerprint svih originalnih solo nota ostaje jednak; svaki generirani događaj ima `sourceNoteUid`, evidence ID i reason code.

**Rezultat:** 80/80 PASS. `ExpressionPlan 2.0` povezuje fizički `trackUid`, 1-based Track/Channel, vremenski SoundBinding, SongMap fraze i GroovePlan full-duration peak. Svaka od 16 originalnih solo nota dobiva immutable `sourceNoteUid`; referentni plan predlaže 83 odvojene grace/trill/turnaround/third/echo preview note i 16 Factory-bounded, zaglađenih CC11 točaka. Slide putanja je zasebno dokazana, svi note slojevi imaju register/harmony/collision/timing gate, a A/B/C procjene ostaju do 20/54. Echo je nerekurzivan, koristi zaseban siguran Delay track i nikada 17. traku. A/B preview i `REMOVE_AI_EXPRESSION_LAYER` uklanjaju samo AI događaje te zadržavaju isti originalni fingerprint i SoundBinding. Ugrađeni relationship corpus namjerno je označen `SOFTWARE_TEST_ONLY`; zato je preview spreman, ali produkcijski MIDI render ostaje blokiran do autoritativnog evidence corpusa, slušnog testa i po potrebi Session 16 uređajnog dokaza. Dokazi su `data/session24-test-report.json`, `data/session24-benchmark-report.json`, `data/session24-schema-catalog.json`, `artifacts/session24-expression-plan.json` i `artifacts/session24-remove-ai-layer.json`. Status je `SOFTWARE_VALIDATED_PREVIEW / PRODUCTION_EVIDENCE_BLOCKED`.

### Sesija 25 — Potvrđene Guitar/RX/DNC articulation mape — ZAVRŠENO U SOFTWARE OPSEGU / DEVICE BLOCKED

**Cilj:** pretvoriti uređajne artikulacije iz eksperimentalnih u podatkovno upravljane Premium funkcije.

**Isporuke:**

- capture alat za bilježenje stvarnog Bank/Program/trigger ponašanja;
- verzionirane mape s uređajem, OS-om, izvorom, datumom i dokaznim hashom;
- playable/trigger range i collision provjera;
- standardni key-switch, CC i pressure događaji; proprietary SysEx ostaje blokiran bez potvrde;
- mapa kompatibilnosti po Soundu, ne po približnom nazivu;
- GUI oznake `CONFIRMED`, `UNKNOWN`, `BLOCKED`.

**Gate:** nepoznat zvuk daje `KEEP` ili `MANUAL_REVIEW`; nikada automatski „najbliži” trigger.

**Rezultat:** 88/88 PASS. `ArticulationMap 2.0` i zasebni capture ugovor strogo vode `CONFIRMED`, `UNKNOWN` i `BLOCKED` zapise za Guitar, RX i DNC. Svaka mapa je vezana uz točan CC00/CC32/Program, ulogu, playable raspon i odvojeni trigger raspon; podržani su samo standardni key-switch, CC i channel-pressure događaji. Key-switch zahtijeva pozitivan note-off, Bank/RPN/NRPN kontroleri, proprietary SysEx, duplicirani triggeri, playable kolizije i približno/„najbliže” mapiranje su blokirani. Read-only `ArticulationPlan 2.0` veže svaki događaj uz fizički `trackUid`, `sourceNoteUid`, evidence ID i reason code te koristi veći GroovePlan/ExpressionPlan peak prije 54-note provjere. Referentne tri mape imaju 9 zapisa i generiraju 11 sigurnih preview događaja uz maksimum 19/54, ali nose autoritet `SOFTWARE_TEST_ONLY`; čak ih ni ručno dodavanje njihova hasha ne može promovirati. Produkcijski status zahtijeva `DEVICE_CAPTURED`, potvrđen hardware, audio/slikovne hashove i zaseban operator-approved capture hash. Dokazi su `data/session25-test-report.json`, `data/session25-benchmark-report.json`, `data/session25-schema-catalog.json`, `artifacts/session25-articulation-map.json` i tri engine plana. Status je `SOFTWARE_VALIDATED / DEVICE_CAPTURE_BLOCKED`.

### Sesija 26 — Premium Preview i audio kontrola

**Cilj:** omogućiti korisniku pouzdaniju A/B odluku prije izvoza.

**Isporuke:**

- brzi lokalni MIDI preview s boljim GM/Pa800 mapiranjem;
- opcionalni SoundFont ili vanjski render adapter koji ne utječe na MIDI verdict;
- sinkronizirani A/B/C transport, loop sekcije i loudness-matched preview;
- solo/mute po ulozi i prikaz aktivne polifonije;
- uređajni capture import za usporedbu Pa800 snimke s previewom;
- jasno upozorenje da preview nije Pa800 certifikat.

**Gate:** promjena preview profila ne mijenja finalni MIDI hash ni validator rezultat.

**Rezultat:** 96/96 PASS. `PreviewSession 2.0` veže provjereni MIDI i immutable validator identitet uz jedan sinkronizirani A/B/C clock, section loop, role solo/mute, aktivne note te full-duration peak po ulozi, fizičkoj traci, kanalu i `trackUid`-u. A je verificirani baseline, B dodaje expression bez echa, a C puni expression i articulation audit; svaka nota prikazuje SoundBinding i izvor sloja. Ugrađeni GM/Pa800 proxy WAV je deterministički 16-bit PCM, koristi jasno označen MIDI-energy RMS proxy i nikada ne predstavlja uređajni zvuk. SoundFont/vanjski renderer postoji samo kao hashirani manifest bez putanje ili automatskog izvršavanja. Pa800 WAV capture može se uvesti i usporediti po trajanju i RMS-u, ali uvijek nosi `DEVICE_AUDIO_COMPARISON_ONLY`, `certificationAllowed=false`; Session 16 ostaje jedini uređajni autoritet. Promjena profila, glasnoće, targeta, loopa ili role-mixa mijenja samo preview hash, dok MIDI SHA-256 i validator identity ostaju jednaki. Dokazi su `data/session26-test-report.json`, `data/session26-benchmark-report.json`, `data/session26-schema-catalog.json`, `artifacts/session26-preview-session.json`, deterministički proxy WAV i audio comparison manifest. Status je `SOFTWARE_VALIDATED / DEVICE_AUDIO_COMPARISON_ONLY`.

### Sesija 27 — Music Quality Evaluator i benchmark — ZAVRŠENO U SOFTWARE OPSEGU

**Cilj:** mjeriti napredak glazbenom kvalitetom, a ne samo tehničkim PASS rezultatom.

**Isporuke:**

- automatske metrike za harmoniju, groove, register collision, density curve, transition continuity, repetitivnost i ending resolution;
- slijepi A/B protokol protiv 3.17 baselinea;
- ocjene najmanje dva ljudska evaluatora kada je moguće;
- zasebne ocjene Drum, Bass, Guitar, Accompaniment, Solo, Transition i Overall;
- zapis hard faila odvojen od subjektivne ocjene;
- regression set „zvučalo bolje prije” koji blokira izdanje.

**Gate:** medijan Overall ocjene najmanje 4/5, nijedan tehnički neispravan rezultat i najmanje 70% preferencije Premium kandidata nad baselineom na zaključanom benchmarku.

**Rezultat:** 104/104 PASS za software evaluator. `EvaluationReport 2.0` strogo odvaja hard tehnički gate, sedam automatiziranih strukturnih metrika i stvarni slijepi ljudski listening. Referentna C varijanta prolazi tehnički gate i postiže automatizirani rezultat 4,543/5: harmonija 5,000, groove 4,781, register collision 5,000, density curve 3,550, transition continuity 4,250, repetitivnost 3,929 i ending resolution 4,800. Zaključani paket ima dva nasumično označena A/C pokusa vezana uz immutable 3.17 baseline; javni paket ne otkriva identitet varijanti, a privatni ključ ostaje odvojen od GUI-ja. `SOFTWARE_TEST_ONLY` odgovor dokazuje protokol, ali se ne računa kao ljudski dokaz. Zato konačni quality release gate ispravno ostaje `BLOCKED_HUMAN_LISTENING`: trenutačno je 0/2 verificiranih neovisnih evaluatora, nema ljudskog Overall medijana ni dokazane 70% Premium preferencije. Otvoreni zapis „baseline zvučao bolje” blokira izdanje, dok razriješeni zapis ostaje u hashiranom regresijskom vaultu. Evaluator je read-only, ne mijenja MIDI i ne certificira Pa800. Dokazi su `data/session27-test-report.json`, `data/session27-benchmark-report.json`, `data/session27-schema-catalog.json`, `artifacts/session27-evaluation-report.json`, `artifacts/session27-blind-listening-package.json` i odvojeni privatni ključ.

### Sesija 28 — Premium GUI i Producer Workflow — ZAVRŠENO U SOFTWARE OPSEGU

**Cilj:** spojiti sve mogućnosti u brz i razumljiv profesionalni radni tok.

**Isporuke:**

- vođeni proces `Import → Analyze → Brief → Plan → Variants → Edit → Verify → Export`;
- Arrangement Graph timeline s energijom, akordima i prijelazima;
- Track Matrix sa SoundBindingom, rasponom, peak polifonijom i articulation statusom;
- Explain panel: zašto je odluka donesena i što ju blokira;
- globalni i per-element lock;
- diff za note, kontrolere, Sound setup i manifest;
- command palette, tipkovnički prečaci i pristupačne boje;
- background job progress, cancel/resume i recovery.

**Gate:** novi korisnik mora završiti referentni song-to-style zadatak bez terminala; napredni korisnik mora moći reproducirati isti rezultat iz projekta i seeda.

**Rezultat:** 112/112 PASS. `PremiumWorkflow 2.0` povezuje strogo hashirani lanac SongMap → ProducerBrief → ArrangementGraph → CandidateSet → GroovePlan → ExpressionPlan → PreviewSession → EvaluationReport u jedan vođeni radni prostor. Osam faza ima zaseban job/progress status; prvih sedam prolazi, a `EXPORT` je ispravno blokiran stvarnim quality, evidence i device gateovima. Timeline prikazuje svih deset Pa800 elemenata, Track Matrix četiri fizičke trake s `trackUid`/kanalom/SoundBindingom/registrom/full-duration peakom, a Explain panel 52 odabira s izvorom, scoreom, razlogom, lockom i blockerom. Referentni diff ima 118 baseline i 179 preview nota, 61 uklonjivu dodanu notu, 16 CC11 točaka te nula promijenjenih originalnih nota i SoundBindinga. Globalni/per-element lock, deset naredbi i prečaca, pristupačne palete, cancel na `VERIFY`, hashirani checkpoint i siguran resume imaju strojni dokaz. GUI/API/CLI daju isti workflow hash; projekt i preview mogu se preuzeti, ali finalni MIDI nije generiran. Dokazi su `data/session28-test-report.json`, `data/session28-benchmark-report.json`, `data/session28-schema-catalog.json`, `artifacts/session28-premium-workflow.json`, `artifacts/session28-workflow-diff.json` i `artifacts/session28-recovery-checkpoint.json`.

### Sesija 29 — Personal Producer Profile — ZAVRŠENO U SOFTWARE OPSEGU

**Cilj:** učiti ukus korisnika bez potajnog mijenjanja autoritativnih pravila.

**Isporuke:**

- učenje samo iz izričito prihvaćenih A/B odluka i ručnih lockova;
- lokalni profil preferencija po žanru, gustoći, fillovima, registru i slojevima;
- pregled, uređivanje, export i potpuno brisanje profila;
- profil utječe samo na ranking, nikada na hard validator ili Factory dinamiku;
- cold-start preset bez osobnih podataka;
- test da brisanje profila vraća neutralni deterministički rezultat.

**Gate:** korisnik može objasniti i poništiti svaku naučenu preferenciju; nema skrivenog slanja MIDI-ja ili projekta.

**Rezultat:** 120/120 PASS. `PersonalProducerProfile 2.0` uči isključivo iz izričito prihvaćene A/B/C odluke i ručnog locka; preslušavanje, pozicija previewa, odbijanje, hover, implicitno ponašanje, MIDI sadržaj i cloud telemetrija odbijeni su kao izvori. Referentni profil ima dvije hashirane korisničke odluke, 52 evidence-backed pattern preferencije, sedam uloga, svih deset markera i sedam role-scoped registarskih pojaseva. Ranking overlay obrađuje 52 zahtjeva i 624 kandidata koji su već prošli hard constraints, s ograničenim maksimalnim bonusom 0,063889; svih 829 hard-odbijenih kandidata ostaje netaknuto, bez ponovne procjene ili zaobilaženja hard gatea. Cold start, isključen profil i potpuno brisanje daju isti neutralni redoslijed za svih 52 zahtjeva. Profil se može pregledati, eksplicitno urediti, sanitizirano izvesti i potpuno izbrisati; ne sadrži MIDI, projekt ni audio i nema Factory, SoundBinding, Bank/Program, validator ni MIDI mutation autoritet. CLI, API i GUI koriste isti ugovor. Dokazi su `data/session29-test-report.json`, `data/session29-benchmark-report.json`, `data/session29-schema-catalog.json`, `artifacts/session29-personal-profile.json`, `artifacts/session29-ranking-overlay.json` i `artifacts/session29-profile-deletion.json`.

### Sesija 30 — AI Premium Arranger Release Gate — ZAVRŠENO U SOFTWARE RC OPSEGU

**Cilj:** izdati prvu verziju koja smije nositi naziv AI Premium Arranger.

**Isporuke:**

- migracija starih `.dnaproject.json` projekata;
- clean-machine Windows test bez razvojnog okruženja;
- performance, memory, long-path, Unicode, crash i disk-full testovi;
- potpisani manifest aplikacije, registryja, model/prompt verzije i DeviceProfilea;
- offline install/run/test workflow;
- korisnički vodič, onboarding i recovery postupak;
- jasna matrica što je `SOFTWARE_VALIDATED`, `PA800_DEVICE_CERTIFIED` i samo preview;
- finalni benchmark i poznata ograničenja.

**Gate:** svi P0 kriteriji prolaze, nema otvorenog severity-1/2 defekta, clean-extract suite je zelen i fizički Pa800 profil je certificiran. Bez fizičkog certifikata izdanje se smije zvati `AI PREMIUM ARRANGER PREVIEW`, ali ne finalna Pa800 Premium verzija.

**Rezultat:** 128/128 PASS. `ReleaseReadiness 2.0` objedinjuje nedestruktivnu migraciju projekta, SHA-256 sadržajni manifest, stvarna performance/memory mjerenja, Unicode/long-path provjeru te naslijeđene crash, cancel, disk-full i clean-extract dokaze. Analiza 25.000 nota završava ispod 10 sekundi, globalni plan ispod 5 sekundi, parcijalna regeneracija ispod 2 sekunde, a migracija 10.000 audit/lock stavki ostaje ispod 64 MB. Statusna matrica ima 17 eksplicitnih software, quality, evidence, device, export i marketing gateova bez otvorenog severity-1/2 software defekta. Software izdanje smije nositi samo naziv `AI PREMIUM ARRANGER PREVIEW`; finalni MIDI export i naziv `AI PREMIUM ARRANGER` ostaju blokirani jer je ljudski listening 0/2, produkcijski expression/articulation dokaz nije potvrđen, a Pa800 profil i voice-cost nisu fizički certificirani. Dokazi su `data/session30-test-report.json`, `data/session30-benchmark-report.json`, `data/session30-hardening-report.json`, `data/session30-schema-catalog.json`, `artifacts/session30-software-manifest.json`, `artifacts/session30-release-status-matrix.json` i `artifacts/session30-release-readiness.json`.

## 6. Mjerljivi Premium kriteriji

### Tehnička sigurnost

- 100% prolaz hard validatora za svaki objavljeni MIDI;
- 0 GOLD velocity/bank/program utjecaja;
- 0 promijenjenih originalnih solo nota izvan ručnog edit audita;
- 0 pogrešno mapiranih track/channel/SoundBinding slučajeva u zaključanom adversarial korpusu;
- byte-identičan rezultat za isti ulaz, seed, konfiguraciju i baze;
- 0 djelomičnih output datoteka nakon cancel/crash/disk-full testa.

### Glazbena kvaliteta

- najmanje 70% slijepe preferencije Premium varijante nad 3.17 baselineom;
- medijan najmanje 4/5 za ukupnu koherentnost;
- nijedan automatski odabir s hard harmony ili register collisionom;
- svaki Fill ima deklarirani transition target;
- V1–V4 imaju mjerljiv rast ili namjerno dokumentiranu alternativnu krivulju energije;
- manual-review stopa pada kroz kalibraciju, ali se nikad ne smanjuje skrivanjem nesigurnosti.

### Brzina i ergonomija

- preflight i osnovna analiza tipičnog MIDI-ja do 25.000 nota završavaju unutar 10 sekundi na referentnom računalu;
- generiranje jednog plana unutar 5 sekundi nakon završene analize;
- parcijalna regeneracija jednog elementa unutar 2 sekunde kada registryji ostaju učitani;
- GUI ostaje responzivan, a svaki duži posao ima progress i cancel;
- projekt se nakon rušenja vraća bez gubitka posljednjeg potvrđenog koraka.

## 7. Testna piramida

Za svaku Premium sesiju obavezni su:

- unit testovi za sheme, scoreove, budgete i pretvorbe;
- property testovi za track/channel mapping, note pairing i polifoniju;
- integration testovi za AI brief → planner → engine → verifier;
- E2E testovi kroz GUI, API, CLI i batch;
- corpus regression na stvarnim songovima;
- adversarial testovi protiv lažnih mappinga, skrivenog GOLD autoriteta i prompt-injectiona;
- listening test za funkcije čija se kvaliteta ne može dokazati samo MIDI strukturom;
- fizički device test za sve tvrdnje o Pa800 zvuku, NTT-u, RX/DNC-u i voice stealingu.

## 8. Predloženi release vlak

### 3.17 — Premium Plan Baseline

Završeno: Sesija 15 ima 20/20 PASS, devet ugovora, feature matricu i zamrznuti regresijski baseline. Nema marketinške oznake Premium.

### 3.18 — Track Identity / Solo Safety Foundation

Završeno: Sesija 18 ima 28/28 PASS, vremenski SoundBinding i pipeline-wide zaštitu originalnog sola. Aktivni recovery/Premium suite ima 337/337 PASS. Ovo je sigurnosni temelj za Alpha, ne dovršeni AI Arranger.

### 3.19 — Production Adapter Foundation

Završeno: Sesija 17 ima 35/35 PASS, a objedinjeni recovery/Premium suite 372/372 PASS. Produkcijski drum, bass/riff i Factory-guitar adapteri rade kroz isti dispatcher; solo je Factory-expression-only, dok RX/DNC i Guitar Mode kontrole ostaju uređajno blokirani. Ovo je produkcijska adapterska osnova za Alpha, ne dovršeni AI Arranger.

### 3.20 — Song Understanding 2.0 Foundation

Završeno: Sesija 19 ima 36/36 PASS, a objedinjeni recovery/Premium suite 408/408 PASS. SongMap 2.0 daje determinističku, velocity-blind analizu s uncertainty/manual-review slojem i read-only korekcijama. Zaključani benchmark prelazi zadane F1 pragove, ali šira produkcijska kalibracija još nije završena.

### 3.21 — AI Producer Brief 2.0

Završeno: Sesija 20 ima 52/52 PASS, a objedinjeni recovery/Premium suite 460/460 PASS. Hrvatski/engleski lokalni parser, strogi ugovor, konfliktno odobrenje, prompt-injection zaštita, GUI/API/CLI parity i sigurni opcionalni AI fallback pretvaraju slobodnu namjeru u read-only konfiguraciju bez MIDI, Bank/Program ili validator autoriteta.

### 3.22 — Arrangement Graph 2.0

Završeno: Sesija 21 ima 62/62 PASS, a objedinjeni recovery/Premium suite 522/522 PASS. SongMap i ProducerBrief sada se spajaju u globalni plan svih Pa800 elemenata s energijom, motivom, transition obvezama, lockovima te harmony/register/polyphony budgetima. Dvije do četiri varijante ostaju read-only; runtime pattern selection pripada Sesiji 22.

### 4.0 — AI Arranger Alpha

Završeno u read-only selection opsegu: Sesija 22 ima 68/68 PASS, a objedinjeni recovery/Premium suite 590/590 PASS. Produkcijski CandidateSet 2.0 daje stabilne A/B/C/D selekcije, lock/exclude/next, relationship/diversity ranking i parcijalnu regeneraciju. Status ostaje `ALPHA` jer CandidateSet još nije finalni MIDI render, quality/listening benchmark i uređajni dokaz nisu završeni.

### 4.1 — Groove/Polyphony Alpha

Završeno: Sesija 23 ima 70/70 PASS, a objedinjeni recovery/Premium suite 660/660 PASS. GroovePlan 2.0 dodaje dokazni microtiming/gate sloj, full-duration peak po traci/kanalu/markeru i 54-note simplification gate. Pa800 oscillator/voice cost ostaje `UNCONFIRMED`, a finalni MIDI render još nije dopušten.

### 4.2 — Solo/Expression Preview Alpha

Završeno: Sesija 24 ima 80/80 PASS, a objedinjeni recovery/Premium suite 740/740 PASS. ExpressionPlan 2.0 daje phrase-aware, evidence-gated i potpuno uklonjive A/B solo slojeve uz Factory dinamiku/CC11, immutable originalni fingerprint i GroovePlan 54-note budget. Produkcijski ornament corpus, listening gate i finalni MIDI render još nisu potvrđeni.

### 4.3 — Articulation Mapping Alpha

Završeno u software opsegu: Sesija 25 ima 88/88 PASS, a objedinjeni recovery/Premium suite 828/828 PASS. Strogi capture/import, exact SoundBinding, `CONFIRMED/UNKNOWN/BLOCKED`, standardni key-switch/CC/pressure, note-off, deduplikacija i Groove/Expression 54-note gate rade kroz CLI/API/GUI. Referentne Guitar/RX/DNC mape su samo `SOFTWARE_TEST_ONLY`; produkcijska aktivacija ostaje `DEVICE_CAPTURE_BLOCKED` do fizičkog Pa800 dokaza i operator-approved hasha.

### 4.4 — Premium Preview Alpha

Završeno: Sesija 26 ima 96/96 PASS, a objedinjeni recovery/Premium suite 924/924 PASS. Sinkronizirani A/B/C transport, section loop, role solo/mute, aktivna polifonija, deterministički GM/Pa800 proxy WAV, loudness-matched usporedba i Pa800 capture import rade bez promjene MIDI-ja, rankinga ili validator identiteta. Uređajni audio je samo usporedni dokaz; nije certifikat.

### 4.5 — Music Quality Alpha

Završeno u software opsegu: Sesija 27 ima 104/104 PASS, a objedinjeni recovery/Premium suite 1028/1028 PASS. Sedam automatiziranih metrika, immutable 3.17 baseline, blind A/B paket, odvojeni privatni ključ, dvostruki ljudski evidence gate i regresijski vault rade kroz CLI/API/GUI. Automatizirani rezultat je 4,543/5 bez hard faila, ali release quality gate ostaje `HUMAN_LISTENING_PENDING` s 0/2 stvarna evaluatora; proxy i testni odgovori ne mogu ga zadovoljiti.

### 4.6 — Premium Producer Workflow Alpha

Završeno u software opsegu: Sesija 28 ima 112/112 PASS, a objedinjeni recovery/Premium suite 1140/1140 PASS. Jedan GUI povezuje osam faza, deset Pa800 timeline elemenata, Track Matrix, 52 explain odluke, note/controller/Sound diff, lockove, command palette i siguran cancel/resume. Referentni zadatak završava bez terminala i reproducira isti workflow hash iz projekta i seeda. Finalni MIDI export ostaje blokiran dok Session 27 nema stvarni listening PASS, Session 24 produkcijski evidence i Session 16 fizički Pa800 certifikat.

### 4.7 — Personal Producer Profile Alpha

Završeno u software opsegu: Sesija 29 ima 120/120 PASS, a objedinjeni recovery/Premium suite 1260/1260 PASS. Lokalni profil uči samo iz izričito prihvaćenih varijanti i ručnih lockova, daje objašnjiv i ograničen soft-ranking bonus samo hard-pass kandidatima te podržava pregled, uređivanje, export i potpuno brisanje. Cold start, disable i delete vraćaju isti neutralni deterministički redoslijed. Profil nema MIDI, Factory, SoundBinding, Bank/Program, validator ni uređajni autoritet.

### 4.8 — AI Premium Arranger Preview Release Candidate

Završeno u software RC opsegu: Sesija 30 ima 128/128 PASS, a objedinjeni recovery/Premium suite 1388/1388 PASS. Nedestruktivna migracija, sadržajni manifest, performance/memory/path/rollback hardening, statusna matrica i GUI/API/CLI readiness pregled prolaze. Dopušten je naziv `AI PREMIUM ARRANGER PREVIEW`; finalni export i naziv bez oznake Preview ostaju blokirani vanjskim listening, produkcijskim evidence i fizičkim Pa800 gateovima.

### 4.9 — Automatic Analysis Foundation

Završena Faza 1: Sesija 31A ima 136/136 PASS, a objedinjeni recovery/Premium/Analysis suite 1524/1524 PASS. Automatska analiza sada prikazuje fizičke trake, vremenski SoundBinding, exact Factory instrument, GM obitelj kao neautoritativni hint, ulogu, registar, gustoću i polifoniju. Shared channel, nepotpun mapping i nedostajući profil ostaju fail-closed. Ovo je read-only temelj za puni optimizer i EvidenceLedger; finalni MIDI export nije otključan.

### 4.9.1 — Evidence Authority Foundation

Završena Faza 2: Sesija 31B ima 144/144 PASS, a objedinjeni recovery/Premium/Analysis/Evidence suite 1668/1668 PASS. `EvidenceLedger 3.0` sadržajno veže provjerene produkcijske Factory velocity, GOLD performance i Factory strumming registryje te sedam planerskih dokumenata uz 1.657 jednoznačnih odluka. Varijanta C ima 52 autorizirana pattern odabira i 1.490 timing-only Groove događaja; 83 `SOFTWARE_TEST_ONLY` expression događaja i 11 uređajno nepotvrđenih articulation događaja automatski se preskaču, dok 16 Factory-bounded CC11 točaka prolazi. Pokrivenost eksplicitnim hash-lancem iznosi 100\%, bez implicitnog fallbacka i bez MIDI mutation, renderer, validator ili export autoriteta.

### 4.9.2 — TrackPlan / Full Optimizer Foundation

Završena Faza 3: Sesija 32 ima 152/152 PASS, a objedinjeni recovery/Premium/Analysis/Evidence/TrackPlan suite 1820/1820 PASS. `TrackPlan 3.0` daje pet source-track planova i 52 marker-role ugovora; svih 52 arrangerska fragmenta imaju exact Factory SoundBinding i odluku `REPLACE`, uz ukupno 249 budžetiranih operacija. Jedna izvorna drum traka ostaje `MANUAL_REVIEW` jer nema potpun Factory dokaz. Dry-run piše 0 MIDI bajtova, ne mijenja originalni solo, GOLD dinamiku ni Bank/Program te ostavlja finalni export blokiranim do Sesije 33.

### 4.9.3 — Deterministic Arrangement Renderer Foundation

Završena Faza 4: Sesija 33 ima 160/160 PASS, a objedinjeni recovery/Premium/Analysis/Evidence/TrackPlan/Renderer suite 1980/1980 PASS. `Arrangement Renderer 2.0` pretvara 52 hash-podudarna fragmenta u stvarni SMF0/PPQ480 MIDI s deset Pa800 markera, 1.400 nota i kanalima 9–15. GOLD ostaje ograničen na timing, gate i relativni pitch; velocity i CC7 dolaze samo iz exact Factory profila, dok je CC11=127 zadržan kao postojeći Pa800 Style initialization ugovor. Neovisni byte-parser i Pa800 hard validator potvrđuju vrh 14/54, marker-scoped SoundBinding, note pairing, registre, Factory velocity granice i identičan CLI/API/GUI/batch hash. Atomic publish uklanja `.tmp`/lock ostatke, a uređajno nepotvrđenih 83 expression i 11 articulation događaja ne ulaze u MIDI. Dopušten je software preview MIDI, ali finalni certificirani export ostaje blokiran.

### 4.10 — Global Coherence Foundation

Završena Faza 5: Sesija 34 ima 168/168 PASS. Tri A/B/C preview MIDI varijante imaju ostvarene Fill bass targete, Ending root rezolucije, collision-safe voice leading i motivsku konturu bez dodavanja nota ili promjene timing/velocity/kontrolera. Sve ostaju na 1.400 nota i vrhu 14/54.

### 4.10.1 — Song-to-Style End-to-End Workflow Foundation

Završena Faza 6: Sesija 35 ima 176/176 PASS, a objedinjeni suite 2324/2324 PASS. `SongToStyleProject 1.0` povezuje deset faza `IMPORT → ANALYZE → BRIEF → PLAN → SELECT → RENDER → COHERE → VERIFY → PREVIEW → PUBLISH`. Benchmark daje 50/50 dovršenih projekata, nula neobrađenih iznimki, downstream-only invalidaciju, checkpoint/resume, undo/redo i batch izolaciju. Parcijalna regeneracija mijenja samo dva autorizirana eventa u `v1cv1:guitar`, dok sve izvan fragmenta ostaje nepromijenjeno. Publication tier ostaje `PREVIEW_ONLY`.

### 4.10.2 — Zero-Silent-Failure Reliability Foundation

Završena Faza 7: Sesija 36 ima 184/184 PASS, a objedinjeni suite 2508/2508 PASS. Reliability gate zaključava 24 malformirana MIDI slučaja, 200 sealed-byte mutacija, sedam atomskih kvarova i clean-extract version guard u vault od 232 regresije. Otkrivena i zatvorena parser-rupa za format-1 MIDI s nula traka sada uvijek fail-closed blokira ulaz. Disk-full, read-only, cancel, crash nakon privremenog zapisa, verifier exception, validator block i output lock ostavljaju nula partial ili `.tmp` datoteka. Worker 1/2/4 rezultat je byte-identičan; 25.000 nota ostaje ispod jedne sekunde i oko 18 MB peak memorije, a 100.000 nota ispod četiri sekunde i oko 73 MB. Dopušten je samo `AI PREMIUM ARRANGER PREVIEW`.

### 4.11 — Quality Calibration Foundation

Završena software Faza 8: Sesija 37 ima 192/192 PASS, a objedinjeni suite 2700/2700 PASS. Zaključani self-authored corpus ima 32 MIDI slučaja: 24 TRAIN i osam HOLDOUT, bez preklapanja i s pokrivenošću sedam žanrovskih oznaka, taktova 3/4, 4/4 i 6/8 te LOW/MEDIUM/HIGH gustoće. Strukturni normalizer smije čitati samo TRAIN oznake; kalibracija se hashira prije otvaranja holdouta. Bez stvarnih ljudskih ocjena ne mijenjaju se težine sedam metrika ni pragovi 4/5 i 70\%. Testni expression ili evaluator bundle nikada nije produkcijski eligible. Quality gate zato ostaje `BLOCKED_EXTERNAL_EVIDENCE` s 0/2 evaluatora i statusom `AWAITING_OPERATOR_CAPTURE`.

### 4.11.1 — Device Certification Intake Foundation

Završena software Faza 9: Sesija 38 ima 200/200 PASS, a objedinjeni suite 2900/2900 PASS. Strogi `Pa800DeviceCapture 2.0`, `DeviceProfile 2.0` i `DeviceCertificationReport 2.0` pokrivaju osam kanala 9–16, deset markera, svih 17 fizičkih provjera iz Sessiona 14, exact Bank/Program i Track Type/NTT vezanja, Guitar/RX/DNC status, osam mjerenja voice costa te hashirane slikovne i audio dokaze. Putanje, file magic, operator approval, capture hash i neovisni review provjeravaju se fail-closed. Objavljeni predložak i profil namjerno ostaju `WAITING_FOR_DEVICE`; software dokaz ne dodjeljuje `PA800_DEVICE_CERTIFIED` i ne otključava finalni MIDI export.

### 4.5 — Premium Device Beta — UVJETNO

Sesija 16 nad dovršenom software polifonijskom, expression, articulation i preview osnovom Sesija 23–26: Pa800 mapping/certifikacija, stvarni audio i aktivacija potvrđenih uređajnih mapa. Ako fizički test nije završen, naziv ostaje `DEVICE BETA`.

### 5.0 — AI Premium Arranger

Software dio Sesije 30 je završen, ali naziv 5.0 dopušten je tek kada svi P0 kriteriji, ljudski listening pragovi, produkcijski expression/articulation dokaz i fizički Pa800 profil prođu.

## 9. Procjena opsega

Procjena je izražena u fokusiranim razvojnim sesijama, ne kalendarskim obećanjima:

| Radni paket | Procjena | Glavna ovisnost |
|---|---:|---|
| Baseline, sheme i benchmark | 2–3 sesije | postojeći 3.16 artefakti |
| Pa800 mapping i certifikacija | 2–4 sesije | fizički uređaj i operator |
| Production adapter + Mapping 2.0 | 4–6 sesija | produkcijski corpus |
| Song Understanding + AI Brief | 4–6 sesija | označeni testni songovi |
| Arrangement Graph + candidate search | 5–7 sesija | prethodne dvije cjeline |
| Groove, solo i articulation | 4–6 sesija | potvrđene uređajne mape |
| Preview, evaluator i Premium GUI | 5–8 sesija | stabilan engine |
| Personalizacija i release hardening | 3–5 sesija | zaključan benchmark |

Ukupno: približno 29–45 fokusiranih sesija, uz fizički uređaj dostupan u ranoj fazi. Nedostupnost Pa800 uređaja ne blokira AI Alpha rad, ali blokira konačnu Pa800 Premium oznaku.

## 10. Kritični redoslijed

```text
15 Baseline
   |
   +--> 16 Pa800 Mapping ---------------------------+
   |                                                |
   +--> 17 Production Adapter --> 18 Mapping 2.0    |
                              |                     |
                              v                     |
                      19 Song Understanding         |
                              |                     |
                              v                     |
                         20 AI Brief                |
                              |                     |
                              v                     |
                     21 Arrangement Graph           |
                              |                     |
                              v                     |
                     22 Candidate/Variants          |
                              |                     |
                    +---------+---------+            |
                    v                   v            |
              23 Groove/Polyphony  24 Solo/Expression
                    |                   |            |
                    +---------+---------+------------+
                              v
                      25 Articulation Maps
                              |
                              v
                       26 Premium Preview
                              |
                              v
                       27 Quality Benchmark
                              |
                              v
                         28 Premium GUI
                              |
                              v
                       29 Personal Profile
                              |
                              v
                         30 Release Gate
```

## 11. Ubrzani cilj: funkcionalan Arranger bez slabljenja dokaza

Nakon 4.8 Preview Release Candidatea prioritet se mijenja s izgradnje novih read-only planova na jedan pouzdan, evidence-driven produkcijski tok. Cilj nije obećati da software nikada neće imati defekt, nego postići mjerljivo stanje bez poznatog severity-1/2 defekta, bez neobrađene iznimke na zaključanom korpusu i bez objave rezultata koji nije prošao neovisni verifier.

Uvode se dvije jasno odvojene razine rezultata:

1. `SOFTWARE_VALIDATED_ARRANGER_MIDI` — deterministički MIDI koji koristi samo software-potvrđene autoritete, prolazi hard validator i jasno navodi da nije fizički Pa800 certifikat;
2. `PA800_DEVICE_CERTIFIED_MIDI` — isti sigurnosni lanac uz dodatno potvrđen DeviceProfile, articulation capture, listening i fizički import/save/reload dokaz.

Nepotvrđeni uređajni podaci više ne smiju blokirati cijeli osnovni Arranger. Oni blokiraju samo pripadajuću funkciju: nepoznat RX/DNC/Guitar Mode trigger znači `KEEP` ili uklanjanje tog AI sloja, dok dokazani Factory/GOLD, mapping, harmony, groove i validator tok nastavlja raditi. Finalna oznaka `AI PREMIUM ARRANGER` i dalje ostaje rezervirana za puni uređajni i ljudski gate.

## 12. Kako Arranger mora koristiti sve postojeće dokaze

„Koristiti sve dokaze” ne znači primijeniti svaki pronađeni događaj. Pozitivan dokaz daje ograničeni autoritet, negativan ili nepotpun dokaz određuje što se mora preskočiti, zadržati ili poslati u `MANUAL_REVIEW`.

| Sloj dokaza | Dokazani autoritet u Arrangeru | Sigurno ponašanje bez dokaza |
|---|---|---|
| Factory velocity profili | velocity, potvrđeni CC11 i mixer granice | `MANUAL_REVIEW`; nema izmišljene dinamike |
| GOLD performance patterni | ritam, relativni pitch, gate, fraziranje i potvrđene veze | kandidat se odbija; nema velocity/Bank/Program utjecaja |
| Factory Style/strumming | gitarski ritam, smjer udara i potvrđena voicing struktura | gitara ostaje `KEEP`; GOLD ne preuzima Guitar Mode |
| Track Identity i SoundBinding | točan fizički `trackUid`, kanal, CC00/CC32/Program i vremenski scope | mutacija trake se blokira prije rendera |
| Automatic Track Instrument Analysis 3.0 | segmentirani exact Factory identitet, GM obitelj kao hint, detektirana uloga, statistike i preporučena Pa800 traka | shared channel, nepotpun SoundBinding ili nedostajući profil daju `MANUAL_REVIEW` |
| SongMap 2.0 | tempo, takt, tonalitet, akordi, sekcije, fraze, uloge i uncertainty | niska sigurnost vodi u `MANUAL_REVIEW` |
| ProducerBrief 2.0 | korisnička namjera, energija, gustoća, uloge, lockovi i tolerancija promjene | konflikt mora potvrditi korisnik |
| ArrangementGraph 2.0 | globalna forma, rast V1–V4, motiv, Fill targeti i ending obveze | nema lokalnog pattern izbora bez globalnog plana |
| CandidateSet 2.0 | hard-pass kandidati, score, alternative, lock/exclude/next i diversity | nema kandidata znači `KEEP` ili ručni odabir |
| GroovePlan 2.0 | bounded microtiming/gate i full-duration 54-note budget | timing ostaje izvorni; nema GOLD dinamike |
| ExpressionPlan 2.0 | immutable solo, Factory CC11 i samo evidence-backed uklonjivi slojevi | test-only ornamenti se ne renderiraju produkcijski |
| ArticulationMap 2.0 | samo exact-sound `DEVICE_CAPTURED` triggeri | `UNKNOWN/BLOCKED` zapis ne emitira događaj |
| Preview i EvaluationReport | A/B usporedba, tehničke metrike i regresijski signal | ne mijenjaju MIDI hash ni validator verdict |
| PersonalProducerProfile | ograničen soft-ranking već valjanih kandidata | cold start ili delete vraća neutralni ranking |
| Independent Verifier i transaction journal | konačni autoritet za objavu, rollback i reproducibility | svaki fail blokira download i čuva original |

Svaka finalna nota, kontroler, program, marker i transformacija mora imati `evidenceId`, `authorityClass`, `reasonCode`, `confidence`, `budgetCost` i rezultat verifiera. Neiskorišten dokaz mora imati razlog `NOT_APPLICABLE`, `LOW_CONFIDENCE`, `DEVICE_BLOCKED`, `CONFLICT`, `BUDGET_EXCEEDED` ili `USER_LOCKED`.

## 13. Ubrzani razvojni roadmap 4.9–5.0

### Sesija 31A — Automatic Song/Track Analysis i Instrument Detector 3.0 — FAZA 1 ZAVRŠENA

**Cilj:** zamijeniti agregatno program/register nagađanje vremenski segmentiranom, evidence-first analizom svake fizičke MIDI trake.

**Isporuke:**

- strogi `AutomaticTrackInstrumentAnalysis 3.0` ugovor, `analysisHash` i velocity-neovisan `decisionHash`;
- stabilni fizički `trackUid`, odvojeni Track/Channel indeksi i brojevi te track-local CC00/CC32/Program state;
- zaseban segment za svaku promjenu zvuka usred pjesme;
- exact Factory profil, instrument, uloga, registar, note count, gustoća, trajanje i full-duration peak za sigurne segmente;
- GM obitelj, track-name i register analiza samo kao objašnjivi hint bez mutation autoriteta;
- fail-closed `MANUAL_REVIEW` za shared channel, nepotpun Bank/Program, nedostajući ili parcijalni Factory profil;
- `FACTORY_BOUNDED_SAFE`, `ANALYSIS_ONLY_MANUAL_REVIEW` i `KEEP_METADATA` politike kao ulaz budućem TrackPlanu;
- CLI `session31_track_analysis.py`, API `/api/automatic-track-analysis` i GUI Track Instrument Matrix.

**Gate:** detekcija ne čita velocity, ne koristi GOLD, ne mijenja MIDI i ne prihvaća approximate SoundBinding; promjena samo velocityja daje isti `decisionHash`.

**Rezultat:** 136/136 PASS. Referentni MIDI ima šest fizičkih traka, pet notnih traka i šest vremenskih SoundBinding segmenata; svih pet exact-evidence traka prolazi, a promjena gitarskog programa usred pjesme stvara dva zasebna instrument segmenta. Property sweep nad 12 velocity vrijednosti daje isti `decisionHash`. Shared-channel fixture ispravno blokira obje konfliktne trake, a izostanak Factory registryja pretvara sve GM rezultate u `MANUAL_REVIEW`. Produkcijski registry od 1.964 profila uključen je u benchmark, ali njegov nedostatak dokaza ne nadomješta se najbližim zvukom. Dokazi su `data/session31-test-report.json`, `data/session31-benchmark-report.json`, `data/session31-schema-catalog.json`, `artifacts/session31-track-instrument-analysis.json` i `artifacts/session31-application-optimization-baseline.json`.

### Sesija 31B — Evidence Authority Resolver 3.0 — FAZA 2 ZAVRŠENA

**Cilj:** spojiti sve postojeće registre i ugovore u jedan strojno provjerljiv autoritativni sloj.

**Isporuke:**

- `EvidenceLedger` sa svim Factory, GOLD, SongMap, brief, graph, candidate, groove, expression, articulation, profile i device dokazima;
- `AuthorityDecision` za svaki planirani događaj: `ALLOW`, `KEEP`, `SKIP`, `MANUAL_REVIEW` ili `BLOCK`;
- stroga zabrana konfliktnog autoriteta, primjerice GOLD velocityja ili approximate SoundBindinga;
- coverage izvještaj koji pokazuje iskorištene, odbijene i nedostajuće dokaze;
- cache po evidence hashu kako se veliki registryji ne bi ponovno skenirali za svaku varijantu;
- CLI/API/GUI pregled „Zašto je dopušteno?” i „Zašto je preskočeno?”.

**Gate:** 100% planiranih događaja ima jednoznačnu odluku i evidence lanac; nula implicitnih fallbackova; isti ulazi daju isti `EvidenceLedger` hash.

**Rezultat:** 144/144 PASS. Resolver provjerava hash produkcijskih Factory velocity, GOLD performance i Factory strumming registryja, indeksira sedam aktivnih dokumenata te izdaje 1.657 `AuthorityDecision` zapisa. Svih 52 odabrana patterna i 1.490 Groove događaja imaju dopušten, ograničen autoritet; tri nesigurna Track Instrument segmenta ostaju `MANUAL_REVIEW`, a exact solo profil dobiva `ALLOW`. Svih 83 testnih expression događaja i 11 nepotvrđenih Guitar/RX/DNC triggera dobivaju `SKIP`, dok 16 exact Factory CC11 točaka dobiva `ALLOW`. Sadržajni cache ne mijenja `ledgerHash`; CLI, API i GUI adapter daju isti rezultat. Dokazi su `data/session31b-test-report.json`, `data/session31b-benchmark-report.json`, `data/session31b-schema-catalog.json` i `artifacts/session31b-evidence-ledger.json`.

### Sesija 32 — TrackPlan 3.0 i Safe Render Contract — FAZA 3 ZAVRŠENA

**Cilj:** prije pisanja MIDI-ja zaključati što se na svakoj traci i sekciji smije promijeniti.

**Isporuke:**

- odluka `KEEP`, `REPAIR`, `REPLACE` ili `MANUAL_REVIEW` za svaku kombinaciju marker × `trackUid` × uloga;
- zasebni budget za note, timing, gate, CC11, articulation i SoundBinding;
- eksplicitni output tier `SOFTWARE_VALIDATED_ARRANGER_MIDI` ili `PA800_DEVICE_CERTIFIED_MIDI`;
- zabrana rendera ako se TrackPlan, EvidenceLedger, CandidateSet ili SoundBinding hash ne podudaraju;
- lock propagation kroz plan, parcijalnu regeneraciju, render i verifier;
- read-only dry-run diff prije svake mutacije.

**Gate:** nijedna MIDI promjena ne postoji izvan odobrenog TrackPlana; svi uređajno nepotvrđeni slojevi uklanjaju se bez utjecaja na dokazani core aranžman.

**Rezultat:** 152/152 PASS. Implementirani su strogi `TrackPlan 3.0`, `OptimizerOperation 1.0` i `OptimizerDryRun 1.0`, hash-chain `source → analysis → ledger → TrackPlan`, exact Factory binding za 52 marker-role fragmenta, source-track `KEEP/REPAIR/MANUAL_REVIEW`, lock propagation i downstream-only invalidacija. Referentni plan ima pet source-track planova, 52 `REPLACE` fragmenta i 249 operacija: pattern replacement, timing/gate, Factory dynamics/mixer, register provjeru, CC11 i 54-note polifonijski gate. Dry-run generira 0 MIDI bajtova i čuva originalni solo. Dokazi su `data/session32-test-report.json`, `data/session32-benchmark-report.json`, `data/session32-schema-catalog.json`, `artifacts/session32-track-plan.json` i `artifacts/session32-optimizer-dry-run.json`.

### Sesija 33 — Deterministički Arrangement Renderer 2.0 — FAZA 4 FOUNDATION ZAVRŠENA

**Cilj:** pretvoriti dokazani plan u stvarni SMF0 MIDI bez gubitka postojećih sigurnosnih pravila.

**Isporuke:**

- render CandidateSet ritma i relativnog pitcha uz isključivo Factory velocity;
- primjena GroovePlana samo na onset/gate u dopuštenom budgetu;
- exact SoundBinding na kanalima 9–16 i svi obavezni CC00/CC32/Program/CC11 događaji;
- očuvanje originalnog solo fingerprinta i render samo produkcijski dopuštenih AI slojeva;
- marker ugovor za Intro, V1–V4, Fill i Ending uz PPQ 480 i SMF0;
- neovisni byte-level verifier, atomic publish i potpuno uklanjanje `.tmp`/partial rezultata;
- identičan output kroz CLI, API, GUI i batch.

**Gate:** najmanje 20 stvarnih legalnih songova daje byte-identičan rezultat za isti seed; 100% objavljenih kandidata prolazi hard validator; nula promijenjenih originalnih solo nota i nula GOLD dinamike.

**Rezultat:** 160/160 PASS. Renderer prihvaća samo hash-podudarni `TrackPlan 3.0`, `EvidenceLedger 3.0`, CandidateSet, GroovePlan i Factory registry. Referentnih 52 marker-role fragmenta daju jedan SMF0/PPQ480 Style-import MIDI s deset markera, sedam aktivnih logičkih traka, 1.400 nota i globalnim vrhom 14/54. Vremenski SoundBinding dopušta točne promjene Bank/Programa po markeru bez promjene fizičkog `trackUid`/kanala. Per-channel Pa800 limit deterministički skraćuje 70 repova i uklanja 90 prekobrojnih nota, što je zapisano u manifestu i ponovno provjereno iz MIDI bajtova. GOLD nema velocity, mixer ni Bank/Program autoritet; Factory profili određuju sve note velocityje i CC7, a obavezni CC11=127 dolazi iz postojećeg Pa800 import ugovora. Neovisni verifier potvrđuje marker setup, fragment output hash, note pairing, registre, Factory velocity granice, polifoniju i izvorni MIDI hash. CLI, API, GUI adapter i batch daju isti SHA-256 `80462ef34beebb69f048c9de187586ba954b0ded2b69ed0f131922d9278dac27`; atomic writer potvrđuje commit/resume/cancel bez partial outputa. Dokazi su `data/session33-test-report.json`, `data/session33-benchmark-report.json`, `data/session33-schema-catalog.json`, `artifacts/session33-render-manifest.json`, `artifacts/session33-render-verification.json` i `artifacts/session33-publish/session33-arranger-preview_OPT.mid`. Status je `SOFTWARE_VALIDATED / ARRANGER PREVIEW MIDI`; širi 20-song produkcijski render/corpus gate, ljudski listening i Pa800 certifikacija ostaju otvoreni.

### Sesija 34 — Global Coherence i Transition Renderer — FAZA 5 FOUNDATION ZAVRŠENA

**Cilj:** osigurati da rezultat zvuči kao jedan aranžman, a ne kao skup nepovezanih patterna.

**Isporuke:**

- motivska veza između Introa, Variationa, Fillova i Endinga;
- mjerljiva V1–V4 krivulja energije, gustoće i registra;
- Fill target realizacija: pickup, crash, bass approach i harmonic anticipation;
- ending cadence i kontrolirano zatvaranje sustain repova;
- collision-aware voice leading između susjednih elemenata;
- globalni simplification koji prvo uklanja ukrase, zatim support, ali nikad core drums/bass/solo ili lock;
- A/B/C renderer varijante s objašnjivom razlikom, ne samo drugim seedom.

**Gate:** svaki Fill ima ostvareni target, svaki Ending potvrđenu rezoluciju, nema hard harmony/register collisiona i sve varijante ostaju unutar 54-note software ceilinga.

**Rezultat:** 168/168 PASS. A/B/C varijante ostaju na 1.400 nota i 14/54, ostvaruju oba Fill targeta i obje Ending rezolucije te ne mijenjaju timing, trajanje, velocity, kontrolere, programe ili markere. Neispravna revoicing kolizija blokira se prije zapisa.

### Sesija 35 — Song-to-Style End-to-End Arranger — FAZA 6 FOUNDATION ZAVRŠENA

**Cilj:** spojiti import, analizu, brief, planiranje, izbor, render, preview, edit i provjeru u jedan funkcionalan tok.

**Isporuke:**

- jedan projektni state machine: `IMPORT → ANALYZE → BRIEF → PLAN → SELECT → RENDER → VERIFY → PREVIEW → PUBLISH`;
- automatska invalidacija samo downstream faza čiji se hash promijenio;
- parcijalna regeneracija jednog markera, uloge ili trake bez promjene zaključanih fragmenata;
- undo/redo, cancel/resume i crash recovery za cijeli Arranger, ne samo pojedine module;
- strukturirani error code, korisnička poruka i recovery akcija za svaki očekivani fail;
- GUI koji može završiti standardni zadatak bez terminala;
- batch način koji izolira grešku jedne pjesme i nastavlja ostale.

**Gate:** 50 referentnih projekata prolazi cijeli software tok bez neobrađene iznimke; nakon crasha se vraća posljednji potvrđeni hash; parcijalna regeneracija ne mijenja nijedan izvanjski fragment.

**Rezultat:** 176/176 PASS. Pedeset projekata završava svih deset faza. Hash-chain, downstream invalidacija, lockovi, undo/redo, checkpoint/resume i osam stabilnih fail-closed error kodova rade kroz zajednički core. Parcijalna regeneracija mijenja dva događaja unutar jednog autoriziranog fragmenta uz `outsideFragmentUnchanged=true`. CLI, API, GUI adapter i batch koriste isti projektni model. Dokazi su `data/session35-test-report.json`, `data/session35-benchmark-report.json` i `artifacts/session35-*`.

### Sesija 36 — Zero-Silent-Failure Reliability Gate — FAZA 7 ZAVRŠENA

**Cilj:** ukloniti greške koje mogu dati pogrešan ili djelomičan rezultat bez jasne blokade.

**Isporuke:**

- property/fuzz testovi za parser, evidence resolver, TrackPlan, renderer i verifier;
- oštećeni MIDI, stuck note, running status, SysEx, RPN/NRPN i program-change adversarial korpus;
- shared-channel, SMF0 merge, 16-track granica, disk-full, read-only direktorij, Unicode i long-path testovi;
- višestruki worker, paralelni batch, output lock i race-condition testovi;
- memory/CPU profiliranje za 25.000 i stress 100.000 nota;
- fail-closed pravilo za svaki neočekivani exception;
- regresijski vault za svaki pronađeni defekt prije popravka.

**Gate:** nula neobrađenih iznimki na zaključanom korpusu, nula djelomičnih datoteka, nula tihih fallbackova, nula otvorenih severity-1/2 defekata i byte-identičan rezultat za 1/2/4 workera.

**Rezultat:** 184/184 PASS. Adversarial corpus ima 24 strukturna/note-integrity slučaja, a sealed fuzz mijenja 200 pojedinačnih bajtova i svaki blokira SHA-256 mismatch prije objave. Sedam kontroliranih transakcijskih kvarova ostavlja nula partial, `.tmp` ili lock ostataka; uspješna transakcija sigurno se nastavlja samo uz jednaki identitet i output hash. Batch nakon blokirane stavke nastavlja sljedeću pjesmu, a 1/2/4 worker izvršenja daju isti parcijalni MIDI hash. Zaključane su 232 regresije, uključujući clean-extract version guard, bez otvorenog severity-1/2 defekta. Stress profil mjeri 25.000 i 100.000 nota unutar CPU/memory budgeta. Dokazi su `data/session36-test-report.json`, `data/session36-benchmark-report.json`, `artifacts/session36-reliability-report.json` i `artifacts/session36-regression-vault.json`.

### Sesija 37 — Production Evidence Expansion i Quality Calibration — SOFTWARE FOUNDATION ZAVRŠEN / VANJSKI DOKAZ OTVOREN

**Cilj:** povećati glazbenu kvalitetu stvarnim dokazom, ne popuštanjem sigurnosnih pragova.

**Isporuke:**

- širi legalni corpus različitih žanrova, taktova, gustoća i tonaliteta;
- ručno označeni chord/section/role i transition ground truth;
- potvrđeni production expression relationshipi bez apsolutnog GOLD pitch/velocity autoriteta;
- stvarni blind listening paket s najmanje dva neovisna evaluatora;
- per-role ocjene za drums, bass, guitar, accompaniment, solo, transition i overall;
- regresijski skup za slučajeve „baseline je zvučao bolje”;
- kalibracija scorea samo na trening dijelu uz zaključan holdout.

**Gate:** medijan Overall najmanje 4/5, najmanje 70% Premium preferencije, bez pada hard-safety metrika i bez naknadnog mijenjanja benchmark uzoraka.

**Rezultat:** 192/192 PASS u software opsegu. Korpus je proširen na 32 stvarna self-authored MIDI artefakta i zaključan prije scoringa u 24 TRAIN / 8 HOLDOUT podjelu. Ground-truth vault zasebno veže akorde, sekcije, track uloge i prijelaze; holdout pokriva sedam žanrovskih oznaka, tri takta i tri razreda gustoće. `QualityCalibrationReport 1.0` ne mijenja metric weights, hard-safety ni ljudske pragove. `ProductionExpressionIntake 1.0` zahtijeva exact SoundBinding, stvarni MIDI/audio/attestation hash i operator approval, a zabranjuje GOLD velocity, apsolutni pitch i Bank/Program autoritet. `HumanListeningIntake 1.0` ne broji proxy audio ni SOFTWARE TEST ONLY bundle. Zato je software foundation PASS, ali quality release gate ostaje blokiran s 0/2 stvarna evaluatora i bez production expression capturea. Dokazi su `data/session37-test-report.json`, `data/session37-benchmark-report.json`, `artifacts/session37-quality-corpus.json`, `artifacts/session37-private-ground-truth-vault.json`, `artifacts/session37-calibration-report.json` i `artifacts/session37-quality-release-gate.json`.

### Sesija 38 — Pa800 Mapping Lab i DeviceProfile Certification — SOFTWARE INTAKE ZAVRŠEN / VANJSKI P0 OTVOREN

**Cilj:** zatvoriti postojeću Sesiju 16 i aktivirati samo fizički potvrđene uređajne funkcije.

**Isporuke:**

- USB import, SHIFT + Execute, marker/CV, Track Type i NTT dokaz;
- exact Bank/Program i Guitar/RX/DNC articulation capture;
- save/reload, audio/slikovni dokaz i operator-approved hash;
- mjereni oscillator/voice cost i prihvatljivi voice-stealing pragovi;
- `CONFIRMED`, `UNSUPPORTED` i `UNKNOWN` DeviceProfile stavke;
- automatska regresija svakog uređajno pronađenog odstupanja.

**Gate:** samo potpuni potpisani rezultat smije dodijeliti `PA800_DEVICE_CERTIFIED`; parcijalni rezultat ostaje `DEVICE_TEST_FAILED` ili `WAITING_FOR_DEVICE`.

**Rezultat:** 200/200 PASS u software intake opsegu. Implementirani su strogi capture, profil i certifikacijski report ugovori, CLI `reference/seal/verify`, lokalni API/GUI adapter i negativni testovi za nepotpune kanale/markere/provjere, krivi SoundBinding, nedopušten trigger, path traversal, hash ili file-magic mismatch, lažno operator odobrenje i nepotpun neovisni review. Referentni artefakti ostaju `WAITING_FOR_DEVICE`, s nula potvrđenih fizičkih testova i `finalCertifiedMidiExportAllowed=false`. Dokazi su `data/session38-test-report.json`, `data/session38-benchmark-report.json`, `data/session38-schema-catalog.json`, `artifacts/session38-device-capture-template.json`, `artifacts/session38-device-profile.json` i `artifacts/session38-device-certification-report.json`.

### Sesija 39 — AI Premium Arranger 5.0 Release Gate — P0

**Cilj:** objaviti finalni proizvod tek kada se spoje software, quality, production evidence i device dokaz.

**Isporuke:**

- migracija svih podržanih projekata i clean-machine Windows test;
- finalni RenderManifest, EvidenceLedger, EvaluationReport i DeviceProfile;
- reproducibilan ZIP, checksum i identitetski code-signing postupak ako je dostupan;
- onboarding, recovery, poznata ograničenja i jasni output tierovi;
- finalni MIDI download samo nakon verifiera i odgovarajućeg certifikacijskog gatea;
- release matrica bez otvorenog severity-1/2 defekta.

**Gate:** 5.0 i naziv `AI PREMIUM ARRANGER` dopušteni su tek nakon prolaza Sesija 31–38. Bez Sesije 37 ili 38 izlazi samo novija `AI PREMIUM ARRANGER PREVIEW` verzija.

## 14. Ubrzani kritični put

```text
4.9.3 Renderer Foundation
      |
      v
31A Automatic Track Analysis
      |
      v
31B Evidence Resolver
      |
      v
32 TrackPlan / Safe Render Contract
      |
      v
33 Deterministic Renderer -----------+
      |                              |
      v                              v
34 Global Coherence              37 Quality/Evidence
      |                              |
      v                              |
35 End-to-End Workflow               |
      |                              |
      v                              |
36 Reliability Gate                  |
      |                              |
      +---------------+--------------+
                      |
             38 Pa800 Certification
                      |
                      v
                 39 Release 5.0
```

Sesija 37 može početi čim Sesija 33 daje stabilan render. Sesija 38 može se izvoditi čim je fizički Pa800 dostupan. Time vanjski rad ne čeka završetak svih GUI i reliability poboljšanja, ali nijedan rezultat ne preskače zajednički release gate.

## 15. Mjerljiva definicija „radi bez grešaka”

- 100% objavljenih MIDI datoteka prolazi neovisni hard validator;
- 0 neobrađenih iznimki na zaključanom unit/integration/E2E/adversarial korpusu;
- 0 partial, `.tmp` ili oštećenih outputa nakon cancel/crash/disk-full scenarija;
- 0 promijenjenih originalnih solo nota izvan eksplicitnog ručnog edit audita;
- 0 GOLD velocity, Bank Select, Program Change ili mixer utjecaja;
- 0 mutacija bez `EvidenceLedger` i TrackPlan autorizacije;
- 0 approximate SoundBinding ili nagađanih RX/DNC/Guitar Mode triggera;
- isti source + config + registry + seed + profile daju iste MIDI bajtove;
- 100% očekivanih failova ima strukturirani error code, objašnjenje i recovery akciju;
- 25.000 nota: analiza ispod 10 s, plan ispod 5 s, parcijalni render ispod 2 s na referentnom računalu;
- GUI ostaje responzivan, a batch greška jedne datoteke ne prekida ostale;
- nema otvorenog severity-1/2 defekta prije bilo kojeg javnog izdanja.

## 16. Predloženi ubrzani release vlak

| Izdanje | Obuhvat | Dopuštena oznaka |
|---|---|---|
| 4.9 | Sesija 31A: automatska analiza i exact-evidence detekcija instrumenta | `AI PREMIUM ARRANGER PREVIEW` |
| 4.9.1 | Sesija 31B: EvidenceLedger i fail-closed authority resolver | `AI PREMIUM ARRANGER PREVIEW` |
| 4.9.2 | Sesija 32: TrackPlan, Full Optimizer dry-run i safe render contract | `AI PREMIUM ARRANGER PREVIEW` |
| 4.9.3 | Sesija 33: stvarni deterministički evidence-driven renderer | `AI PREMIUM ARRANGER PREVIEW` |
| 4.10 | Sesija 34: globalna koherentnost — završeno 168/168 | `AI PREMIUM ARRANGER PREVIEW` |
| 4.10.1 | Sesija 35: puni Song-to-Style workflow — završeno 176/176 | `AI PREMIUM ARRANGER PREVIEW` |
| 4.10.2 | Sesija 36: zero-silent-failure reliability — završeno 184/184 | `AI PREMIUM ARRANGER PREVIEW` |
| 4.11 | Sesija 37 software calibration — završeno 192/192; ljudski/production evidence otvoren | `AI PREMIUM ARRANGER PREVIEW` |
| 4.11.1 | Sesija 38 software Device Lab intake — završeno 200/200; fizički dokaz otvoren | `AI PREMIUM ARRANGER PREVIEW` |
| 4.12 Device RC | Potpuno ispunjen i potpisan Session 38 Pa800 DeviceProfile | `AI PREMIUM ARRANGER DEVICE RC` |
| 5.0 | Sesija 39, svi P0 i svi vanjski gateovi | `AI PREMIUM ARRANGER` |

## 17. Program potpune optimizacije cijele aplikacije

Potpuna optimizacija ne znači automatski mijenjati sve trake. Znači da svaki modul dobiva zajednički evidence ulaz, mjerljiv performance budget, deterministički cache, strukturirani error i regresijski dokaz, dok se nesiguran glazbeni sadržaj zadržava ili šalje na ručni pregled.

| Optimizacijski tok | Konkretno unapređenje | Sesija | Mjerljivi gate |
|---|---|---:|---|
| Automatski import i analiza | jedan parser prolaz za note, tempo, takt, track identity, SoundBinding, instrument, ulogu, registar i polifoniju | 31A | završeno 136/136; bez velocity/GOLD utjecaja |
| Evidence indeks i cache | sadržajno adresirani Factory/GOLD/plan/device indeks; inkrementalna invalidacija samo promijenjenih hashova | 31B | završeno 144/144; 1.657 odluka, 100% eksplicitne hash-pokrivenosti i nula implicitnih fallbackova |
| Full MIDI Optimizer | zajednički per-track plan za cleanup, overlap, quantize, Factory dinamiku/mixer, register repair, FX i phase operacije | 32 | završeno 152/152; 52/52 fragmenta spremna, 249 operacija, 0 zapisanih MIDI bajtova |
| Arranger render | stvarni marker/role/pattern render uz Factory velocity i neovisni verifier | 33 | završeno 160/160; 52 fragmenta, 1.400 nota, 14/54 peak i byte-identičan CLI/API/GUI/batch |
| Glazbena koherentnost | globalni voice leading, Fill target, V1–V4 energija i ending resolution | 34 | završeno 168/168; 1.400 nota i 14/54 u svakoj varijanti |
| Workflow i GUI | hashirani state machine, downstream invalidacija, lock, partial regenerate, undo/redo i checkpoint/resume | 35 | završeno 176/176; 50/50 projekata i 10/10 faza |
| CPU, memorija i I/O | jedan MIDI parse, lazy registry index, bounded cache, streaming batch, ograničen preview i atomic write | 36 | završeno: 25k ispod 1 s / oko 18 MB peak; 100k ispod 4 s / oko 73 MB peak |
| Pouzdanost | fuzz/property, race, disk-full, Unicode/long-path, stuck-note i worker parity | 36 | završeno 184/184; 232 zaključane regresije, nula silent/partial outputa i severity-1/2 defekta |
| Kvaliteta i kalibracija | zaključani train/holdout corpus, stvarni listening i baseline-better vault | 37 | software 192/192; 32 slučaja i 24/8 split; vanjski gate čeka Overall najmanje 4/5 i 70% preferencije |
| Device intake | strogi capture/profile/report, osam kanala, deset markera, 17 provjera, evidence hash i operator/reviewer potpisi | 38 | software 200/200; objavljeni profil ostaje `WAITING_FOR_DEVICE` |
| Uređaj i release | fizički Pa800 profil, voice cost, articulation capture i clean Windows paket | 38–39 | potpisani device dokaz i svi P0 gateovi |

Tehnički prioritet optimizacije je: ukloniti ponovljeno parsiranje i skeniranje velikih registryja, zatim uvesti inkrementalni hash graph, potom paralelizirati samo neovisne read-only analize. MIDI mutacija i objava ostaju serijalizirane i zaključane kako performance poboljšanje ne bi stvorilo race-condition ili nedeterminističan output.

## 18. Prvi sljedeći konkretni posao

Faze 1–9 završene su u dokazivom software opsegu, uključujući 200/200 Session 38 i objedinjeni 2900/2900 rezultat. Sljedeći korak zahtijeva stvarni vanjski dokaz:

1. dva neovisna evaluatora moraju ispuniti zaključani blind paket s dokaznim rating-form i attestation hashovima;
2. Overall medijan mora biti najmanje 4/5, a Premium preferencija najmanje 70%;
3. operator mora uvesti stvarni exact-SoundBinding MIDI/audio production expression capture;
4. svaki baseline-better slučaj mora ući u zaključani quality regression vault prije korekcije;
5. na fizičkom Pa800 izvršiti USB import, SHIFT + Execute, marker/CV, Track Type, NTT, save/reload i voice-stealing testove te popuniti Session 38 capture;
6. capture zapečatiti stvarnim evidence hashovima i operator approvalom, zatim provesti neovisni review kroz postojeći `seal/verify` tok;
7. tek potpuni ljudski, production-evidence i uređajni PASS mogu voditi u Sesiju 39 i naziv bez oznake Preview.

Do tada se distribuira samo `AI PREMIUM ARRANGER PREVIEW`; software test, proxy audio ili prazna potvrda ne mogu otključati release gate.