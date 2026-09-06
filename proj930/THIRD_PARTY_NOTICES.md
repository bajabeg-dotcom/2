# Third-party provenance and notices

Ovaj projekat može sadržavati ili biti izveden iz javno dostupnih GitHub projekata, MIDI/pattern korpusa, Python paketa i modela. Sama javna dostupnost ili korisnikova dozvola da se nešto kopira ne prenosi autorska prava niti automatski dopušta komercijalnu redistribuciju.

Prije prodaje, za svaku treću komponentu treba evidentirati: naziv, izvorni URL i commit, autora, licencu i verziju licence, izmjene, datoteke koje su korištene, te obaveze atribucije/source-disclosure. Stavka bez provjerljive licence mora biti uklonjena ili zamijenjena originalnim materijalom.

Trenutni status: **PROVENANCE REVIEW REQUIRED**. Ovaj dokument nije potvrda da su sva komercijalna prava očišćena.

## MidiTok
Vendored from Natooz/MidiTok. MIT License. Original license at `third_party/miditok/LICENSE`.

## Microsoft Muzic / MuseCoco
Selected MuseCoco MIDI attribute extractor source vendored from microsoft/muzic. MIT License. Original license at `third_party/muzic_musecoco/LICENSE`.

### Microsoft Muzic — GETMusic / Museformer selected reference sources
Selected source/reference files are retained under `third_party/muzic_getmusic/` and `third_party/muzic_museformer/` with the upstream MIT license. Runtime 7.20 uses their architectural concepts through DNA adapters; the default path does not require Fairseq/blocksparse.
