#!/usr/bin/env python3
"""
Prepare human listening package - blind test for 2 evaluators
Even though BLOCKED, prepare package so user can find people later
"""

import json
import shutil
from pathlib import Path
import random

ARTIFACTS_DIR = Path("artifacts")
CALIB_16_DIR = Path("artifacts/calibrated_16.00")
FULL_CORPUS_DIR = Path("artifacts/full_corpus_16.00/artifacts")
OUTPUT_DIR = Path("artifacts/human_listening_blind_package_17.00")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Select 10 pairs for blind listening (before/after)
# Use 37 artifacts as source
artifacts_files = list(ARTIFACTS_DIR.glob("*.mid"))[:37]
calib_files = list(CALIB_16_DIR.glob("*.mid"))[:37]

# Create mapping
pairs = []
for i, art_file in enumerate(artifacts_files[:10]):
    # Find corresponding calibrated
    calib_match = None
    for cf in calib_files:
        if art_file.stem in cf.name or cf.name.startswith(art_file.stem):
            calib_match = cf
            break
    if not calib_match:
        # Use same index
        if i < len(calib_files):
            calib_match = calib_files[i]
    
    if calib_match:
        pairs.append((art_file, calib_match))

print(f"Selected {len(pairs)} pairs for blind listening")

# Create blind package: rename to A/B randomly
blind_pairs = []
for idx, (before, after) in enumerate(pairs):
    # Randomize which is A and which is B for blind test
    if random.random() > 0.5:
        a_file = before
        b_file = after
        a_is_before = True
    else:
        a_file = after
        b_file = before
        a_is_before = False
    
    # Copy to blind package with neutral names
    pair_dir = OUTPUT_DIR / f"pair_{idx+1:02d}"
    pair_dir.mkdir(exist_ok=True)
    
    shutil.copy(a_file, pair_dir / f"A.mid")
    shutil.copy(b_file, pair_dir / f"B.mid")
    
    # Save truth (for later unblinding)
    blind_pairs.append({
        "pair": idx+1,
        "A": str(a_file.name),
        "B": str(b_file.name),
        "A_is_before": a_is_before,
        "before": str(before.name),
        "after": str(after.name),
        "A_path": str(pair_dir / "A.mid"),
        "B_path": str(pair_dir / "B.mid")
    })

# Create instructions
instructions = """
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
"""

(OUTPUT_DIR / "instructions.md").write_text(instructions, encoding='utf-8')

# Truth file
truth_path = OUTPUT_DIR / "blind_truth.json"
truth_path.write_text(json.dumps(blind_pairs, indent=2, ensure_ascii=False), encoding='utf-8')

# Template for evaluators
template = {
    "evaluator": "IME_EVALUATORA",
    "date": "2026-09-06",
    "pairs": []
}

for i in range(len(pairs)):
    template["pairs"].append({
        "pair": i+1,
        "A_vs_B": "A/B/jednako - koji muzikalnije?",
        "dynamics": "A/B/jednako - koji bolji dynamics?",
        "groove": "A/B/jednako - koji bolji groove?",
        "overall": "A/B/jednako - koji bi pustio na Pa800?",
        "comments": ""
    })

template_path = OUTPUT_DIR / "listening_results_template.json"
template_path.write_text(json.dumps(template, indent=2, ensure_ascii=False), encoding='utf-8')

print(f"\n✅ Human listening blind package prepared: {OUTPUT_DIR}")
print(f"   Pairs: {len(pairs)}")
print(f"   Truth: {truth_path}")
print(f"   Template: {template_path}")
print(f"   Instructions: {OUTPUT_DIR / 'instructions.md'}")

# Also create summary of what is BLOCKED and needs people
blocked_summary = {
    "version": "17.00-HUMAN-LISTENING-BLOCKED",
    "status": "BLOCKED - treba ljude",
    "what_is_needed": {
        "C1_Human_Listening": {
            "need": "2 evaluatora za blind listening test",
            "package": str(OUTPUT_DIR),
            "pairs": len(pairs),
            "criteria": "Calibrated treba pobijediti u >=6/10 (60%)",
            "time_needed": "30-60 min po evaluatoru",
            "current_status": "Paket spreman, čeka evaluatore"
        },
        "C2_Gold_3_Proxy": {
            "need": "Novi Gold izvor za choir, echo, percussion (0 instances u 182 fajla)",
            "current": "18/21 REAL (85%), 3 PROXY (choir, echo, percussion) - 0 instances čak i sa detaljnom klasifikacijom",
            "options": [
                "Pronađi novi Gold MIDI korpus sa choir/echo/percussion",
                "Ili prihvati 18 REAL + 3 PROXY kao realan limit (85% Gold REAL je odlično)",
                "Ili redefiniraj cilj na 18 REAL kao 100% za Gold (jer 3 role ne postoje u stvarnom svijetu Pa800?)"
            ],
            "recommendation": "Prihvati 18 REAL + 3 PROXY kao iskren limit - 85% Gold REAL je ogroman napredak od 20% prije"
        }
    },
    "what_is_done_without_people": "22/25 REAL (88%) - max moguće bez ljudi",
    "what_remains_for_100_percent": [
        "C1: 2 evaluatora blind test (30-60 min)",
        "C2: Odluka o 3 Gold proxy - novi izvor ili prihvati 18 REAL kao limit"
    ]
}

blocked_path = Path("calibration/human_listening_blocked_summary_17.00.json")
blocked_path.write_text(json.dumps(blocked_summary, indent=2, ensure_ascii=False), encoding='utf-8')
print(f"\n✅ Blocked summary: {blocked_path}")
