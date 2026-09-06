
# HUMAN LISTENING BLIND TEST - UPUTE

**Cilj:** 2 evaluatora slušaju 10 parova MIDI fajlova (A vs B) i ocjenjuju koji zvuči bolje/muzikalnije

**Paket:** 10 parova u folderima pair_01 do pair_10, svaki ima A.mid i B.mid

**Zadatak evaluatora:**
1. Slušati A i B za svaki par (koristiti isti instrument/synth)
2. Ocijeniti:
   - Koji zvuči muzikalnije? (A ili B ili jednako)
   - Dynamics (velocity variation) - koji bolji?
   - Groove/timing - koji bolji?
   - Ukupno - koji bi pustio na Korg Pa800?
3. Upisati ocjene u listening_results_template.json

**Blind:** Evaluatori ne znaju koji je before/after - A/B randomizirano

**Truth file:** blind_truth.json sadrži istinu (koji je before/after) - NE pokazivati evaluatorima prije testa

**Nakon testa:** Usporediti rezultate sa truth file, izračunati koliko puta je calibrated pobijedio

**Kriterij PASS:** Calibrated treba pobijediti u >=6/10 parova (60%) za musical improvement

**Files:**
- pair_XX/A.mid i B.mid - blind parovi
- blind_truth.json - istina (samo za admina)
- listening_results_template.json - template za evaluatore
- instructions.md - ove upute
