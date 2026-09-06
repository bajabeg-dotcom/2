# Vizija projekta — DNA MIDI Studio za Korg Pa800

Datum vizije: 2. rujna 2026.

## Status realizacije

Glavna software vizija sada je realizirana kao lokalni Python/web proizvod: Home, MIDI Optimizer, stvarni piano-roll editor, napredna Song Analysis, Pa800 Style Builder, Pattern Inspector, Factory/Gold Library, Reports & Safety, Settings, verzionirani projektni format, recovery kopije i Windows `.bat` pokretači. Core uključuje Factory Style/CV i strumming registry, puni GOLD performance registry, povezane drum–bass grooveove, pola-takta Chord Timeline, Phase Arranger i zaštitu solo vremena od quantizea. Jedinstveni release-check prolazi 43/43 formalna testa.

Jedina namjerno nezatvorena točka je fizička certifikacija: status ostaje `WAITING_FOR_DEVICE` dok se generirani MIDI ne uveze, posluša, podesi NTT/Track Type, spremi i ponovno učita na stvarnom Korg Pa800.

## 1. Osnovna ideja

DNA MIDI Studio zamišljam kao profesionalni lokalni glazbeni alat koji spaja tri posla koja se danas uglavnom rade odvojeno:

1. tehničko čišćenje i optimizaciju postojećih MIDI songova;
2. analizu pjesme i pretvaranje njezine glazbene strukture u aranžmanski plan;
3. izradu sigurnog Style Import MIDI-ja za Korg Pa800.

Aplikacija ne bi trebala djelovati kao tehnički eksperiment ili običan MIDI konverter. Treba izgledati i ponašati se kao mali produkcijski studio: korisnik učita pjesmu, vidi što je u njoj pronađeno, bira koliko želi automatike, sluša rezultat, uspoređuje ga s originalom i tek nakon jasne validacije izvozi novu datoteku.

Najvažnija vrijednost projekta nije samo generiranje nota. Vrijednost je u tome da rezultat bude:

- glazbeno smislen;
- tehnički čist;
- ponovljiv;
- objašnjiv;
- siguran za Pa800 workflow;
- potpuno lokalno obrađen;
- dovoljno jednostavan da ga može koristiti glazbenik koji nije programer.

## 2. Identitet proizvoda

Predloženi naziv proizvoda je **DNA MIDI Studio**, dok je **DNA Style Arranger** specijalizirani modul unutar aplikacije.

Naziv “DNA” ima smisla jer aplikacija koristi dvije odvojene baze glazbenog znanja:

- **Factory DNA** opisuje kako pojedini instrument prirodno reagira dinamički;
- **Gold DNA** opisuje kako se glazba izvodi kroz ritam, fraziranje, trajanje, ukrase i patterne.

To razdvajanje mora biti vidljivo i u sučelju. Korisnik uvijek treba znati odakle dolazi određena odluka. Ako vidi velocity 92, aplikacija treba moći pokazati Factory profil koji ga je odredio. Ako vidi odabrani ritmički pattern, treba moći otvoriti njegov Gold ID, izvor, confidence i kriterije po kojima je izabran.

## 3. Kome je aplikacija namijenjena

### Primarni korisnik

Glazbenik ili producent koji koristi Korg Pa800 i želi:

- popraviti postojeći MIDI song;
- pripremiti kvalitetniju pratnju;
- iz songa izvući strukturu za novi Style;
- dobiti Pa800-kompatibilan SMF bez ručnog pisanja svih markera i kontrolera;
- zadržati kontrolu nad zvukovima, dinamikom i sekcijama.

### Sekundarni korisnik

MIDI aranžer koji želi alat za batch analizu, audit, usporedbu verzija i tehničko čišćenje prije nastavka rada u DAW-u.

### Korisnik koji nije cilj

Aplikacija nije zamišljena kao zamjena za kompletan DAW. Ne treba pokušavati kopirati Cubase, Logic ili Ableton. Fokus mora ostati na MIDI inteligenciji, optimizaciji i Pa800 Style pripremi.

## 4. Kako bi aplikacija trebala izgledati

Vizualno bih zadržao tamno, profesionalno sučelje koje već postoji, ali bih ga organizirao kao pravi desktop studio.

### Gornja traka

Gornja traka treba uvijek prikazivati:

- naziv otvorenog projekta;
- status automatskog spremanja;
- Undo i Redo;
- naziv učitanog MIDI-ja;
- status lokalnog enginea;
- status Factory i Gold baze;
- veliki sigurnosni indikator: `VALID`, `WARNING` ili `BLOCKED`.

Korisnik ne bi trebao tražiti informaciju je li datoteka sigurna. Ta informacija mora biti stalno vidljiva.

### Glavna navigacija

Predlažem sljedeće radne prostore:

1. **Home / Project**
2. **MIDI Optimizer**
3. **Song Analysis**
4. **Style Builder**
5. **MIDI Editor**
6. **Factory & Gold Library**
7. **Reports & Safety**
8. **Settings**

Na manjim ekranima navigacija može biti u gornjim tabovima. U konačnoj Windows verziji bolje bi odgovarala lijeva bočna navigacija, jer ostavlja više mjesta za piano-roll i timeline.

## 5. Home / Project ekran

Početni ekran treba biti miran i jednostavan. Korisniku trebaju biti ponuđene četiri velike akcije:

- **Optimiziraj postojeći MIDI**
- **Analiziraj song**
- **Napravi novi Pa800 Style**
- **Otvori spremljeni projekt**

Ispod toga treba prikazati posljednje projekte, datum zadnjeg spremanja, korišteni seed, cilj uređaja i status zadnje validacije.

Novi projekt treba imati vlastitu projektnu datoteku, primjerice:

```text
NazivPjesme.dnaproject.json
```

Ta datoteka ne mora sadržavati sam MIDI ako korisnik to ne želi. Može čuvati putanju ili hash izvora, postavke, seed, odabrane profile, patterne, edit history i rezultate validacije.

## 6. MIDI Optimizer

Optimizer treba biti prvi potpuno zaokružen profesionalni workflow.

### Korak 1 — Import

Nakon učitavanja aplikacija treba prikazati:

- naziv i veličinu datoteke;
- SMF format;
- broj traka;
- PPQ;
- trajanje;
- tempo i promjene tempa;
- takt i promjene takta;
- broj nota i MIDI kanala;
- broj Program Change, CC, SysEx i marker događaja;
- početni quality score.

Originalna datoteka mora ostati read-only.

### Korak 2 — Preflight analiza

Prije optimizacije aplikacija treba pokazati pronađene probleme, grupirane po ozbiljnosti:

#### Kritično

- oštećena SMF struktura;
- neuparene note;
- nevaljano trajanje;
- nedostajući End Of Track;
- nečitljiv delta-time ili event.

#### Važno

- preklapanje iste note;
- duplicirane note;
- redundantni kontroleri;
- ekstremni velocity;
- note izvan očekivanog registra.

#### Informativno

- note izvan quantize mreže;
- velik broj tempo događaja;
- neuobičajeno velika datoteka;
- nekorišteni kanali ili trake.

### Korak 3 — Profil optimizacije

Korisniku bih ponudio gotove profile:

- **Safe Cleanup** — samo tehnički problemi;
- **Natural Timing** — blagi quantize koji čuva groove;
- **Factory Dynamics** — dinamika prema Factory profilima;
- **Pa800 Song Prep** — sigurne postavke za daljnji rad na Pa800;
- **Custom** — ručno podešavanje svega.

Postojeće pojedinačne kontrole za note cleanup, controller cleanup, quantize i Factory dynamics ostaju dostupne u naprednom prikazu.

### Korak 4 — Prije/poslije

Ovo treba biti središnji dio Optimizera:

- dva quality score kruga;
- popis svake intervencije;
- originalni i optimizirani SHA-256;
- promjena veličine datoteke;
- tehnički parametri koji su očuvani;
- upozorenja;
- validation rezultat.

Piano-roll treba podržavati:

- A/B Original/Optimized;
- boje po kanalu;
- solo i mute;
- zoom po vremenu i visini;
- pomicanje playheada;
- prikaz velocityja bojom ili visinom;
- prikaz intervencija kao posebnih oznaka.

Korisnik bi trebao moći uključiti prikaz “Show changes” i odmah vidjeti koje su note pomaknute, skraćene, uklonjene ili dinamički promijenjene.

## 7. Song Analysis

Song Analysis treba objasniti pjesmu, ne samo vratiti nekoliko brojeva.

### Glavni rezultat

Ekran treba prikazati:

- tonalitet i confidence;
- tempo mapu;
- time-signature mapu;
- akorde po taktovima;
- prepoznate sekcije;
- gustoću nota;
- polifoniju;
- harmonijsku aktivnost;
- registarsku raspodjelu;
- instrumentalne uloge.

Velocity korisničkog songa ne smije ulaziti u style/intensity zaključke. Intensity se računa iz gustoće, polifonije, pozicije fraze, registra, harmonijske aktivnosti i uloge sekcije.

### Timeline forme

Na vrhu treba postojati vodoravni timeline:

```text
Intro | Strofa 1 | Refren 1 | Strofa 2 | Refren 2 | Bridge | Refren 3 | Ending
```

Svaka sekcija treba imati:

- početni i završni takt;
- intenzitet;
- dominantni akord;
- gustoću bubnja, basa i harmonije;
- confidence detekcije;
- preporučeni Pa800 element.

Korisnik treba moći ručno preimenovati, podijeliti, spojiti ili promijeniti granice sekcije. Automatska analiza daje početni prijedlog, ali čovjek ostaje glazbeni autoritet.

## 8. Pa800 Style Builder

Style Builder treba biti vođen proces, a ne samo velika forma s mnogo polja.

### Korak 1 — Style identitet

- naziv Stylea;
- tempo;
- takt;
- referentni Key/Chord;
- seed;
- izvorni song ili prazan Style;
- žanr i produkcijska namjera.

### Korak 2 — Elementi

Elementi trebaju biti prikazani kao kartice ili timeline blokovi:

- Intro 1 i Intro 2;
- Variation 1–4;
- Fill 1 i Fill 2;
- Ending 1 i Ending 2.

Svaki blok prikazuje:

- marker;
- broj taktova;
- intensity;
- korištene patterne;
- aktivne trake;
- status validacije;
- kratki playback gumb.

### Korak 3 — Osam Pa800 traka

Mixer prikaz treba koristiti stvarne Pa800 uloge:

| Traka | Kanal | Namjena |
|---|---:|---|
| Bass | 9 | bas linija i prijelazi |
| Drum | 10 | glavni drum kit |
| Percussion | 11 | dodatne udaraljke |
| Acc1 | 12 | osnovni akordski sloj |
| Acc2 | 13 | drugi ritmički/harmonijski sloj |
| Acc3 | 14 | melodijski odgovor ili fraza |
| Acc4 | 15 | pad, gornji sloj ili kontra-melodija |
| Acc5 | 16 | akcenti i rijetki prijelazi |

Svaka traka treba imati:

- enable;
- solo/mute;
- Factory Sound;
- bank MSB/LSB i program;
- Factory velocity profil;
- registar;
- polifonijski limit;
- Track Type i NTT preporuku;
- pattern lock.

Pattern lock je važan: korisnik može zaključati dobar pattern i ponovno generirati ostale trake bez gubitka tog izbora.

### Korak 4 — Pattern Inspector

Klik na pattern ID treba otvoriti detalje:

- Gold pattern ID;
- izvor i source ID;
- broj pojavljivanja;
- confidence;
- metar;
- uloga;
- gustoća;
- registar;
- source section;
- svih sedam ranking rezultata;
- razlog konačnog odabira.

Korisnik tada može birati:

- **Keep**
- **Find similar**
- **Next deterministic candidate**
- **Exclude from project**

Promjena kandidata mora biti zabilježena u manifestu.

## 9. MIDI Editor

MIDI Editor ne treba odmah pokušati imati sve funkcije DAW-a. Treba biti usmjeren na popravke koje su važne za aranžer.

### Obavezni editorski alati konačne verzije

- odabir i pomicanje nota;
- promjena trajanja;
- promjena velocityja unutar dopuštenog Factory raspona;
- quantize odabranih nota;
- transpozicija;
- brisanje i dupliciranje;
- solo/mute po kanalu;
- undo/redo;
- prikaz akorda i sekcija iznad piano-rolla.

### Sigurnosne granice

Ako korisnik ručno postavi velocity izvan Factory raspona, aplikacija ne treba tiho promijeniti njegov unos. Treba prikazati upozorenje i ponuditi:

- clamp u Factory raspon;
- zadržavanje kao eksplicitni manual override;
- povratak na Factory optimum.

Manual override mora biti vidljiv u auditu.

## 10. Factory & Gold Library

Ovo je važan dio transparentnosti sustava.

### Factory Library

Korisnik treba moći pretraživati profile prema:

- nazivu instrumenta;
- ulozi;
- bank/program kombinaciji;
- registru;
- confidenceu;
- broju uzoraka;
- drum elementu.

Profil treba prikazivati min, optimum i max te jednostavan graf dinamičke krivulje od intensity 0 do 100.

### Gold Library

Gold pregled ne smije prikazivati niti sadržavati velocity kao izvor dinamike. Treba prikazivati:

- pattern note/timing oblik;
- pitch ili relativne intervale;
- trajanja;
- ulogu;
- metar;
- gustoću;
- izvorne sekcije;
- confidence;
- broj ponavljanja.

Korisnik treba moći preslušati pattern uz trenutno odabrani Factory profil. U tom slučaju note dolaze iz Golda, ali velocity za playback dolazi iz Factory profila.

## 11. Glazbena inteligencija

Glazbena inteligencija treba biti podijeljena u slojeve.

### Sloj 1 — Sigurna deterministička pravila

- uloga instrumenta;
- osnovni registar;
- polifonijski limit;
- mapiranje na C Major;
- izbjegavanje preklapanja;
- izbor patterna prema sedam kriterija;
- intenzitet prema Factory krivulji.

Ovaj sloj je autoritet za finalni MIDI.

### Sloj 2 — Napredna heuristika

- voice leading;
- akordske inverzije;
- detekcija sudara registara;
- inteligentni fill prijelazi;
- frazno pozicioniranje ukrasa;
- trill prilagodba tempu i harmoniji;
- section-aware expression.

Ovaj sloj smije predložiti ili prilagoditi plan, ali rezultat i dalje prolazi isti hard validator.

### Sloj 3 — AI agenti

AI agenti trebaju raditi kao savjetnici:

- Music Director opisuje formu i namjeru;
- Style Evaluator uspoređuje A/B varijante;
- Codex agent održava engine i testove;
- Compliance agent potvrđuje tehnički izlaz.

Agent ne smije izravno pisati finalni MIDI, gasiti validator ili automatski spremati Style na uređaj.

## 12. Reports & Safety

Ovaj ekran treba biti kontrolni centar projekta.

### Projektni audit

Treba prikazati:

- input i output SHA-256;
- seed;
- verziju Factory i Gold baze;
- konfiguracijski hash;
- broj intervencija;
- korištene profile;
- korištene patterne;
- manual override odluke;
- validation rezultat;
- datum izvoza.

### Validation panel

Svaka provjera treba biti zaseban red:

```text
SMF Format 0                         PASS
Track count = 1                     PASS
PPQ = 480                           PASS
Channels 9–16                       PASS
Markers lowercase/unique/supported PASS
CC00/CC32/PC/CC11 per marker        PASS
Note pairing                        PASS
Invalid durations                   PASS
End Of Track                        PASS
Event order                         PASS
```

Ako bilo koja blokirajuća provjera ne prođe, gumb za MIDI download treba biti onemogućen. Korisnik i dalje može preuzeti JSON izvještaj da vidi razlog.

### Status certifikacije

Treba jasno razlikovati:

- **SOFTWARE VALIDATED** — strojni testovi prolaze;
- **WAITING FOR DEVICE** — fizička provjera još nije napravljena;
- **PA800 CERTIFIED** — dopušteno tek nakon dokumentiranog testa na uređaju.

## 13. Fizički Pa800 workflow

Kada bude dostupan uređaj, aplikacija treba imati ugrađeni checklist:

1. kopirati `.MID` na USB;
2. otvoriti Style Record;
3. napraviti novi Style;
4. otvoriti Import SMF;
5. držati SHIFT i odabrati Execute;
6. potvrditi da su svi marker elementi učitani;
7. provjeriti kanale i zvukove;
8. postaviti originalni Key/Chord;
9. provjeriti Track Type i NTT;
10. preslušati sve Variation/Fill prijelaze;
11. spremiti u USER/FAVORITE;
12. ponovno učitati spremljeni Style;
13. zabilježiti rezultat u certification report.

Tek nakon svih prolaznih koraka projekt može dobiti oznaku `PA800 CERTIFIED` za testiranu verziju enginea i baze.

## 14. Tehnička arhitektura

Predlažem jasnu podjelu na module:

```text
DNA MIDI Studio
├── Data Layer
│   ├── Factory Profile Registry
│   ├── Gold Pattern Registry
│   └── Database Versioning
├── MIDI Core
│   ├── Parser
│   ├── Note Pairing
│   ├── Controller Model
│   ├── Tempo/Meter Map
│   └── Writer
├── Intelligence
│   ├── Song Analyzer
│   ├── Section Detector
│   ├── Chord/Key Detector
│   ├── Pattern Ranker
│   └── Velocity Engine
├── Pa800
│   ├── Style Builder
│   ├── Marker Package
│   ├── Channel Mapper
│   └── Hard Validator
├── Application
│   ├── Local HTTP API
│   ├── Web GUI
│   ├── Project Store
│   └── Download Cache
└── Quality
    ├── Audit
    ├── Unit Tests
    ├── Integration Tests
    ├── E2E Tests
    ├── Regression Tests
    └── Negative Validation Tests
```

Refaktor je proveden: aktivni Style Builder, validator, muzička inteligencija, MIDI editor, optimizer, analizator songa, projektni model i cache imaju zasebne module. `server.py` služi kao lokalni transportni/API sloj i zadržava kompatibilne pomoćne funkcije za postojeće testove.

## 15. Predložena struktura projekta

```text
dna-midi-studio/
├── app/
│   ├── server.py
│   ├── routes/
│   └── project_store.py
├── core/
│   ├── midi_parser.py
│   ├── midi_writer.py
│   ├── midi_optimizer.py
│   ├── song_analyzer.py
│   └── audit.py
├── pa800/
│   ├── style_builder.py
│   ├── marker_rules.py
│   └── validator.py
├── dna/
│   ├── factory_builder.py
│   ├── gold_builder.py
│   └── registry.py
├── web/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── editor.js
├── data/
├── tests/
├── docs/
├── tools/
├── install.bat
├── run.bat
└── README.md
```

Postojeća kompaktna struktura je dobra za prototip. Ova podjela je cilj kada projekt prijeđe u veću produkcijsku fazu.

## 16. Windows izdanje

Konačna Windows verzija treba nuditi dvije mogućnosti.

### Portable paket

- raspakira se u mapu;
- pokreće se dvostrukim klikom;
- ne zahtijeva administratorska prava;
- svi podaci i projekti ostaju lokalno;
- uključuje provjeru integriteta DNA baze.

### Instalirana desktop aplikacija

- vlastiti prozor bez vidljivog terminala;
- automatsko otvaranje zadnjeg projekta;
- Windows file association za `.dnaproject.json`;
- sigurno ažuriranje aplikacije i odvojeno ažuriranje DNA baze;
- automatske lokalne sigurnosne kopije.

Prvo bih završio portable izdanje. Installer i automatsko ažuriranje dolaze tek nakon stabilnog formata projekta i fizičke Pa800 provjere.

## 17. Zaštita podataka

Aplikacija treba poštovati sljedeća pravila:

- MIDI se ne šalje na internet;
- API sluša samo na `127.0.0.1`;
- original se nikada ne prepisuje;
- privremeni optimizirani rezultati automatski istječu;
- projektne sigurnosne kopije imaju ograničen broj verzija;
- svaki export dobiva hash;
- AI/cloud integracije, ako se ikada dodaju, moraju biti potpuno opcione i isključene po defaultu.

## 18. Testni standard

Svaka nova funkcija treba imati dokaz na odgovarajućoj razini:

- mala formula ili helper: unit test;
- komunikacija modula: integration test;
- cijeli korisnički workflow: E2E test;
- stabilnost baze i ID-eva: regression test;
- svaka blokirajuća greška: negative validation test.

Release ne smije proći ako padne bilo koji core invariant:

```text
goldAffectsDynamics = false
analysisVelocityUsed = false
sameSeedSameOutput = true
invalidMidiExported = false
```

Uz automatski test treba ostati i mali ručni checklist za GUI, playback i Windows pokretanje.

## 19. Roadmap koji bih slijedio

### Etapa A — Stabilizacija trenutnog corea — IMPLEMENTIRANO

- razdvojiti veliki serverski modul;
- dodati schema migracije projektnih datoteka;
- centralizirati audit i error model;
- napraviti automatski release test command;
- dodati više reprezentativnih MIDI regresijskih primjera.

### Etapa B — Stvarni MIDI editor — IMPLEMENTIRANO

- odabir i edit nota;
- solo/mute;
- velocity lane;
- transpozicija;
- selection quantize;
- vizualni prikaz promjena;
- spremanje edit historyja u projekt.

### Etapa C — Napredni Style Builder — IMPLEMENTIRANO

- pattern lock i zamjena kandidata;
- Pattern Inspector;
- akordske inverzije i voice leading;
- registarski collision detector;
- pametniji Variation/Fill prijelazi;
- NTT/Track Type preporuke po traci.

### Etapa D — Pa800 certifikacija — ČEKA FIZIČKI UREĐAJ

- definirani testni Style;
- fizički import svih elemenata;
- slušna kontrola;
- save/load test;
- evidentiranje potrebnih korekcija;
- zaključavanje prve certificirane verzije.

### Etapa E — Windows portable proizvod — IMPLEMENTIRANO

- portable paket;
- ugrađeni runtime;
- automatske sigurnosne kopije;
- crash recovery;
- installer nakon stabilizacije.

## 20. Kako izgleda idealan korisnički workflow

Idealni proces treba imati što manje prekida:

1. Korisnik dvaput klikne aplikaciju.
2. Povlači MIDI na početni ekran.
3. Aplikacija automatski napravi preflight i song analizu.
4. Korisnik bira želi li optimizirati song ili iz njega napraviti Style.
5. Kod optimizacije bira profil, pregleda promjene i posluša A/B.
6. Kod Stylea potvrđuje sekcije, trake, Factory zvukove i patterne.
7. Engine generira rezultat istim seedom.
8. Hard validator provjerava cijelu datoteku.
9. Reports ekran pokazuje zašto je rezultat prošao ili zašto je blokiran.
10. Korisnik preuzima `.MID`, manifest i audit.
11. Za Pa800 slijedi vođeni USB checklist.

Korisnik nikada ne bi trebao razmišljati o tome je li marker napisan velikim slovom, je li EOT na kraju ili je li Program Change na pravom ticku. To su odgovornosti enginea i validatora.

## 21. Konačna slika projekta

Konačni DNA MIDI Studio vidim kao spoj glazbenog asistenta i strogog tehničkog kontrolora.

Glazbeni dio treba pomagati korisniku da brzo dođe do boljeg aranžmana. Tehnički dio treba biti nepovjerljiv: ništa se ne izvozi samo zato što “vjerojatno radi”. Svaki rezultat mora imati dokaz o izvoru dinamike, odabranim patternima, seedu, verziji baze i prolaznoj validaciji.

Projekt će biti uspješan kada korisnik može uzeti prosječan ili problematičan MIDI, u nekoliko minuta dobiti čišću verziju ili smislen Pa800 Style, razumjeti što je aplikacija promijenila i bez straha nastaviti rad na instrumentu.

Najkraće rečeno, aplikacija treba biti:

```text
jednostavna za glazbenika
precizna za MIDI
transparentna u odlukama
stroga prema greškama
sigurna za Pa800
```