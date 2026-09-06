# Završne sesije — DNA MIDI Studio

Datum plana: 3. rujna 2026.
Polazna točka: `SOFTWARE_VALIDATED`, 37/37 testova prije završnih sesija; fizički Pa800 je `WAITING_FOR_DEVICE`.

## Pravilo rada

Svaka sesija ima jedan ograničen cilj, produkcijski ulaz, strojni dokaz i ažuriran compliance zapis. Funkcija nije završena dok nije dostupna kroz podržani ulaz aplikacije, dok nema opaženi MIDI rezultat i dok ne prođe neovisnu provjeru. Postojeći core i pravila Factory/GOLD izolacije ne smiju se oslabiti.

## Raspored

### Sesija 1 — Chord Timeline i Phase Arranger — ZAVRŠENO

- akordi najmanje na pola takta, s bas/harmonija/melodija dokazima i confidenceom;
- granice faza prema gustoći, ponavljanju, harmoniji, pauzama i prijelazima;
- inspectable `KEEP`, `REPAIR`, `REPLACE`, `MANUAL_REVIEW` plan prije mutacije;
- solo ostaje `KEEP` i nikada se ne kvantizira;
- dry-run, transformation budget i deterministički test na sintetičkom i stvarnom songu.

**Rezultat:** Phase Arranger radi kroz GUI/API; pola-takta analiza, dry-run, sintetički apply i stvarni GOLD determinizam prolaze. Puni paket ima 43/43 PASS. Dokaz: `data/phase5-test-report.json`.

### Sesija 2 — Drum i Percussion reconstruction — TEMELJ VALIDIRAN / ČEKA PRODUKCIJSKI KORPUS

- stvarna section-aware zamjena GOLD patternima, ne samo prosječnim timingom;
- kick, snare, hat, cymbal, tom, ghost i fill kao odvojeni elementi;
- Factory velocity po svakoj drum noti;
- prijelazni kontinuitet, kit-map sigurnost i kontrola prekomjerne perkusije.

**Kraj sesije:** slab drum/percussion fixture mjerljivo je popravljen bez stuck nota, krivog kita ili GOLD dinamike.

**Ponovno izgrađeni rezultat:** dependency-free MIDI codec, section-aware `PLAN -> APPLY` engine i CLI rade na stvarnom binarnom sintetičkom fixtureu. Slabi prozor s 4 note zamijenjen je s 26 element-aware nota; svaki velocity dolazi iz pripadajućeg Factory profila. Program Change ostaje očuvan, kit mismatch i nedostajući Factory profil vraćaju `MANUAL_REVIEW`, element budget ograničava prekomjernu perkusiju, a isti seed daje iste MIDI bajtove. Samostalni gate ima 12/12 PASS. Dokazi: `data/session2-test-report.json`, `artifacts/session2-before.mid`, `artifacts/session2-after.mid` i `artifacts/session2-manifest.json`.

**Preostala blokada:** produkcijski Factory/GOLD registryji, stvarni song korpus i povijesni GUI/API source nisu u ovom radnom prostoru. Zbog toga cijela sesija još nije označena `ZAVRŠENO`.

### Sesija 3 — Bass, power-chord i riff engine — TEMELJ VALIDIRAN / ČEKA PRODUKCIJSKI KORPUS

- GOLD događaji kao chord/scale funkcije umjesto kopiranja apsolutnih tonova;
- korijen, inverzija, approach note i manual-bass zaštita;
- drum–bass relationship odabir, voice-leading, register i collision budget;
- power/riff identitet ostaje zaštićen kada je postojeći dio kvalitetan.

**Kraj sesije:** chord-aware rekonstrukcija prolazi pozitivne i negativne fixturee te stvarni song.

**Ponovno izgrađeni rezultat:** GOLD registry koristi samo stupnjeve, intervale, inverzije i approach funkcije; apsolutni GOLD pitch se odbija. Chord timeline mapira C-dur i a-mol ćelije, potvrđena veza `210.010.001 -> 220.010.001` bira bass pattern, a Factory profil određuje program, registar i velocity. Manual bass i kvalitetan postojeći power/riff vraćaju `KEEP`; nedostajući akord, odnos, profil/program, nemoguć voicing ili prekoračen collision budget vraćaju `MANUAL_REVIEW`. Voice-leading, power-chord inverzija, round-trip i isti seed prolaze. Samostalni gate ima 16/16 PASS, a recovery suite Sesija 2–3 ukupno 28/28 PASS. Dokazi: `data/session3-test-report.json`, `artifacts/session3-before.mid`, `artifacts/session3-after.mid` i `artifacts/session3-manifest.json`.

**Preostala blokada:** isti gate mora proći nad produkcijskim GOLD/Factory registryjima i stvarnim songom kroz podržani GUI/API ulaz prije statusa `ZAVRŠENO`.

### Sesija 4 — Factory Guitar Mode i strumming — TEMELJ VALIDIRAN / ČEKA PRODUKCIJSKI FACTORY DOKAZ

- Factory ACC potezi ostaju jedini autoritet ritam-gitare;
- down/up/block/mute/stop, gate, inter-string timing i raspon žica;
- Guitar Mode kontrolne note samo iz potvrđene Korg mape;
- nemogući voicing ili nepotvrđen trigger vraća `KEEP` ili `MANUAL_REVIEW`.

**Kraj sesije:** strum je harmonijski ispravan, izvediv i potpuno dokaziv iz Factory izvora.

**Ponovno izgrađeni rezultat:** ritam-gitara odbija svaki GOLD pattern i bira samo Factory ACC dokaz sa stabilnim pattern/profile/source ID-evima. Down/up potezi čuvaju smjer i inter-string timing, block note imaju zajednički onset, gate ostaje iz Factory poteza, a C-dur i a-mol voicingi prolaze string/fret/register i maksimalni fret-span validator. Mute/stop kontrolne note nastaju samo iz potvrđene, verzionirane mape točnog programa; nedostajuća ili nepotvrđena akcija vraća `MANUAL_REVIEW`. Sintetička mapa mora imati eksplicitni testni opt-in i nije produkcijski Pa800 dokaz. Session 4 ima 19/19 PASS, a recovery suite Sesija 2–4 ukupno 47/47 PASS. Dokazi: `data/session4-test-report.json`, `artifacts/session4-before.mid`, `artifacts/session4-after.mid` i `artifacts/session4-manifest.json`.

**Preostala blokada:** potreban je produkcijski Factory strumming registry i službeno ili uređajno potvrđena Pa800 Guitar Mode mapa. Bez njih automatski kontrolni triggeri ostaju blokirani.

### Sesija 5 — Solo, trill, expression, terca i echo — TEMELJ VALIDIRAN / ČEKA PRODUKCIJSKI KORPUS

- originalna melodija ostaje zaštićena i timing se ne kvantizira;
- kontekstualni trill/grace/slide samo uz GOLD intervalni i frazni dokaz;
- CC11 phrase/tension profil je zaglađen, ograničen i Factory-headroom siguran;
- terca i echo imaju pozitivne i negativne relationship testove;
- echo cilj ostaje podesivo tiši od glavnog sola bez feedback nakupljanja.

**Kraj sesije:** stavke 26 i 29 prelaze u `SOFTWARE_VALIDATED` ili ostaju eksplicitno blokirane dokazom.

**Ponovno izgrađeni rezultat:** engine radi isključivo kao dodatni sloj i bajt-po-bajt čuva onset, trajanje, pitch i velocity svake izvorne solo note. Trill, grace i slide nastaju samo iz relativnog GOLD intervalnog dokaza i slobodnog vremenskog prostora; terca zahtijeva potvrđen odnos i dijatonski interval od tri ili četiri polutona. Echo je odgođen, kraći, Factory-tiši i nikada se rekurzivno ne umnaža. Delay/Echo se smješta na prvi potpuno slobodan MIDI track, zadržava kanal izvornog sola i kopira CC00, CC32, Program Change te dostupni mixer/expression setup; nikada ne dodaje Delay note na solo track niti otvara 17. traku. Vanjski `trackNumber/channelNumber` nedvosmisleno su 1-based, interni `track_index/channel` 0-based, exact Bank/Program čita se samo s odabrane solo trake, a dijeljeni solo kanal vraća `MANUAL_REVIEW`. Slabo potvrđeni GOLD ornament/third/echo dokazi više ne generiraju događaje. Session 5 ima 36/36 PASS, a recovery suite Sesija 2–5 ukupno 83/83 PASS. Dokazi: `data/session5-test-report.json`, `artifacts/session5-before.mid`, `artifacts/session5-after.mid` i `artifacts/session5-manifest.json`.

**Preostala blokada:** produkcijski GOLD ornament/relationship corpus, stvarni song kroz podržani GUI/API ulaz i slušna provjera nisu dostupni. Zato se stavke 26 i 29 vode kao validiran temelj, ne kao završen produkcijski modul.

### Sesija 6 — RX engine — TEMELJ VALIDIRAN / ČEKA POTVRĐENU PRODUKCIJSKU MAPU

- verzionirani katalog potvrđenih RX noise/humanize događaja po zvuku;
- false-positive zaštita i zabrana nagađanja triggera;
- primjena samo uz točan Sound/Bank/Program i dovoljan Factory/Korg dokaz;
- audit i rollback svake artikulacije.

**Kraj sesije:** RX je aktivan samo za potvrđene mape; sve ostalo sigurno ostaje `KEEP`.

**Ponovno izgrađeni rezultat:** verzionirani RX katalog zahtijeva stabilne map/profile/source ID-eve, izvor `official-korg`, `device-captured` ili eksplicitno dopušten `synthetic-test`, te točno podudaranje CC00, CC32 i Program Changea ciljne trake. Engine ne izvodi trigger iz naziva zvuka ni raspona nota. Potvrđene akcije koriste uvjete every-note, long-note, leap i phrase-end, dok velocity svake generirane RX note dolazi samo iz Factory profila. Nepoznata akcija, nepotvrđena mapa, sound mismatch, nedostajući Bank Select, prekoračen budget ili sintetička mapa bez opt-ina vraćaju `MANUAL_REVIEW`. Postojeći RX događaji se ne dupliciraju, ponovna primjena nije rekurzivna, svi izvorni događaji i ciljni sound ostaju netaknuti, a isti seed daje iste MIDI bajtove. Session 6 ima 26/26 PASS, a recovery suite Sesija 2–6 ukupno 100/100 PASS. Dokazi: `data/session6-test-report.json`, `artifacts/session6-before.mid`, `artifacts/session6-after.mid` i `artifacts/session6-manifest.json`.

**Preostala blokada:** u snapshotu nema službene ni uređajno snimljene Pa800 RX mape, povijesnog GUI/API ulaza ni fizičke slušne provjere. Sintetička mapa potvrđuje sigurnost enginea, ali se ne smije koristiti kao produkcijski autoritet.

### Sesija 7 — DNC engine — TEMELJ VALIDIRAN / ČEKA POTVRĐENU PRODUKCIJSKU MAPU

- data-driven DNC trigger mapa, role i range validacija;
- aftertouch, CC, key-switch i proprietary događaji ne smiju se izmišljati;
- collision, trajanje, program i note-off provjera;
- adversarial test protiv lažne DNC detekcije.

**Kraj sesije:** stavka 28 ima stvarni produkcijski put ili dokumentiran dokaz da Pa800 nema primjenjivu DNC funkciju za odabrani zvuk.

**Ponovno izgrađeni rezultat:** data-driven DNC katalog zahtijeva stabilne map/profile/source ID-eve, točan CC00/CC32/Program, potvrđenu ulogu te odvojeni playable i trigger raspon. Engine podržava samo izričito mapirane key-switch note, CC i channel pressure. Velocity key-switcha dolazi iz Factory profila; SysEx/proprietary događaji i zaštićeni Bank/RPN/NRPN kontroleri su blokirani. Nepotvrđena ili sintetička mapa bez opt-ina, pogrešan role/range/sound, nepoznata artikulacija i prekoračen budget vraćaju `MANUAL_REVIEW`. Postojeći triggeri se ne dupliciraju, ponovna primjena nije rekurzivna, key-switch duration/note-off i collision su validirani, svi izvorni događaji ostaju netaknuti, a isti seed daje iste MIDI bajtove. Session 7 ima 30/30 PASS, a recovery suite Sesija 2–7 ukupno 130/130 PASS. Dokazi: `data/session7-test-report.json`, `artifacts/session7-before.mid`, `artifacts/session7-after.mid` i `artifacts/session7-manifest.json`.

**Preostala blokada:** nema službene ni uređajno snimljene Pa800 DNC mape, povijesnog GUI/API ulaza ni fizičke provjere. Sintetički katalog potvrđuje sigurnost standardnih MIDI događaja, ali proprietary DNC ostaje namjerno blokiran.

### Sesija 8 — Agent runtime i opcionalni Cloud/API — ZAVRŠENO

- lokalni strukturirani poslovi, handoff, approval, trace i eval zapis;
- agenti dobivaju read-only brief i nikad ne pišu finalni MIDI;
- cloud je isključen po defaultu i ne prima MIDI bez izričitog pristanka;
- API ključ nije u projektu; prekid mreže ne utječe na offline core;
- validator ostaje konačni autoritet.

**Kraj sesije:** stavka 34 radi kroz ograničeni runtime; stavka 35 je siguran opt-in dodatak.

**Rezultat:** dependency-free lokalni manager-with-specialists runtime provodi stabilne task/owner ID-eve, ekskluzivno vlasništvo datoteka, potpuni read-only brief, ugovorene handoffe, hash-chain trace, zabilježeni testni izlaz, ljudsko odobrenje za osjetljive akcije i zaseban Pa800 validator gate. Agentski submission ne može navesti `.mid`/`.midi` kao proizvedenu datoteku niti završiti posao bez neovisnog validatora. Cloud adapter je ugašen po defaultu, zahtijeva izričit pristanak, prihvaća samo metadata payload bez MIDI-ja i tajni te se pri mrežnoj grešci vraća na identični lokalni core. CLI i strojni manifest su ponovno izvršivi. Session 8 ima 21/21 PASS, a recovery suite Sesija 2–8 ukupno 151/151 PASS. Dokazi: `data/session8-test-report.json`, `data/session8-demo-task.json` i `artifacts/session8-manifest.json`.

### Sesija 9 — Jedinstveni engine: GUI, web, CLI i batch — ZAVRŠENO

- izdvojiti glazbenu logiku iz transportnog `server.py` sloja;
- GUI, API, CLI i batch koriste isti konfiguracijski model i pipeline;
- 16-track pregled, plan i izvještaji daju iste rezultate na svim ulazima;
- kvalitetniji lokalni GM/Pa800 preview bez utjecaja na MIDI validaciju.

**Kraj sesije:** parity test potvrđuje jednake manifeste i MIDI hashove.

**Rezultat:** glazbena logika Sesija 2–7 dostupna je kroz jedan transportno-neutralni dispatcher i verzionirani `PipelineConfig`. Direktni engine, CLI, lokalni HTTP API, GUI adapter i batch za iste MIDI bajtove i konfiguraciju daju jednak manifest i jednak output SHA-256. Pipeline strogo provjerava registry putanje, ne mijenja ulaz, zapisuje svaki stage/plan, uvijek daje 16-track pregled te ograničeni read-only GM/Pa800 preview koji ne sudjeluje u validaciji. Session 9 ima 19/19 PASS, a recovery suite Sesija 2–9 ukupno 170/170 PASS. Dokazi: `data/session9-test-report.json`, `data/session9-demo-config.json`, `artifacts/session9-before.mid`, `artifacts/session9-after.mid` i `artifacts/session9-manifest.json`.

### Sesija 10 — Atomic commit, cancel, resume i crash recovery — ZAVRŠENO

- privremeni izlaz, neovisna provjera i atomsko objavljivanje;
- batch progress, cancel token, nastavak prema source/config/database hashovima;
- zaključavanje izlaza, disk-full/locked-file simulacija i rollback;
- Unicode, dugi Windows pathovi, sanitizacija imena i path-traversal zaštita.

**Kraj sesije:** prekinut ili srušen proces ne ostavlja djelomičan MIDI.

**Rezultat:** `AtomicMidiPublisher` piše kandidata u privremenu datoteku, izvršava validator prije objave i tek tada radi atomski replace. Ekskluzivni lock sprječava paralelno pisanje, a journal dopušta resume samo kada se podudaraju source, config i database SHA-256 te stvarni output hash. Cancel prije ili nakon privremenog zapisa, validator failure, verifier crash i simulirani disk-full rade rollback bez djelomičnog MIDI-ja. Batch čuva per-file rezultat i nastavlja nakon izolirane greške. Unicode se čuva, Windows rezervirana/nevaljana imena se sanitiziraju, duljina se ograničava, a traversal ostaje unutar autoriziranog direktorija. Session 10 ima 22/22 PASS, a recovery suite Sesija 2–10 ukupno 192/192 PASS. Dokazi: `data/session10-test-report.json`, `artifacts/session10-before.mid`, `artifacts/session10-after_OPT.mid` i pripadajući journal.

### Sesija 11 — Neovisni verifier i reproduktivnost — ZAVRŠENO

- parser/verifier ne koristi optimizerov verdict;
- protected-note diff, event preservation, manifest-to-MIDI i Pa800 ugovor;
- idempotency pravila, isti seed i jednaki rezultati s različitim brojem workera;
- provjera rollbacka i autoriziranih iznimki.

**Kraj sesije:** svaki nevaljan kandidat je blokiran, a valjan rezultat je byte-reproducibilan.

**Rezultat:** zasebni byte-level verifier ne uvozi niti vjeruje optimizerovu/plannerovu verdictu. Ponovno parsira izvor i kandidat, uspoređuje originalne note uključujući velocity, štiti SysEx/meta, Bank Select, Program Change i RPN/NRPN, a nove note dopušta samo unutar eksplicitne track/channel/time/pitch autorizacije s razlogom. Manifest, završni stage i atomic journal moraju pokazivati stvarni kandidat hash. Implementirani su Pa800 SMF/PPQ/channel/marker/setup gate, note-pairing blokada, idempotency i reproducibility za 1/2/4 workera. Session 11 i naknadna solo mapping regresija zajedno daju recovery suite Sesija 2–11 od 223/223 PASS. Dokazi: `data/session11-test-report.json` i `artifacts/session11-independent-report.json`.

### Sesija 12 — Property, fuzz, adversarial i puni corpus — ZAVRŠENO

- truncated chunk/VLQ, SMPTE, running status, SysEx, RPN/NRPN, aftertouch i pitch bend;
- zero-note i ogromne trake, illegal bytes, EOT greške i stuck note;
- lažni RX/DNC/terca/echo i duboko skrivena GOLD velocity polja;
- puni Factory/GOLD rebuild, stabilni ID-evi, checksumovi i regression vault;
- kalibracija odluka po ulozi umjesto univerzalnog confidence praga.

**Kraj sesije:** svi MUST testovi, regresijski korpus i objašnjeni skipovi imaju strojne izvještaje.

**Ponovno izgrađeni rezultat:** 36/36 adversarial testova pokriva truncated header/chunk/VLQ, SMPTE, running status, SysEx, RPN/NRPN, channel/poly aftertouch, pitch bend, illegal data, EOT, orphan/dangling/zero-duration note, zero-note MIDI i 5.000-note round-trip. Polifonijski testovi potvrđuju da se računaju svi aktivni sustain repovi, a ne samo note istog onseta, te da neovisni validator blokira prekoračenje kanalskog limita. Deterministički fuzz izvršava 200 mutacija bez curenja neočekivanih iznimki. Duboko skrivena GOLD dinamika, proprietary DNC, RX velocity te apsolutni solo pitch se odbijaju; slabo potvrđeni ornament/third/echo dokazi više se ne primjenjuju. Role calibrator nema univerzalni fallback, a namespace-aware checksum vault zaključava 12 demo/produkcijskih izvora i 59.635 stabilnih ID-eva. Recovery suite Sesija 2–12 ima 261/261 PASS.

**Produkcijski corpus rezultat:** vraćena arhiva sadrži 3.211 Factory i 182 GOLD MIDI datoteke. Ponovno je izgrađeno svih pet registryja, legacy gate ima 43/43 PASS, a namespace-aware vault zaključava 12 izvora i 59.635 stabilnih ID-eva bez runtime-pattern kolizije. `data/session12-test-report.json` više nema corpus skipove.

### Sesija 13 — Windows release paket — ZAVRŠENO

- podržane Python/Windows verzije, zaključane ovisnosti i clean-machine smoke test;
- `pokreni.bat`, `izgradi-dna.bat`, `testiraj.bat` i batch/CLI workflow;
- user guide, troubleshooting, checksum i reproducibility manifest;
- jedan jedini korisnički ZIP bez zastarjelih međuarhiva.

**Kraj sesije:** izdanje dobiva `SOFTWARE_VALIDATED` i jedan provjerljiv release artefakt.

**Rezultat:** portable paket podržava Windows 10/11 x64 i CPython 3.11–3.14 bez third-party runtime ovisnosti. ASCII/CRLF skripte `pokreni.bat`, `izgradi-dna.bat` i `testiraj.bat` imaju kompatibilne `run.bat`/`install.bat` aliase. ZIP uključuje produkcijske registryje, kod, testove, vodič, PDF i hashirane dokaze. Session 13 ima 16/16 PASS, a objedinjeni suite nakon Sessiona 38 ima 2900/2900 PASS. Paket je `dist/DNA-MIDI-Studio-Pa800-Windows-4.11.1-device-certification-intake-foundation.zip`.

### Sesija 14 — Fizička Pa800 certifikacija

- korisnik izvodi USB import, SHIFT + Execute, marker/CV, kanal i NTT provjeru;
- preslušavaju se svi Intro/Variation/Fill/Break/Ending prijelazi;
- provjeravaju se RX/DNC, gitara, solo, terca, echo, clipping i headroom;
- Style se sprema, ponovno učitava i rezultat se potpisuje s checksumom.

**Kraj sesije:** samo potpuni prolaz smije promijeniti status u `PA800_DEVICE_CERTIFIED`.

**Pripremljeni rezultat:** 12/12 softverskih testova generira i provjerava funkcionalni Style sa svih deset osnovnih marker-sekcija te zasebni polifonijski stress Style sa svih osam kanala i vrhom od 54 istodobne MIDI note. `kit-manifest.json` zaključava svaki artefakt SHA-256 hashom, a deterministički uređajni ZIP dostupan je kroz GUI i lokalne `/api/device-test-kit` i `/api/device-preflight` rute. Rezultatna shema odbija nepotpunu provjeru, budući datum, krivi model/OS, izmijenjeni kit, path traversal i nedostajući slikovni ili audio dokaz. Potpuna ljudska potvrda može se obraditi naredbom `py session14_device_check.py verify ...`, ali preflight ne tvrdi da je vidio instrument. Dokazi: `data/session14-preflight-report.json`, `SESSION14_DEVICE_CHECKLIST.md` i `artifacts/session14-device-kit/`.

**Preostala blokada:** fizički Korg Pa800 još nije korišten. Status ostaje `WAITING_FOR_DEVICE` dok korisnik ne dovrši USB import, Track Type/NTT, slušni, polifonijski, save/reload i evidence postupak.

### Sesija 15 — Premium Baseline Freeze — ZAVRŠENO

Session 15 uvodi devet strogih Draft 2020-12 podatkovnih ugovora, `PremiumConfig`, deterministic config/plan hash, P0/P1 feature matricu, immutable baseline produkcijskih registryja i izvještaja te validirani referentni Pa800 MIDI. AI izlaz je isključivo read-only plan: MIDI mutacija, finalni zapis, validator bypass, GOLD dinamika i promjena originalnog sola izričito su zabranjeni.

**Rezultat:** 20/20 PASS. Baseline `premium-3.17-98a6d52a09ccc789` zaključava autoritativnu arhivu, pet produkcijskih registryja, schema katalog, snapshot izvještaje i referentni Style. Dokazi: `data/premium-baseline.json`, `data/premium-feature-matrix.json`, `data/session15-test-report.json`, `premium/schemas/catalog.json` i `artifacts/session15-read-only-plan.json`.

### Sesija 17 — Production Adapter — FOUNDATION VALIDATED / PRODUCTION PARTIAL

Session 17 uvodi jedinu dopuštenu granicu između pet produkcijskih DNA registryja i enginea Sesija 2–7. Svaki stage prije mapiranja provjerava stabilni fizički `trackUid`, puni vremenski CC00/CC32/Program SoundBinding i shared-channel vlasništvo. Pipeline prihvaća točno jedan izvor podataka — mali testni registry ili produkcijski adapter — te za svaki stage zapisuje before/after hash, broj nota/traka i rollback status.

Drum/percussion koriste produkcijski GOLD ritam samo kada exact Factory kit ima profil za svaku notu. Bass, power-riff i riff koriste samo relativne GOLD intervale, dok apsolutni pitch, registar i velocity dolaze iz akorda i Factory profila. Gitara koristi isključivo Factory strumming; GOLD gitarski autoritet i nepotvrđene Guitar Mode kontrole ostaju zabranjeni. Solo adapter je namjerno ograničen na exact Factory CC11 izraz i čuva fingerprint svih originalnih nota. RX i DNC vraćaju `DEVICE_BLOCKED` dok nema potvrđenih Pa800 mapa.

**Rezultat:** 35/35 PASS. Dokazani su stvarni Factory drum i bass izvori, stvarni Factory strumming segment, tri stvarna GOLD songa koja sigurno završavaju u manual reviewu bez nagađanja uloge, CLI/web/API/GUI/batch parity te byte-exact no-op rollback. Dokazi: `data/session17-test-report.json`, `data/session17-production-registry-catalog.json`, `data/session17-real-corpus-manifest.json` i `artifacts/session17-production-adapter-manifest.json`.

### Sesija 18 — Track Identity i Solo Safety 2.0 — ZAVRŠENO

Session 18 uklanja klasu pogrešnog track/channel mapiranja. Svaka fizička traka dobiva stabilni `trackUid`; interni indeksi i vanjski brojevi izričito su odvojeni. Bank Select i Program Change provjeravaju se po fizičkoj traci kroz cijeli vremenski prozor, uključujući promjene usred pjesme. Pipeline prije obrade zaključava fingerprint originalnog sola i provjerava ga nakon svakog stagea.

**Rezultat:** 28/28 PASS. SMF0 merge i shared-channel konflikt su vidljivi, postojeći shared channel traži izričito odobrenje, a Delay/Echo bira prvi potpuno slobodan track i nikada ne otvara 17. traku. Mapping manifest prikazuje izvorni/ciljni `trackUid`, Track, Channel i SoundBinding. Dokazi: `data/session18-test-report.json`, `data/session18-schema-catalog.json`, `artifacts/session18-mapping-manifest.json` i tri ugovora u `premium/schemas/v2/`.

### Sesija 19 — Song Understanding 2.0 — FOUNDATION VALIDATED / PRODUCTION CALIBRATION PENDING

Session 19 uvodi strogi `SongMap 2.0` i zaseban correction-overlay ugovor. Analizator je read-only i velocity-blind: obrađuje promjenjivi tempo/takt, beat/downbeat, half-bar akorde, sus/slash/seventh kvalitete, modalnu i neharmonsku nesigurnost, kadence, frazne signale, vremenske uloge i full-duration polifoniju. Svaki slabi zaključak završava u `MANUAL_REVIEW` s razlogom.

**Rezultat:** 36/36 PASS. Zaključani self-authored benchmark sadrži 20 MIDI songova i 320 označenih half-bar ćelija; chord weighted-F1 i section-boundary F1 iznose 1,000. Analiza 25.000 nota prolazi granicu od 10 sekundi. Dokazi: `data/session19-test-report.json`, `data/session19-labeled-benchmark.json`, `data/session19-benchmark-report.json`, `data/session19-schema-catalog.json` i `artifacts/session19-song-map.json`. Šira produkcijska, žanrovska i ljudski označena kalibracija još je potrebna.

### Sesija 20 — AI Producer Brief 2.0 — SOFTWARE VALIDATED

Session 20 prevodi slobodan hrvatski ili engleski opis u strogi read-only `ProducerBrief 2.0`. Kontrolirani rječnik obuhvaća žanr, energiju po sekciji, gustoću, sinkopaciju, prostor, prijelaze, solo tretman, potrebne/zabranjene uloge, točne Pa800 lockove i transformation tolerance. Konflikti blokiraju planner do izričite korisničke odluke, a Home prikazuje karticu **AI je razumio**.

**Rezultat:** 52/52 PASS. Zaključani self-authored korpus ima 30 dvojezičnih namjera, 62 označena polja, field accuracy 1,000 i conflict accuracy 1,000. Prompt injection, MIDI bajtovi, putanje, Bank/Program autoritet i validator bypass blokiraju se. Opcionalni AI adapter je default-off, traži pristanak, prima samo metadata payload i pri mrežnoj ili schema grešci zadržava lokalni rezultat. Dokazi: `data/session20-test-report.json`, `data/session20-intent-corpus.json`, `data/session20-benchmark-report.json`, `data/session20-schema-catalog.json` i `artifacts/session20-producer-brief.json`.

### Sesija 21 — Arrangement Graph 2.0 — SOFTWARE VALIDATED

Session 21 spaja validirani `SongMap 2.0` i potvrđeni `ProducerBrief 2.0` u jedan strogi, globalni i read-only plan svih deset Pa800 elemenata. V1–V4 dobivaju kontrolirani rast energije/gustoće, svi čvorovi dijele motivsku obitelj, Fillovi imaju obavezne ciljeve, a rubovi eksplicitno nose pickup, crash, bass-approach, harmonic-anticipation i ending-cadence obveze. Svaki čvor ima harmony context, software-safe register plan, full-duration MIDI-note polyphony budget i transformation budget.

**Rezultat:** 62/62 PASS. Dvije do četiri determinističke plan-varijante čuvaju zaključane elemente, kandidatni patterni se još ne biraju, MIDI se ne mijenja, a niski SongMap confidence, unresolved evidence, nedostajući core section ili 54-note overflow vode u `MANUAL_REVIEW`. Zaključani benchmark nad 20 songova daje 20/20 determinističkih grafova, 200 čvorova, 180 rubova i 40 globalnih planova uz stopu 1,000 za rast energije, Fill targete, lock zaštitu i ponovljivost. Dokazi: `data/session21-test-report.json`, `data/session21-benchmark-report.json`, `data/session21-schema-catalog.json`, `artifacts/session21-arrangement-graph.json` i `artifacts/session21-locked-four-plan-graph.json`.

### Sesija 22 — Premium Candidate Search i Variation Engine — SOFTWARE VALIDATED / AI ARRANGER ALPHA

Session 22 povezuje `ArrangementGraph 2.0` sa stvarnim produkcijskim registryjima. Dvostupanjski retrieval najprije smanjuje pool, zatim hard constrainti odbijaju pogrešnu ulogu/takt/pitch-mode, nedovoljan dokaz, register ili full-duration polyphony overflow te prevelik transformation budget. Tek preživjeli kandidati dobivaju 14 objašnjivih score kriterija. GOLD se koristi za relativne drum, bass, riff i accompaniment odnose, dok gitara dolazi isključivo iz Factory strumminga.

**Rezultat:** 68/68 PASS. Stabilne A/B/C/D varijante koriste relationship-aware drum–bass izbor i diversity penalty protiv gotovo jednakih V1–V4. Lock, exclude, next-candidate i parcijalna regeneracija imaju stroge ugovore; fragment hash potvrđuje da neregenerirani markeri ostaju identični. Benchmark obuhvaća 20 songova: svih 15 podobnih prolazi Candidate Search, a svih pet s neriješenim SongMap dokazom ispravno se blokira prije pretrage. Obrađeno je 775 zahtjeva, 2.325 selekcija, 13.022 detaljno auditirana odbijanja i 118 potvrđenih relationship odabira, uz sve stope 1,000. CandidateSet je read-only i ne generira finalni MIDI. Dokazi: `data/session22-test-report.json`, `data/session22-benchmark-report.json`, `data/session22-schema-catalog.json`, `artifacts/session22-candidate-set.json` i `artifacts/session22-partial-regeneration.json`.

### Sesija 23 — Groove, Humanization i polifonija — SOFTWARE VALIDATED / AI ARRANGER ALPHA

Session 23 pretvara odabrani `CandidateSet 2.0` u strogi event-level `GroovePlan 2.0`. GOLD je autoritet samo za onset/gate odnose; Factory strumming zadržava vlastiti timing dokaz, dok dinamika, SoundBinding, originalni solo i zaključani fragmenti ostaju izvan dosega humanizacije. Svaka uloga ima zasebni microtiming i gate limit, Pa800 kanal 9–16 te prioritet očuvanja.

Full-duration sweep mjeri aktivne note po logičkoj traci, kanalu, svih deset marker-sekcija i svakoj A/B/C varijanti. Prije budućeg rendera vrijedi čvrsti ceiling od 54 istodobne MIDI note. Ako ga plan prijeđe, engine prvo uklanja cijeli ukrasni sloj, zatim stanjuje pomoćne akordske glasove; drums, bass, solo i zaključani fragmenti nikada se tiho ne brišu. Nerješivi overflow završava u `MANUAL_REVIEW`. Sustain-aware test uključuje duga trajanja i pedal-prozor.

**Rezultat:** 70/70 PASS. Produkcijski primjer daje 107 groove-templateova, 168 fragmenata, 4.497 timing događaja i maksimalni A/B/C peak 18/54. Stress test potvrđuje decorative-first simplification, support thinning do 54, blokadu core/locked overflowa, pravilni note-off/onset redoslijed i sustain produženje. Pa800 oscillator/voice cost ostaje `UNCONFIRMED`: procjena se aktivira samo uz hashiran fizički certificiran DeviceProfile s mjerenim role-cost modelom. CLI, API i Home GUI vraćaju isti read-only plan; finalni MIDI još se ne generira. Dokazi: `data/session23-test-report.json`, `data/session23-benchmark-report.json`, `data/session23-schema-catalog.json`, `artifacts/session23-groove-plan.json` i `artifacts/session23-polyphony-stress.json`.

### Sesija 24 — Premium Solo i Expression Director — SOFTWARE VALIDATED PREVIEW / PRODUCTION EVIDENCE BLOCKED

Session 24 povezuje točan fizički `trackUid`, 1-based Track/Channel, vremenski SoundBinding i immutable fingerprint glavne melodije sa SongMap frazama i GroovePlan polifonijom. Svaka originalna nota dobiva stabilni `sourceNoteUid`. Grace, trill, slide, turnaround, dijatonska terca i nerekurzivni echo postoje kao zasebni vizualni slojevi; svaki generirani događaj mora imati source note, evidence ID, reason code, pozitivno trajanje, dopušten registar i slobodan timing prostor.

Factory profil jedini određuje generated-note velocity i CC11 granice. Tension/release CC11 krivulja ostaje unutar sedam Factory točaka i zaglađena je; postojeći ručni CC11 se ne prepisuje. Echo koristi zaseban Delay track, nikad izvornu solo traku ili 17. traku. Prije svakog dodatka koristi se full-duration peak odgovarajuće GroovePlan varijante. Kada nema prostora, engine prvo uklanja echo, zatim ornament i tek potom tercu; originalni solo se nikada ne dira.

**Rezultat:** 80/80 PASS. Referentni self-authored dokaz čuva 16 originalnih solo nota, generira 83 uklonjive preview note i 16 Factory CC11 točaka, a A/B/C procjene ostaju do 20/54. A preview sadrži samo original, B samo jasno označene AI slojeve; `REMOVE_AI_EXPRESSION_LAYER` vraća originalni fingerprint i SoundBinding. Ugrađeni intervalni/relationship evidence ima status `SOFTWARE_TEST_ONLY`, pa produkcijski MIDI render i marketinška tvrdnja o Premium ornamentima ostaju blokirani do autoritativnog corpusa, slušnog testa i po potrebi fizičkog uređaja. Dokazi: `data/session24-test-report.json`, `data/session24-benchmark-report.json`, `data/session24-schema-catalog.json`, `artifacts/session24-expression-plan.json` i `artifacts/session24-remove-ai-layer.json`.

### Sesija 25 — ArticulationMap 2.0 — SOFTWARE VALIDATED / DEVICE CAPTURE BLOCKED

Session 25 uvodi strogi capture/import ugovor za Guitar, RX i DNC. Svaki zapis ima `CONFIRMED`, `UNKNOWN` ili `BLOCKED` status i pripada točnom CC00/CC32/Program SoundBindingu, ulozi, playable rasponu i odvojenom trigger rasponu. Standardni key-switch, CC i channel pressure su jedini dopušteni događaji; protected Bank/RPN/NRPN kontroleri, proprietary SysEx, duplicirani triggeri, nedostajući note-off, playable kolizije i približno mapiranje su blokirani.

**Rezultat:** 88/88 PASS. Tri referentne mape imaju 9 zapisa i proizvode 11 read-only preview događaja uz najviši procijenjeni peak 19/54. Svaki događaj ima fizički `trackUid`, `sourceNoteUid`, evidence ID, reason code i hash. `ArticulationPlan 2.0` koristi veći GroovePlan/ExpressionPlan peak prije dodatka. Referentni capture je namjerno `SOFTWARE_TEST_ONLY`; ne može postati produkcijski čak ni ako se njegov hash stavi u approval listu. Produkcija zahtijeva `DEVICE_CAPTURED`, potvrđen hardware, audio/slikovne hashove i zaseban operator-approved capture hash. Dokazi: `data/session25-test-report.json`, `data/session25-benchmark-report.json`, `data/session25-schema-catalog.json`, `artifacts/session25-articulation-map.json` i Guitar/RX/DNC planovi.

### Sesija 26 — Premium Preview i audio kontrola — SOFTWARE VALIDATED / DEVICE AUDIO COMPARISON ONLY

Session 26 uvodi strogi `PreviewSession 2.0` koji jedan provjereni MIDI i immutable validator identitet prikazuje kroz sinkronizirane A/B/C varijante. A ostaje verificirani baseline, B dodaje expression slojeve bez echa, a C puni expression i articulation audit. Section loop, role solo/mute, aktivne note, traka, kanal, `trackUid`, SoundBinding, izvor sloja i full-duration peak dio su istog read-only manifesta.

Ugrađeni GM/Pa800 renderer proizvodi deterministički mono 16-bit PCM proxy WAV. Loudness matching koristi jasno označenu MIDI-energy RMS procjenu, ne LUFS ni uređajni model. SoundFont i command adapter postoje samo kao hashirani manifest bez putanje i bez automatskog izvršavanja. Uvezeni Korg Pa800 WAV može se usporediti po trajanju i RMS-u, ali ugovor uvijek postavlja `DEVICE_AUDIO_COMPARISON_ONLY`, `certificationAllowed=false` i `pa800DeviceCertified=false`; Session 16 ostaje jedini certifikacijski gate.

**Rezultat:** 96/96 PASS. Referentne A/B/C varijante imaju 12/16/17 nota i full-duration peak 6/7/7. Proxy WAV i njegov manifest byte-su deterministički. Promjena profila, glasnoće, targeta, loopa ili role-mixa čuva isti MIDI SHA-256 i validator identity. CLI, API i Home GUI koriste isti ugovor, a Pa800 capture usporedba ne može promovirati fizički certifikat. Dokazi: `data/session26-test-report.json`, `data/session26-benchmark-report.json`, `data/session26-schema-catalog.json`, `artifacts/session26-preview-session.json`, `artifacts/session26-variant-c-proxy.wav` i `artifacts/session26-audio-comparison.json`.

### Sesija 27 — Music Quality Evaluator — SOFTWARE VALIDATED / HUMAN LISTENING PENDING

Session 27 uvodi `EvaluationReport 2.0` koji odvojeno vodi tehničke hard failove, automatizirane strukturne metrike i stvarne ljudske ocjene. Harmonija, groove, register collision, density curve, transition continuity, repetitivnost i ending resolution imaju auditne činjenice i zajednički score, ali ne tvrde da zamjenjuju slušanje.

**Rezultat:** 104/104 PASS. Referentna C varijanta postiže automatiziranih 4,543/5 bez tehničkog hard faila. Immutable 3.17 baseline, dva slijepa A/C pokusa, odvojeni privatni ključ, sedam kategorija ocjene, minimalno dva neovisna evaluatora, Overall medijan 4/5, prag Premium preferencije 70% i hashirani „zvučalo bolje prije” vault imaju strojni dokaz. Trenutačno postoji 0/2 verificiranih ljudskih evaluatora; testni odgovor se ne računa, pa quality release gate ostaje blokiran. Dokazi: `data/session27-test-report.json`, `data/session27-benchmark-report.json`, `data/session27-schema-catalog.json`, `artifacts/session27-evaluation-report.json` i `artifacts/session27-blind-listening-package.json`.

### Sesija 28 — Premium Producer Workflow — SOFTWARE VALIDATED / EXPORT GATES PENDING

Session 28 objedinjuje postojeće planerske, preview i quality ugovore u jedan vođeni profesionalni radni tok. `PremiumWorkflow 2.0` provjerava hash-chain od SongMapa do EvaluationReporta prije nego što prikaže osam faza `Import → Analyze → Brief → Plan → Variants → Edit → Verify → Export`. Svaka faza ima zaseban background job, status, progress i mogućnost otvaranja dokaza.

Timeline prikazuje svih deset Pa800 elemenata, njihove energije, gustoće, harmonijski kontekst, motiv, prijelazne obveze i lockove. Track Matrix prikazuje fizički `trackUid`, odvojene Track/Channel indekse i brojeve, exact SoundBinding, registar, broj originalnih i AI nota, full-duration peak te articulation status. Explain panel za referentnu C varijantu ima 52 hashirane odluke s pattern ID-em, scoreom, Factory/GOLD autoritetom, razlogom i blockerom. Diff uspoređuje note, CC11, Bank/Program/SoundBinding i svih osam ulaznih manifesta.

**Rezultat:** 112/112 PASS. Referentni workflow ima 7/8 dovršenih faza, svih deset timeline elemenata, četiri fizičke trake, deset command-palette naredbi i siguran `VERIFY` cancel/resume checkpoint. Diff pokazuje 118 baseline i 179 preview nota, 61 uklonjivu dodanu notu, 16 CC11 točaka te nula promijenjenih originalnih nota i SoundBindinga. CLI, API i GUI daju isti workflow hash, korisnik može završiti referentni preview zadatak bez terminala, a projekt/preview download ostaju dopušteni. `EXPORT` je namjerno blokiran dok nema ljudskog Session 27 PASS-a, produkcijskog expression/articulation dokaza i fizičkog Session 16 certifikata. Dokazi: `data/session28-test-report.json`, `data/session28-benchmark-report.json`, `data/session28-schema-catalog.json`, `artifacts/session28-premium-workflow.json`, `artifacts/session28-workflow-diff.json` i `artifacts/session28-recovery-checkpoint.json`.

### Sesija 29 — Personal Producer Profile — SOFTWARE VALIDATED / LOCAL EXPLICIT ONLY

Session 29 uvodi strogi `PersonalProducerProfile 2.0` koji uči samo iz `USER_EXPLICIT` događaja `ACCEPT_VARIANT` i `LOCK_SELECTION`. Playback, preview pozicija, hover, odbijena varijanta, implicitno ponašanje, MIDI sadržaj i cloud telemetrija odbijaju se kao izvori učenja. Profil je zaseban od projekta i ne sadrži MIDI ni audio.

**Rezultat:** 120/120 PASS. Referentne dvije odluke stvaraju 52 pattern preferencije, sedam role preferencija, svih deset marker preferencija i sedam registarskih pojaseva. Soft-ranking overlay može preurediti samo 624 kandidata koji su već prošli hard constraints, s maksimalnim bonusom 0,063889; svih 829 hard-odbijenih kandidata ostaje netaknuto. Cold start, isključivanje i potpuno brisanje vraćaju jednak neutralni redoslijed. Profil je pregledan, urediv, izvoziv i potpuno izbrisiv, ali nema hard constraint, Factory dynamics, SoundBinding, Bank/Program, validator ili MIDI mutation autoritet. Dokazi: `data/session29-test-report.json`, `data/session29-benchmark-report.json`, `data/session29-schema-catalog.json`, `artifacts/session29-personal-profile.json`, `artifacts/session29-ranking-overlay.json` i `artifacts/session29-profile-deletion.json`.

### Sesija 30 — Preview Release Candidate — SOFTWARE VALIDATED / EXTERNAL GATES BLOCKED

Session 30 uvodi `ReleaseReadiness 2.0`, nedestruktivnu migraciju starih projektnih dokumenata, SHA-256 sadržajni manifest aplikacije/registryja/ugovora te statusnu matricu od 17 software, quality, evidence, device, export i marketing gateova. Sadržajni seal potvrđuje lokalnu cjelovitost, ali nije identitetski ili komercijalni code-signing certifikat.

**Rezultat:** 128/128 PASS. Mjereni hardening obrađuje 25.000 nota ispod 10 sekundi, globalni plan ispod 5 sekundi, parcijalnu regeneraciju ispod 2 sekunde i migraciju 10.000 audit/lock stavki ispod 64 MB. Unicode, dugi nazivi, rezervirana Windows imena, traversal, crash, cancel, disk-full, atomic replace i clean-extract prolaze. Nema otvorenog severity-1/2 software defekta i Preview RC je spreman, ali `finalMidiExportAllowed` ostaje `false`: ljudski listening je 0/2, Premium preferencija nije potvrđena, production expression/articulation evidence je blokiran, a Pa800 profil i voice-cost nisu fizički certificirani. Dopušten je samo naziv `AI PREMIUM ARRANGER PREVIEW`.

### Sesija 16 — put do finalnog AI Premium Arrangera — DEVICE BLOCKED

Korisnik je nakon završetka izvornog rasporeda izričito proširio opseg projekta. Novi cilj je dokaziv prijelaz iz validiranog 3.17 MIDI/Pa800 baselinea u profesionalni **AI Premium Arranger**.

Novi roadmap obuhvaća baseline freeze, fizički Pa800 Mapping Lab, produkcijske adaptere za Sesije 2–7, Track Identity i Solo Safety 2.0, Song Understanding 2.0, strukturirani AI Producer Brief, globalni Arrangement Graph, Premium candidate/variation engine, groove i voice-cost polifoniju, solo/expression director, potvrđene articulation mape, A/B audio preview, slijepi quality benchmark, Premium GUI, lokalni osobni profil i završni release gate.

Detaljni ciljevi nalaze se u `AI_PREMIUM_ARRANGER_PLAN.md`. Session 33 daje verificirani MIDI, Session 34 A/B/C globalnu koherentnost, Session 35 desetofazni Song-to-Style workflow, Session 36 zaključava zero-silent-failure reliability, Session 37 zaključava 32-case quality corpus i 24/8 train/holdout granicu, a Session 38 daje fail-closed fizički evidence intake bez lažne certifikacije. Postojeći 43/43 i 2900/2900 rezultati dokazuju 4.11.1 Device Certification Intake Foundation, a ne dovršeni finalni Premium proizvod.

## Redoslijed i blokade

- Sesije 1–15 zaključavaju povijesni i Premium baseline, Session 18 zaključava identitet traka i solo sigurnost, Session 17 povezuje dokazive dijelove produkcijskih registryja, Sesije 19–21 zaključavaju SongMap, ProducerBrief i globalni ArrangementGraph, Session 22 daje read-only produkcijske A/B/C odabire, Session 23 dodaje GroovePlan i 54-note full-duration gate, Session 24 uklonjivi solo-expression sloj, Session 25 stroge exact-sound articulation mape, Session 26 sinkronizirani validation-neutral audio pregled, Session 27 odvojeni automatski i ljudski quality gate, Session 28 sve spaja u vođeni Premium Producer workflow, Session 29 dodaje lokalni eksplicitni preference overlay, a Session 30 zaključava Preview RC hardening i statusnu matricu. Preostali su samo stvarni ljudski, produkcijski evidence i fizički uređajni gateovi iz `AI_PREMIUM_ARRANGER_PLAN.md`.
- Session 2 temelj smije prijeći u puni `SOFTWARE_VALIDATED` status tek nakon istog testa nad produkcijskim registryjima i barem jednim stvarnim songom kroz podržani aplikacijski ulaz.
- Isto pravilo vrijedi za Session 3: sintetički byte-real dokaz potvrđuje engine, ali ne zamjenjuje produkcijski corpus gate.
- Session 4 ne smije pretvoriti sintetičku testnu kontrolnu mapu u produkcijski RX/Guitar Mode autoritet; potreban je službeni ili uređajno potvrđen dokaz.
- Session 5 mora zadržati originalni solo netaknut i ne smije sintetički intervalni registry prikazati kao produkcijski GOLD dokaz; puni status zahtijeva stvarni corpus, podržani aplikacijski ulaz i slušnu provjeru.
- Delay/Echo iz Sesije 5 mora koristiti prvi slobodan track; isti solo track nije dopušten. Novi track kopira sound setup, ali izvorna solo traka ostaje jedini nositelj glavne melodije, terce, ornamenata i CC11.
- Session 6 ne smije zaključivati RX trigger iz naziva, programa ili raspona nota. Bez potvrđene verzionirane mape točnog Bank/Program zvuka rezultat ostaje `KEEP` ili `MANUAL_REVIEW`.
- Sesije 6 i 7 ne smiju nagađati RX/DNC događaje. Nedostatak službene ili uređajne potvrde znači siguran `KEEP`, ne lažnu implementaciju.
- Sesija 8 ostaje opcionalna pri korištenju aplikacije; offline core mora raditi identično bez mreže.
- Sesija 14 zahtijeva fizički Korg Pa800 OS 2.0+ i korisnikovu potvrdu.
- Nakon svake sesije ažuriraju se `MASTER_PROMPT_COMPLIANCE.md`, JSON izvještaji, `README.md` i glavni PDF.