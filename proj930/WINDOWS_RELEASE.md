# Windows portable release

Podržani sustavi: 64-bit Windows 10 i Windows 11. Podržan je CPython 3.11–3.14.
Aplikacija koristi samo Python standardnu biblioteku i ne instalira pakete s interneta.

## Pokretanje

1. Raspakiraj cijeli ZIP u mapu u kojoj korisnik ima pravo pisanja.
2. Pokreni `testiraj.bat`. Očekivani rezultat je legacy 43/43 PASS i recovery + uređajni preflight + Premium/Renderer/Coherence/Workflow/Reliability/Quality/Device Intake sigurnost 2900/2900 PASS.
3. Pokreni `pokreni.bat` i otvori `http://127.0.0.1:8765/`.
4. U **Reports & Safety** preuzmi deterministički Pa800 test-paket za fizičku Session 14 provjeru.
5. `run.bat` je kompatibilni alias za `pokreni.bat`.

Workspace **Personal Profile** sprema samo lokalne, izričito prihvaćene glazbene preferencije. Ne sprema MIDI, projekt ni audio; gumb za potpuno brisanje vraća neutralni deterministički ranking.

Workspace **Release Readiness** prikazuje 17 software, quality, evidence, device, export i marketing gateova. Zeleni software RC ne otključava finalni MIDI: dopušten je samo naziv `AI PREMIUM ARRANGER PREVIEW` dok listening i fizički Pa800 dokaz ne prođu.

## Ponovna izgradnja DNA baza

`izgradi-dna.bat` koristi autoritativnu `prism-uploads/DNA.zip` arhivu, ponovno gradi
pet registryja u `data` i odmah pokreće puni `release_check.py`. `install.bat` je kompatibilni
alias za isti postupak. Rebuild može trajati nekoliko minuta.

## Rješavanje problema

- Poruka da Python nije pronađen: instaliraj CPython 3.11–3.14 i uključi “Add Python to PATH”.
- Port 8765 je zauzet: zatvori drugi lokalni proces ili pokreni `py -3 server.py --port 8766`.
- Registry/hash greška: ponovno pokreni `izgradi-dna.bat`; originalni source ZIP se ne mijenja.
- Antivirus blokira zapis: raspakiraj paket u korisničku mapu, ne u `Program Files`.
- Na sporijem računalu clean-extract provjera može trajati više od četiri minute. Zadani limit je
  900 sekundi; po potrebi se prije provjere može postaviti
  `set DNA_RELEASE_SMOKE_TIMEOUT_SECONDS=1200` (dopušten raspon je 60–3600 sekundi).
- Fizički Pa800 status ostaje `WAITING_FOR_DEVICE` do potpisane USB/NTT/listening provjere.

Datoteka `data/release-package-manifest.json` sadrži SHA-256 i veličinu svake datoteke paketa.
Vanjska `.sha256` datoteka potvrđuje cijeli ZIP.
