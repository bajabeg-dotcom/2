# DNA MIDI Studio 6.03 — Pre-sale release candidate

Datum audita: 2026-09-05

Dozvoljeni naziv proizvoda prije završetka vanjskih provjera je **AI PREMIUM ARRANGER PREVIEW**.

## Stanje

- Glavni GUI tok: FULL AI Optimization 6.0.
- Obnovljen je kanonski `prism-uploads/DNA.zip` i potvrđen SHA-256 `125f4486625db44f7cdd49bd670aff252a961c88ea14741ec970ec3ae5eec85a`.
- Popravljen je neispravan zbirni hash Premium 3.17 baseline manifesta; baseline testovi prolaze 20/20.
- Obnovljen je Pa800 device-test kit; softverski preflight prolazi 12/12.
- Windows paket sada uključuje oba runtime modula koja su ranije nedostajala i prolazi clean-extract import provjeru.
- Verzije paketa, Python projekta i VERSION datoteka usaglašene su na 6.03 / 6.3.0.
- MAX batch CLI sada fail-closed zapisuje pojedinačni BLOCKED izvještaj kada Brain analiza ili validator naiđu na neispravan MIDI, umjesto da prekine cijelu mapu.

## Obavezni uslovi prije konačne prodajne tvrdnje

1. Završiti puni regresioni suite bez grešaka ili formalno arhivirati zastarjele Session 9/11/17/31/32 testove uz odobrenu novu specifikaciju.
2. Završiti svih 150 pjesama; prethodni dokaz pokriva samo 13/150.
3. Izvršiti Style Works XT round-trip na stvarnoj instalaciji i sačuvati ulaz, izlaz, log i hashove.
4. Izvršiti test na fizičkom Korg Pa800 i popuniti potpisani device-result obrazac sa audio/foto dokazima.
5. Potvrditi licence i porijeklo svih GitHub/trećih obrazaca, modela, podataka i zvučnih/muzičkih materijala.
6. Prodavac i kupac moraju potpisati ugovor koji definiše IP prenos/licencu, cijenu, podršku, garancije, ograničenje odgovornosti i acceptance kriterije.

Dok ovi uslovi nisu zatvoreni, paket je demonstracijski/pre-sale RC, a ne certificirani finalni Pa800 proizvod.
