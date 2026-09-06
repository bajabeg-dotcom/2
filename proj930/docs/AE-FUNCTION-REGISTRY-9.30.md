# DNA MIDI Studio 9.30 — AE (Architecture Envelope) Function Registry

**Verzija:** 9.30  
**Datum:** 2026-09-06  
**Ukupno funkcija:** 234  
**Jezgra:** Chord Tracking — *Mora sve pratit Chord kao osnovno*  

---

## Autoritet Model

| Autoritet | Domena | Opis |
|---|---|---|
| **FACTORY** | Velocity / Volume / Mixer | Jedini velocity autoritet — HARDWARE_PENDING |
| **GOLD** | Timing / Expression / Articulation / Playing Logic | Nikad velocity — 12918 referentnih paterna |
| **PA800_ENGINE** | Mapping / Range / RX-DNC / NTT / Export | Hard limiti po Korg PA800 specifikaciji |
| **CHORD** | Tonalitet / Harmonija / Sekcije | Osnova — chord_timeline hrani sve tri autoriteta |

### Chord Flow Arhitektura

```
MIDI Input ──→ song_analyzer.chord_timeline() ──┬──→ FACTORY (velocity po chord kontekstu)
                                                ├──→ GOLD (timing/artikulacija po chord sekciji)
                                                └──→ PA800 (NTT/range po chord root-u)
                                                      │
                                                      ▼
                                              optimize_midi() ──→ General Rules Gate ──→ Output
```

**Princip:** Svaka funkcija prati Chord. Nijedna funkcija ne može djelovati bez chord konteksta.

---

## Chord Dependency Skala

| Nivo | Značenje | Broj funkcija |
|---|---|---|
| **STRONG** | Direktno čita chord_timeline / odlučuje po chord ćeliji | 37 |
| **MEDIUM** | Ponašanje se mijenja po chord sekciji / chord kontekstu | 31 |
| **WEAK** | Radi na podacima koji su već chord-filtrirani kroz pipeline | 166 |

**Ukupno:** 234 funkcija → 100% chord-dependent

---

## 1. MIXER/LEVEL — FACTORY Autoritet (26 funkcija)

| # | ID | Naziv | Status | Chord |
|---|---|---|---|---|
| 1 | factory_mixer | Factory Mixer (CC7/CC11) | HARDWARE_PENDING | WEAK |
| 2 | factory_volume_profile | Factory Volume Profile | HARDWARE_PENDING | WEAK |
| 3 | channel_volume_balance | Channel Volume Balance | HARDWARE_PENDING | WEAK |
| 4 | velocity_to_volume | Velocity→Volume Compensation | HARDWARE_PENDING | WEAK |
| 5 | dynamic_volume_curve | Dynamic Volume Curve | HARDWARE_PENDING | WEAK |
| 6 | drum_kit_balance | Drum Kit Volume Balance | HARDWARE_PENDING | WEAK |
| 7 | bass_level | Bass Level Control | HARDWARE_PENDING | STRONG |
| 8 | chord_level | Chord Level Control | HARDWARE_PENDING | STRONG |
| 9 | guitar_level | Guitar Level Control | HARDWARE_PENDING | MEDIUM |
| 10 | solo_level | Solo Level Control | HARDWARE_PENDING | MEDIUM |
| 11 | pad_level | Pad Level Control | HARDWARE_PENDING | MEDIUM |
| 12 | mute_solo_logic | Mute/Solo Logic (per-track) | HARDWARE_PENDING | WEAK |
| 13 | cc7_insertion | CC7 Insertion | HARDWARE_PENDING | WEAK |
| 14 | cc11_insertion | CC11 Expression Insertion | HARDWARE_PENDING | WEAK |
| 15 | cc10_pan | CC10 Pan Control | HARDWARE_PENDING | WEAK |
| 16 | cc91_reverb | CC91 Reverb Send | HARDWARE_PENDING | WEAK |
| 17 | cc93_chorus | CC93 Chorus Send | HARDWARE_PENDING | WEAK |
| 18 | cc1_modulation | CC1 Modulation | SOFTWARE_VALIDATED | WEAK |
| 19 | master_volume | Master Volume Meta | HARDWARE_PENDING | WEAK |
| 20 | track_gain_offset | Track Gain Offset | HARDWARE_PENDING | WEAK |
| 21 | velocity_trim | Velocity Trim per-track | HARDWARE_PENDING | WEAK |
| 22 | volume_fade_in | Volume Fade-In | SOFTWARE_VALIDATED | WEAK |
| 23 | volume_fade_out | Volume Fade-Out | SOFTWARE_VALIDATED | WEAK |
| 24 | dynamic_compression | Dynamic Compression | HARDWARE_PENDING | WEAK |
| 25 | ducking | Ducking (Bass vs Kick) | SOFTWARE_VALIDATED | STRONG |
| 26 | sidechain_sim | Sidechain Simulation | SOFTWARE_VALIDATED | STRONG |

---

## 2. VELOCITY — FACTORY Autoritet (28 funkcija)

| # | ID | Naziv | Status | Chord |
|---|---|---|---|---|
| 1 | factory_velocity_profile | Factory Velocity Profile | 1713 profiles | WEAK |
| 2 | instrument_velocity_curve | Instrument Velocity Curve | HARDWARE_PENDING | WEAK |
| 3 | pp_fff_mapping | PP→FFF Dynamic Mapping | 7-point curves | WEAK |
| 4 | velocity_range_enforcement | Velocity Range Enforcement (GR) | ENFORCED | WEAK |
| 5 | velocity_outlier_correction | Velocity Outlier Correction | HARDWARE_PENDING | WEAK |
| 6 | ghost_note_velocity | Ghost Note Velocity | HARDWARE_PENDING | WEAK |
| 7 | accent_velocity | Accent Velocity | HARDWARE_PENDING | WEAK |
| 8 | velocity_sensitivity | Velocity Sensitivity Curve | HARDWARE_PENDING | WEAK |
| 9 | velocity_scale | Velocity Scale (global) | HARDWARE_PENDING | WEAK |
| 10 | velocity_curve_linear | Linear Velocity Curve | HARDWARE_PENDING | WEAK |
| 11 | velocity_curve_log | Logarithmic Velocity Curve | HARDWARE_PENDING | WEAK |
| 12 | velocity_curve_exp | Exponential Velocity Curve | HARDWARE_PENDING | WEAK |
| 13 | velocity_curve_s | S-Curve Velocity | HARDWARE_PENDING | WEAK |
| 14 | velocity_curve_wide | Wide Dynamic Range | HARDWARE_PENDING | WEAK |
| 15 | velocity_curve_narrow | Narrow Dynamic Range | HARDWARE_PENDING | WEAK |
| 16 | velocity_per_instrument | Per-Instrument Velocity Map | 1713 profiles | WEAK |
| 17 | velocity_per_drum_key | Per-Drum-Key Velocity | HARDWARE_PENDING | WEAK |
| 18 | velocity_floor | Velocity Floor (min 1) | ENFORCED | WEAK |
| 19 | velocity_ceiling | Velocity Ceiling (max 127) | ENFORCED | WEAK |
| 20 | velocity_randomize | Velocity Randomize (human) | HARDWARE_PENDING | WEAK |
| 21 | velocity_groove_shift | Velocity Groove Shift | GOLD reference | STRONG |
| 22 | velocity_phrase_arc | Velocity Phrase Arc | HARDWARE_PENDING | MEDIUM |
| 23 | velocity_section_map | Velocity Section Map | GOLD reference | MEDIUM |
| 24 | velocity_tendency_curve | Velocity Tendency Curve | HARDWARE_PENDING | WEAK |
| 25 | velocity_clamp_note_on | Note-On Velocity Clamp (GR) | ENFORCED | WEAK |
| 26 | velocity_clamp_note_off | Note-Off Velocity Clamp | ENFORCED | WEAK |
| 27 | velocity_aftertouch | Aftertouch Velocity Response | SOFTWARE_VALIDATED | WEAK |
| 28 | velocity_breath_ctrl | Breath Controller Velocity | SOFTWARE_VALIDATED | WEAK |

---

## 3. EXPRESSION — GOLD Autoritet (25 funkcija)

| # | ID | Naziv | Status | Chord |
|---|---|---|---|---|
| 1 | gold_expression_logic | Gold Expression Logic | 12918 patterns | WEAK |
| 2 | cc11_humanization | CC11 Humanization | HARDWARE_PENDING | WEAK |
| 3 | phrase_expression_curve | Phrase Expression Curve | SOFTWARE_VALIDATED | MEDIUM |
| 4 | swell_detection | Swell Detection | SOFTWARE_VALIDATED | STRONG |
| 5 | swell_generation | Swell Generation | SOFTWARE_VALIDATED | STRONG |
| 6 | expression_smoothing | Expression Smoothing | HARDWARE_PENDING | WEAK |
| 7 | crescendo_curve | Crescendo Curve | SOFTWARE_VALIDATED | MEDIUM |
| 8 | diminuendo_curve | Diminuendo Curve | SOFTWARE_VALIDATED | MEDIUM |
| 9 | cc1_modulation_expression | CC1 Modulation Expression | SOFTWARE_VALIDATED | WEAK |
| 10 | cc74_brightness | CC74 Brightness (timbre) | SOFTWARE_VALIDATED | WEAK |
| 11 | cc71_filter_resonance | CC71 Filter Resonance | SOFTWARE_VALIDATED | WEAK |
| 12 | pitch_bend_expression | Pitch Bend Expression | SOFTWARE_VALIDATED | WEAK |
| 13 | channel_pressure | Channel Pressure (mono AT) | SOFTWARE_VALIDATED | WEAK |
| 14 | poly_pressure | Polyphonic Aftertouch | SOFTWARE_VALIDATED | WEAK |
| 15 | portamento_time | Portamento Time (CC5/CC84) | SOFTWARE_VALIDATED | WEAK |
| 16 | portamento_switch | Portamento On/Off (CC65) | SOFTWARE_VALIDATED | WEAK |
| 17 | vibrato_depth | Vibrato Depth | SOFTWARE_VALIDATED | WEAK |
| 18 | vibrato_rate | Vibrato Rate | SOFTWARE_VALIDATED | WEAK |
| 19 | breath_controller_cc2 | Breath Controller CC2 | SOFTWARE_VALIDATED | WEAK |
| 20 | legato_expression | Legato Expression | SOFTWARE_VALIDATED | MEDIUM |
| 21 | staccato_expression | Staccato Expression | SOFTWARE_VALIDATED | WEAK |
| 22 | sustain_pedal_cc64 | Sustain Pedal CC64 | SOFTWARE_VALIDATED | WEAK |
| 23 | soft_pedal_cc67 | Soft Pedal CC67 | SOFTWARE_VALIDATED | WEAK |
| 24 | sostenuto_cc66 | Sostenuto CC66 | SOFTWARE_VALIDATED | WEAK |
| 25 | release_time_cc72 | Release Time CC72 | SOFTWARE_VALIDATED | WEAK |

---

## 4. TIMING/GROOVE — GOLD Autoritet (30 funkcija)

| # | ID | Naziv | Status | Chord |
|---|---|---|---|---|
| 1 | gold_timing_profile | Gold Timing Profile | 12918 patterns | WEAK |
| 2 | micro_timing | Micro Timing | SOFTWARE_VALIDATED | WEAK |
| 3 | human_timing | Human Timing | SOFTWARE_VALIDATED | WEAK |
| 4 | groove_template | Groove Template | GOLD reference | STRONG |
| 5 | swing_detection | Swing Detection | SOFTWARE_VALIDATED | WEAK |
| 6 | drum_timing | Drum Timing | SOFTWARE_VALIDATED | WEAK |
| 7 | bass_timing | Bass Timing | SOFTWARE_VALIDATED | MEDIUM |
| 8 | chord_timing | Chord Timing | CHORD FOUNDATION | STRONG |
| 9 | quantize_grid | Quantize Grid | SOFTWARE_VALIDATED | WEAK |
| 10 | quantize_strength | Quantize Strength (0-100%) | SOFTWARE_VALIDATED | WEAK |
| 11 | quantize_swing | Quantize Swing % | SOFTWARE_VALIDATED | WEAK |
| 12 | quantize_groove | Groove Quantize | GOLD reference | STRONG |
| 13 | humanize_delay | Humanize Delay (random) | SOFTWARE_VALIDATED | WEAK |
| 14 | push_timing | Push Timing (ahead of beat) | GOLD reference | WEAK |
| 15 | laid_back_timing | Laid-Back Timing | GOLD reference | WEAK |
| 16 | metronome_timing | Metronome Timing (strict) | SOFTWARE_VALIDATED | WEAK |
| 17 | rubato_timing | Rubato Timing | SOFTWARE_VALIDATED | WEAK |
| 18 | tempo_track | Tempo Track | SOFTWARE_VALIDATED | WEAK |
| 19 | tempo_detection | Tempo Detection | SOFTWARE_VALIDATED | WEAK |
| 20 | tempo_mapping | Tempo Mapping | SOFTWARE_VALIDATED | WEAK |
| 21 | time_signature_detect | Time Signature Detection | SOFTWARE_VALIDATED | WEAK |
| 22 | bar_line_alignment | Bar Line Alignment | SOFTWARE_VALIDATED | WEAK |
| 23 | half_bar_cells | Half-Bar Cells (chord) | CHORD FOUNDATION | STRONG |
| 24 | beat_subdivision | Beat Subdivision | SOFTWARE_VALIDATED | WEAK |
| 25 | phrase_timing | Phrase Timing | GOLD reference | STRONG |
| 26 | fill_timing | Fill Timing | GOLD reference | STRONG |
| 27 | break_timing | Break Timing | GOLD reference | WEAK |
| 28 | syncopation_detection | Syncopation Detection | SOFTWARE_VALIDATED | WEAK |
| 29 | offbeat_emphasis | Offbeat Emphasis | SOFTWARE_VALIDATED | WEAK |
| 30 | sixteenth_swing | 16th Swing | SOFTWARE_VALIDATED | WEAK |

---

## 5. ARTICULATION — GOLD Autoritet (25 funkcija)

| # | ID | Naziv | Status | Chord |
|---|---|---|---|---|
| 1 | gold_articulation_profile | Gold Articulation Profile | 12918 patterns | WEAK |
| 2 | trill_detection | Trill Detection | SOFTWARE_VALIDATED | WEAK |
| 3 | slide_generation | Slide Generation | SOFTWARE_VALIDATED | WEAK |
| 4 | strum_pattern | Strum Pattern | FACTORY reference | MEDIUM |
| 5 | strum_timing | Strum Timing | SOFTWARE_VALIDATED | MEDIUM |
| 6 | grace_note_detection | Grace Note Detection | SOFTWARE_VALIDATED | STRONG |
| 7 | ornament_generation | Ornament Generation | SOFTWARE_VALIDATED | STRONG |
| 8 | legato_articulation | Legato Articulation | SOFTWARE_VALIDATED | WEAK |
| 9 | staccato_articulation | Staccato Articulation | SOFTWARE_VALIDATED | WEAK |
| 10 | marcato_articulation | Marcato Articulation | SOFTWARE_VALIDATED | WEAK |
| 11 | tenuto_articulation | Tenuto Articulation | SOFTWARE_VALIDATED | WEAK |
| 12 | accent_articulation | Accent Articulation | SOFTWARE_VALIDATED | WEAK |
| 13 | fp_articulation | Forte-Piano | SOFTWARE_VALIDATED | WEAK |
| 14 | sfz_articulation | Sforzando | SOFTWARE_VALIDATED | WEAK |
| 15 | mordent_upper | Upper Mordent | SOFTWARE_VALIDATED | MEDIUM |
| 16 | mordent_lower | Lower Mordent | SOFTWARE_VALIDATED | MEDIUM |
| 17 | turn_articulation | Turn | SOFTWARE_VALIDATED | MEDIUM |
| 18 | appoggiatura | Appoggiatura | SOFTWARE_VALIDATED | MEDIUM |
| 19 | acciaccatura | Acciaccatura | SOFTWARE_VALIDATED | WEAK |
| 20 | glissando | Glissando | SOFTWARE_VALIDATED | WEAK |
| 21 | bend_up | Bend Up | SOFTWARE_VALIDATED | WEAK |
| 22 | bend_down | Bend Down | SOFTWARE_VALIDATED | WEAK |
| 23 | slide_guitar | Slide Guitar | FACTORY reference | WEAK |
| 24 | hammer_on | Hammer-On | SOFTWARE_VALIDATED | WEAK |
| 25 | pull_off | Pull-Off | SOFTWARE_VALIDATED | WEAK |

---

## 6. DRUMS/PERCUSSION — FACTORY+GOLD Autoritet (25 funkcija)

| # | ID | Naziv | Status | Chord |
|---|---|---|---|---|
| 1 | drum_element_profile | Drum Element Profile | SOFTWARE_VALIDATED | WEAK |
| 2 | kick_profile | Kick Profile | SOFTWARE_VALIDATED | WEAK |
| 3 | snare_profile | Snare Profile | SOFTWARE_VALIDATED | WEAK |
| 4 | hihat_profile | Hi-Hat Profile | SOFTWARE_VALIDATED | WEAK |
| 5 | ghost_snare_logic | Ghost Snare Logic | SOFTWARE_VALIDATED | WEAK |
| 6 | drum_fill_logic | Drum Fill Logic | GOLD reference | STRONG |
| 7 | drum_velocity_humanization | Drum Velocity Humanization | FACTORY | WEAK |
| 8 | drum_pattern_density | Drum Pattern Density | GOLD reference | WEAK |
| 9 | ride_cymbal_profile | Ride Cymbal Profile | SOFTWARE_VALIDATED | WEAK |
| 10 | crash_cymbal_profile | Crash Cymbal Profile | SOFTWARE_VALIDATED | WEAK |
| 11 | toms_profile | Toms Profile | SOFTWARE_VALIDATED | WEAK |
| 12 | percussion_conga | Conga Profile | SOFTWARE_VALIDATED | WEAK |
| 13 | percussion_bongo | Bongo Profile | SOFTWARE_VALIDATED | WEAK |
| 14 | percussion_timbale | Timbale Profile | SOFTWARE_VALIDATED | WEAK |
| 15 | percussion_cowbell | Cowbell Profile | SOFTWARE_VALIDATED | WEAK |
| 16 | rimshot_logic | Rimshot Logic | SOFTWARE_VALIDATED | WEAK |
| 17 | cymbal_choke | Cymbal Choke | SOFTWARE_VALIDATED | WEAK |
| 18 | hihat_open_close | Hi-Hat Open/Close | SOFTWARE_VALIDATED | WEAK |
| 19 | drum_key_validation | Drum Key Validation (GR) | ENFORCED | WEAK |
| 20 | drum_channel_enforcement | Drum Channel=10 (GR) | ENFORCED | WEAK |
| 21 | drum_duck_logic | Drum Duck Logic (groove) | SOFTWARE_VALIDATED | WEAK |
| 22 | drum_flam_detection | Flam Detection | SOFTWARE_VALIDATED | WEAK |
| 23 | drum_roll_detection | Roll Detection | SOFTWARE_VALIDATED | WEAK |
| 24 | drum_crescendo | Drum Crescendo Logic | SOFTWARE_VALIDATED | MEDIUM |
| 25 | shaker_tambourine | Shaker/Tambourine Profile | SOFTWARE_VALIDATED | WEAK |

---

## 7. ARRANGEMENT/PATTERN — GOLD+CHORD Autoritet (25 funkcija)

| # | ID | Naziv | Status | Chord |
|---|---|---|---|---|
| 1 | pattern_dna | Pattern DNA | SOFTWARE_VALIDATED | WEAK |
| 2 | pattern_density | Pattern Density | GOLD reference | WEAK |
| 3 | intro_pattern | Intro Pattern Logic | GOLD reference | WEAK |
| 4 | variation_pattern | Variation Pattern Logic | GOLD reference | WEAK |
| 5 | fill_pattern | Fill Pattern Logic | GOLD reference | WEAK |
| 6 | chord_pattern_adaptation | Chord Pattern Adaptation | CHORD FOUNDATION | STRONG |
| 7 | bass_pattern_adaptation | Bass Pattern Adaptation | CHORD+FACTORY | STRONG |
| 8 | guitar_pattern_adaptation | Guitar Pattern Adaptation | FACTORY reference | MEDIUM |
| 9 | section_detection | Section Detection | SOFTWARE_VALIDATED | STRONG |
| 10 | verse_detection | Verse Detection | SOFTWARE_VALIDATED | STRONG |
| 11 | chorus_detection | Chorus Detection | SOFTWARE_VALIDATED | STRONG |
| 12 | bridge_detection | Bridge Detection | SOFTWARE_VALIDATED | STRONG |
| 13 | break_detection | Break Detection | SOFTWARE_VALIDATED | STRONG |
| 14 | outro_detection | Outro Detection | SOFTWARE_VALIDATED | STRONG |
| 15 | phase_plan_construction | Phase Plan Construction | GOLD reference | STRONG |
| 16 | repeat_detection | Repeat Detection | SOFTWARE_VALIDATED | WEAK |
| 17 | ending_detection | Ending Detection | SOFTWARE_VALIDATED | WEAK |
| 18 | style_variation_auto | Style Variation Auto-Select | PA800 reference | MEDIUM |
| 19 | fill_auto_trigger | Fill Auto-Trigger | GOLD reference | MEDIUM |
| 20 | break_fill_generation | Break/Fill Generation | GOLD reference | MEDIUM |
| 21 | chord_change_fill | Chord-Change Fill | CHORD FOUNDATION | STRONG |
| 22 | transition_logic | Transition Logic | GOLD reference | STRONG |
| 23 | part_select_logic | Part Select Logic | PA800 reference | MEDIUM |
| 24 | arrangement_map | Arrangement Map | SOFTWARE_VALIDATED | STRONG |
| 25 | auto_accomp_logic | Auto-Accomp Logic | PA800 reference | STRONG |

---

## 8. KORG PA800 — PA800_ENGINE Autoritet (25 funkcija)

| # | ID | Naziv | Status | Chord |
|---|---|---|---|---|
| 1 | pa800_channel_mapping | PA800 Channel Mapping | ENFORCED | WEAK |
| 2 | gm_pa800_mapping | GM→PA800 Mapping | ENFORCED | WEAK |
| 3 | rx_sound_mapping | RX Sound Mapping | DEVICE_CONFIRMED | WEAK |
| 4 | dnc_sound_mapping | DNC Sound Mapping | DEVICE_CONFIRMED | WEAK |
| 5 | cc00_bank_select | CC00 Bank Select | ENFORCED | WEAK |
| 6 | program_change_mapping | Program Change Mapping | ENFORCED | WEAK |
| 7 | ntt_detection | NTT Detection | DEVICE_CONFIRM | STRONG |
| 8 | chord_recognition_compat | Chord Recognition Compat | CHORD FOUNDATION | STRONG |
| 9 | korg_range_enforcement | Korg Range Enforcement | ENFORCED | WEAK |
| 10 | korg_note_limit | Korg Note Limit Enforcement | ENFORCED | MEDIUM |
| 11 | korg_controller_validation | Korg Controller Validation | SOFTWARE_VALIDATED | WEAK |
| 12 | style_format_output | Style Format Output | ENFORCED | WEAK |
| 13 | midi_file_format_output | MIDI File Format Output | ENFORCED | WEAK |
| 14 | korg_sysex_encoding | Korg SysEx Encoding | SOFTWARE_VALIDATED | WEAK |
| 15 | korg_chord_sysex | Korg Chord SysEx Events | SOFTWARE_VALIDATED | WEAK |
| 16 | style_intelligence_ntt | Style Intelligence NTT | DEVICE_CONFIRM | WEAK |
| 17 | ntt_transposition | NTT Transposition | CHORD FOUNDATION | STRONG |
| 18 | voice_lead_logic | Voice Lead Logic | DEVICE_CONFIRM | WEAK |
| 19 | unison_resolution | Unison Resolution | DEVICE_CONFIRM | WEAK |
| 20 | pa800_polyphony_limit | PA800 Polyphony Limit (54) | ENFORCED | MEDIUM |
| 21 | c_major_reference | C Major Reference Build | PA800 reference | STRONG |
| 22 | track_label_mapping | Track Label Mapping | ENFORCED | WEAK |
| 23 | style_segment_output | Style Segment Output | ENFORCED | WEAK |
| 24 | korg_sts_mapping | STS (Single Touch Set) | DEVICE_CONFIRMED | WEAK |
| 25 | keyboard_track_split | Keyboard Track Split | PA800 reference | WEAK |

---

## 9. OPTIMIZATION/QA — CROSS_DOMAIN Autoritet (25 funkcija)

| # | ID | Naziv | Status | Chord |
|---|---|---|---|---|
| 1 | midi_dna_fingerprint | MIDI DNA Fingerprint | SOFTWARE_VALIDATED | WEAK |
| 2 | instrument_role_classification | Instrument Role Classification | 19 roles | WEAK |
| 3 | anomaly_detection | Anomaly Detection | SOFTWARE_VALIDATED | WEAK |
| 4 | range_correction | Range Correction (GR) | ENFORCED | STRONG |
| 5 | export_integrity_check | Export Integrity Check | ENFORCED | WEAK |
| 6 | general_rules_gate | General Rules Gate | ENFORCED on every export | STRONG |
| 7 | note_off_pairing | Note-Off Pairing | ENFORCED | MEDIUM |
| 8 | key_clamp_low | Key Clamp Low (per GM) | ENFORCED | STRONG |
| 9 | key_clamp_high | Key Clamp High (per GM) | ENFORCED | STRONG |
| 10 | drum_key_block | Drum Key Block (non-GM) | ENFORCED | WEAK |
| 11 | velocity_clamp | Velocity Clamp (1-127) | ENFORCED | WEAK |
| 12 | polyphony_check | Polyphony Check (54 max) | ENFORCED | MEDIUM |
| 13 | chord_gate_validation | Chord Gate Validation | SOFTWARE_VALIDATED | STRONG |
| 14 | bass_gate_validation | Bass Gate Validation | SOFTWARE_VALIDATED | MEDIUM |
| 15 | guitar_gate_validation | Guitar Gate Validation | SOFTWARE_VALIDATED | MEDIUM |
| 16 | solo_gate_validation | Solo Gate Validation | SOFTWARE_VALIDATED | MEDIUM |
| 17 | pad_gate_validation | Pad Gate Validation | SOFTWARE_VALIDATED | MEDIUM |
| 18 | batch_optimizer | Batch Optimizer | SOFTWARE_VALIDATED | WEAK |
| 19 | calibration_reporter | Calibration Reporter | SOFTWARE_VALIDATED | WEAK |
| 20 | dna_fingerprint_hash | DNA Fingerprint Hash | SOFTWARE_VALIDATED | WEAK |
| 21 | corpus_forensics_report | Corpus Forensics Report | SOFTWARE_VALIDATED | WEAK |
| 22 | neural_model_validator | Neural Model Validator | SOFTWARE_VALIDATED | WEAK |
| 23 | evidence_authority_status | Evidence Authority Status | SOFTWARE_VALIDATED | WEAK |
| 24 | compliance_check | Compliance Self-Check | SOFTWARE_VALIDATED | WEAK |
| 25 | smf_integrity_validator | SMF Integrity Validator | ENFORCED | WEAK |

---

## Statistika

| Metrika | Vrijednost |
|---|---|
| Ukupno funkcija | 234 |
| Jezgreni moduli | 19 |
| Factory profili | 1713 velocity + 251 strumming |
| Gold referentni paterni | 12918 |
| GM programi sa key range | 128 |
| Validni drum ključevi | 61 |
| Polifoni limit (PA800) | 54 |
| Chord kandidati | 168 (14 kvaliteta × 12 rootova) |
| Neuronski modeli | 6 |
| Valja korpus | 163 fajla, 18120 ispravki |
| Chord STRONG | 37 |
| Chord MEDIUM | 31 |
| Chord WEAK | 166 |

---

## Chord Consumer Map (eksplicitni)

Slijedeće funkcije direktno konzumiraju `chord_timeline()`:

| Modul | Funkcija | Autoritet | Chord ulaz |
|---|---|---|---|
| song_analyzer | detect_key | CHORD | → chord kandidati |
| song_analyzer | chord_candidates | CHORD | 14×12 = 168 kandidata |
| song_analyzer | detect_chord | CHORD | histogram + key + bass |
| song_analyzer | chord_timeline | CHORD | **OSNOVA** half-bar ćelije |
| song_analyzer | korg_chord_evidence | PA800 | Pa800 SysEx dekodiranje |
| corpus_forensics | decode_korg_chord | PA800 | FF 7F 07 42 60 08 |
| phase_optimizer | build_phase_plan | GOLD | chordTimeline → pattern |
| phase_optimizer | _chord_root | GOLD | ćelija pri ticku → NTT |
| phase_optimizer | apply_phase_plan | GOLD | chord-aware pitch folding |
| performance_engine | optimize_power_chords | FACTORY | chord gate → normalizacija |
| performance_engine | interlock_bass_to_kick | FACTORY | bass prati chord root + kick |
| performance_engine | optimize_guitar_gate | FACTORY | rhythm-guitar chord gate |
| special_track_engine | optimize_existing_echo_tercia | GOLD | 3/6 glas iz chorda |
| special_track_engine | _diatonic_third_target | GOLD | dijatonska 3/6 u chordu |
| special_track_engine | _plan_third_sequence | GOLD | DP harmonija prati chord |
| special_track_engine | _harmonic_map | GOLD | bar_ticks → chord simboli |
| pa800_style_builder | build_style | PA800 | Referenca C Major za NTT |
| style_intelligence | track_recommendation | PA800 | NTT kandidat po chord ulozi |
| style_intelligence | voice_lead | PA800 | chord-aware oktava |
| style_intelligence | resolve_unison | PA800 | chord voicing kolizija |
| midi_optimizer | _apply_general_rules | PA800 | key range po GM programu |

---

*DNA MIDI Studio 9.30 — AE Function Registry v1.0 — 2026-09-06*
