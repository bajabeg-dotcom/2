# DNA MIDI Studio 6.03 — PRE-SALE RC

> Prodajni status: **AI PREMIUM ARRANGER PREVIEW**. Softverski kandidat nije konačno Pa800 certificiran dok se ne završe Style Works XT round-trip, fizički Pa800 test, kompletan 150-song batch i provjera licenci/porijekla. Detalji su u `PRE_SALE_RELEASE_REPORT.md`.

Default workflow: **FULL AI Optimization 6.0** — MAX AI BRAIN + MAX OPTIMIZER + Critic.

# DNA MIDI Studio za Korg Pa800

## 4.15 Suno-like RECONSTRUCT workflow (4. septembar 2026.)

Glavni Song workflow sada koristi jedan **RECONSTRUCT MIDI** poziv koji pravi tri determinističke, validirane varijante: **A Balanced Live**, **B Groove Forward** i **C Conservative**. Sve tri koriste isti Factory/GOLD authority model i isti sigurni optimizer; source MIDI se ne prepisuje. Detalji su u `RELEASE_4_15_REPORT.md`.


Profesionalna lokalna web-aplikacija za optimizaciju i uređivanje MIDI songova, analizu glazbene forme te izradu Style Import MIDI-ja za Korg Pa800.

> **Status radnog prostora (3. rujna 2026.):** legacy gate ima 43/43 PASS, a objedinjeni recovery + uređajni preflight + Premium/Renderer/Coherence/Workflow/Reliability/Quality/Device Intake sloj ima **2900/2900 PASS**. Session 38 podiže baseline na **4.11.1 Device Certification Intake Foundation**: capture, DeviceProfile i certifikacijski report strogo provjeravaju osam kanala, deset markera, 17 fizičkih provjera i hashirane audio/slikovne dokaze. Objavljeni profil ostaje `WAITING_FOR_DEVICE`. Dopušten je samo naziv **AI PREMIUM ARRANGER PREVIEW**; finalni certificirani export ostaje blokiran do 2/2 evaluatora, produkcijskog expression/articulation dokaza i fizičkog Pa800 certifikata.

## Pokretanje na Windowsu

1. Prvi put dvaput klikni `install.bat`.
2. Nakon uspješne instalacije dvaput klikni `run.bat`.
3. Otvori `http://127.0.0.1:8765/` ako se preglednik ne otvori automatski.
4. Pri prvom pokretanju pričekaj približno 1–3 minute za potpunu izgradnju DNA baza.

`install.bat` pronalazi lokalni Python, po potrebi gradi Factory/Gold registry i pokreće cijeli release-check. Batch datoteke su namjerno napisane samo ASCII znakovima radi kompatibilnosti s Windows CMD-om.

Aplikacija radi lokalno i ništa ne šalje na internet.

## Full reference authority workflow

Kalibracija sada prije svih transformacija gradi
`calibration/reference_authority_plan_10.00.json`. Plan eksplicitno veže svaki
domen (velocity, range, timing, groove, articulation, expression,
humanization, drums, Korg constraints, validation i determinism) za obavezne
Factory/Gold/Engine izvore, njihove SHA-256 hashove i downstream potrošače.

Proxy izvori i tihi fallback su zabranjeni. Ako ijedan obavezni izvor nedostaje,
reference preflight je `BLOCKED` i transformacija zahtijeva manual review.
`REFERENCE_COVERAGE` je dodat u finalni certification matrix.

## Master Prompt v3.1 status

Legacy software core ponovno je izvršiv i ima **43/43 PASS** nad 3.211 Factory i 182 GOLD MIDI datoteke. Sesije 2–38 daju objedinjeni paket od **2900/2900 PASS**. Fizička certifikacija, production expression capture i stvarni ljudski listening još čekaju dokaz.

Session 2 provjera iz trenutačnog stabla:

```text
py session2_release_check.py
```

Session 3 provjera:

```text
py session3_release_check.py
```

Session 4 provjera:

```text
py session4_release_check.py
```

Session 5 provjera:

```text
py session5_release_check.py
```

Session 6 provjera:

```text
py session6_release_check.py
```

Session 7 provjera:

```text
py session7_release_check.py
```

Session 8 provjera:

```text
py session8_release_check.py
```

Session 9 provjera:

```text
py session9_release_check.py
```

Session 10 provjera:

```text
py session10_release_check.py
```

Session 11 provjera:

```text
py session11_release_check.py
```

Session 12 adversarial provjera:

```text
py session12_release_check.py
```

Session 13 Windows paket:

```text
py session13_release_check.py
```

Session 14 uređajni preflight i priprema test-paketa:

```text
py session14_release_check.py
py session14_device_check.py prepare
```

Session 15 AI Premium baseline:

```text
py session15_release_check.py
```

Session 17 Production Adapter:

```text
py session17_release_check.py
```

Session 18 Track Identity i Solo Safety 2.0:

```text
py session18_release_check.py
```

Session 19 Song Understanding 2.0:

```text
py session19_release_check.py
```

Session 20 AI Producer Brief 2.0:

```text
py session20_release_check.py
```

Session 21 Arrangement Graph 2.0:

```text
py session21_release_check.py
```

Session 22 Premium Candidate Search i A/B/C varijante:

```text
py session22_release_check.py
```

Session 23 Groove, Humanization i polifonija:

```text
py session23_release_check.py
```

Session 24 Premium Solo i Expression Director:

```text
py session24_release_check.py
```

Session 25 ArticulationMap 2.0:

```text
py session25_release_check.py
py session25_articulation_map.py --help
```

Session 26 Premium Preview 2.0:

```text
py session26_release_check.py
py session26_premium_preview.py --help
```

Session 27 Music Quality Evaluator 2.0:

```text
py session27_release_check.py
py session27_quality_evaluator.py --help
```

Session 28 Premium Producer Workflow 2.0:

```text
py session28_release_check.py
py session28_premium_workflow.py --help
```

Session 29 Personal Producer Profile 2.0:

```text
py session29_release_check.py
py session29_personal_profile.py --help
```

Session 30 Preview Release Readiness 2.0:

```text
py session30_release_check.py
py session30_release_readiness.py --help
```

Session 31A automatska analiza i detekcija Track Instrumenta:

```text
py session31_release_check.py
py session31_track_analysis.py song.mid --output track-analysis.json
```

Session 31B Evidence Authority Resolver:

```bat
py session31b_release_check.py
py session31b_evidence_resolver.py project-documents.json --variant C --output evidence-ledger.json
```

Resolver sadržajno provjerava produkcijske registryje i sve aktivne planerske dokumente. Svaki track segment, pattern, Groove događaj, expression sloj, Factory CC11 točka i articulation trigger dobiva jednu fail-closed odluku. Ledger je read-only i ne daje MIDI writer, validator ili uređajni autoritet.

Session 32 TrackPlan i Full Optimizer dry-run:

```bat
py session32_release_check.py
py session32_track_plan.py song.mid project-documents.json evidence-ledger.json target-bindings.json --output track-plan.json
```

TrackPlan povezuje source MIDI, automatsku analizu, EvidenceLedger, exact Factory profile i svih 52 marker-role fragmenta. Rezultat je read-only ugovor s budgetima, lockovima, predviđenim diffom i parcijalnom invalidacijom; ne zapisuje MIDI i ne može preskočiti renderer/verifier.

Detektor prihvaća automatsku klasifikaciju samo kada fizička traka ima točan vremenski CC00/CC32/Program i odgovarajući Factory profil. GM obitelj, naziv trake i registar služe samo kao objašnjivi hint; shared channel ili nepotpun dokaz daju `MANUAL_REVIEW`.

Objedinjena provjera svih ponovno izgrađenih modula:

```text
py recovery_release_check.py
```

CLI alati `session2_reconstruct.py`, `session3_reconstruct.py`, `session4_reconstruct.py`, `session5_enhance.py`, `session6_rx.py` i `session7_dnc.py` koriste stvarne MIDI bajtove. `session8_agent_runtime.py` prima strukturirani JSON posao i izdaje samo read-only agentski brief/manifest: agent ne smije pisati finalni MIDI, validator se ne može zaobići, a cloud je metadata-only, ugašen po defaultu i traži izričit pristanak. Session 4 potpuno zabranjuje GOLD kao izvor ritam-gitare. Session 5 nikada ne mijenja originalne solo note; izričito razlikuje vanjski 1-based Track/Channel od internih indeksa, Bank/Program provjerava samo na ciljnoj solo traci, blokira dijeljeni solo kanal i nikad ne otvara 17. track. Delay/Echo ide na prvi slobodan track uz isti kanal i kopirani Sound/Bank/Program setup. Session 6 i 7 traže točan Bank Select i Program Change te potvrđenu verzioniranu RX/DNC mapu. Sve sintetičke mape zahtijevaju izričit testni opt-in i nisu produkcijski Pa800 autoritet.

`session9_pipeline.py`, lokalni endpoint `/api/unified-pipeline`, GUI adapter i batch koriste isti `PipelineConfig` i isti dispatcher za svih šest recovery enginea. Parity manifest uključuje input/config/output hash, plan svakog stagea, jedinstveni pregled 16 traka i read-only GM/Pa800 preview koji ne utječe na MIDI validaciju.

`session10_transaction.py` objavljuje rezultat tek nakon zapisa u privremenu datoteku i uspješne provjere, zatim koristi atomski replace. Lock i journal podržavaju siguran batch, cancel i resume prema source/config/database hashovima; disk-full, crash ili validator failure ne ostavljaju djelomičan MIDI. Unicode, dugi Windows nazivi, rezervirana imena i path traversal imaju negativne testove.

`session11_verify.py` ponovno parsira izvor i kandidat neovisno o optimizerovu verdictu. Provjerava protected-note diff, SysEx/meta, Bank Select, Program Change, RPN/NRPN, autorizirane dodatke, manifest-to-MIDI i atomic journal hash, Pa800 ugovor, idempotency te jednakost rezultata za 1, 2 i 4 workera.

Session 12 testira oštećene chunkove/VLQ, SMPTE, running status, SysEx, RPN/NRPN, aftertouch, pitch bend, EOT i stuck note slučajeve te velike i prazne trake. Lažni ili slabo potvrđeni RX/DNC/solo događaji i duboko skrivena GOLD dinamika blokiraju se. `data/session12-regression-vault.json` zaključava checksumove i 59.635 stabilnih ID-eva iz demo i produkcijskih registryja te autoritativne source arhive.

Session 14 stvara `artifacts/session14-device-kit/` s funkcionalnim Style MIDI-jem, polifonijskim stress MIDI-jem, manifestima, rezultatskim obrascem i uputama. Verifier zahtijeva sve PASS odgovore, serijski broj/OS, potpisanu ljudsku potvrdu te hashiranu sliku i audiosnimku. Sam preflight nikada ne dodjeljuje uređajni certifikat. U GUI-ju je paket dostupan kroz **Reports & Safety → Preuzmi Pa800 test-paket**, a lokalni API koristi `/api/device-test-kit` i `/api/device-preflight`.

Session 15 dodaje strogi `PremiumConfig`, devet verzioniranih JSON ugovora, immutable 3.17 baseline, P0/P1 feature matricu, validirani referentni Pa800 MIDI i read-only plan. AI još ne mijenja MIDI, ne piše finalni output i ne dobiva mogućnost preskakanja validatora. Dokazi su `data/premium-baseline.json`, `data/premium-feature-matrix.json` i `data/session15-test-report.json`.

Session 18 uvodi stabilni identitet fizičke trake neovisan o prikazu brojeva, odvojene `trackIndex`/`trackNumber` i `channelIndex`/`channelNumber`, vremenski segmentirani Bank/Program SoundBinding, SMF0/shared-channel detekciju i original-solo fingerprint nakon svakog pipeline stagea. Delay/Echo bira prvi potpuno slobodan track, ne stvara 17. traku i za postojeći shared-channel konflikt traži izričito odobrenje. GUI/API manifest prikazuje izvorni i ciljni track, kanal i SoundBinding.

Session 17 dodaje jedan produkcijski adapter za svih šest recovery enginea. Prije svake mutacije provjerava fizički `trackUid`, puni vremenski CC00/CC32/Program SoundBinding i shared-channel konflikt. Drum/percussion, bass/power-riff/riff i Factory strumming koriste stvarne produkcijske registryje; solo koristi samo potvrđeni Factory CC11 profil. Nepotvrđeni RX/DNC i Guitar Mode kontrolni triggeri završavaju kao `DEVICE_BLOCKED`, a blokirani stage vraća izvorne MIDI bajtove. Dokazi obuhvaćaju stvarne Factory trake, tri stvarna GOLD songa, per-stage diff/rollback i jednak rezultat kroz CLI, web, API, GUI i batch.

Session 19 dodaje deterministički `SongMap 2.0`: promjenjivi tempo i takt, beat/downbeat mrežu, akorde na pola takta, sus/slash/seventh kvalitete, kadence, frazne signale, vremenski scoped uloge, full-duration polifoniju i uncertainty koji vodi u `MANUAL_REVIEW`. Korekcije akorda i sekcija zaseban su overlay i nikada ne mijenjaju izvorni MIDI. Zaključani self-authored benchmark ima 20 songova i 320 half-bar ćelija; trenutačni chord weighted-F1 i section-boundary F1 iznose 1,000, ali status ostaje `PRODUCTION_CALIBRATION_PENDING` do šire ljudski označene provjere.

Session 20 pretvara hrvatski ili engleski opis u strogi `ProducerBrief 2.0`: žanr, energiju sekcija, gustoću, sinkopaciju, prostor, prijelaze, solo tretman, uloge, lockove i transformation budget. Home prikazuje karticu **AI je razumio** prije generiranja. Konfliktni zahtjevi blokiraju planiranje dok ih korisnik izričito ne razriješi. Lokalni parser radi bez mreže; opcionalni AI adapter je default-off, consent-gated i metadata-only te ne može dobiti MIDI writer, putanju, Bank/Program ili validator autoritet.

Session 21 spaja validirani `SongMap 2.0` i potvrđeni `ProducerBrief 2.0` u strogi `ArrangementGraph 2.0` za svih deset Pa800 elemenata. Globalno planira V1–V4 energiju/gustoću, zajednički motiv, Fill ciljeve, harmonijski kontekst, registre, full-duration MIDI-note polifoniju i transformation budget. Lockovi ostaju nepromjenjivi u svim planovima, a niski confidence, izvorni manual review ili overflow blokiraju Candidate Search. Home može iz MIDI-ja prikazati dva read-only globalna plana; Session 21 još ne bira runtime patterne i ne mijenja MIDI.

Session 22 pretražuje 12.918 GOLD performance i 2.919 Factory strumming patterna u dva koraka. Hard constrainti za ulogu, takt, relativni pitch, registar, full-duration polifoniju i transformation budget izvršavaju se prije 14-kriterijskog scorea. Drum–bass veze ulaze u odabir, gitara je isključivo Factory, a GOLD i dalje nema velocity ni Bank/Program autoritet. Stabilne A/B/C varijante podržavaju lock, exclude, next candidate i parcijalnu regeneraciju uz hash-dokaz da ostali fragmenti nisu promijenjeni. Pet od 20 benchmark songova s neriješenim dokazom namjerno je blokirano prije pretrage; svih 15 podobnih songova i svi sigurnosni gateovi prolaze stopom 1,000. CandidateSet ostaje read-only selection manifest i još ne generira finalni MIDI.

Session 23 širi CandidateSet u strogi `GroovePlan 2.0` s 4.497 event-level timing zapisa i 107 produkcijskih groove-templateova. Microtiming i gate imaju zasebne granice za drums, percussion, bass, guitar, accompaniment, riff i pad; zaključani fragmenti i solo ostaju bez promjene. Full-duration sweep mjeri peak po logičkoj traci, kanalu i svih deset markera, a produkcijske A/B/C varijante trenutačno imaju maksimalno 18/54 nota. Stress testovi pokrivaju sustain, guste fillove i simplification redoslijed: ukrasni slojevi prije support glasova, dok core drums/bass/solo nikada nisu tiho uklonjeni. Pa800 oscillator/voice cost ostaje `UNCONFIRMED` bez fizički certificiranog DeviceProfilea. GroovePlan je read-only i još ne piše finalni MIDI.

Session 24 povezuje fizički `trackUid`, 1-based Track/Channel, vremenski SoundBinding i originalni solo fingerprint sa SongMap frazama i GroovePlan polifonijskim peakom. Grace, trill, slide, turnaround, dijatonska terca i nerekurzivni echo postoje kao zasebni, uklonjivi preview slojevi; svaki događaj ima `sourceNoteUid`, evidence ID i reason code. Factory profil jedini određuje velocity i CC11 granice, postojeći ručni CC11 se čuva, a Delay koristi zaseban siguran track bez 17. trake. Referentni testni corpus daje 83 preview note i 16 CC11 točaka uz maksimum 20/54, ali nije produkcijski autoritet: finalni render ostaje blokiran do potvrđenog ornament/relationship corpusa i slušnog gatea.

Session 25 uvodi capture/import granicu za Guitar, RX i DNC. `ArticulationMap 2.0` prihvaća samo exact CC00/CC32/Program SoundBinding, eksplicitnu ulogu i razdvojene playable/trigger raspone. `CONFIRMED`, `UNKNOWN` i `BLOCKED` zapisi nikada se ne pretvaraju u „najbliži” Sound; key-switch mora imati note-off, a dopušteni su još standardni CC i channel pressure. Referentne tri software mape imaju 9 zapisa i 11 preview događaja uz peak 19/54. One su `SOFTWARE_TEST_ONLY`: produkcija zahtijeva fizički `DEVICE_CAPTURED` dokaz, audio/slikovne hashove i operator-approved capture hash.

Session 26 dodaje strogi `PreviewSession 2.0`. A/B/C varijante dijele jedan clock i section loop; pregled prikazuje aktivne note, ulogu, traku, kanal, `trackUid`, SoundBinding, izvor sloja i full-duration polifoniju. Role solo/mute, proxy profil, glasnoća i loudness matching mijenjaju samo preview hash. Ugrađeni GM/Pa800 WAV je deterministički proxy, a vanjski SoundFont/renderer samo hashirani manifest bez automatskog izvršavanja. Pa800 WAV capture može se usporediti, ali ostaje `DEVICE_AUDIO_COMPARISON_ONLY` i ne može zamijeniti Session 16 certifikaciju.

Session 27 dodaje read-only `EvaluationReport 2.0` s odvojenim tehničkim i ljudskim gateom. Automatizirano mjeri harmoniju, groove, register collision, density curve, prijelaze, repetitivnost i ending resolution; referentni C preview postiže 4,543/5 bez hard faila. Slijepi paket je vezan uz immutable 3.17 baseline, javne oznake ne otkrivaju varijantu, a privatni ključ se ne šalje GUI-ju. `SOFTWARE_TEST_ONLY` odgovor, proxy WAV i automatske metrike ne računaju se kao ljudski dokaz. Release ostaje `HUMAN_LISTENING_PENDING` dok najmanje dva neovisna evaluatora ne daju Overall medijan 4/5 i najmanje 70% Premium preferencije.

Session 28 dodaje `PremiumWorkflow 2.0` i novi **Premium Producer** workspace. Vođene faze `Import → Analyze → Brief → Plan → Variants → Edit → Verify → Export` dijele jedan hashirani lanac dokaza. Timeline prikazuje svih deset Pa800 elemenata, Track Matrix fizičke trake i SoundBinding, a Explain/Diff razloge, lockove, dodane note, CC11 i nepromijenjeni Sound setup. Referentni workflow ima 7/8 dovršenih faza, 52 objašnjene odluke i siguran cancel/resume checkpoint. `Export` ostaje blokiran dok nisu zadovoljeni ljudski quality, produkcijski expression/articulation i fizički Pa800 gateovi.

Session 29 dodaje `PersonalProducerProfile 2.0` i zaseban **Personal Profile** workspace. Profil prihvaća samo `USER_EXPLICIT` odluke `ACCEPT_VARIANT` i `LOCK_SELECTION`; playback, odbijanje, hover, preview pozicija, MIDI sadržaj, implicitno ponašanje i cloud telemetrija nisu dopušteni signali. Referentni profil daje 52 objašnjive pattern preferencije i ograničen soft-ranking overlay nad 624 hard-pass kandidata, dok svih 829 hard-odbijenih kandidata ostaje netaknuto. Cold start, disable i potpuno brisanje vraćaju isti neutralni rezultat. Profil nema MIDI, projekt, audio, Factory dinamiku, SoundBinding, Bank/Program, validator ni uređajni autoritet.

Session 30 dodaje `ReleaseReadiness 2.0` i zaseban **Release Readiness** workspace. Nedestruktivna migracija čuva stanje, audit, lockove i originalnu datoteku; sadržajni manifest hashira aplikaciju, pet registryja i sve ugovore, ali se izričito ne predstavlja kao identitetski code-signing certifikat. Stvarna mjerenja pokrivaju 25.000 nota, globalni plan, parcijalnu regeneraciju, 10.000 migracijskih stavki, Unicode/duge putanje te naslijeđene crash/cancel/disk-full i clean-extract gateove. Software Preview RC prolazi bez severity-1/2 defekta, dok ljudski listening, produkcijski expression/articulation evidence, Pa800 profil, voice-cost i finalni export ostaju blokirani.

Konačni portable paket je `dist/DNA-MIDI-Studio-Pa800-Windows-4.11.1-device-certification-intake-foundation.zip`; pripadajuća `.sha256` datoteka potvrđuje cijeli ZIP. Objedinjeni gate ponovno pokreće svih 2900 recovery/preflight/Premium/Renderer/Coherence/Workflow/Reliability/Quality/Device Intake testova.

Software faze do Sesije 37 završene su u dokazivom Preview opsegu. Sljedeći korak nije moguće pošteno zatvoriti samo kodom: potrebna su dva neovisna evaluatora, operator-approved production expression/articulation capture i fizički Pa800 test. Finalna Pa800 Premium oznaka i certificirani MIDI export ostaju blokirani do tih vanjskih dokaza.

Optimizer koristi transakciju `ANALYZE -> PLAN -> DRY RUN -> APPLY -> VERIFY -> COMMIT`. Neovisni verifier blokira promjenu zaštićenih SysEx/meta, Bank Select, Program Change i RPN/NRPN događaja. GOLD nema autoritet nad velocityjem, Bank Selectom ni Program Changeom.

Phase Arranger analizira akorde na pola takta i granice faza, zatim prije mutacije prikazuje `KEEP`, `REPAIR`, `REPLACE` ili `MANUAL_REVIEW`. Solo trake uvijek ostaju `KEEP` i nisu kandidati za quantize. Strojni dokaz je u `data/phase5-test-report.json`.

Puna produkcijska provjera:

```text
py release_check.py
```

Detaljna matrica nalazi se u `MASTER_PROMPT_COMPLIANCE.md`.

Detaljna proizvodna i tehnička slika konačne aplikacije nalazi se u `VIZIJA_PROJEKTA.md`.

## Profesionalni Web GUI

Aktivno sučelje ima osam radnih prostora:

1. **Home** — ulaz u glavne workflowe i stalni status validacije.
2. **Premium Producer** — osam vođenih faza, graph timeline, Track Matrix, Explain/Diff i recovery.
3. **Music Quality** — automatizirane metrike i strogo odvojeni ljudski listening gate.
4. **MIDI Optimizer** — čišćenje, A/B pregled i stvarno uređivanje `.mid`/`.midi` datoteka.
5. **Pa800 Style Builder** — analiza songa i izrada SMF0 Style importa.
6. **DNA Library** — pregled Factory/GOLD izvora i dokaznih ID-eva.
7. **Reports & Safety** — release, audit i compliance izvještaji.
8. **Settings** — lokalni autosave i glasnoća preview syntha.

### MIDI Optimizer

- uklanja duplicirane note
- popravlja overlap, orphan note-off i dangling note
- uklanja obične redundantne CC događaje; Bank Select, Program Change i RPN/NRPN ostaju zaštićeni
- nudi quantize Off, 1/8, 1/16 ili 1/32 s podesivim strengthom; prepoznate solo trake uvijek se preskaču
- približava velocity Factory optimalnoj vrijednosti unutar Factory min/max raspona
- detektira i popravlja note s nevaljanim ili nultim trajanjem
- prikazuje before/after quality score i broj svake intervencije
- čuva tempo, takt, markere, tekstualne meta događaje, format, PPQ, broj traka i program semantiku
- original se ne prepisuje; optimizirani MIDI dobiva novu `_OPT.mid` datoteku
- MIDI writer ponovno koristi running status kako očišćena datoteka ne bi nepotrebno rasla
- finalni validator blokira izvoz ako note pairing, EOT ili struktura nisu valjani
- download token vrijedi jedan sat; cache čuva najviše 10 rezultata i 128 MB

### Piano-roll, editor i preslušavanje

- učitani MIDI odmah dobiva vizualni piano-roll s bojama po kanalu
- transport nudi Play/Pause, Stop i klik na timeline za pomicanje playheada
- kanalni filter i zoom olakšavaju pregled velikih songova
- nakon optimizacije moguće je A/B prebacivanje između **Original** i **Optimizirano**
- ugrađeni Web Audio synth služi samo za brzu kontrolu nota; ne pokušava imitirati Pa800 zvukove
- klikom ili Ctrl+klikom biraju se note; drag mijenja položaj/pitch, a desni rub trajanje
- dostupni su transpose, Factory-clamped velocity, quantize, duplicate i delete; editor također ne kvantizira solo trake
- velocity lane, Show Changes, solo/mute po kanalu i zasebni edit Undo/Redo
- preview je ograničen na 25.000 nota ili prvih 10 minuta radi stabilnog rada preglednika

### Projektna sigurnost

- Undo/Redo pamti do 50 promjena postavki tijekom rada
- postavke Optimizera i Style Buildera automatski se spremaju u lokalnu memoriju preglednika
- spremljene postavke vraćaju se pri sljedećem lokalnom pokretanju
- MIDI sadržaj i audio ne spremaju se u `localStorage`
- čuva se do pet lokalnih recovery kopija postavki
- `.dnaproject.json` ima verzioniranu shemu, migraciju, hash i auditne artefakte

## Analiza MIDI songa

U web-sučelju odaberi **Odaberi MIDI song**. Analizator automatski predlaže:

- početni tempo i takt
- tonalitet
- tempo i time-signature mapu, akorde po taktovima, polifoniju, registre i gustoće uloga
- intro, strofa, refren, bridge i ending sekcije s confidenceom i Pa800 preporukom
- duljinu i intenzitet Pa800 Style elemenata
- Factory instrumente prema bank/program podacima songa
- timeline dopušta ručno preimenovanje, promjenu granica i intenziteta te split/merge sekcija

Velocity iz učitanog songa se ne koristi. Dinamika generiranog Stylea i dalje dolazi isključivo iz Factory profila.

## Pa800 validator

Svaki Style se prije preuzimanja ponovno parsira. Izvoz se blokira ako:

- nije SMF format 0 s jednom trakom i PPQ 480
- koristi kanal izvan 9–16
- marker nije valjan ili nije napisan malim slovima
- na početku CV-a nedostaje Time Signature, CC00, CC32, Program Change ili CC11
- postoje preklopljene, neuparene, viseće ili note nultog trajanja
- nedostaje End Of Track, postoji više EOT događaja ili EOT nije posljednji događaj

Sučelje nakon uspješne provjere prikazuje **Pa800 validator PASS**. Prije validacije engine uklanja duplikate, ograničava polifoniju po traci kroz cijelo trajanje svake note, skraćuje stare sustain repove na novom onsetu i skraćuje preklapanja iste note. Neovisni validator ponovno računa peak istodobnih MIDI nota po kanalima 9–16 i blokira prekoračenje. Taj broj ne dokazuje stvarni oscillator/voice trošak pojedinog Pa800 Sounda; to ostaje dio fizičkog testa.

Style engine dodatno radi deterministički voice-leading oktavnim inverzijama, rješava nepotrebne unisone ACC traka, zapisuje Variation/Fill prijelaze te daje Track Type/NTT kandidate. Kandidati nisu fizička potvrda i moraju se provjeriti na Pa800.

## Pa800 izlaz

- Standard MIDI File format 0, jedna MIDI traka
- Bass kanal 9
- Drum kanal 10
- Percussion kanal 11
- Acc1–Acc5 kanali 12–16
- markeri `i1cv1`, `i2cv1`, `v1cv1`–`v4cv1`, `f1cv1`, `f2cv1`, `e1cv1`, `e2cv1`
- Time Signature, CC00, CC32, Program Change i CC11 na početku svakog Chord Variationa
- referentni Key/Chord: C Major

## Uvoz na Pa800

1. Kopiraj generirani `.MID` na USB.
2. Na Pa800 otvori Style Record i napravi novi Style.
3. Otvori Import SMF.
4. Drži SHIFT i pritisni Execute za uvoz svih marker-sekcija.
5. Za novi Style koristi Initialize.
6. Potvrdi originalni Key/Chord C Major, Track Type i NTT postavke.
7. Spremi Style u USER ili FAVORITE lokaciju.

## DNA pravila

- Factory MIDI je jedini izvor dinamike.
- Svaki instrument ima stabilni ID, ulogu, registar, confidence, source IDs, sedmerotočkastu velocity krivulju i Factory CC7/CC11 mixer profil kada postoji dovoljan izvorni dokaz.
- Key-range repair vraća melodijsku notu oktavom u potvrđeni raspon, bez brisanja i bez promjene pitch-classa; slab dokaz ostavlja za ručni pregled.
- Drum profili su odvojeni po noti i kategorijama Kick, Snare, Closed/Open Hi-Hat, Crash, Ride, Toms, Clap i Percussion.
- Gold patterni su filtrirani, kvantizirani i deduplicirani.
- Gold runtime patterni rekurzivno nemaju velocity, Bank Select, Program Change, `instrumentKey` ni Factory profile reference.
- Before/after izvještaj prikazuje MIDI energy/headroom proxy; ne predstavlja audio LUFS mjerenje.
- FX Auto Profile podešava samo CC91/CC93 prema ulozi i nikad ne kopira GOLD FX vrijednosti ili nepoznati SysEx.
- Solo Delay koristi prvi slobodan track, zadržava isti zvuk/kanal kopiranjem Bank/Program setupa te koristi Factory velocity; Terca ostaje uz izvorni solo. Oba sloja poštuju globalni/per-layer note budget.
- Style engine koristi 12.918 punih GOLD performance patterna za drum, percussion, bass, power-riff, riff i accompaniment, uključujući 4.373 drum–bass groove odnosa.
- Ritam-gitara koristi isključivo 2.919 Factory ACC strumming patterna s 46.995 stvarnih poteza; GOLD ne upravlja strummingom.
- Pattern ranking zapisuje deset kriterija, uključujući tempo, transition compatibility i transformation budget.
- Pattern Inspector podržava lock, unlock, sljedeći deterministički kandidat i isključenje patterna iz projekta.

Izračunato je 1.964 Factory profila, 26.922 Factory Style/CV segmenta, 2.919 Factory strumming patterna, 12.918 punih GOLD performance patterna i 10.637 legacy GOLD patterna.

Detaljni postojeći razvojni roadmap nalazi se u `ULTRA_PLAN.md`, a novi izvedbeni put od verzije 3.16 do proizvoda **AI Premium Arranger** nalazi se u `AI_PREMIUM_ARRANGER_PLAN.md`. Premium dokument definira Sesije 15–30, P0/P1/P2 prioritete, AI podatkovne ugovore, mapping/solo/polifonijske gateove, listening benchmark i uvjete za verziju 5.0.

Audit ranijeg prototipa nalazi se u `APP_AUDIT.md`, a test piano-roll/editorskog sloja u `data/phase4-editor-test-report.json`.
## 4.14 MAX Performance Engine
The optimizer now includes role-aware processing for drums, bass, rhythm guitar, power-chords and solo, plus the 4.13 Echo/Terca relationship engine. Select **MAX Performance 4.14** in the Optimizer GUI. Factory remains the only velocity authority.

## 4.16 Neural AI Learning System

The project now includes a local PyTorch learning subsystem under `src/dna_midi_studio/ai_learning/`.
Build the neural dataset with `build-learning-dataset.bat` and train with `train-ai.bat`.
The neural layer never owns velocity: Factory remains the sole velocity/dynamics authority and all AI output requires deterministic hard validation. See `AI_LEARNING_SYSTEM_ANALYSIS.md`.

## 4.18 Song-conditioned neural inpainting

The AI subsystem can analyze a real MIDI song region, generate 8 deterministic masked-repair candidates and render three A/B/C MIDI alternatives while preserving velocity and non-target MIDI events. Use `ai_reconstruct_song.py` or `ai-reconstruct-song.bat`. Empty-track `REPLACE` remains blocked until retrieval-seed and Factory-velocity authorities are integrated. See `AI_SONG_INPAINTING_V418.md`.


## v5.01 Corpus Evidence Arranger

Build a Pattern DNA evidence database from a MIDI folder:

```bat
build-pattern-evidence.bat "D:\MIDI\Factory" FACTORY
build-pattern-evidence.bat "D:\MIDI\Gold" GOLD
```

The extractor is read-only on source MIDI, segments musical sections into phrase windows, resolves instrument roles, creates deterministic Pattern DNA, applies the role-aware Quality Gate, and inserts only accepted evidence into `data/pattern-evidence.sqlite`. See `RELEASE_5.01.md`.


## Suno-like Symbolic Brain 6.10

The project now includes `dna_midi_studio.suno_like_brain.SunoLikeConductor`. It is a whole-song symbolic arranger/reconstructor, not an audio clone of Suno. Its production loop is: SongMap/roles/harmony -> REMI+/FIGARO-inspired token language -> hierarchical section intent -> GOLD/Factory memory retrieval -> optional neural candidate generation (Transformer infill, event decoder, autoregressive decoder, 4-bar multibar decoder, context/phrase/section/transition scorers) -> global critic/retry -> Factory-only velocity -> protected-event and Pa800 validators.

`SunoLikeConductor.neural_replace_region(...)` creates real A/B/C MIDI candidates and never auto-commits them. The restored checkpoints under `models/`, `learning_data/`, and `data/ai_*` make the previously present AI-learning modules executable again. `suno_brain_cli.py` emits the structured whole-song decision plan for inspection.

Research influences used for architecture: MidiTok REMI+ multi-track tokenization, FIGARO description-conditioned structure, Magenta MusicVAE/GrooVAE hierarchical/groove modeling, and multitrack Transformer-style cross-instrument context. External repositories are architectural references; DNA/Factory/GOLD authority and Pa800 safety remain local project rules.

## 6.20 Full-Song Autoregressive Reconstruction

New public entry point:

```python
from dna_midi_studio.suno_like_brain import reconstruct_full_song_autoregressive
result = reconstruct_full_song_autoregressive(raw, project_root=ROOT, source="song.mid")
```

The 6.20 conductor performs whole-song role/section analysis, conservative role-first repair,
bounded A/B/C neural/evidence regeneration, Factory-only velocity proof, and independent
preservation checks outside explicitly authorized regeneration windows. Solo, terca and echo
remain protected from blind regeneration.

See `FULL_SONG_AI_6.20_REPORT.md` and `tests/test_full_song_autoregressive_v620.py`.

## 7.01 vendored MIDI-GPT backend
The project now bundles the reviewed MIT-licensed MIDI-GPT 0.3.4 source under `third_party/MIDI-GPT-0.3.4`. Run `scripts\\install_midigpt_windows.bat` to create the isolated backend environment. DNA Studio keeps Factory-only velocity authority and uses MIDI-GPT only inside explicitly authorized generative regions. See `GITHUB_MIDIGPT_7.01_INTEGRATION.md`.


## 7.03 Generative Backend Router
KEEP / REPAIR / REGENERATE now route through a shared proposal layer. MIDI-GPT 0.3.4 and the existing DNA neural stack can compete under one symbolic critic. External candidates are scope-gated, protected-event-gated, and Factory velocity is rebound before acceptance. See `GITHUB_GENERATIVE_ROUTER_7.03.md`.

## 7.10 GitHub Symbolic Foundation
7.10 vendors the official MIT MidiTok implementation and the Microsoft Muzic / MuseCoco MIDI attribute extractor. `SymbolicFoundation` creates a velocity-blind REMI+-style canonical stream plus objective song/track attributes (instrumentation, density, polyphony, register, onset activity). `GenerativeBackendRouter` uses this intent to condition MIDI-GPT note density before candidate generation. Factory remains the only velocity authority.

Optional Windows setup for the real vendored MidiTok runtime: `scripts\\install_symbolic_backends_windows.bat`.

## 7.20 Cross-Track Brain

Version 7.20 adds `CrossTrackBrain`, a GETMusic/Museformer-inspired planning layer. Before a REPAIR/REGENERATE request reaches MIDI-GPT, the target region is evaluated against peer tracks in a fine local window and against the 7.10 whole-song symbolic summary. The resulting context adjusts note-density conditioning and sampling confidence while preserving all 7.03 mutation gates and Factory-only velocity authority.

See `GITHUB_CROSS_TRACK_BRAIN_7.20.md`.

## 7.30 Candidate Critic / Preference Brain

Generation candidates from MIDI-GPT and the DNA neural stack are now ranked by a backend-neutral musical preference critic. The critic evaluates groove fit, harmonic fit, cross-track fit, repetition/variation balance, density fit, transition quality and safety. Velocity is explicitly excluded; Factory remains the sole velocity authority. Candidate selection uses the preference score as the dominant signal and retains the previous low-level sanity/evidence score only as a minority signal.

## 7.40 Self-Refinement Loop

The candidate critic now feeds bounded diagnostic feedback back into generation. Weak groove, harmony, cross-track fit, repetition, density or transition quality can trigger up to two controlled MIDI-GPT retry rounds. Refined candidates must still pass scope safety and Factory-only velocity rendering before ranking. See `GITHUB_SELF_REFINEMENT_7.40.md`.

## 7.50 Hierarchical Song Planner

Global read-only song planning now runs before destructive generation. It adds section energy curves, role lifecycle (entry/exit/silence/density), transition intent and a confidence gate for REGENERATE. Velocity remains excluded from AI planning and Factory remains the sole velocity authority.


## 8.00 DNA Calibration
See `DNA_CALIBRATION_8.00_REPORT.md`. Terca fallback is now GOLD-DNA selective (PLAY/SKIP/HOLD) with 3rd/6th voicing; Factory remains velocity authority.

## 8.10 Bass + Drum DNA Calibration
GOLD performance evidence now calibrates bass/drum density, bass gate behavior, drum element balance and shared-source drum↔bass pocket ranking. Factory remains the only velocity authority. See `DNA_BASS_DRUM_CALIBRATION_8.10_REPORT.md`.

## 8.20 Rhythm Guitar / Strum DNA Calibration
Rhythm-guitar selection now combines GOLD accompaniment intent with Factory-only strum execution. GOLD contributes density/gate/syncopation/section character; Factory remains authoritative for Down/Up strokes, inter-string spread, voicing, and velocity. The 7.41 polyphony protection remains mandatory.


## 8.31 Terca + Rhythm Guitar safety
See `TERCA_GUITAR_SAFETY_FIX_8.31.md`. Terca now requires an eligible instrumental harmony layer and is blocked for vocal/lyric leads. Healthy chordal rhythm-guitar gates are preserved; only pathological micro-gates are repaired in the safe pass.

## 8.30 SOLO / ORNAMENT DNA CALIBRATION
- Raw GOLD ornament corpus drives phrase placement, interval, duration and corpus-rate gating.
- Long solos are no longer eligible for an ornament on every gap; density follows GOLD evidence.
- Solo candidate preference ranking includes velocity-free GOLD ornament-density fit.
- Pitch bend is preserved/evidence-gated rather than synthesized blindly.
- 8.31 terca/guitar safety rules remain active.
- Targeted combined regression: 74/74 PASS.
See `SOLO_ORNAMENT_DNA_8.30_REPORT.md`.

## 8.40 Echo / Answer DNA Calibration
GOLD relationship DNA now controls echo PLAY/SKIP/HOLD, delay, duration and phrase placement. Echo is no longer a fixed copy+delay rule. See `ECHO_ANSWER_DNA_8.40_REPORT.md`.

## 8.50 Power-Riff / Riff DNA Calibration

8.50 adds GOLD evidence-driven power-riff/riff ranking and protects healthy staccato/mute gates. See `POWER_RIFF_DNA_8.50_REPORT.md`.

## 8.60 — Accompaniment / Strings / Brass / Pad DNA Calibration
GOLD accompaniment evidence now calibrates accompaniment-family candidate ranking. The corpus contains 3,039 accepted accompaniment patterns; strings/brass/pad are conservatively projected from that shared evidence plus their role behavior policies rather than mislabeled as separately learned GOLD corpora. Factory remains the sole velocity authority. Regression: 32/32 PASS.

## 8.70 — Full DNA Balance / Cross-Role Calibration
Adds a read-only, velocity-free cross-role balance scorer to the candidate critic. It evaluates existing bass↔drum pocket, guitar↔pad/strings space, brass↔lead call-response, and terca/echo↔lead masking. It never invents missing roles and preserves Factory-only velocity authority. See `FULL_DNA_BALANCE_8.70_REPORT.md`.

## 8.80 Full Corpus Calibration
The safe repair path is now corpus-calibrated against 164 canonical VALJA MIDI files. Bass gate edits fell from 50.88% to 5.29%, rhythm-guitar gate edits from 7.17% to 0.57%, and power-riff safe edits from 22.91% to 0% by preserving valid short mute/staccato articulation. See `FULL_CORPUS_CALIBRATION_8.80_REPORT.md`.

## 9.00 Balkan Meter / Groove Calibration
GOLD performance patterns now provide direct meter-specific density/gate/syncopation priors for 4/4, 2/4, 7/8 and 9/8. Candidate ranking no longer treats odd meters as if they were 4/4. 6/8 remains a truthful low-confidence fallback until stronger direct corpus evidence exists. This layer is read-only and velocity-free; Factory remains the only velocity authority. See `BALKAN_METER_GROOVE_9.00_REPORT.md`.

## 9.01 Factory Style Family Calibration
Direct Factory profiles are now available for 6/8, Rock, Techno/Dance, Ballad and Beat. The 6/8 meter no longer falls back to 4/4 when Factory evidence is available. See `FACTORY_STYLE_FAMILY_9.01_REPORT.md`.

## 9.10 — Tempo-Dependent Calibration
Adds GOLD/Factory tempo-bucket priors for slow, medium, brisk and fast material. Candidate scoring and bounded generation guidance now account for BPM. Velocity remains Factory-only. See `TEMPO_DEPENDENT_CALIBRATION_9.10_REPORT.md`.

## 9.20 — Instrument / Register Calibration
Adds evidence-based register ranking to the candidate critic. Factory supplies absolute register evidence where available, GOLD supplies relative phrase-span evidence, and the original phrase remains the primary anchor for solo/lead material. There is no hard octave clamp or automatic octave folding, and drums/percussion are excluded from melodic register logic. Velocity remains FACTORY ONLY. See `INSTRUMENT_REGISTER_CALIBRATION_9.20_REPORT.md`.

## 9.30 RX/DNC Articulation Calibration
- Adds velocity-free `articulation_fit` to candidate ranking.
- Preserves real pitch-bend/aftertouch/CC articulation evidence during regeneration.
- Protects melodic ornament density and guitar/riff mute-staccato character.
- Never invents RX/DNC trigger mappings. Exact confirmed sound profile/map remains mandatory for executable device articulation.
- Regression: 30/30 PASS.
