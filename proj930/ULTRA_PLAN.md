# Ultra plan: DNA Arranger za Korg Pa800

Datum početka: 2. rujna 2026.

## Nepromjenjiva pravila

1. Factory MIDI je jedini izvor dinamike. Za svaki instrument čuva se sedam velocity točaka: `floor`, `soft`, `lowMid`, `optimal`, `highMid`, `strong`, `ceiling`.
2. Gold se prvo filtrira, kvantizira i deduplicira. Gold pattern nikada ne sadrži velocity niti mijenja dinamiku.
3. Svaki instrument i pattern ima stabilan trodijelni brojčani ID, primjerice `120.111.231`.
4. Svaki generirani rezultat mora biti ponovljiv iz istih postavki i mora imati zapis izvora podataka.
5. Primarni cilj je Korg Pa800 s OS 2.0 ili novijim i službeni uvoz Style SMF-a razdvojenog markerima.

## Arhitektura

```text
Factory MIDI ──> profiliranje velocityja ──> Instrument Profile Registry ──┐
                                                                          ├─> Pa800 Style Engine ─> SMF0/JSON
Gold MIDI ─────> filter ─> kvantizacija ─> Pattern Registry ──────────────┘
Song MIDI ─────> tempo/takt/instrumenti/sekcije/akordi ────────────────────┘
```

## Agentski sloj

- **ChatGPT Orchestrator** vodi plan, bira specijaliste i traži ljudsku potvrdu za osjetljive korake.
- **ChatGPT Music Director** priprema strukturirani muzički brief bez pristupa MIDI writeru.
- **ChatGPT Style Evaluator** ocjenjuje A/B varijante tek nakon tehničke validacije.
- **Codex Lead Engineer** implementira engine, API, testove i dokumentaciju.
- **Codex MIDI Compliance Agent** provjerava SMF0, markere, kanale i kontrolere te blokira neispravan izvoz.
- **Codex Data/Regression Agent** održava Factory/Gold pipeline, stabilnost ID-eva i regresijske baselineove.
- **Korisnik** potvrđuje prijenos, uvoz, NTT/Track Type i spremanje Stylea na fizički Pa800.

Agenti razmjenjuju strukturirani JSON. Ne smiju mijenjati pravilo Factory-only dinamike, preskočiti validator niti samostalno zapisivati na instrument.

## Faza 1 — DNA baza

- Parsiranje ugniježđenih ZIP i MIDI datoteka bez vanjskih biblioteka.
- Factory profil po bank MSB, bank LSB, programu i drum noti.
- Gold patterni na mreži 1/16, bez velocityja.
- Filter: mikro-note, loša kvantizacija, premalo/previše nota, jednokratni i duplicirani patterni.
- Izvještaj s brojem prihvaćenih i odbijenih elemenata.
- Factory schema 3.3 sa sedmerotočkastom krivuljom, CC7/CC11 mixer profilom, kvantilima, ulogom, registrom, confidenceom, source ID-evima i per-element drum klasifikacijom.
- Verzije Factory i Gold baze izvedene su deterministički iz sadržaja izvora.

Status: implementirano.

## Faza 2 — Korg Pa800 Style engine

- Forma za tempo, takt, originalni ključ/akord i Pa800 Style elemente.
- Automatski izbor patterna za Drum, Percussion, Bass i Acc1–Acc5.
- Stabilan izbor patterna pomoću seeda iz Best Deterministic Seta.
- Ranking obavezno boduje deset kriterija: role, meter, tempo, section, density/accent, harmony, register/articulation, evidence quality, transition i transformation budget.
- Primjena Factory optimalnog velocityja po izlaznoj traci.
- Izvoz Standard MIDI File formata 0, jer ga Pa800 Style import zahtijeva.
- Kanali su fiksirani po Korg standardu: Bass 9, Drum 10, Percussion 11, Acc1–Acc5 na 12–16.
- Marker imena su mala slova: `i1cv1`, `v1cv1`…`v4cv1`, `f1cv1`, `e1cv1`.
- Time Signature, CC00/CC32, Program Change i CC11 pišu se na početak svakog Chord Variationa.
- Paralelni izvoz aranžmanskog JSON-a za nastavak rada.

Status: prva Pa800-kompatibilna verzija implementirana i strojno provjerena; čeka probni uvoz na fizičkom Pa800.

### Ugrađeni compliance i quality sloj

- Izvoz se ponovno parsira prije preuzimanja i blokira ako nije SMF0 s jednom trakom.
- Provjeravaju se PPQ 480, marker redoslijed, mala slova, kanali 9–16, Time Signature, CC00, CC32, Program Change i CC11.
- Validator otkriva note-off bez note-on, preklopljene, viseće i note nultog trajanja te nedostajući, višestruki ili prerani End Of Track.
- Prije izvoza uklanjaju se note koje nakon C-major mapiranja postanu duplikati.
- Polifonija je ograničena po traci: Bass 1, Acc1/Acc2 4, Acc3/Acc4 1 i Acc5 3 tona po onsetu.
- Preklapanje iste note na istom kanalu skraćuje prethodnu notu umjesto stvaranja stuck-note rizika.

Status: implementirano; prošireni paket ima 43/43 prolazna testa. GOLD runtime schema rekurzivno blokira velocity/bank/program polja i Factory profile reference. Optimizer koristi protected-event transakciju `ANALYZE -> PLAN -> DRY RUN -> APPLY -> VERIFY -> COMMIT`.

## Faza 3 — Muzička inteligencija

- Učitavanje MIDI songa kroz lokalno web-sučelje.
- Detekcija tempa, takta, tonaliteta i akorda po taktovima.
- Prepoznavanje intro/strofa/refren/bridge/ending sekcija.
- Voice-leading, ograničenje registra, kontrola polifonije i izbjegavanje sudara nota.
- Intenzitet po sekcijama računa se samo iz gustoće nota, bez čitanja velocityja songa.
- Fill i prijelazi samo na granicama sekcija.

Status: implementirano. Analiza daje tempo/takt mapu, akorde na pola takta, dokazne granice faza, polifoniju, harmonijsku aktivnost, registre i gustoće uloga; timeline podržava ručne granice, intenzitet, preimenovanje, split i merge. Phase Arranger prije promjene daje deterministički `KEEP/REPAIR/REPLACE/MANUAL_REVIEW` plan, štiti solo timing i primjenjuje samo Factory-dynamic note unutar transformation budgeta.

### Etapa 3 proširenog optimizera

Status: završeno. Factory schema 3.3 daje sedmerotočkaste velocity i CC7/CC11 mixer profile; key-range vraća note oktavama bez brisanja. GOLD schema 3.2 fizički uklanja velocity/bank/program autoritet. FX Auto Profile, Solo Delay i akordski potvrđena Terca imaju role detector, Factory-only generirani velocity, zaštitu Program Changea i stroge transformation budgete. Solo trake nisu kandidati za automatski ni ručni quantize. MIDI energy/headroom ostaje jasno označen kao proxy, ne LUFS.

### Etapa 4 — stvarni arranger-pattern engine

- 26.922 Factory Style/CV segmenta iz svih uloga `DRUMS`, `PERC`, `BASS`, `ACC1–ACC5`, elemenata i CV1–CV6.
- 2.919 Factory ACC strumming patterna s 46.995 down/up/block/mixed poteza i očuvanim inter-string timingom, gateom, registrom i element/CV dokazom.
- 12.918 punih GOLD performance patterna na rezoluciji 96 tickova po četvrtinki: drum, percussion, bass, power-riff, riff i accompaniment.
- 4.373 stvarna drum–bass relationship zapisa; bass izbor se veže uz već odabrani kompatibilni groove.
- Style engine ciklički koristi jedno- i dvotaktne obrasce, primjenjuje Factory dinamiku po svakoj drum noti i koristi GOLD samo za note/timing/gate/harmonsko ponašanje.
- Svi runtime ID-evi su strogo `DDD.DDD.DDD`; kolizija prekida build.

Status: završeno i uključeno u GUI/Style Builder. Factory tempo ulazi u strumming ranking, a Guitar Mode kontrolne note se ne sintetiziraju bez potvrđene službene mape.

## Faza 4 — Ultra editor

- Profesionalni GUI s odvojenim radnim prostorima MIDI Optimizer, Pa800 Style Builder i Reports.
- MIDI Optimizer: note cleanup, controller cleanup, podesivi quantize za ne-solo trake i Factory dynamics strength.
- Before/after quality score, detaljne metrike, SHA-256 trag i tokenizirano preuzimanje nove datoteke.
- Ne-destruktivni rad: original se nikada ne prepisuje, a tempo/takt/meta/program semantika se čuva.
- Running-status kompresija, jednosatni tokeni te cache granice 10 rezultata i 128 MB.
- Piano-roll s bojama kanala, timelineom, zoomom, seekom i filtrom kanala.
- Solo/mute, zamjena instrumenta, transpozicija i auditirane izmjene nota.
- Lokalno Web Audio preslušavanje i A/B usporedba originalne i optimizirane verzije.
- Undo/redo do 50 koraka i automatsko lokalno spremanje postavki projekta.

Status: implementirano. GUI ima Home, Optimizer, Style Builder, DNA Library, Reports i Settings; stvarni MIDI editor, velocity lane, Show Changes, solo/mute, playback, A/B, Pattern Inspector, projektni import/export, edit i projektni undo/redo te autosave s recovery kopijama. Kvalitetniji GM/Pa800 preview zvuk ostaje neblokirajuća buduća nadogradnja.

## Faza 5 — Produkcijski Windows paket

- Lokalni server/pokretač s provjerom podataka.
- Offline PWA ili samostalna Windows aplikacija.
- Paket bez instalacije, automatsko ažuriranje DNA baze i sigurnosne kopije.
- Testni korpus, provjera MIDI kompatibilnosti i deterministički regresijski testovi.

Status: portable Python izdanje implementirano kroz ASCII-safe `install.bat` i `run.bat`; instalacija po potrebi koristi winget, gradi DNA bazu i pokreće jedinstveni release-check. Samostalni EXE/installer ostaje opcionalna distribucijska nadogradnja nakon fizičke certifikacije.

## Kriteriji završetka

- Gold velocity utjecaj mora ostati točno nula.
- Svaka generirana nota ima dokaziv Factory profil ili eksplicitno označen neutralni fallback.
- Izvezeni Style MIDI mora biti SMF0 s jednom trakom, važećim Pa800 markerima i samo kanalima 9–16.
- Datoteka mora proći postupak Style Record > Import SMF na Pa800 OS 2.0+.
- JSON mora sadržavati seed, izabrane pattern ID-eve, profile i sve postavke potrebne za ponavljanje rezultata.

## Master Prompt v3.1 — završni raspored

- Obavezni software core: `SOFTWARE_VALIDATED`.
- MUST zahtjevi: 22/22 `IMPLEMENTED`.
- Invarianti: `goldAffectsDynamics=false`, `analysisVelocityUsed=false`, `sameSeedSameOutput=true`, `invalidMidiExported=false`.
- Preostali obavezni release gateovi i sve opcionalne funkcije raspoređeni su u 14 kratkih razvojnih sesija u `ZAVRSNE_SESIJE.md`.
- Nakon njih slijedi samo sesija usavršavanja, bez širenja opsega.
- Fizička Pa800 certifikacija: `WAITING_FOR_DEVICE`; nije dopušteno koristiti oznaku `PA800 CERTIFIED` prije stvarnog testa.