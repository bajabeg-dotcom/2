# Session 14 — fizička Korg Pa800 certifikacija

Status: **TEST-PAKET PRIPREMLJEN / WAITING_FOR_DEVICE**

Ovaj korak zahtijeva stvarni Korg Pa800 s OS-om 2.0 ili novijim. Softverski test ne smije sam dodijeliti `PA800_DEVICE_CERTIFIED`.

## Priprema paketa

```text
py session14_device_check.py prepare
```

Datoteke nastaju u `artifacts/session14-device-kit/`:

- `DNA_PA800_FUNCTIONAL_TEST.mid` — svih deset osnovnih marker-sekcija i osam Style kanala;
- `DNA_PA800_POLYPHONY_STRESS.mid` — istodobni projektni maksimum od 54 MIDI note bez prekoračenja limita pojedine trake;
- pripadajući JSON manifesti i SHA-256;
- `device-result-template.json` — obrazac koji korisnik ispunjava nakon testa;
- `DNA-PA800-Session14-Device-Test-Kit.zip` — deterministički paket bez korisničkih rezultata i dokaza.

Isti ZIP može se preuzeti u lokalnom GUI-ju kroz **Reports & Safety → Preuzmi Pa800 test-paket** ili putem rute `/api/device-test-kit`. Status preflighta dostupan je na `/api/device-preflight`.

## Postupak na instrumentu

1. Kopiraj oba MIDI-ja na USB.
2. Uđi u Style Record i napravi novi Style.
3. Otvori Import SMF, drži SHIFT i pritisni Execute.
4. Za novi Style uključi Initialize.
5. Potvrdi C Major, Track Type i NTT za svaku traku.
6. Preslušaj Intro, Variation, Fill i Ending prijelaze funkcionalnog Stylea.
7. Provjeri solo, Delay, RX/DNC samo na potvrđenim zvukovima, stuck note, clipping i headroom.
8. Učitaj polifonijski stress Style i poslušaj postoji li neprihvatljiv voice stealing.
9. Spremi Style u USER/FAVORITE, ponovno ga učitaj i ponovi test.
10. Spremi barem jednu fotografiju ekrana i jednu audiosnimku uz ispunjeni rezultatni JSON.

## Provjera rezultata

```text
py session14_device_check.py verify --result artifacts/session14-device-kit/device-result.json
```

Tek potpuno ispunjen rezultat s odgovarajućim hashovima, slikovnim/audio dokazom i izričitom ljudskom potvrdom može proizvesti status `PA800_DEVICE_CERTIFIED`.

Važno: 54 istodobne MIDI note nisu isto što i 54 fizička oscillator glasa. Višeslojni Pa800 Sound može trošiti više hardverskih glasova po noti, pa je slušni stress test obavezan.