#!/usr/bin/env python3
"""
DNA MIDI Studio 9.30 — Deterministic Humanization Engine
=========================================================
Deterministička humanizacija: isti ulaz = isti izlaz, NIKAD random.

Koristi profile iz merged alias mapa:
  - humanization type (PHRASE_DRIVEN, BREATH_PHRASE, BOW_PHRASE, etc.)
  - groove profile (BREATH_PHRASE, BOW_PHRASE, PLECTRUM_PHRASE, etc.)
  - early/late bias
  - gate distribucija
  - velocity authority: FACTORY (samo skalira, nikad ne zamjenjuje)

Hard limits (BLOCK/CLAMP):
  - BLOCK: nikad ne generiši random vrijednosti
  - BLOCK: nikad ne zamjenjuj Factory velocity
  - CLAMP: velocity scale ∈ [0.5, 1.2]
  - CLAMP: timing offset ∈ [-8, +8] PPQ
  - CLAMP: gate scale ∈ [0.3, 2.0]
  - Chord tracking: obavezan za sve instrumente

Version: 9.30.0
"""

import json
import sqlite3
import hashlib
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent / 'data'

# ─── HARD LIMITS (BLOCK/CLAMP) ────────────────────────────────────────────
HARD_LIMITS = {
    'velocityScale': {'min': 0.5, 'max': 1.2, 'mode': 'CLAMP'},
    'timingOffsetPPQ': {'min': -8, 'max': 8, 'mode': 'CLAMP'},
    'gateScale': {'min': 0.3, 'max': 2.0, 'mode': 'CLAMP'},
    'velocityOverride': {'mode': 'BLOCK', 'rule': 'FACTORY_is_sole_authority'},
    'randomGeneration': {'mode': 'BLOCK', 'rule': 'deterministic_only'},
    'chordTracking': {'mode': 'BLOCK', 'rule': 'mandatory_for_all_instruments'},
    'maxOrnamentPPQ': {'min': -6, 'max': 6, 'mode': 'CLAMP'},
}

def clamp(value, min_val, max_val):
    """CLAMP: ograniči vrijednost na [min_val, max_val]."""
    return max(min_val, min(max_val, value))


# ─── DETERMINISTIC SEED ENGINE ────────────────────────────────────────────

def deterministic_seed(instrument: str, position_ppq: int, chord_root: int,
                       bar_number: int, section: str = 'verse') -> int:
    """
    Generiši deterministički seed iz pozicije i konteksta.
    ISTI ulaz = ISTI izlaz, uvijek.
    """
    raw = f'{instrument}|{position_ppq}|{chord_root}|{bar_number}|{section}'
    h = hashlib.sha256(raw.encode()).hexdigest()
    return int(h[:8], 16)


def seed_to_float(seed: int, lo: float = 0.0, hi: float = 1.0) -> float:
    """Pretvori seed u float u rasponu [lo, hi]."""
    normalized = (seed % 10000) / 10000.0
    return lo + normalized * (hi - lo)


# ─── HUMANIZATION TYPE DEFINITIONS ────────────────────────────────────────

HUMANIZATION_TYPES = {
    'PHRASE_DRIVEN': {
        'description': 'Frazna humanizacija — prirodni kraj i početak fraze',
        'applicable': ['sax', 'melody', 'riff'],
        'timingProfile': 'phrase_end_late',
        'velocityProfile': 'phrase_arc',
    },
    'BREATH_PHRASE': {
        'description': 'Dah-fraza — timing kod promjene daha',
        'applicable': ['clarinet', 'frula', 'sax', 'wind'],
        'timingProfile': 'breath_point_late',
        'velocityProfile': 'breath_cresc_dim',
    },
    'BOW_PHRASE': {
        'description': 'Gudalo-fraza — timing kod promjene gudala',
        'applicable': ['violin', 'violina', 'cello', 'strings'],
        'timingProfile': 'bow_change_micro',
        'velocityProfile': 'bow_pressure_arc',
    },
    'BOW_FREE': {
        'description': 'Slobodno gudalo — rubato sa širokim vibratom',
        'applicable': ['gusle', 'folk_fiddle'],
        'timingProfile': 'rubato_free',
        'velocityProfile': 'rubato_swell',
    },
    'BELLOW_PHRASE': {
        'description': 'Meh-fraza — dinamika mijeha harmonike',
        'applicable': ['harmonika', 'accordion'],
        'timingProfile': 'bellow_change',
        'velocityProfile': 'bellow_cresc_dim',
    },
    'PLECTRUM_PHRASE': {
        'description': 'Trzalka-fraza — timing kod promjene trzalka',
        'applicable': ['tambura', 'guitar', 'mandolin'],
        'timingProfile': 'pick_alternating',
        'velocityProfile': 'pick_accent',
    },
    'STANDARD': {
        'description': 'Standardna humanizacija — blagi micro-timing',
        'applicable': ['piano', 'bass', 'chords'],
        'timingProfile': 'standard_micro',
        'velocityProfile': 'standard_arc',
    },
    'DRUM_GROOVE': {
        'description': 'Bubanj-groove — element-specific timing',
        'applicable': ['drums', 'percussion'],
        'timingProfile': 'element_groove',
        'velocityProfile': 'element_accent',
    },
}

# ─── TIMING PROFILE TEMPLATES ─────────────────────────────────────────────

TIMING_PROFILES = {
    'phrase_end_late': {
        'phraseStart': -1,   # PPQ: ranije na početku fraze
        'phraseMiddle': 0,   # PPQ: na gridu
        'phraseEnd': 3,      # PPQ: kasni na kraju fraze
        'breathGap': 6,      # PPQ: gap prije novog daha
    },
    'breath_point_late': {
        'breathBefore': -2,
        'breathAfter': 2,
        'sustainedNote': 0,
        'staccatoNote': -1,
    },
    'bow_change_micro': {
        'bowDownStart': -2,
        'bowUpStart': 1,
        'bowChangeMid': 0,
        'sustainedNote': 0,
    },
    'rubato_free': {
        'rubatoRange': 0.15,   # ±15% tempo deviation
        'accentPush': -3,      # akcent ranije
        'cadencePull': 4,      # kadenc kasni
        'phraseBreath': 6,     # dah na kraju fraze
    },
    'bellow_change': {
        'bellowOpen': -1,
        'bellowClose': 2,
        'sustainedChord': 0,
        'rhythmicChord': -1,
    },
    'pick_alternating': {
        'downPick': -1,
        'upPick': 1,
        'strum': 0,
        'arpeggio': 2,
    },
    'standard_micro': {
        'strongBeat': -1,
        'weakBeat': 1,
        'syncopation': 2,
        'offbeat': 1,
    },
    'element_groove': {
        'kick': {'strongBeat': -2, 'weakBeat': 0, 'fill': 1},
        'snare': {'strongBeat': 0, 'ghost': 1, 'fill': 2},
        'closed_hat': {'timekeeper': 0, 'open': 1},
        'open_hat': {'offbeat': -1, 'accent': 0},
        'ride': {'timekeeper': 0, 'accent': -1},
        'crash': {'accent': -2, 'fill': 0},
        'toms': {'fill': 1, 'accent': -1},
    },
}

# ─── VELOCITY PROFILE TEMPLATES ───────────────────────────────────────────
# VAŽNO: Ovo su SCALE faktori za Factory velocity, NIKAD zamjena!

VELOCITY_PROFILES = {
    'phrase_arc': {
        'phraseStart': 0.85,   # meksi početak
        'phraseBuild': 0.95,   # postepeno jačanje
        'phrasePeak': 1.10,    # kulminacija
        'phraseEnd': 0.80,    # fade na kraju
        'breathRecovery': 0.90,
    },
    'breath_cresc_dim': {
        'inBreath': 0.75,     # prije daha — tiho
        'afterBreath': 1.05,  # poslije daha — novo gorivo
        'sustained': 0.95,    # održavanje
        'endOfBreath': 0.70,  # zadnji dah — tiho
    },
    'bow_pressure_arc': {
        'bowDown': 1.05,      # jači pritisak
        'bowUp': 0.92,       # slabiji
        'sulPonte': 0.60,     # blizu mosta — tiho
        'sulTasto': 1.10,     # blizu hvataljke — toplije
    },
    'rubato_swell': {
        'phraseRise': 1.15,   # crescendo
        'phraseCalm': 0.75,   # diminuendo
        'accentBite': 1.20,   # akcent
        'resolution': 0.80,   # rješenje — tiho
    },
    'bellow_cresc_dim': {
        'bellowOpen': 1.05,
        'bellowClose': 0.90,
        'sustainedChord': 0.98,
        'rhythmicChord': 1.08,
    },
    'pick_accent': {
        'downPick': 1.10,
        'upPick': 0.85,
        'strum': 1.05,
        'arpeggio': 0.90,
    },
    'standard_arc': {
        'strongBeat': 1.05,
        'weakBeat': 0.90,
        'syncopation': 0.95,
        'offbeat': 0.88,
    },
    'element_accent': {
        'kick': {'strongBeat': 1.10, 'weakBeat': 0.85, 'fill': 1.05},
        'snare': {'strongBeat': 1.08, 'ghost': 0.70, 'fill': 1.00},
        'closed_hat': {'timekeeper': 0.92, 'open': 1.05},
        'ride': {'timekeeper': 0.95, 'accent': 1.10},
        'crash': {'accent': 1.15, 'fill': 1.00},
    },
}

# ─── GATE DISTRIBUTION TEMPLATES ──────────────────────────────────────────

GATE_PROFILES = {
    'PHRASE_DRIVEN': {'shortNote': 0.6, 'longNote': 0.95, 'phraseEnd': 0.5},
    'BREATH_PHRASE': {'breathNote': 0.5, 'sustainedNote': 0.95, 'staccatoNote': 0.3},
    'BOW_PHRASE': {'detache': 0.85, 'legato': 0.95, 'staccato': 0.35, 'spiccato': 0.4},
    'BOW_FREE': {'rubatoLong': 0.98, 'rubatoShort': 0.5, 'graceNote': 0.2},
    'BELLOW_PHRASE': {'sustainedChord': 0.98, 'rhythmicChord': 0.75, 'bellowsShake': 0.5},
    'PLECTRUM_PHRASE': {'downPick': 0.5, 'upPick': 0.35, 'strum': 0.85, 'arpeggio': 0.7},
    'STANDARD': {'strongBeat': 0.85, 'weakBeat': 0.80, 'syncopation': 0.70},
    'DRUM_GROOVE': {
        'kick': 1.0, 'snare': 1.0, 'closed_hat': 1.0,
        'open_hat': 0.7, 'ride': 0.95, 'crash': 0.4, 'toms': 0.8,
    },
}


# ─── MAIN HUMANIZATION FUNCTION ──────────────────────────────────────────

def humanize_note(instrument: str, position_ppq: int, duration_ppq: int,
                  factory_velocity: int, chord_root: int, bar_number: int,
                  section: str = 'verse', meter: str = '4/4',
                  beat_position: int = 0, phrase_position: str = 'middle',
                  element: str = None) -> dict:
    """
    Deterministička humanizacija jedne note.
    
    Args:
        instrument: ime instrumenta (iz merged profila)
        position_ppq: PPQ pozicija note
        duration_ppq: trajanje note u PPQ
        factory_velocity: Factory autoritet za velocity
        chord_root: MIDI pitch osnovnog tona akorda
        bar_number: broj takta
        section: 'verse', 'chorus', 'bridge', 'intro', 'outro'
        meter: '4/4', '7/8', '9/8', itd.
        beat_position: beat pozicija unutar takta
        phrase_position: 'start', 'middle', 'end', 'breath'
        element: za drums — koji element (kick, snare, itd.)
    
    Returns:
        dict sa:
          - velocity: int (CLAMP(1, 127)) — Factory * scale
          - timing_offset: int PPQ — CLAMP(-8, +8)
          - gate_scale: float — CLAMP(0.3, 2.0)
          - velocity_scale: float — korišteni scale faktor
          - humanization_type: str
          - authority: dict — ko je šta odlučio
    """
    # 1. Load instrument profile (from merged)
    human_type = _get_humanization_type(instrument)
    groove = _get_groove_profile(instrument)
    
    # 2. Compute deterministic seed
    seed = deterministic_seed(instrument, position_ppq, chord_root, bar_number, section)
    seed_float = seed_to_float(seed, 0.85, 1.15)  # ±15% variation
    
    # 3. Get timing offset
    timing_profile = TIMING_PROFILES.get(groove, TIMING_PROFILES['standard_micro'])
    timing_offset = _compute_timing_offset(timing_profile, beat_position, phrase_position, element)
    
    # Add deterministic micro-variation (±1 PPQ)
    micro_variation = int((seed % 3) - 1)  # -1, 0, or 1
    timing_offset += micro_variation
    timing_offset = int(clamp(timing_offset, HARD_LIMITS['timingOffsetPPQ']['min'], HARD_LIMITS['timingOffsetPPQ']['max']))
    
    # 4. Get velocity scale
    vel_profile = VELOCITY_PROFILES.get(
        HUMANIZATION_TYPES.get(human_type, {}).get('velocityProfile', 'standard_arc'),
        VELOCITY_PROFILES['standard_arc']
    )
    velocity_scale = _compute_velocity_scale(vel_profile, beat_position, phrase_position, element)
    
    # Apply deterministic seed variation (±5%)
    velocity_scale *= (0.95 + (seed % 100) / 1000.0)  # 0.95 - 1.05
    velocity_scale = clamp(velocity_scale, HARD_LIMITS['velocityScale']['min'], HARD_LIMITS['velocityScale']['max'])
    
    # 5. Apply Factory velocity * scale (BLOCK: nikad ne zamjenjujemo Factory)
    humanized_velocity = int(clamp(factory_velocity * velocity_scale, 1, 127))
    
    # 6. Get gate scale
    gate_profile = GATE_PROFILES.get(human_type, GATE_PROFILES['STANDARD'])
    gate_scale = _compute_gate_scale(gate_profile, phrase_position, element, duration_ppq)
    gate_scale = clamp(gate_scale, HARD_LIMITS['gateScale']['min'], HARD_LIMITS['gateScale']['max'])
    
    # 7. Balkan meter accent adjustment
    if meter in ('7/8', '9/8', '6/4'):
        from balkan_folk_specialist import compute_balkan_accent_offsets
        balkan = compute_balkan_accent_offsets(meter, position_ppq, element or instrument)
        velocity_scale *= balkan['velocity_scale']
        velocity_scale = clamp(velocity_scale, HARD_LIMITS['velocityScale']['min'], HARD_LIMITS['velocityScale']['max'])
        humanized_velocity = int(clamp(factory_velocity * velocity_scale, 1, 127))
        timing_offset += balkan['timing_offset']
        timing_offset = int(clamp(timing_offset, HARD_LIMITS['timingOffsetPPQ']['min'], HARD_LIMITS['timingOffsetPPQ']['max']))
    
    return {
        'velocity': humanized_velocity,
        'timing_offset': timing_offset,
        'gate_scale': round(gate_scale, 3),
        'velocity_scale': round(velocity_scale, 4),
        'humanization_type': human_type,
        'authority': {
            'velocity': 'FACTORY_SCALED',
            'timing': 'GOLD_PROFILE',
            'gate': 'HUMANIZATION_PROFILE',
            'chord': 'MANDATORY_TRACKED',
        },
        'seed': seed,
        'hardLimitsApplied': True,
    }


def _get_humanization_type(instrument: str) -> str:
    """Dohvati humanization tip za instrument iz merged profila."""
    # Default map based on instrument name
    default_map = {
        'sax': 'PHRASE_DRIVEN',
        'clarinet': 'BREATH_PHRASE',
        'klarinet': 'BREATH_PHRASE',
        'frula': 'BREATH_PHRASE',
        'violin': 'BOW_PHRASE',
        'violina': 'BOW_PHRASE',
        'gusle': 'BOW_FREE',
        'harmonika': 'BELLOW_PHRASE',
        'accordion': 'BELLOW_PHRASE',
        'tambura': 'PLECTRUM_PHRASE',
        'guitar': 'PLECTRUM_PHRASE',
        'piano': 'STANDARD',
        'bass': 'STANDARD',
        'chords': 'STANDARD',
        'drums': 'DRUM_GROOVE',
        'percussion': 'DRUM_GROOVE',
    }
    
    # Try loading from merged profile
    try:
        merged_path = DATA_DIR / 'instrument-playing-profiles-9.30-merged.json'
        if merged_path.exists():
            with open(merged_path, 'r') as f:
                merged = json.load(f)
            profiles = merged.get('profiles', {})
            inst_prof = profiles.get(instrument, profiles.get(instrument.lower(), {}))
            if 'humanization' in inst_prof:
                return inst_prof['humanization']
    except Exception:
        pass
    
    return default_map.get(instrument.lower(), 'STANDARD')


def _get_groove_profile(instrument: str) -> str:
    """Dohvati groove profil za instrument iz merged profila."""
    try:
        merged_path = DATA_DIR / 'instrument-playing-profiles-9.30-merged.json'
        if merged_path.exists():
            with open(merged_path, 'r') as f:
                merged = json.load(f)
            profiles = merged.get('profiles', {})
            inst_prof = profiles.get(instrument, profiles.get(instrument.lower(), {}))
            if 'grooveProfile' in inst_prof:
                return inst_prof['grooveProfile']
    except Exception:
        pass
    
    # Default based on humanization type
    human_type = _get_humanization_type(instrument)
    return HUMANIZATION_TYPES.get(human_type, {}).get('timingProfile', 'standard_micro')


def _compute_timing_offset(profile: dict, beat_position: int, phrase_position: str,
                            element: str = None) -> int:
    """Izračunaj timing offset iz profila."""
    if element and element in profile:
        # Drum element-specific
        elem_prof = profile[element]
        if isinstance(elem_prof, dict):
            return elem_prof.get('strongBeat', 0)
        return elem_prof
    
    offset = 0
    
    if phrase_position == 'start':
        offset = profile.get('phraseStart', profile.get('inBreath', profile.get('bowDownStart', profile.get('strongBeat', 0))))
    elif phrase_position == 'end' or phrase_position == 'breath':
        offset = profile.get('phraseEnd', profile.get('breathGap', profile.get('phraseBreath', profile.get('weakBeat', 0))))
    elif phrase_position == 'middle':
        offset = profile.get('phraseMiddle', profile.get('sustainedNote', profile.get('bowChangeMid', 0)))
    
    return int(offset)


def _compute_velocity_scale(profile: dict, beat_position: int, phrase_position: str,
                            element: str = None) -> float:
    """Izračunaj velocity scale iz profila."""
    if element and element in profile:
        elem_prof = profile[element]
        if isinstance(elem_prof, dict):
            return elem_prof.get('strongBeat', 1.0)
        return float(elem_prof)
    
    scale = 1.0
    
    if phrase_position == 'start':
        scale = profile.get('phraseStart', profile.get('inBreath', profile.get('bowDown', profile.get('strongBeat', 1.0))))
    elif phrase_position == 'end' or phrase_position == 'breath':
        scale = profile.get('phraseEnd', profile.get('endOfBreath', profile.get('phraseCalm', profile.get('weakBeat', 1.0))))
    elif phrase_position == 'middle':
        scale = profile.get('phraseBuild', profile.get('sustained', profile.get('sustainedNote', profile.get('bowUp', 1.0))))
    
    return float(scale)


def _compute_gate_scale(profile, phrase_position: str, element: str = None,
                        duration_ppq: int = 0) -> float:
    """Izračunaj gate scale iz profila."""
    if isinstance(profile, dict):
        if element and element in profile:
            return float(profile[element])
        
        if phrase_position == 'start':
            return float(profile.get('sustainedNote', profile.get('downPick', profile.get('strongBeat', 0.85))))
        elif phrase_position == 'end' or phrase_position == 'breath':
            return float(profile.get('phraseEnd', profile.get('breathNote', profile.get('upPick', profile.get('weakBeat', 0.80)))))
        elif phrase_position == 'middle':
            return float(profile.get('longNote', profile.get('legato', profile.get('strum', 0.85))))
    
    return 0.85


# ─── BATCH HUMANIZATION ───────────────────────────────────────────────────

def humanize_pattern(instrument: str, pattern_notes: list, chord_root: int,
                     bar_number: int, section: str = 'verse', meter: str = '4/4',
                     ppq_per_bar: int = 96) -> list:
    """
    Humanizuj cijeli pattern (listu nota).
    
    Args:
        pattern_notes: lista [start, duration, pitch, velocity, ...]
        chord_root: osnovni ton akorda
        bar_number: broj takta
        section: sekcija
        meter: meter
        ppq_per_bar: PPQ po taktu
    
    Returns:
        Lista humanizovanih nota [start, duration, pitch, velocity]
    """
    humanized = []
    
    # Determine phrase positions
    if not pattern_notes:
        return humanized
    
    # Sort by position
    sorted_notes = sorted(pattern_notes, key=lambda n: n[0] if len(n) > 0 else 0)
    
    # Identify phrase boundaries
    max_pos = max(n[0] for n in sorted_notes if len(n) > 0)
    phrase_count = max(1, len(sorted_notes) // 8)  # ~8 notes per phrase
    phrase_size = max(1, len(sorted_notes) // phrase_count)
    
    for i, note in enumerate(sorted_notes):
        if len(note) < 4:
            continue
        
        start = note[0]
        duration = note[1]
        pitch = note[2]
        factory_vel = note[3]
        
        # Determine phrase position
        note_in_phrase = i % phrase_size
        if note_in_phrase == 0:
            phrase_pos = 'start'
        elif note_in_phrase >= phrase_size - 1:
            phrase_pos = 'end'
        else:
            phrase_pos = 'middle'
        
        # Beat position
        beat_pos = start // 24
        
        result = humanize_note(
            instrument=instrument,
            position_ppq=start,
            duration_ppq=duration,
            factory_velocity=factory_vel,
            chord_root=chord_root,
            bar_number=bar_number,
            section=section,
            meter=meter,
            beat_position=beat_pos,
            phrase_position=phrase_pos,
        )
        
        # Apply humanization
        new_start = start + result['timing_offset']
        new_vel = result['velocity']
        new_duration = int(duration * result['gate_scale'])
        
        humanized.append([new_start, new_duration, pitch, new_vel])
    
    return humanized


# ─── BUILD COMPLETE HUMANIZATION DATABASE ─────────────────────────────────

def build_humanization_database():
    """Generiši kompletu bazu humanizacionih profila."""
    print('DNA MIDI Studio 9.30 — Deterministic Humanization Engine')
    print('=' * 56)
    
    # Load merged profiles to get instrument list
    merged_path = DATA_DIR / 'instrument-playing-profiles-9.30-merged.json'
    with open(merged_path, 'r') as f:
        merged = json.load(f)
    
    profiles = merged.get('profiles', {})
    print(f'\n  Učitano {len(profiles)} instrumenata iz merged profila')
    
    # Build humanization profile for each instrument
    human_profiles = {}
    for inst_name, inst_data in profiles.items():
        human_type = inst_data.get('humanization', _get_humanization_type(inst_name))
        groove = inst_data.get('grooveProfile', _get_groove_profile(inst_name))
        
        human_profiles[inst_name] = {
            'humanizationType': human_type,
            'grooveProfile': groove,
            'timingProfile': TIMING_PROFILES.get(groove, TIMING_PROFILES['standard_micro']),
            'velocityProfile': VELOCITY_PROFILES.get(
                HUMANIZATION_TYPES.get(human_type, {}).get('velocityProfile', 'standard_arc'),
                VELOCITY_PROFILES['standard_arc']
            ),
            'gateProfile': GATE_PROFILES.get(human_type, GATE_PROFILES['STANDARD']),
            'hardLimits': HARD_LIMITS,
            'authority': {
                'velocity': 'FACTORY_SCALED',
                'timing': 'GOLD_PROFILE',
                'gate': 'HUMANIZATION_PROFILE',
                'chord': 'MANDATORY',
            },
        }
    
    print(f'  Generisano {len(human_profiles)} humanizacionih profila')
    
    # Also add folk instruments from Balkan specialist
    try:
        from balkan_folk_specialist import FOLK_INSTRUMENTS
        for inst_name, inst_data in FOLK_INSTRUMENTS.items():
            if inst_name not in human_profiles:
                human_type = inst_data.get('humanization', 'STANDARD')
                human_profiles[inst_name] = {
                    'humanizationType': human_type,
                    'grooveProfile': inst_data.get('grooveProfile', 'standard_micro'),
                    'timingProfile': TIMING_PROFILES.get(
                        inst_data.get('grooveProfile', 'standard_micro'),
                        TIMING_PROFILES['standard_micro']
                    ),
                    'velocityProfile': VELOCITY_PROFILES.get(
                        HUMANIZATION_TYPES.get(human_type, {}).get('velocityProfile', 'standard_arc'),
                        VELOCITY_PROFILES['standard_arc']
                    ),
                    'gateProfile': GATE_PROFILES.get(human_type, GATE_PROFILES['STANDARD']),
                    'hardLimits': HARD_LIMITS,
                    'authority': {
                        'velocity': 'FACTORY_SCALED',
                        'timing': 'GOLD_PROFILE',
                        'gate': 'HUMANIZATION_PROFILE',
                        'chord': 'MANDATORY',
                    },
                    'folkSpecific': True,
                }
        print(f'  Dodano {len(FOLK_INSTRUMENTS)} folk instrumenata')
    except ImportError:
        print('  ⚠️  Balkan folk modul nije dostupan')
    
    # Build complete output
    output = {
        'schema': 'dna-deterministic-humanization',
        'version': '9.30.0',
        'hardLimits': HARD_LIMITS,
        'humanizationTypes': HUMANIZATION_TYPES,
        'timingProfiles': TIMING_PROFILES,
        'velocityProfiles': VELOCITY_PROFILES,
        'gateProfiles': GATE_PROFILES,
        'instrumentProfiles': human_profiles,
        'authority': {
            'velocity': 'FACTORY_SCALED',
            'timing': 'GOLD_PROFILE',
            'gate': 'HUMANIZATION_PROFILE',
            'chord': 'MANDATORY',
            'determinism': 'SHA256_POSITION_SEED',
        },
    }
    
    # Save JSON
    json_path = DATA_DIR / 'deterministic-humanization-9.30.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f'\n✅ Humanization JSON: {json_path}')
    
    # Save SQLite
    db_path = DATA_DIR / 'deterministic-humanization-9.30.db'
    if db_path.exists():
        db_path.unlink()
    
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    
    # Instrument humanization table
    c.execute('''CREATE TABLE IF NOT EXISTS instrument_humanization (
        instrument TEXT PRIMARY KEY,
        humanization_type TEXT,
        groove_profile TEXT,
        timing_template TEXT,
        velocity_template TEXT,
        gate_template TEXT,
        velocity_authority TEXT,
        timing_authority TEXT,
        chord_required TEXT,
        folk_specific INTEGER DEFAULT 0,
        total_profiles INTEGER DEFAULT 1
    )''')
    
    for inst, prof in human_profiles.items():
        c.execute('INSERT OR REPLACE INTO instrument_humanization VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                  (inst, prof.get('humanizationType',''),
                   prof.get('grooveProfile',''),
                   prof.get('grooveProfile',''),  # timing template = groove profile name
                   HUMANIZATION_TYPES.get(prof.get('humanizationType',''), {}).get('velocityProfile',''),
                   prof.get('humanizationType',''),  # gate template = humanization type name
                   prof.get('authority',{}).get('velocity',''),
                   prof.get('authority',{}).get('timing',''),
                   prof.get('authority',{}).get('chord',''),
                   1 if prof.get('folkSpecific', False) else 0,
                   1))
    
    # Hard limits table
    c.execute('''CREATE TABLE IF NOT EXISTS hard_limits (
        limit_name TEXT PRIMARY KEY,
        min_val REAL,
        max_val REAL,
        mode TEXT,
        rule TEXT
    )''')
    
    for name, conf in HARD_LIMITS.items():
        c.execute('INSERT OR REPLACE INTO hard_limits VALUES (?,?,?,?,?)',
                  (name, conf.get('min', None), conf.get('max', None),
                   conf.get('mode', ''), conf.get('rule', '')))
    
    conn.commit()
    conn.close()
    print(f'✅ Humanization SQLite: {db_path}')
    
    # Generate report
    report_path = DATA_DIR / 'deterministic-humanization-report-9.30.md'
    report = _generate_humanization_report(output, human_profiles)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f'✅ Humanization report: {report_path} ({len(report.splitlines())} linija)')
    
    return output


def _generate_humanization_report(output: dict, human_profiles: dict) -> str:
    lines = []
    lines.append('# DNA MIDI Studio 9.30 — Deterministic Humanization Report')
    lines.append('')
    lines.append(f'**Schema:** {output["schema"]}')
    lines.append(f'**Version:** {output["version"]}')
    lines.append(f'**Ukupno instrumenata:** {len(human_profiles)}')
    lines.append('')
    
    lines.append('## Autoriteti')
    lines.append('')
    for k, v in output['authority'].items():
        lines.append(f'- **{k}**: {v}')
    lines.append('')
    
    lines.append('## Hard Limits (BLOCK/CLAMP)')
    lines.append('')
    for name, conf in output['hardLimits'].items():
        mode = conf.get('mode', '—')
        if mode == 'BLOCK':
            lines.append(f'- **{name}**: 🚫 BLOCK — {conf.get("rule", "")}')
        else:
            lines.append(f'- **{name}**: 🔒 CLAMP({conf.get("min","—")}, {conf.get("max","—")})')
    lines.append('')
    
    lines.append('## Humanizacioni Tipovi')
    lines.append('')
    lines.append('| Tip | Opis | Timing profil | Velocity profil |')
    lines.append('|-----|------|---------------|-----------------|')
    for ht, conf in output['humanizationTypes'].items():
        lines.append(f'| {ht} | {conf["description"]} | {conf["timingProfile"]} | {conf["velocityProfile"]} |')
    lines.append('')
    
    lines.append('## Instrument → Humanizacija Mapa')
    lines.append('')
    lines.append('| Instrument | Tip | Groove profil | Folk |')
    lines.append('|-----------|-----|--------------|------|')
    for inst, prof in sorted(human_profiles.items()):
        folk = '✅' if prof.get('folkSpecific', False) else ''
        lines.append(f'| {inst} | {prof["humanizationType"]} | {prof["grooveProfile"]} | {folk} |')
    lines.append('')
    
    lines.append('## Determinizam')
    lines.append('')
    lines.append('- **Seed:** SHA-256(instrument + position + chord_root + bar + section)')
    lines.append('- **Isti ulaz = isti izlaz** — nema random() nigdje')
    lines.append('- **Micro-variation:** ±1 PPQ iz seeda (deterministički)')
    lines.append('- **Velocity varijacija:** ±5% iz seeda (deterministički)')
    lines.append('- **Chord tracking:** obavezni za sve instrumente')
    lines.append('')
    
    lines.append('## Test: Determinizam Verifikacija')
    lines.append('')
    lines.append('```')
    lines.append('# Isti ulaz poziva 3 puta = isti izlaz')
    for inst in ['sax', 'violin', 'harmonika', 'drums']:
        r1 = humanize_note(inst, 48, 24, 98, 60, 1, 'verse')
        r2 = humanize_note(inst, 48, 24, 98, 60, 1, 'verse')
        r3 = humanize_note(inst, 48, 24, 98, 60, 1, 'verse')
        match = r1['velocity'] == r2['velocity'] == r3['velocity']
        lines.append(f'  {inst}: vel={r1["velocity"]}, offset={r1["timing_offset"]}, gate={r1["gate_scale"]} — determinističan={"✅" if match else "❌"}')
    lines.append('```')
    lines.append('')
    
    return '\n'.join(lines)


if __name__ == '__main__':
    build_humanization_database()
