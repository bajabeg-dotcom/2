# DNA corpus audit — etapa 1

Datum: 2. rujna 2026.

Izvor: `prism-uploads/DNA.zip`  
SHA-256: `125f4486625db44f7cdd49bd670aff252a961c88ea14741ec970ec3ae5eec85a`

Strojni dokaz nalazi se u `data/corpus-forensics-report.json`. Audit je pročitao sve izvore bez izmjene arhive: 3.211 Factory MIDI datoteka i 182 GOLD MIDI datoteke, bez parser grešaka.

## 1. Najvažniji ispravak dosadašnjeg modela

Factory nije samo baza velocityja. Factory datoteke sadrže stvarne Korg Style elemente, Chord Variation oznake, Pa800 uloge traka, početni izbor zvuka, glasnoću, expression i dovoljno ACC gitarskog materijala za učenje strumminga.

GOLD nije pouzdan izvor Program Changea, velocityja ili Factory ritam-gitare. GOLD je vrijedan kao zbirka cijelih izvedbi: note, trajanja, ritam, gate, bas/drum odnosi, fraze, prijelazi, stihovi, FX kontroleri i Korgovi proprietarni događaji. U GOLD-u nema pouzdanih eksplicitnih `Intro`, `Variation`, `Fill` i `Ending` markera; faze se moraju zaključivati iz pjesme ili iz događaja čije je značenje dokazano.

Zato su autoriteti od sada:

| Odluka | Autoritet |
|---|---|
| velocity i sedmerotočkasta dinamička krivulja | Factory |
| Program Change / Bank Select i izbor boljeg zvuka | originalni MIDI + odobreni Factory/Pa800 katalog |
| ritam-gitara i Pa800 Guitar Mode strumming | Factory ACC1–ACC5 |
| drum, bass, riff, fraze, timing, gate i prijelazi | filtrirani GOLD bez velocityja |
| ciljni akordi, tonalitet i forma | analizirani korisnički song |
| konačni izlaz | deterministički engine + neovisni validator |

## 2. Neiskorišteni Factory resursi

Audit je pronašao 65.021 traku i 1.432.867 nota. Tekstualne oznake daju 370 različitih kombinacija Style elementa, uloge i CV broja.

Potvrđeni elementi uključuju:

- `Variation 1–4`, `Intro 1–3`, `Ending 1–3`, `Fill 1–2` i `Break`;
- `DRUMS`, `PERC`, `BASS`, `ACC1–ACC5`;
- `CV1–CV6`, ovisno o elementu;
- stvarni broj taktova pojedinog elementa;
- CC00, CC32, Program Change, CC7 i CC11 na izvornim Factory trakama.

Factory sadrži 29.825 CC7 i 29.826 CC11 događaja te 581 prepoznatu kombinaciju zvuka s volume/expression dokazom. To omogućuje profil miksa po instrumentu, ulozi, elementu i intenzitetu. U Factory izvoru nije pronađen CC91–95 FX-send dokaz, pa se ne smije tvrditi da je kompletan FX profil naučen samo iz Factory MIDI-ja.

Za gitaru je pronađeno 5.643 ACC traka s GM guitar programima, 380.901 nota i 51.308 kandidata poteza s najmanje tri tona. Ovo je dovoljan korpus za izgradnju Factory strum registryja, ali svaki potez još mora proći chord, smjer, gate, registar i Pa800 Guitar Mode validaciju.

## 3. Sedam vrijednosti velocity analize

Postojećih 1.964 profila nije dovoljno opisati samo s `min`, `optimal` i `max`. Novi profil će sadržavati najmanje:

```text
floor, soft, lowMid, optimal, highMid, strong, ceiling
```

Vrijednosti se računaju iz robusnih kvantila i moda, ali moraju biti monotone, ostati unutar opaženog Factory raspona i imati confidence prema broju uzoraka. Trenutna pokrivenost:

- 1.197 profila ima najmanje 32 uzorka;
- 810 profila ima najmanje 128 uzoraka;
- 424 profila ima najmanje 512 uzoraka.

Profili s premalo uzoraka ne dobivaju lažnu preciznost. Koriste potvrđeni Factory fallback po ulozi i registru ili ostavljaju originalni velocity (`KEEP`). Bubnjevi ostaju profilirani po pojedinačnoj drum noti/elementu.

## 4. Neiskorišteni GOLD resursi

GOLD audit je pronašao:

- 2.272.811 note-on događaja;
- 40.867 Korg chord događaja u 177 datoteka;
- 151.684 SysEx događaja;
- 45.491 manufacturer-specific meta događaj;
- 7.610 CC91–95 FX-send događaja;
- 3.566 lyric događaja;
- 74.180 potpuno uparenih Korg native događaja obitelji `42 3f 78 01`, bez visećeg para.

Korg chord događaj oblika `42 60 08 type root bass flags` može dati vrlo jaku početnu chord mapu. Decoder je zasad označen kao `EVIDENCE_BACKED_CANDIDATE_REQUIRES_DEVICE_CONFIRMATION`: mora se usporediti s notama i službenom tablicom prije nego postane autoritet.

Nepoznati Korg meta/SysEx događaji moraju ostati bajt-po-bajt sačuvani. Engine ih ne smije brisati, preuređivati ili sintetizirati dok semantika nije neovisno dokazana.

## 5. Odluke za tražene optimizacije

### Volume i jednaka jačina

CC7 postavlja osnovni miks trake, CC11 izvodi fraznu dinamiku, a velocity upravlja napadom i često odabirom sloja uzorka. Ne smiju se svesti na jednu vrijednost. MIDI bez audio rendera ne može dokazati jednaku akustičku glasnoću različitih Pa800 zvukova i FX lanaca. Zato će offline engine garantirati isti ciljni MIDI energy/headroom profil, dok je prava LUFS normalizacija moguća tek nad snimljenim Pa800 audiom.

### FX Auto Profile

FX se bira konzervativno iz vrste instrumenta, uloge, gustoće, registra i prostora u aranžmanu. GOLD CC91/93 može biti dokaz odnosa i namjere, ali ne smije automatski prepisati vrijednost u drugi song. Nepoznati SysEx se čuva. Svaka FX promjena mora imati before/after zapis i mogućnost `KEEP`.

### Key Range

Nota izvan potvrđenog raspona ne briše se. Najprije se pokušava oktavno vraćanje uz očuvanje pitch-classa i smjera fraze; zatim voice-leading kandidati; tek nerješiv slučaj dobiva `MANUAL_REVIEW`.

### Solo, delay i terca

Solo se odvaja od ritam/harmonijskih traka prema monofoniji, registru, frazama i ekspresivnim kontrolerima. Echo/delay kopija mora biti tiša, vremenski vezana uz tempo, unutar raspona i ne smije stvoriti harmonijski sudar. Terca se dodaje samo gdje akord dopušta dijatonski chord-tone; nije trajno paralelno pomicanje za tri ili četiri polutona.

### Guitar Mode

Generički arpeggio nije dovoljan. Registry mora učiti Factory ACC poteze, smjer, razmak žica, mute/stop, gate, registar i element/CV kontekst. Pa800 Guitar Mode kontrolne note smiju se generirati samo prema službeno potvrđenoj mapi.

## 6. Implementacijska etapa 2 — završeno

Uveden je modul `midi_integrity.py` s eksplicitnim ugovorom autoriteta i neovisnim protected-event snapshotom. Optimizer sada radi nad memorijskom kopijom i vraća rezultat samo kroz slijed `ANALYZE -> PLAN -> DRY RUN -> APPLY -> VERIFY -> COMMIT`.

Zaštićeni su meta/SysEx payload, tick i međusobni redoslijed, Bank Select, Program Change, RPN/NRPN, Data Entry te ostali ne-note channel događaji. Obični redundantni CC smije se ukloniti samo kada je ta transformacija uključena; Program Change i zaštićeni kontroleri više nisu kandidati za controller cleanup.

Dodana su tri formalna dokaza: autoritet zabranjuje GOLD velocity/program, stvarni optimizer round-trip čuva zaštićene događaje i negativni test namjerno mijenja Program Change te potvrđuje da verifier blokira kandidat. Cijeli release-check sada prolazi 31/31 testova.

## 7. Implementacijska etapa 3A — završeno

Factory registry je nadograđen na schemu 3.1. Svih 1.964 profila sada ima sedam monotonih velocity točaka, sedam opisnih kvantila, dopušteni raspon, broj uzoraka i dokaz da GOLD ne utječe na dinamiku. Optimizer više ne vuče sve note prema jednoj optimalnoj vrijednosti: čuva relativni ulazni intenzitet i preslikava ga kroz krivulju od `floor` do `ceiling`. DNA Library prikazuje svih sedam vrijednosti.

## 8. Implementacijska etapa 3B — završeno

Factory schema 3.3 dodaje stvarne CC7 i CC11 profile: 1.892 instrument profila imaju volume, a 1.894 expression dokaz te stroge `DDD.DDD.DDD` ID-eve. Mixer transformacija čuva relativni oblik postojećeg kontrolera, koristi samo točan Factory bank/program profil i smije dodati nedostajući CC7/CC11 samo kada je opcija uključena. GOLD mixer utjecaj ostaje nula.

Key-range engine za melodijske kanale traži točan `instrumentKey`, najmanje 32 Factory uzorka i raspon širok najmanje jednu oktavu. Notu izvan raspona premješta isključivo cijelim oktavama, čime čuva pitch-class; nikada je ne briše. Ako nema sigurnog kandidata, ostavlja notu i zapisuje manual-review metriku. Integracijski test istodobno potvrđuje mixer, key-range i očuvani Program Change. Release-check prolazi 32/32 testa.

## 9. Implementacijska etapa 3C — završeno

GOLD runtime schema 3.2 više ne sadrži `instrumentKey`, Factory profile ID, Bank Select, Program Change ni bilo koje actionable velocity polje. Rekurzivni validator provjerio je svih 10.637 legacy patterna, a adversarial test potvrđuje da se blokiraju i duboko ugniježđena polja poput `velocity_curve` i `programChange`.

Optimizer i preflight sada mjere duration-weighted MIDI energy/headroom proxy koristeći velocity, CC7 i CC11. Izvještaj sadrži prije/poslije indeks, cilj, odstupanje, peak note amplitude i per-voice headroom. Polje `audioLufsMeasured` uvijek je `false`, jer bez Pa800 audio rendera nema valjanog LUFS dokaza.

## 10. Implementacijska etapa 3D — završeno

Posebni engine sada klasificira uloge Drum, Bass, Rhythm Guitar, Solo, Pad, Chords i Accompaniment. FX Auto Profile prilagođava ili dodaje CC91/CC93 prema konzervativnom role-based profilu, čuva postojeću automatizacijsku konturu i izričito ne koristi GOLD vrijednosti ni nepoznati SysEx.

Solo Delay i Terca najprije provjeravaju postoji li odnos. Ako Delay nedostaje, generira se ograničeni 1/8 echo sloj samo za dovoljno kratke solo note, na istom kanalu i zvuku, s Factory velocityjem i bez preklapanja izvorne note. Terca se dodaje samo kada major/minor chord mapa s dovoljnim confidenceom potvrdi malu ili veliku tercu te kada postoji točan Factory profil i siguran registar. Globalni limit je 18% izvornih nota, najviše 4.000, a svaki solo sloj ima vlastiti limit 25%, najviše 512 nota.

Dokazni test generira dva Delay i dva Terca događaja bez promjene programa ili broja traka. E2E test na stvarnom songu `AKO TE DRUGI PR-SAMIR R UZIVO.MID` prepoznaje postojeći Delay odnos i generira 68 akordski dopuštenih Terca nota; protected-event verifier prolazi. Prepoznate solo trake izuzete su iz automatskog i ručnog quantizea.

Time je razvojna etapa 3 završena.

## 11. Implementacijska etapa 4 — završeno

Factory Style registry sadrži 26.922 stvarna segmenta i 1.283.645 nota, sve uloge `DRUMS`, `PERC`, `BASS`, `ACC1–ACC5`, 13 elemenata i CV1–CV6. Svaki segment čuva tempo, takt, broj taktova, zvučni dokaz, source hash, tick range i Factory profile reference.

Factory strumming registry sadrži 2.919 patterna, 185.850 nota i 46.995 poteza: 24.488 down, 10.676 up, 10.881 block i 950 mixed. Engine čuva inter-string timing, gate, chord size, registar, element i CV. Ne generira Guitar Mode kontrolne note čije značenje nije potvrđeno.

GOLD performance registry sadrži 12.918 ponovljenih jedno- i dvotaktnih patterna te 4.373 drum–bass odnosa. Uloge su drum, percussion, bass, power-riff, riff i accompaniment. Timing radi na 96 tickova po četvrtinki, umjesto plitke 1/16 mreže; runtime nema velocity, Bank Select, Program Change ni ritam-gitarski autoritet.

Pa800 Style Builder koristi GOLD performance za drum/bass/riff, vezuje bass uz kompatibilni drum groove i primjenjuje Factory per-note drum dinamiku. Kada je odabran ritam-gitarski zvuk, pattern dolazi isključivo iz Factory ACC registryja. Ranking koristi deset kriterija i sve odluke zapisuje u manifest.

Formalni rezultat etape je tada bio 37/37 PASS. Nakon završne sesije 1 cijeli paket ima 43/43 PASS. Software ostaje `SOFTWARE_VALIDATED`, a fizički uređaj `WAITING_FOR_DEVICE`.

## 12. Završna sesija 1 — završeno

Song analiza sada daje pola-takta chord timeline, dokazne granice faza i Korg chord događaje kao neautoritativne kandidate. Phase Arranger izrađuje read-only `KEEP/REPAIR/REPLACE/MANUAL_REVIEW` plan prije svake promjene. Solo je uvijek zaštićen, GOLD daje samo note/timing/gate, ritam-gitara ostaje Factory-only, a svaki generirani velocity dolazi iz točnog Factory profila.

Sintetički test potvrđuje `REPLACE`, očuvani Program Change, jednak broj traka, Factory raspon i nepromijenjene solo onsete. Stvarni GOLD song daje 89 odluka kroz 11 faza, 236 chord ćelija i 239 sačuvanih Korg chord kandidata; isti seed daje isti plan hash. Puni release-check prolazi 43/43 testa. Dokaz je `data/phase5-test-report.json`.

## 13. Službene referentne točke

- Korg Pa800 Advanced Edit, OS 2.0: Bank Select/Program Change format, Vel/Key Zone, Sound FX1/FX2 i popis efektnih procesora.
- Korg Pa800 OS 1.60 Upgrade Manual: Guitar Track Type, Guitar Mode, NTT Type, CC11 monitor, RX Noise/Humanize Guitar i chord-type kodovi.
- Korg tutorial za SMF razdvojen markerima: format 0, kanali 9–16, markeri, obavezni događaji i SHIFT + Execute import.
