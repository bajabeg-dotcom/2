#!/usr/bin/env python3
"""DNA MIDI Studio 9.30 — Instrument Playing Intelligence / Musical DNA Engine

Potpuni sistem za izgradnju profesionanih Instrument Playing Profila po Master Prompt specifikaciji.

Autoritet model:
  FACTORY  → velocity, dynamics, volume (KOLIKO JAKO)
  GOLD     → timing, articulation, expression, phrasing (KAKO SE SVIRA)
  PA800    → mapping, range, NTT, export (KAKO SE PREVODI)
  CHORD    → osnova svih odluka (ŠTA PRATI)

Svaki profil ima 13 sekcija po Master Promptu:
  IDENTITY, RANGE, VELOCITY, TIMING, NOTE_BEHAVIOR,
  HARMONY, RHYTHM, ARTICULATION, EXPRESSION,
  SECTION_BEHAVIOR, INTERACTION, PA800_BEHAVIOR

Verzija: 9.30.0
Datum: 2026-09-06
"""

import json, math, sqlite3, hashlib, os, sys
from pathlib import Path
from collections import defaultdict, Counter
from typing import Optional, Dict, List, Any, Tuple

# ── Konstante ──
DATA_DIR = Path(__file__).parent / 'data'
VERSION = '9.30.0'

# Master Prompt: 20 instrument familija
INSTRUMENT_FAMILIES = {
    'bass':             {'family': 'bass',              'subfamily': 'electric_bass',    'priority_order': ['harmony','groove','root','timing','note_length','passing','velocity','expression','ornament']},
    'drums':            {'family': 'drums',              'subfamily': 'drum_kit',         'priority_order': ['groove','pattern','accent','timing','element_rel','velocity','fill','density','articulation']},
    'piano':            {'family': 'keyboard',           'subfamily': 'piano',            'priority_order': ['chord_voicing','rhythm','register','velocity','timing','note_length','phrase']},
    'organ':            {'family': 'keyboard',           'subfamily': 'organ',            'priority_order': ['sustain','rhythm','expression','register','velocity','timing']},
    'rhythm_guitar':    {'family': 'guitar',            'subfamily': 'rhythm',           'priority_order': ['strum','voicing','timing','mute','accent','harmony','articulation','velocity']},
    'solo_guitar':      {'family': 'guitar',            'subfamily': 'solo',             'priority_order': ['phrase','articulation','microtiming','expression','ornaments','velocity','note_length']},
    'accordion':        {'family': 'free_reed',          'subfamily': 'accordion',        'priority_order': ['chord_pulse','melody','ornament','rhythm','expression','timing','velocity']},
    'strings':          {'family': 'bowed_strings',      'subfamily': 'ensemble',         'priority_order': ['sustain','harmony','voice_leading','expression','attack','release','density']},
    'brass':            {'family': 'brass',              'subfamily': 'section',          'priority_order': ['attack','accent','rhythm','note_length','phrase','articulation','velocity']},
    'sax':              {'family': 'wind',               'subfamily': 'saxophone',       'priority_order': ['phrase','articulation','expression','timing','ornaments','note_length','velocity']},
    'woodwind':         {'family': 'wind',               'subfamily': 'folk_woodwind',   'priority_order': ['phrase','ornament','expression','timing','grace','breath','microtiming','velocity']},
    'clarinet':         {'family': 'wind',               'subfamily': 'clarinet_folk',   'priority_order': ['phrase','ornament','expression','timing','trill','grace','breath','microtiming']},
    'violin':           {'family': 'bowed_strings',      'subfamily': 'violin_fiddle',  'priority_order': ['legato','bow','grace','slide','ornament','sustain','accent','phrase']},
    'synth_lead':       {'family': 'synth',              'subfamily': 'lead',            'priority_order': ['density','phrase','repetition','variation','glide','accent','sustain']},
    'pad':              {'family': 'synth',              'subfamily': 'pad',             'priority_order': ['sustain','harmony','voice_leading','expression','attack','release','density']},
    'mallet':           {'family': 'percussion',         'subfamily': 'mallet',          'priority_order': ['attack','repetition','alternation','arpeggio','sustain','accent','velocity']},
    'choir':            {'family': 'vocal',              'subfamily': 'choir',           'priority_order': ['sustain','harmony','voice_leading','expression','attack','release','density']},
    'percussion':       {'family': 'percussion',         'subfamily': 'hand_perc',       'priority_order': ['interlock','ghost','rhythm','accent','microtiming','density']},
    'fx':               {'family': 'fx',                 'subfamily': 'special',        'priority_order': ['trigger','section','duration','impact','repeatability']},
    'accompaniment':    {'family': 'keyboard',           'subfamily': 'generic_comp',   'priority_order': ['chord_voicing','rhythm','register','velocity','timing','note_length']},
}

# PA800 track type mapping
PA800_TRACK_MAP = {
    'bass':          {'trackType': 'BASS',  'ntt': None,               'guitarMode': None},
    'drums':         {'trackType': 'DRUM',  'ntt': None,               'guitarMode': None},
    'percussion':    {'trackType': 'PERC',  'ntt': None,               'guitarMode': None},
    'rhythm_guitar': {'trackType': 'ACC1',  'ntt': 'Chord',           'guitarMode': 'NORM/FINGER/PICK'},
    'piano':         {'trackType': 'ACC2',  'ntt': 'Chord/Fixed',     'guitarMode': None},
    'organ':         {'trackType': 'ACC3',  'ntt': 'Fixed',            'guitarMode': None},
    'strings':       {'trackType': 'ACC4',  'ntt': 'Fixed/Parallel',  'guitarMode': None},
    'brass':         {'trackType': 'ACC5',  'ntt': 'Parallel',        'guitarMode': None},
    'accordion':     {'trackType': 'ACC1',  'ntt': 'Chord/Fixed',     'guitarMode': None},
    'sax':           {'trackType': 'ACC3',  'ntt': 'Parallel',        'guitarMode': None},
    'woodwind':      {'trackType': 'ACC3',  'ntt': 'Parallel',        'guitarMode': None},
    'clarinet':      {'trackType': 'ACC2',  'ntt': 'Parallel',        'guitarMode': None},
    'violin':        {'trackType': 'ACC4',  'ntt': 'Parallel',        'guitarMode': None},
    'synth_lead':    {'trackType': 'ACC3',  'ntt': 'Parallel',        'guitarMode': None},
    'pad':           {'trackType': 'ACC4',  'ntt': 'Fixed',            'guitarMode': None},
    'mallet':        {'trackType': 'ACC2',  'ntt': 'Chord/Parallel',  'guitarMode': None},
    'choir':         {'trackType': 'ACC5',  'ntt': 'Fixed',            'guitarMode': None},
    'fx':            {'trackType': 'ACC5',  'ntt': None,               'guitarMode': None},
    'accompaniment': {'trackType': 'ACC2',  'ntt': 'Chord/Fixed',     'guitarMode': None},
}

# Arrangement roles (Master Prompt #43)
ARRANGEMENT_ROLES = [
    'BASS', 'DRUM', 'PERCUSSION', 'RHYTHMIC_CHORD', 'HARMONIC_PAD',
    'COUNTER_MELODY', 'MELODY', 'SOLO', 'FILL', 'TRANSITION', 'TEXTURE', 'FX'
]

# Style Elements (Master Prompt #30)
STYLE_ELEMENTS = ['Variation1', 'Variation2', 'Variation3', 'Variation4',
                  'Intro1', 'Intro2', 'Intro3', 'Fill1', 'Fill2', 'Fill3',
                  'Break', 'Ending1', 'Ending2', 'Ending3']

# NTT types (Master Prompt #31)
NTT_TYPES = ['Parallel', 'Fixed', 'Root', 'Fifth', 'NoTranspose', 'Chord']

# ── Statistički pomoćni funkcije ──

def pct(data, p):
    """Percentile iz liste."""
    if not data:
        return 0
    s = sorted(data)
    idx = int(len(s) * p / 100)
    return s[min(idx, len(s) - 1)]


def stats_dict(data, label=''):
    """Izračunaj kompletan statistički model za parametar (Master Prompt #36)."""
    if not data:
        return {'n': 0, 'confidence': 0.0, 'source': 'NONE'}
    n = len(data)
    m = sum(data) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in data) / n) if n > 1 else 0
    iqr = pct(data, 75) - pct(data, 25)
    try:
        mode = Counter(data).most_common(1)[0][0]
    except:
        mode = pct(data, 50)
    return {
        'n': n,
        'mean': round(m, 3),
        'median': pct(data, 50),
        'sd': round(sd, 3),
        'mode': mode,
        'p5': pct(data, 5),
        'p25': pct(data, 25),
        'p50': pct(data, 50),
        'p75': pct(data, 75),
        'p95': pct(data, 95),
        'min': min(data),
        'max': max(data),
        'iqr': round(iqr, 3),
        'outliers_low': sum(1 for x in data if x < pct(data, 25) - 1.5 * iqr) if iqr > 0 else 0,
        'outliers_high': sum(1 for x in data if x > pct(data, 75) + 1.5 * iqr) if iqr > 0 else 0,
    }


def confidence_from_samples(n, min_confidence=0.1, max_confidence=0.99, k=50):
    """Izračunaj confidence iz broja uzoraka (Master Prompt #34, #35).
    
    Više uzoraka = veći confidence, ali sa saturacijom.
    LOW_CONFIDENCE ako je n < k.
    """
    if n == 0:
        return 0.0
    c = min_confidence + (max_confidence - min_confidence) * (1 - math.exp(-n / k))
    return round(c, 4)


def classify_outlier(value, data_stats, role=''):
    """Klasifikuj outlier kao BAD_DATA ili MUSICAL_EVENT (Master Prompt #37)."""
    iqr = data_stats.get('iqr', 0)
    if iqr <= 0:
        return 'NO_OUTLIER'
    low_fence = data_stats['p25'] - 1.5 * iqr
    high_fence = data_stats['p75'] + 1.5 * iqr
    if value < low_fence:
        # Niski outlier — može biti ghost note, floor, ili greška
        if role in ['bass', 'drums']:
            return 'POSSIBLE_GHOST_OR_FLOOR'
        return 'POSSIBLE_BAD_DATA'
    if value > high_fence:
        # Visoki outlier — može biti accent, crash, phrase peak
        if role in ['brass', 'drums', 'sax']:
            return 'POSSIBLE_ACCENT_OR_PEAK'
        return 'POSSIBLE_BAD_DATA'
    return 'NO_OUTLIER'


# ── Data Loading ──

def load_factory_profiles() -> list:
    """Učitaj Factory velocity profile iz factory-velocity-profiles.json."""
    path = DATA_DIR / 'factory-velocity-profiles.json'
    if not path.exists():
        return []
    d = json.loads(path.read_text(encoding='utf-8'))
    return d.get('profiles', [])


def load_factory_catalog() -> dict:
    """Učitaj Factory velocity catalog 9.30."""
    path = DATA_DIR / 'factory-velocity-catalog-9.30.json'
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def load_gold_patterns() -> list:
    """Učitaj Gold performance patterns."""
    path = DATA_DIR / 'gold-performance-patterns.json'
    if not path.exists():
        return []
    d = json.loads(path.read_text(encoding='utf-8'))
    return d.get('patterns', [])


def load_gold_relationships() -> list:
    """Učitaj Gold relationships (interakcije među instrumentima)."""
    path = DATA_DIR / 'gold-performance-patterns.json'
    if not path.exists():
        return []
    d = json.loads(path.read_text(encoding='utf-8'))
    return d.get('relationships', [])


def load_drum_evidence() -> dict:
    """Učitaj Drum element evidence 4.46."""
    path = DATA_DIR / 'drum-element-evidence-4.46.json'
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def load_instrument_behavior() -> dict:
    """Učitaj postojeće instrument behavior profile (4.39)."""
    path = DATA_DIR / 'instrument-behavior-status-4.39.json'
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def load_general_rules() -> dict:
    """Učitaj General Rules 9.30."""
    path = DATA_DIR / 'general-rules-9.30.json'
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def load_factory_strumming() -> dict:
    """Učitaj Factory strumming podatke."""
    path = DATA_DIR / 'factory-strumming.json'
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


# ── Engine: Extract per-role statistics from Gold patterns ──

def extract_gold_role_stats(gold_patterns: list) -> dict:
    """Iz Gold paterna izvuci kompletnu statistiku po roli.
    
    Returns dict[role] -> {density, timing, duration, offset, register, section, meter}
    """
    by_role = defaultdict(list)
    for p in gold_patterns:
        by_role[p['role']].append(p)

    result = {}
    for role, rpatterns in by_role.items():
        n = len(rpatterns)
        densities = [p['density'] for p in rpatterns]
        lengths = [p['lengthBars'] for p in rpatterns]

        # Extract event-level statistics
        all_offsets, all_durations, all_pitches = [], [], []
        event_counts = []
        velocities = []  # Gold nema velocity, ali checkamo

        for p in rpatterns[:min(500, len(rpatterns))]:
            events = p.get('events', [])
            event_counts.append(len(events))
            for e in events:
                if len(e) >= 3:
                    all_pitches.append(e[0])
                    all_durations.append(e[1])
                    all_offsets.append(e[2])

        # Section distribution
        sec_dist = Counter(p.get('sourceSection', '?') for p in rpatterns)
        meter_dist = Counter(p.get('meter', '?') for p in rpatterns)

        # Tempo
        tempos = []
        for p in rpatterns:
            tr = p.get('tempoRange', [])
            if tr:
                tempos.append((tr[0] + tr[1]) / 2)

        # Register
        reg_lows = [p.get('register', {}).get('low', 0) for p in rpatterns]
        reg_highs = [p.get('register', {}).get('high', 0) for p in rpatterns]

        # Harmonic anchor qualities
        qualities = Counter()
        for p in rpatterns:
            ha = p.get('harmonicAnchor', {})
            if ha:
                q = ha.get('quality', '?')
                qualities[q] += 1

        result[role] = {
            'patternCount': n,
            'density': stats_dict(densities, 'density'),
            'lengthBars': stats_dict(lengths, 'length'),
            'eventsPerPattern': stats_dict(event_counts, 'events'),
            'pitchFromRoot': stats_dict(all_pitches, 'pitch'),
            'duration': stats_dict(all_durations, 'duration'),
            'offset': stats_dict(all_offsets, 'offset'),
            'registerLow': stats_dict(reg_lows, 'regLow'),
            'registerHigh': stats_dict(reg_highs, 'regHigh'),
            'tempo': stats_dict(tempos, 'tempo'),
            'sectionDistribution': dict(sec_dist),
            'meterDistribution': dict(meter_dist),
            'chordQualityDistribution': dict(qualities),
            'confidence': confidence_from_samples(n),
        }

    return result


# ── Engine: Extract per-role velocity from Factory ──

def extract_factory_role_stats(factory_profiles: list, factory_catalog: dict) -> dict:
    """Iz Factory profila izvuci velocity statistiku po roli."""
    by_role = defaultdict(list)
    for p in factory_profiles:
        role = p.get('role', 'unknown')
        by_role[role].append(p)

    result = {}
    for role, profiles in by_role.items():
        n = len(profiles)
        vel_mins = [p.get('velocity', {}).get('min', p.get('velocity_min', 1)) for p in profiles]
        vel_maxs = [p.get('velocity', {}).get('max', p.get('velocity_max', 127)) for p in profiles]
        vel_optimals = [p.get('velocity', {}).get('optimal', p.get('velocity_optimum', 80)) for p in profiles]
        vel_floors = [p.get('velocity', {}).get('floor', 1) for p in profiles]
        vel_softs = [p.get('velocity', {}).get('soft', 40) for p in profiles]
        vel_strongs = [p.get('velocity', {}).get('strong', 100) for p in profiles]
        vel_ceilings = [p.get('velocity', {}).get('ceiling', 127) for p in profiles]

        # Register from factory
        reg_lows = [p.get('register_low', p.get('register', {}).get('low', 0)) for p in profiles]
        reg_highs = [p.get('register_high', p.get('register', {}).get('high', 127)) for p in profiles]

        result[role] = {
            'profileCount': n,
            'velocityMin': stats_dict(vel_mins),
            'velocityMax': stats_dict(vel_maxs),
            'velocityOptimal': stats_dict(vel_optimals),
            'velocityFloor': stats_dict(vel_floors),
            'velocitySoft': stats_dict(vel_softs),
            'velocityStrong': stats_dict(vel_strongs),
            'velocityCeiling': stats_dict(vel_ceilings),
            'registerLow': stats_dict(reg_lows),
            'registerHigh': stats_dict(reg_highs),
            'confidence': confidence_from_samples(n, k=100),
        }

    # Dodaj per-role podatke iz cataloga ako postoje
    per_role = factory_catalog.get('perRole', {})
    for role_name, role_data in per_role.items():
        if role_name not in result:
            result[role_name] = {'profileCount': 0, 'confidence': confidence_from_samples(0)}
        result[role_name]['catalogData'] = role_data

    return result


# ── Engine: Extract drum element statistics ──

def extract_drum_element_stats(drum_evidence: dict) -> dict:
    """Iz drum evidence izvuci statistiku po elementu."""
    elements = drum_evidence.get('gold', {}).get('elements', {})
    if not elements:
        # Fallback na wiring podatke
        wiring = drum_evidence.get('wiring', {})
        elements = wiring

    result = {}
    for elem_name, elem_data in elements.items():
        if isinstance(elem_data, dict):
            result[elem_name] = {
                'data': elem_data,
                'confidence': confidence_from_samples(
                    elem_data.get('patternCount', elem_data.get('samples', 10)), k=30
                ),
            }

    return result


# ── Engine: Build Complete Instrument Profile ──

def build_instrument_profile(role: str,
                              gold_stats: dict,
                              factory_stats: dict,
                              behavior_data: dict,
                              drum_elements: dict,
                              general_rules: dict,
                              strum_data: dict) -> dict:
    """Napravi kompletan Instrument Playing Profile po Master Prompt strukturi.
    
    13 sekcija: IDENTITY, RANGE, VELOCITY, TIMING, NOTE_BEHAVIOR,
    HARMONY, RHYTHM, ARTICULATION, EXPRESSION, SECTION_BEHAVIOR,
    INTERACTION, PA800_BEHAVIOR, CONFIDENCE_REPORT
    """

    # Map role names
    role_key = role
    family_info = INSTRUMENT_FAMILIES.get(role, {
        'family': 'unknown', 'subfamily': 'unknown',
        'priority_order': ['chord_voicing', 'rhythm', 'velocity', 'timing']
    })

    g = gold_stats.get(role, {})
    f = factory_stats.get(role, {})
    b = behavior_data.get('profiles', {}).get(role, {})
    pa8 = PA800_TRACK_MAP.get(role, {'trackType': 'ACC5', 'ntt': 'Chord', 'guitarMode': None})

    # ── 1. IDENTITY ──
    identity = {
        'family': family_info['family'],
        'subfamily': family_info['subfamily'],
        'instrumentRole': _map_arrangement_role(role),
        'musicalRole': _describe_musical_role(role),
        'pa800SoundClass': pa8['trackType'],
        'register': _register_label(role),
        'priority': family_info['priority_order'],
        'playerModel': b.get('musician_model', f'{role}_player'),
    }

    # ── 2. RANGE ──
    range_data = _build_range(role, f, g, general_rules)

    # ── 3. VELOCITY ──
    velocity_data = _build_velocity(role, f, g)

    # ── 4. TIMING ──
    timing_data = _build_timing(role, g)

    # ── 5. NOTE_BEHAVIOR ──
    note_data = _build_note_behavior(role, g)

    # ── 6. HARMONY ──
    harmony_data = _build_harmony(role, g, b)

    # ── 7. RHYTHM ──
    rhythm_data = _build_rhythm(role, g)

    # ── 8. ARTICULATION ──
    articulation_data = _build_articulation(role, g, b)

    # ── 9. EXPRESSION ──
    expression_data = _build_expression(role, g)

    # ── 10. SECTION_BEHAVIOR ──
    section_data = _build_section_behavior(role, g)

    # ── 11. INTERACTION ──
    interaction_data = _build_interaction(role, g, b)

    # ── 12. PA800_BEHAVIOR ──
    pa800_data = _build_pa800(role, pa8, general_rules, g)

    # ── 13. CONFIDENCE_REPORT ──
    confidence = _build_confidence(role, g, f, b)

    profile = {
        'schema': 'dna-instrument-playing-profile',
        'version': VERSION,
        'role': role,
        'identity': identity,
        'range': range_data,
        'velocity': velocity_data,
        'timing': timing_data,
        'noteBehavior': note_data,
        'harmony': harmony_data,
        'rhythm': rhythm_data,
        'articulation': articulation_data,
        'expression': expression_data,
        'sectionBehavior': section_data,
        'interaction': interaction_data,
        'pa800Behavior': pa800_data,
        'confidence': confidence,
    }

    # Dodaj human-readable opis
    profile['howItPlays'] = _generate_how_it_plays(profile)

    return profile


# ── Builder pomoćne funkcije ──

def _map_arrangement_role(role):
    """Mapaj u Master Prompt #43 arrangement role."""
    mapping = {
        'bass': 'BASS', 'drums': 'DRUM', 'percussion': 'PERCUSSION',
        'rhythm_guitar': 'RHYTHMIC_CHORD', 'piano': 'RHYTHMIC_CHORD',
        'organ': 'RHYTHMIC_CHORD', 'accordion': 'RHYTHMIC_CHORD',
        'strings': 'HARMONIC_PAD', 'pad': 'HARMONIC_PAD', 'choir': 'HARMONIC_PAD',
        'brass': 'FILL', 'sax': 'COUNTER_MELODY', 'woodwind': 'COUNTER_MELODY',
        'clarinet': 'COUNTER_MELODY', 'violin': 'MELODY',
        'solo_guitar': 'SOLO', 'synth_lead': 'MELODY',
        'mallet': 'FILL', 'fx': 'FX', 'accompaniment': 'RHYTHMIC_CHORD',
        'power-riff': 'RHYTHMIC_CHORD', 'riff': 'FILL',
    }
    return mapping.get(role, 'TEXTURE')


def _describe_musical_role(role):
    """Human-readable opis muzičke uloge."""
    descriptions = {
        'bass': 'Low-frequency harmonic and rhythmic foundation',
        'drums': 'Primary rhythmic driver and groove keeper',
        'percussion': 'Interlocking rhythmic color and accent',
        'rhythm_guitar': 'Harmonic rhythm with strumming physicality',
        'piano': 'Chordal comping, voicing, and harmonic support',
        'organ': 'Sustained harmonic and rhythmic comping',
        'accordion': 'Melodic and chord-pumping Balkan character',
        'strings': 'Sustained harmonic and emotional support',
        'brass': 'Stab accents and section transition marks',
        'sax': 'Phrase-based melodic counterpoint',
        'woodwind': 'Ornamental melodic phrase with breath',
        'clarinet': 'Folk/Balkan ornamental melodic voice',
        'violin': 'Legato melodic voice with slides and ornaments',
        'solo_guitar': 'Expressive solo phrase with bends and articulation',
        'synth_lead': 'Melodic synthesizer phrase',
        'pad': 'Sustained harmonic bed with slow movement',
        'mallet': 'Clear-attack arpeggiated or repeated color',
        'choir': 'Sustained vocal harmonic texture',
        'fx': 'Event/section-driven special effect',
        'accompaniment': 'Generic chordal/rhythmic support',
    }
    return descriptions.get(role, 'Undefined musical role')


def _register_label(role):
    """Oznaci registar."""
    labels = {
        'bass': 'low', 'drums': 'percussion', 'piano': 'mid',
        'organ': 'mid', 'rhythm_guitar': 'mid', 'solo_guitar': 'mid-high',
        'accordion': 'mid', 'strings': 'mid-high', 'brass': 'mid',
        'sax': 'mid', 'woodwind': 'mid-high', 'clarinet': 'mid-high',
        'violin': 'high', 'synth_lead': 'mid-high', 'pad': 'mid',
        'mallet': 'mid-high', 'choir': 'mid-high', 'percussion': 'percussion',
        'fx': 'full', 'accompaniment': 'mid',
    }
    return labels.get(role, 'mid')


def _build_range(role, factory_stats, gold_stats, general_rules):
    """Sekcija 2: RANGE — po Master Prompt strukturi."""
    f = factory_stats
    g = gold_stats

    # Absolute range from Factory
    f_low = f.get('registerLow', {}).get('p5', 0) if f else 0
    f_high = f.get('registerHigh', {}).get('p95', 127) if f else 127

    # Practical range from Gold (semitones from root)
    g_low = g.get('registerLow', {}).get('p5', 0) if g else 0
    g_high = g.get('registerHigh', {}).get('p95', 12) if g else 12

    # GM key range from General Rules
    gm_range = general_rules.get('programs', {})

    # Instrument-specific absolute ranges
    ABS_RANGES = {
        'bass':          {'min': 24, 'max': 67, 'pracMin': 28, 'pracMax': 55, 'prefLow': 28, 'prefMid': 36, 'prefHigh': 48},
        'drums':         {'min': 27, 'max': 87, 'pracMin': 36, 'pracMax': 79, 'prefLow': 36, 'prefMid': 42, 'prefHigh': 56},
        'piano':         {'min': 21, 'max': 108, 'pracMin': 36, 'pracMax': 96, 'prefLow': 36, 'prefMid': 60, 'prefHigh': 84},
        'organ':         {'min': 36, 'max': 96, 'pracMin': 48, 'pracMax': 84, 'prefLow': 48, 'prefMid': 60, 'prefHigh': 72},
        'rhythm_guitar': {'min': 28, 'max': 84, 'pracMin': 40, 'pracMax': 72, 'prefLow': 40, 'prefMid': 52, 'prefHigh': 64},
        'solo_guitar':   {'min': 40, 'max': 91, 'pracMin': 48, 'pracMax': 84, 'prefLow': 48, 'prefMid': 60, 'prefHigh': 72},
        'accordion':     {'min': 36, 'max': 96, 'pracMin': 48, 'pracMax': 84, 'prefLow': 48, 'prefMid': 60, 'prefHigh': 72},
        'strings':       {'min': 36, 'max': 96, 'pracMin': 48, 'pracMax': 84, 'prefLow': 48, 'prefMid': 60, 'prefHigh': 72},
        'brass':         {'min': 34, 'max': 77, 'pracMin': 41, 'pracMax': 70, 'prefLow': 41, 'prefMid': 53, 'prefHigh': 65},
        'sax':           {'min': 42, 'max': 78, 'pracMin': 49, 'pracMax': 72, 'prefLow': 49, 'prefMid': 58, 'prefHigh': 67},
        'woodwind':      {'min': 48, 'max': 91, 'pracMin': 55, 'pracMax': 84, 'prefLow': 55, 'prefMid': 67, 'prefHigh': 79},
        'clarinet':      {'min': 38, 'max': 79, 'pracMin': 50, 'pracMax': 72, 'prefLow': 50, 'prefMid': 58, 'prefHigh': 67},
        'violin':        {'min': 55, 'max': 98, 'pracMin': 55, 'pracMax': 84, 'prefLow': 55, 'prefMid': 67, 'prefHigh': 79},
        'synth_lead':    {'min': 36, 'max': 96, 'pracMin': 48, 'pracMax': 84, 'prefLow': 48, 'prefMid': 60, 'prefHigh': 72},
        'pad':           {'min': 24, 'max': 96, 'pracMin': 36, 'pracMax': 84, 'prefLow': 36, 'prefMid': 60, 'prefHigh': 72},
        'mallet':        {'min': 48, 'max': 96, 'pracMin': 55, 'pracMax': 84, 'prefLow': 55, 'prefMid': 67, 'prefHigh': 79},
        'choir':         {'min': 36, 'max': 84, 'pracMin': 48, 'pracMax': 72, 'prefLow': 48, 'prefMid': 60, 'prefHigh': 72},
        'percussion':    {'min': 36, 'max': 79, 'pracMin': 42, 'pracMax': 72, 'prefLow': 42, 'prefMid': 56, 'prefHigh': 67},
        'fx':            {'min': 0, 'max': 127, 'pracMin': 0, 'pracMax': 127, 'prefLow': 0, 'prefMid': 64, 'prefHigh': 96},
        'accompaniment': {'min': 36, 'max': 96, 'pracMin': 48, 'pracMax': 84, 'prefLow': 48, 'prefMid': 60, 'prefHigh': 72},
    }

    r = ABS_RANGES.get(role, {'min': 0, 'max': 127, 'pracMin': 0, 'pracMax': 127, 'prefLow': 0, 'prefMid': 60, 'prefHigh': 96})

    return {
        'absoluteMin': r['min'],
        'absoluteMax': r['max'],
        'practicalMin': r['pracMin'],
        'practicalMax': r['pracMax'],
        'preferredLow': r['prefLow'],
        'preferredMid': r['prefMid'],
        'preferredHigh': r['prefHigh'],
        'registerTransition': _register_transition(role),
        'source': 'FACTORY+GM_SPEC' if role in ABS_RANGES else 'ESTIMATED',
        'confidence': confidence_from_samples(f.get('profileCount', 10) if f else 10, k=100),
    }


def _register_transition(role):
    """Opis prijelaza između registara."""
    transitions = {
        'bass': 'octave_jump_for_energy',
        'piano': 'voice_spread_dynamic',
        'guitar': 'string_position_shift',
        'violin': 'position_shift',
        'brass': 'register_hit_for_energy',
        'sax': 'altissimo_entry',
        'clarinet': 'chalumeau_to_clarino',
    }
    return transitions.get(role, 'none_typical')


def _build_velocity(role, factory_stats, gold_stats):
    """Sekcija 3: VELOCITY — FACTORY autoritet, po GM program."""
    f = factory_stats

    # Factory velocity curve (Master Prompt #24)
    if f:
        vel = {
            'min': f.get('velocityMin', {}).get('median', 1),
            'max': f.get('velocityMax', {}).get('median', 127),
            'pp': f.get('velocityFloor', {}).get('p50', 8),
            'p': f.get('velocitySoft', {}).get('p50', 40),
            'mp': round((f.get('velocitySoft', {}).get('p50', 40) + f.get('velocityOptimal', {}).get('p50', 70)) / 2),
            'mf': f.get('velocityOptimal', {}).get('p50', 70),
            'f': f.get('velocityStrong', {}).get('p50', 100),
            'ff': f.get('velocityCeiling', {}).get('p50', 120),
            'fff': f.get('velocityCeiling', {}).get('p95', 127),
            'accent': f.get('velocityStrong', {}).get('p75', 110),
            'ghost': f.get('velocityFloor', {}).get('p75', 30),
            'phrasePeak': f.get('velocityStrong', {}).get('p50', 105),
            'source': 'FACTORY',
            'confidence': f.get('confidence', 0.5),
        }
    else:
        # Estimated defaults are descriptive only and must never become an
        # automatic velocity authority.
        defaults = {
            'bass': {'min': 40, 'pp': 40, 'p': 55, 'mp': 65, 'mf': 80, 'f': 100, 'ff': 115, 'fff': 127, 'accent': 110, 'ghost': 45, 'phrasePeak': 105},
            'drums': {'min': 20, 'pp': 30, 'p': 50, 'mp': 65, 'mf': 80, 'f': 105, 'ff': 118, 'fff': 127, 'accent': 115, 'ghost': 25, 'phrasePeak': 110},
            'piano': {'min': 15, 'pp': 25, 'p': 50, 'mp': 65, 'mf': 75, 'f': 100, 'ff': 118, 'fff': 127, 'accent': 110, 'ghost': 30, 'phrasePeak': 105},
            'rhythm_guitar': {'min': 30, 'pp': 35, 'p': 55, 'mp': 65, 'mf': 78, 'f': 100, 'ff': 115, 'fff': 127, 'accent': 110, 'ghost': 35, 'phrasePeak': 100},
        }
        d = defaults.get(role, {'min': 1, 'pp': 15, 'p': 45, 'mp': 60, 'mf': 75, 'f': 100, 'ff': 118, 'fff': 127, 'accent': 110, 'ghost': 30, 'phrasePeak': 105})
        vel = {
            **d,
            'source': 'UNRESOLVED',
            'authority_status': 'MANUAL_REVIEW',
            'confidence': 0.0,
        }

    # Dodaj element-specific curve za drums
    if role == 'drums':
        vel['elementSpecificCurve'] = {
            'kick': {'accent': 120, 'ghost': 0, 'typical': 90},
            'snare': {'accent': 118, 'ghost': 28, 'typical': 80},
            'hihat': {'accent': 95, 'ghost': 30, 'typical': 65},
            'crash': {'accent': 127, 'ghost': 0, 'typical': 100},
            'ride': {'accent': 90, 'ghost': 40, 'typical': 70},
        }

    # Dodaj strum-specific za guitar
    if role == 'rhythm_guitar':
        vel['strumSpecific'] = {
            'downstroke': {'accent': 110, 'typical': 85},
            'upstroke': {'accent': 85, 'typical': 60},
            'muted': {'accent': 70, 'typical': 50},
            'ghost': {'accent': 45, 'typical': 30},
        }

    return vel


def _build_timing(role, gold_stats):
    """Sekcija 4: TIMING — GOLD autoritet."""
    g = gold_stats

    if not g:
        return {
            'baseOffset': 0, 'earlyLateRange': 0, 'grooveProfile': 'ON_BEAT',
            'swing': 0, 'humanization': 'MINIMAL', 'source': 'NONE', 'confidence': 0.0
        }

    offset_data = g.get('offset', {})
    duration_data = g.get('duration', {})

    # Timing offset iz Gold podataka (u ticks pri 96 PPQ)
    base_offset = offset_data.get('median', 0)
    early_range = abs(offset_data.get('p5', 0))
    late_range = abs(offset_data.get('p95', 0))

    # Swing detekcija iz meter distribucije
    meter_dist = g.get('meterDistribution', {})
    swing = 0.0
    if '7/8' in meter_dist or '9/8' in meter_dist:
        swing = 0.15  # Balkan asimetrija

    # Humanization po roli
    HUMAN_MAP = {
        'bass': 'CONTROLLED', 'drums': 'TIGHT_HUMAN', 'piano': 'SMALL_SPREAD',
        'rhythm_guitar': 'STRUM_SPREAD', 'solo_guitar': 'EXPRESSIVE',
        'accordion': 'BELLOWS_HUMAN', 'strings': 'MINIMAL', 'brass': 'ACCENT_DRIVEN',
        'sax': 'PHRASE_DRIVEN', 'clarinet': 'ORNAMENT_DRIVEN', 'violin': 'BOW_DRIVEN',
        'pad': 'MINIMAL', 'synth_lead': 'PHRASE_DRIVEN', 'mallet': 'TIGHT_HUMAN',
        'choir': 'MINIMAL', 'percussion': 'INTERLOCK', 'fx': 'EVENT_DRIVEN',
    }

    return {
        'baseOffset': base_offset,
        'earlyLateRange': {'early': -early_range, 'late': late_range},
        'grooveProfile': _groove_profile(role),
        'swing': swing,
        'humanization': HUMAN_MAP.get(role, 'MODERATE'),
        'phraseTiming': {
            'startOffset': offset_data.get('p25', 0),
            'endOffset': offset_data.get('p75', 0),
        },
        'sectionTiming': _section_timing_from_gold(g),
        'source': 'GOLD',
        'confidence': g.get('confidence', 0.0),
    }


def _groove_profile(role):
    """Groove tip po instrumentu."""
    profiles = {
        'bass': 'POCKET_DRIVEN', 'drums': 'GROOVE_KEEPER', 'piano': 'COMPING',
        'rhythm_guitar': 'STRUM_PATTERN', 'solo_guitar': 'PHRASE_FLOW',
        'accordion': 'PULSE_PHRASE', 'strings': 'SUSTAIN_FLOW', 'brass': 'STAB_ACCENT',
        'sax': 'BREATH_PHRASE', 'clarinet': 'FOLK_ORNAMENT', 'violin': 'BOW_PHRASE',
        'pad': 'PAD_MOVEMENT', 'synth_lead': 'LEAD_PHRASE',
    }
    return profiles.get(role, 'GENERIC')


def _section_timing_from_gold(g):
    """Iz Gold sekcija izvuci timing po elementima."""
    sec_dist = g.get('sectionDistribution', {})
    return {
        'intro': 'PICKUP_OR_ESTABLISH' if sec_dist.get('intro', 0) > 0 else 'SILENT_OR_SUSTAIN',
        'body': 'GROOVE_ESTABLISHED',
        'transition': 'FILL_OR_VARIATION' if sec_dist.get('transition', 0) > 0 else 'SAME_AS_BODY',
        'ending': 'RELEASE_OR_FINAL' if sec_dist.get('ending', 0) > 0 else 'FADE',
    }


def _build_note_behavior(role, gold_stats):
    """Sekcija 5: NOTE_BEHAVIOR."""
    g = gold_stats

    if not g:
        return {'density': 0, 'repetition': 0, 'restProbability': 0.5,
                'source': 'NONE', 'confidence': 0.0}

    density_data = g.get('density', {})
    duration_data = g.get('duration', {})
    events_data = g.get('eventsPerPattern', {})

    # Note length kategorizacija (Master Prompt #26)
    med = duration_data.get('median', 12)
    p75 = duration_data.get('p75', 23)
    p25 = duration_data.get('p25', 6)

    # Short/medium/long ratio estimation
    short_threshold = p25
    long_threshold = p75

    return {
        'density': {
            'mean': density_data.get('mean', 8),
            'median': density_data.get('median', 8),
            'p5': density_data.get('p5', 2),
            'p95': density_data.get('p95', 20),
        },
        'repetition': _estimate_repetition(role, g),
        'restProbability': _estimate_rest_prob(role, density_data),
        'noteLength': {
            'short': round(short_threshold, 1),
            'medium': round(med, 1),
            'long': round(long_threshold, 1),
            'distribution': {
                'shortRatio': 0.3,  # Estimirano
                'mediumRatio': 0.5,
                'longRatio': 0.2,
            },
            'source': 'GOLD_DURATION',
        },
        'overlap': _estimate_overlap(role),
        'sustain': _estimate_sustain(role),
        'source': 'GOLD',
        'confidence': g.get('confidence', 0.0),
    }


def _estimate_repetition(role, g):
    """Estimiraj ponavljanje nota."""
    # Instrumenti sa puno ponavljanja
    HIGH_REPEAT = ['drums', 'percussion', 'rhythm_guitar', 'bass']
    MED_REPEAT = ['piano', 'organ', 'accordion', 'pad']
    LOW_REPEAT = ['sax', 'violin', 'clarinet', 'solo_guitar', 'brass']

    if role in HIGH_REPEAT:
        return 0.6
    elif role in MED_REPEAT:
        return 0.4
    elif role in LOW_REPEAT:
        return 0.15
    return 0.3


def _estimate_rest_prob(role, density_data):
    """Estimiraj vjerovatnoću pauze."""
    # Veća gustoća = manje pauza
    median_density = density_data.get('median', 8)
    if role == 'bass':
        return max(0.1, 0.5 - median_density * 0.03)
    elif role == 'pad':
        return 0.05
    elif role == 'drums':
        return max(0.05, 0.3 - median_density * 0.02)
    return 0.25


def _estimate_overlap(role):
    """Estimiraj preklapanje nota."""
    HIGH_OVERLAP = ['organ', 'strings', 'pad', 'choir', 'accordion']
    if role in HIGH_OVERLAP:
        return 0.6
    return 0.15


def _estimate_sustain(role):
    """Estimiraj održavanje tona."""
    HIGH_SUST = ['strings', 'pad', 'choir', 'organ']
    MED_SUST = ['bass', 'sax', 'violin', 'synth_lead']
    LOW_SUST = ['drums', 'percussion', 'brass', 'rhythm_guitar', 'mallet']

    if role in HIGH_SUST:
        return 0.8
    elif role in MED_SUST:
        return 0.5
    elif role in LOW_SUST:
        return 0.2
    return 0.4


def _build_harmony(role, gold_stats, behavior_data):
    """Sekcija 6: HARMONY — Chord tracking kao osnova."""
    g = gold_stats
    b = behavior_data

    # Root/Third/Fifth/Seventh težine po instrumentu (Master Prompt #4)
    HARMONY_WEIGHTS = {
        'bass':          {'root': 0.85, 'third': 0.10, 'fifth': 0.40, 'seventh': 0.08},
        'piano':         {'root': 0.40, 'third': 0.80, 'fifth': 0.70, 'seventh': 0.30},
        'organ':         {'root': 0.50, 'third': 0.70, 'fifth': 0.65, 'seventh': 0.25},
        'rhythm_guitar': {'root': 0.45, 'third': 0.75, 'fifth': 0.70, 'seventh': 0.20},
        'strings':       {'root': 0.50, 'third': 0.70, 'fifth': 0.65, 'seventh': 0.30},
        'brass':         {'root': 0.55, 'third': 0.65, 'fifth': 0.60, 'seventh': 0.25},
        'sax':           {'root': 0.30, 'third': 0.55, 'fifth': 0.45, 'seventh': 0.35},
        'clarinet':      {'root': 0.30, 'third': 0.55, 'fifth': 0.45, 'seventh': 0.30},
        'violin':        {'root': 0.25, 'third': 0.50, 'fifth': 0.40, 'seventh': 0.30},
        'solo_guitar':   {'root': 0.30, 'third': 0.55, 'fifth': 0.45, 'seventh': 0.35},
        'accordion':     {'root': 0.50, 'third': 0.70, 'fifth': 0.65, 'seventh': 0.20},
        'pad':           {'root': 0.50, 'third': 0.75, 'fifth': 0.70, 'seventh': 0.30},
        'choir':         {'root': 0.50, 'third': 0.75, 'fifth': 0.70, 'seventh': 0.30},
    }

    weights = HARMONY_WEIGHTS.get(role, {'root': 0.40, 'third': 0.60, 'fifth': 0.55, 'seventh': 0.20})

    # Passing/approach/chromatic rate (Master Prompt #4)
    PASSING_RATES = {
        'bass': 0.12, 'sax': 0.25, 'clarinet': 0.20, 'violin': 0.18,
        'solo_guitar': 0.22, 'piano': 0.08, 'rhythm_guitar': 0.05,
        'strings': 0.05, 'brass': 0.08, 'organ': 0.05, 'pad': 0.02,
    }

    APPROACH_RATES = {
        'bass': 0.10, 'sax': 0.15, 'clarinet': 0.18, 'violin': 0.12,
        'solo_guitar': 0.15, 'piano': 0.05, 'brass': 0.05,
    }

    CHROMATIC_RATES = {
        'bass': 0.05, 'sax': 0.10, 'clarinet': 0.12, 'violin': 0.08,
        'solo_guitar': 0.10, 'accordion': 0.08,
    }

    # Chord change behavior
    CHORD_CHANGE = {
        'bass': 'anticipate_root', 'piano': 'voice_lead_minimal',
        'rhythm_guitar': 'strum_chord_change', 'strings': 'smooth_voice_lead',
        'brass': 'stab_on_change', 'pad': 'sustain_through',
    }

    # Voice leading (Master Prompt #6)
    VOICE_LEADING = {
        'piano': 'COMMON_TONE_RETENTION', 'strings': 'MINIMAL_MOVEMENT',
        'organ': 'COMMON_TONE_RETENTION', 'pad': 'MINIMAL_MOVEMENT',
        'choir': 'MINIMAL_MOVEMENT', 'brass': 'PARALLEL_BLOCK',
    }

    return {
        'rootWeight': weights['root'],
        'thirdWeight': weights['third'],
        'fifthWeight': weights['fifth'],
        'seventhWeight': weights['seventh'],
        'chordToneWeight': round((weights['root'] + weights['third'] + weights['fifth']) / 3, 3),
        'passingNoteRate': PASSING_RATES.get(role, 0.08),
        'approachNoteRate': APPROACH_RATES.get(role, 0.05),
        'chromaticRate': CHROMATIC_RATES.get(role, 0.03),
        'voiceLeading': VOICE_LEADING.get(role, 'DEFAULT'),
        'chordChangeBehavior': CHORD_CHANGE.get(role, 'follow_chord'),
        'chordQualityDistribution': g.get('chordQualityDistribution', {}) if g else {},
        'source': 'GOLD+BEHAVIOR',
        'confidence': g.get('confidence', 0.0) if g else 0.3,
    }


def _build_rhythm(role, gold_stats):
    """Sekcija 7: RHYTHM."""
    g = gold_stats

    # Pattern type
    PATTERN_TYPES = {
        'bass': 'ROOT_PULSE', 'drums': 'GROOVE_PATTERN', 'piano': 'COMPING',
        'rhythm_guitar': 'STRUM_PATTERN', 'accordion': 'CHORD_PULSE',
        'organ': 'CHORD_PULSE', 'strings': 'SUSTAIN', 'brass': 'STAB',
        'sax': 'PHRASE', 'clarinet': 'ORNAMENT_PHRASE', 'violin': 'BOW_PHRASE',
        'pad': 'SUSTAIN', 'mallet': 'ARPEGGIATED',
    }

    # Syncopation
    SYNCOPATION = {
        'bass': 0.15, 'drums': 0.20, 'piano': 0.25, 'rhythm_guitar': 0.30,
        'sax': 0.20, 'clarinet': 0.15, 'violin': 0.10, 'solo_guitar': 0.25,
    }

    # Subdivision preference
    SUBDIVISION = {
        'bass': 'QUARTER_EIGHTH', 'drums': 'SIXTEENTH', 'piano': 'EIGHTH',
        'rhythm_guitar': 'SIXTEENTH', 'accordion': 'EIGHTH_SIXTEENTH',
        'sax': 'EIGHTH_TRIPLET', 'clarinet': 'SIXTEENTH_ORNAMENT',
    }

    # Offbeat probability
    OFFBEAT = {
        'rhythm_guitar': 0.45, 'piano': 0.25, 'drums': 0.30,
        'percussion': 0.40, 'bass': 0.10,
    }

    return {
        'patternType': PATTERN_TYPES.get(role, 'GENERIC'),
        'syncopation': SYNCOPATION.get(role, 0.10),
        'accentMap': _default_accent_map(role),
        'subdivisionPreference': SUBDIVISION.get(role, 'QUARTER'),
        'offbeatProbability': OFFBEAT.get(role, 0.10),
        'pickupProbability': 0.10 if role in ['bass', 'sax', 'violin'] else 0.05,
        'restPlacement': 'WEAK_BEATS' if role == 'bass' else 'PHRASE_END',
        'meterDistribution': g.get('meterDistribution', {}) if g else {},
        'source': 'GOLD+INFERENCE',
        'confidence': g.get('confidence', 0.0) if g else 0.3,
    }


def _default_accent_map(role):
    """Default accent mapa po doba."""
    if role == 'bass':
        return {'beat1': 1.0, 'beat2': 0.5, 'beat3': 0.8, 'beat4': 0.4}
    elif role == 'drums':
        return {'beat1': 1.0, 'beat2': 0.3, 'beat3': 0.3, 'beat4': 0.9}  # snare backbeat
    elif role == 'rhythm_guitar':
        return {'beat1': 0.8, 'and1': 0.6, 'beat2': 0.4, 'and2': 0.5, 'beat3': 0.7, 'beat4': 0.4}
    return {'beat1': 0.8, 'beat2': 0.5, 'beat3': 0.7, 'beat4': 0.5}


def _build_articulation(role, gold_stats, behavior_data):
    """Sekcija 8: ARTICULATION — GOLD autoritet."""
    # Articulacijski parametri po instrumentu
    ARTIC = {
        'bass':          {'legato': 0.4, 'staccato': 0.2, 'accent': 0.3, 'ghost': 0.1, 'grace': 0.05, 'slide': 0.08, 'hammerOn': 0.05, 'pullOff': 0.03},
        'piano':         {'legato': 0.3, 'staccato': 0.3, 'accent': 0.4, 'ghost': 0.05, 'grace': 0.03, 'trill': 0.02},
        'rhythm_guitar': {'legato': 0.2, 'staccato': 0.3, 'accent': 0.5, 'ghost': 0.15, 'mute': 0.2, 'slide': 0.05, 'hammerOn': 0.08},
        'solo_guitar':   {'legato': 0.6, 'staccato': 0.1, 'accent': 0.4, 'bend': 0.25, 'slide': 0.15, 'hammerOn': 0.12, 'pullOff': 0.10, 'grace': 0.10, 'vibrato': 0.20},
        'accordion':     {'legato': 0.5, 'staccato': 0.3, 'accent': 0.4, 'ghost': 0.05, 'grace': 0.12, 'tremolo': 0.08},
        'strings':       {'legato': 0.8, 'staccato': 0.1, 'accent': 0.3, 'grace': 0.05, 'slide': 0.03, 'trill': 0.04},
        'brass':         {'legato': 0.3, 'staccato': 0.4, 'accent': 0.6, 'ghost': 0.05, 'stab': 0.3, 'fall': 0.08},
        'sax':           {'legato': 0.5, 'staccato': 0.2, 'accent': 0.3, 'grace': 0.10, 'slide': 0.08},
        'clarinet':      {'legato': 0.5, 'staccato': 0.2, 'accent': 0.3, 'grace': 0.15, 'trill': 0.12, 'ornament': 0.10},
        'violin':        {'legato': 0.7, 'staccato': 0.15, 'accent': 0.3, 'grace': 0.10, 'slide': 0.12, 'trill': 0.08, 'ornament': 0.06},
        'drums':         {'legato': 0.0, 'staccato': 0.9, 'accent': 0.5, 'ghost': 0.2, 'flam': 0.05, 'roll': 0.03, 'choke': 0.04},
    }

    art = ARTIC.get(role, {'legato': 0.3, 'staccato': 0.2, 'accent': 0.3, 'grace': 0.05})

    # Dodaj release behavior
    RELEASE = {
        'bass': 'CONTROLLED_DECAY', 'piano': 'NATURAL_DECAY', 'organ': 'SHARP_CUT_OR_SUSTAIN',
        'strings': 'BOW_RELEASE', 'brass': 'BREATH_RELEASE', 'sax': 'BREATH_RELEASE',
        'rhythm_guitar': 'MUTE_OR_DECAY', 'solo_guitar': 'FRET_NOISE_OR_DECAY',
    }

    return {
        **art,
        'releaseBehavior': RELEASE.get(role, 'NATURAL_DECAY'),
        'dnC_RX_Aware': role in ['solo_guitar', 'rhythm_guitar', 'sax', 'brass', 'strings'],
        'source': 'GOLD+BEHAVIOR',
        'confidence': 0.7 if role in ARTIC else 0.4,
    }


def _build_expression(role, gold_stats):
    """Sekcija 9: EXPRESSION (Master Prompt #23)."""
    # CC11 expression model
    EXPRESSION_MAP = {
        'bass':     {'cc11_rate': 'LOW', 'swell': 'RARE', 'phraseCurve': 'GROOVE_ALIGNED'},
        'piano':    {'cc11_rate': 'NONE', 'swell': 'RARE', 'phraseCurve': 'VELOCITY_DRIVEN'},
        'organ':    {'cc11_rate': 'HIGH', 'swell': 'COMMON', 'phraseCurve': 'SWELL_DRIVEN'},
        'strings':  {'cc11_rate': 'HIGH', 'swell': 'COMMON', 'phraseCurve': 'PHRASE_ARC'},
        'sax':      {'cc11_rate': 'MEDIUM', 'swell': 'PHRASE_END', 'phraseCurve': 'BREATH_PHRASE'},
        'clarinet': {'cc11_rate': 'MEDIUM', 'swell': 'PHRASE_END', 'phraseCurve': 'FOLK_PHRASE'},
        'violin':   {'cc11_rate': 'MEDIUM', 'swell': 'PHRASE_END', 'phraseCurve': 'BOW_PHRASE'},
        'brass':    {'cc11_rate': 'LOW', 'swell': 'RARE', 'phraseCurve': 'ACCENT_DRIVEN'},
        'pad':      {'cc11_rate': 'SLOW', 'swell': 'SECTION_END', 'phraseCurve': 'SLOW_MOVEMENT'},
        'choir':    {'cc11_rate': 'SLOW', 'swell': 'SECTION_DRIVEN', 'phraseCurve': 'SLOW_ARC'},
    }

    expr = EXPRESSION_MAP.get(role, {'cc11_rate': 'LOW', 'swell': 'RARE', 'phraseCurve': 'DEFAULT'})

    # Section energy (Master Prompt #23 — VERSE < PRE-CHORUS < CHORUS)
    section_energy = {
        'intro': 0.4, 'body': 0.6, 'transition': 0.75, 'ending': 0.3
    }

    if gold_stats:
        sec_dist = gold_stats.get('sectionDistribution', {})
        total = sum(sec_dist.values()) or 1
        section_energy['intro'] = 0.3 + 0.2 * (sec_dist.get('intro', 0) / total)
        section_energy['transition'] = 0.6 + 0.2 * (sec_dist.get('transition', 0) / total)

    return {
        'cc11': expr['cc11_rate'],
        'swell': expr['swell'],
        'phraseCurve': expr['phraseCurve'],
        'accentExpression': 'VELOCITY_BASED' if role not in ['organ', 'strings'] else 'CC11_BASED',
        'releaseExpression': 'NATURAL' if role != 'organ' else 'CC11_PULL',
        'dynamicContour': 'PHRASE_ARC',
        'sectionEnergy': section_energy,
        'source': 'GOLD+INFERENCE',
        'confidence': 0.6,
    }


def _build_section_behavior(role, gold_stats):
    """Sekcija 10: SECTION_BEHAVIOR (Master Prompt #28)."""
    g = gold_stats

    # Default section behaviors
    SECTION_DEFAULTS = {
        'bass': {
            'intro': 'ESTABLISH_ROOT', 'variation': 'GROOVE_WITH_VARIATION',
            'fill': 'WALK_OR_REST', 'break': 'REST_OR_ACCENT', 'ending': 'DESCEND_OR_SUSTAIN',
        },
        'drums': {
            'intro': 'ESTABLISH_GROOVE_OR_PICKUP', 'variation': 'DENSITY_CHANGE',
            'fill': 'FILL_PATTERN', 'break': 'BREAK_PATTERN', 'ending': 'FINAL_FILL_OR_CRASH',
        },
        'rhythm_guitar': {
            'intro': 'ESTABLISH_CHORD_OR_REST', 'variation': 'PATTERN_CHANGE',
            'fill': 'ANSWER_OR_REST', 'break': 'MUTE_OR_REST', 'ending': 'FINAL_STRUM',
        },
        'brass': {
            'intro': 'REST_OR_SUSTAIN', 'variation': 'STAB_ACCENT',
            'fill': 'STAB_FILL', 'break': 'REST_OR_ACCENT', 'ending': 'FINAL_STAB_OR_SUSTAIN',
        },
        'strings': {
            'intro': 'SUSTAIN_OR_SILENT', 'variation': 'SUSTAIN_WITH_MOVEMENT',
            'fill': 'SUSTAIN_OR_CREST', 'break': 'SUSTAIN', 'ending': 'FADE_OR_SUSTAIN',
        },
        'sax': {
            'intro': 'REST_OR_PICKUP', 'variation': 'PHRASE_COUNTER',
            'fill': 'PHRASE_ENDING', 'break': 'REST_OR_LICK', 'ending': 'DESCEND_OR_REST',
        },
    }

    defaults = SECTION_DEFAULTS.get(role, {
        'intro': 'ESTABLISH_OR_REST', 'variation': 'FOLLOW_SECTION',
        'fill': 'ANSWER_OR_REST', 'break': 'REST_OR_SUSTAIN', 'ending': 'RELEASE',
    })

    # Override sa Gold podacima ako postoje
    sec_dist = g.get('sectionDistribution', {}) if g else {}
    total = sum(sec_dist.values()) or 1

    return {
        'intro': defaults.get('intro', 'REST'),
        'variation1': defaults.get('variation', 'FOLLOW_SECTION'),
        'variation2': defaults.get('variation', 'INCREASE_DENSITY'),
        'variation3': defaults.get('variation', 'ADD_ORNAMENTS'),
        'variation4': defaults.get('variation', 'PEAK_ENERGY'),
        'fill': defaults.get('fill', 'ANSWER_OR_REST'),
        'break': defaults.get('break', 'REST_OR_SUSTAIN'),
        'ending': defaults.get('ending', 'RELEASE'),
        'transition': 'FILL_OR_VARIATION' if sec_dist.get('transition', 0) / total > 0.15 else 'SAME_AS_BODY',
        'goldSectionEvidence': dict(sec_dist),
        'source': 'GOLD+DEFAULTS',
        'confidence': g.get('confidence', 0.0) if g else 0.3,
    }


def _build_interaction(role, gold_stats, behavior_data):
    """Sekcija 11: INTERACTION (Master Prompt #29)."""
    b = behavior_data
    follows = b.get('follows', []) if b else []

    # Hard-coded interaction map po Master Prompt #29
    INTERACTIONS = {
        'bass': {
            'bassRelationship': {'with': 'kick', 'type': 'INTERLOCK', 'priority': 'HIGH'},
            'chordRelationship': {'with': 'chord', 'type': 'ROOT_FOLLOW', 'priority': 'CRITICAL'},
            'vocalSpace': {'type': 'LOW_REGISTER_AVOID', 'priority': 'MEDIUM'},
        },
        'drums': {
            'drumRelationship': {'with': 'bass', 'type': 'GROOVE_INTERLOCK', 'priority': 'HIGH'},
            'melodySpace': {'type': 'GROOVE_FOUNDATION', 'priority': 'HIGH'},
        },
        'rhythm_guitar': {
            'chordRelationship': {'with': 'chord', 'type': 'STRUM_VOICING', 'priority': 'HIGH'},
            'drumRelationship': {'with': 'drums', 'type': 'RHYTHM_INTERLOCK', 'priority': 'MEDIUM'},
            'bassRelationship': {'with': 'bass', 'type': 'REGISTER_AVOID', 'priority': 'MEDIUM'},
        },
        'piano': {
            'chordRelationship': {'with': 'chord', 'type': 'VOICING', 'priority': 'HIGH'},
            'bassRelationship': {'with': 'bass', 'type': 'REGISTER_AVOID', 'priority': 'HIGH'},
            'vocalSpace': {'type': 'FREQ_AVOID', 'priority': 'MEDIUM'},
        },
        'sax': {
            'vocalSpace': {'type': 'MELODY_AVOID', 'priority': 'HIGH'},
            'chordRelationship': {'with': 'chord', 'type': 'COUNTER_MELODY', 'priority': 'MEDIUM'},
        },
    }

    interaction = INTERACTIONS.get(role, {
        'chordRelationship': {'with': 'chord', 'type': 'FOLLOW', 'priority': 'MEDIUM'},
    })

    # Dodaj Gold follows ako postoje
    if follows:
        interaction['goldFollows'] = follows

    # Frequency/register competition
    FREQ_MAP = {
        'bass': '20-250Hz', 'drums': '50-5000Hz', 'piano': '80-4000Hz',
        'rhythm_guitar': '100-2500Hz', 'strings': '200-8000Hz', 'brass': '200-3000Hz',
        'sax': '200-1500Hz', 'violin': '300-5000Hz', 'pad': '100-4000Hz',
    }

    interaction['frequencyCompetition'] = FREQ_MAP.get(role, '100-3000Hz')
    interaction['source'] = 'BEHAVIOR+GOLD'
    interaction['confidence'] = 0.7

    return interaction


def _build_pa800(role, pa8_info, general_rules, gold_stats):
    """Sekcija 12: PA800_BEHAVIOR."""
    gr = general_rules

    # NTT recommendation
    ntt_rec = pa8_info.get('ntt', 'Chord')

    # Chord variation (po NTT)
    CHORD_VAR = {
        'Parallel': 'MELODIC_TRANSPOSITION',
        'Fixed': 'MINIMAL_MOVEMENT',
        'Chord': 'CHORD_TONE_FOLLOW',
        'Root': 'ROOT_ANCHOR',
        'Fifth': 'POWER_CHORD',
    }

    # Guitar Mode
    guitar_mode = pa8_info.get('guitarMode')

    # RX/DNC awareness (Master Prompt #33)
    RX_DNC_INSTRUMENTS = ['solo_guitar', 'rhythm_guitar', 'sax', 'brass', 'strings', 'violin']
    rx_dnc = role in RX_DNC_INSTRUMENTS

    # Bank/Program from General Rules
    programs = gr.get('programs', {})

    return {
        'trackType': pa8_info['trackType'],
        'ntt': ntt_rec,
        'chordVariation': CHORD_VAR.get(ntt_rec, 'DEFAULT'),
        'guitarMode': guitar_mode,
        'rx': rx_dnc,
        'dnc': rx_dnc,
        'cc': ['CC7', 'CC10', 'CC11'] if role not in ['drums', 'percussion'] else ['CC7'],
        'bankSelect': 'REQUIRES_CONFIRMATION' if rx_dnc else 'GM_STANDARD',
        'programChange': 'GM_MAPPED' if not rx_dnc else 'RX_DNC_MAPPED',
        'exportRules': {
            'noteRange': 'GENERAL_RULES_ENFORCED',
            'velocityRange': '1-127_ENFORCED',
            'polyphony': 54,
            'drumChannel': 10 if role in ['drums', 'percussion'] else None,
        },
        'source': 'PA800_SPEC+GENERAL_RULES',
        'confidence': 0.85,
    }


def _build_confidence(role, gold_stats, factory_stats, behavior_data):
    """Sekcija 13: CONFIDENCE_REPORT (Master Prompt #34, #35, #36)."""
    g = gold_stats or {}
    f = factory_stats or {}
    b = behavior_data or {}

    gold_n = g.get('patternCount', 0)
    factory_n = f.get('profileCount', 0) if f else 0

    return {
        'overallConfidence': confidence_from_samples(gold_n + factory_n, k=100),
        'goldSampleCount': gold_n,
        'factorySampleCount': factory_n,
        'behaviorDefined': bool(b),
        'sectionsComplete': 12,  # Od 13 sekcija (confidence je 13.)
        'sectionsMissing': [],  # Popunjavamo sve
        'lowConfidenceFlags': ['LOW_CONFIDENCE'] if gold_n < 50 else [],
        'perSection': {
            'identity': {'confidence': 0.95, 'source': 'BEHAVIOR+SPEC'},
            'range': {'confidence': confidence_from_samples(factory_n, k=100), 'source': 'FACTORY+GM'},
            'velocity': {'confidence': confidence_from_samples(factory_n, k=100), 'source': 'FACTORY'},
            'timing': {'confidence': g.get('confidence', 0.0), 'source': 'GOLD'},
            'noteBehavior': {'confidence': g.get('confidence', 0.0) * 0.8, 'source': 'GOLD'},
            'harmony': {'confidence': max(g.get('confidence', 0.0) * 0.7, 0.3), 'source': 'GOLD+INFERENCE'},
            'rhythm': {'confidence': g.get('confidence', 0.0) * 0.8, 'source': 'GOLD+INFERENCE'},
            'articulation': {'confidence': 0.6, 'source': 'INFERENCE+BEHAVIOR'},
            'expression': {'confidence': 0.5, 'source': 'INFERENCE'},
            'sectionBehavior': {'confidence': g.get('confidence', 0.0) * 0.6, 'source': 'GOLD+DEFAULTS'},
            'interaction': {'confidence': 0.7, 'source': 'BEHAVIOR+SPEC'},
            'pa800Behavior': {'confidence': 0.85, 'source': 'PA800_SPEC+GENERAL_RULES'},
        },
    }


# ── Human-Readable Description (Master Prompt #47) ──

def _generate_how_it_plays(profile: dict) -> str:
    """Generiši human-readable opis iz mjerenih parametara (Master Prompt #47)."""
    role = profile['role']
    identity = profile['identity']
    velocity = profile['velocity']
    timing = profile['timing']
    harmony = profile['harmony']
    articulation = profile['articulation']
    section = profile['sectionBehavior']
    interaction = profile['interaction']

    parts = []

    # Role description
    parts.append(f"{identity['musicalRole']}.")

    # Harmony behavior
    if harmony['rootWeight'] > 0.6:
        parts.append(f"Strongly anchors root notes (weight {harmony['rootWeight']:.2f})")
    elif harmony['chordToneWeight'] > 0.5:
        parts.append(f"Follows chord tones (weight {harmony['chordToneWeight']:.2f})")
    if harmony['passingNoteRate'] > 0.10:
        parts.append(f"uses passing tones at rate {harmony['passingNoteRate']:.0%}")
    if harmony['chromaticRate'] > 0.05:
        parts.append(f"applies chromatic approach at {harmony['chromaticRate']:.0%}")

    # Timing behavior
    if timing['humanization'] != 'MINIMAL':
        parts.append(f"{timing['humanization'].replace('_', ' ').lower()} timing")
    if timing['baseOffset'] != 0:
        direction = 'slightly early' if timing['baseOffset'] < 0 else 'slightly late'
        parts.append(f"leans {direction} (offset {timing['baseOffset']})")

    # Velocity behavior
    vel_desc = f"dynamic range {velocity.get('pp', '?')}-{velocity.get('fff', '?')}"
    parts.append(vel_desc)

    # Articulation
    top_artic = sorted(
        [(k, v) for k, v in articulation.items()
         if isinstance(v, (int, float)) and v > 0.1 and k not in ('confidence', 'dnC_RX_Aware')],
        key=lambda x: -x[1]
    )[:3]
    if top_artic:
        art_str = ', '.join(f"{k} ({v:.0%})" for k, v in top_artic)
        parts.append(f"primary articulation: {art_str}")

    # Section behavior
    sec_behavior = section.get('variation1', 'follows section')
    parts.append(f"in variations: {sec_behavior.replace('_', ' ').lower()}")
    if section.get('fill') != 'ANSWER_OR_REST':
        parts.append(f"on fills: {section['fill'].replace('_', ' ').lower()}")

    # Interaction
    if 'bassRelationship' in interaction:
        br = interaction['bassRelationship']
        parts.append(f"{br['type'].replace('_', ' ').lower()} with {br.get('with', '?')}")
    if 'chordRelationship' in interaction:
        cr = interaction['chordRelationship']
        parts.append(f"{cr['type'].replace('_', ' ').lower()} relative to chord")

    # PA800
    pa = profile.get('pa800Behavior', {})
    if pa.get('ntt'):
        parts.append(f"PA800 NTT: {pa['ntt']}")
    if pa.get('guitarMode'):
        parts.append(f"Guitar Mode: {pa['guitarMode']}")

    return ' '.join(parts).capitalize() + '.'


# ── Main Builder ──

def build_all_profiles(output_dir: Path = None, include_gold_roles: bool = True) -> dict:
    """Napravi sve Instrument Playing Profile (Master Prompt #49).
    
    Returns dict sa svim profilima + čuva JSON + SQLite bazu.
    """
    output_dir = output_dir or DATA_DIR

    # Učitaj sve izvore
    factory_profiles = load_factory_profiles()
    factory_catalog = load_factory_catalog()
    gold_patterns = load_gold_patterns()
    gold_rels = load_gold_relationships()
    drum_evidence = load_drum_evidence()
    behavior_data = load_instrument_behavior()
    general_rules = load_general_rules()
    strum_data = load_factory_strumming()

    # Izračunaj statistike
    gold_stats = extract_gold_role_stats(gold_patterns)
    factory_stats = extract_factory_role_stats(factory_profiles, factory_catalog)
    drum_elem_stats = extract_drum_element_stats(drum_evidence)

    # Odredi sve role za profiliranje
    all_roles = set(INSTRUMENT_FAMILIES.keys())
    # Dodaj role iz Gold podataka
    if include_gold_roles:
        all_roles |= set(gold_stats.keys())

    profiles = {}
    for role in sorted(all_roles):
        b_data = behavior_data.get('profiles', {}).get(role, {})
        profiles[role] = build_instrument_profile(
            role=role,
            gold_stats=gold_stats,
            factory_stats=factory_stats,
            behavior_data=b_data,
            drum_elements=drum_elem_stats,
            general_rules=general_rules,
            strum_data=strum_data,
        )

    # Sačuvaj JSON
    output = {
        'schema': 'dna-instrument-playing-profiles',
        'version': VERSION,
        'totalProfiles': len(profiles),
        'authority': {
            'velocity': 'FACTORY_ONLY',
            'timing': 'GOLD_PRIMARY',
            'articulation': 'GOLD_PRIMARY',
            'expression': 'GOLD_PRIMARY',
            'mapping': 'PA800_ENGINE',
            'chordFoundation': 'CHORD_TIMELINE',
        },
        'chordFoundation': 'Mora sve pratit Chord kao osnovno',
        'profiles': profiles,
        'goldStatistics': gold_stats,
        'factoryStatistics': factory_stats,
        'drumElementStatistics': drum_elem_stats,
    }

    json_path = output_dir / 'instrument-playing-profiles-9.30.json'
    json_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"✅ JSON sačuvan: {json_path} ({len(json.dumps(output)) // 1024} KB)")

    # Sačuvaj SQLite bazu
    db_path = output_dir / 'instrument-profiles-9.30.db'
    _save_to_sqlite(profiles, db_path)

    # Sačuvaj human-readable izvještaj
    report_path = output_dir / 'instrument-profile-report-9.30.md'
    _save_human_report(profiles, report_path)

    return output


# ── SQLite Database (Master Prompt #49.C) ──

def _save_to_sqlite(profiles: dict, db_path: Path):
    """Sačuvaj profile u SQLite bazu."""
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()

    # Kreiraj tabele
    c.execute('''CREATE TABLE IF NOT EXISTS profiles (
        role TEXT PRIMARY KEY,
        family TEXT,
        subfamily TEXT,
        arrangement_role TEXT,
        pa800_track_type TEXT,
        ntt TEXT,
        guitar_mode TEXT,
        velocity_source TEXT,
        timing_source TEXT,
        overall_confidence REAL,
        gold_samples INTEGER,
        factory_samples INTEGER,
        how_it_plays TEXT,
        profile_json TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS range_data (
        role TEXT PRIMARY KEY,
        absolute_min INTEGER,
        absolute_max INTEGER,
        practical_min INTEGER,
        practical_max INTEGER,
        preferred_low INTEGER,
        preferred_mid INTEGER,
        preferred_high INTEGER,
        register_transition TEXT,
        FOREIGN KEY (role) REFERENCES profiles(role)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS velocity_data (
        role TEXT PRIMARY KEY,
        pp INTEGER, p INTEGER, mp INTEGER, mf INTEGER,
        f INTEGER, ff INTEGER, fff INTEGER,
        accent INTEGER, ghost INTEGER, phrase_peak INTEGER,
        source TEXT, confidence REAL,
        FOREIGN KEY (role) REFERENCES profiles(role)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS harmony_data (
        role TEXT PRIMARY KEY,
        root_weight REAL, third_weight REAL, fifth_weight REAL, seventh_weight REAL,
        passing_rate REAL, approach_rate REAL, chromatic_rate REAL,
        chord_change_behavior TEXT, voice_leading TEXT,
        FOREIGN KEY (role) REFERENCES profiles(role)
    )''')

    for role, profile in profiles.items():
        ident = profile.get('identity', {})
        rng = profile.get('range', {})
        vel = profile.get('velocity', {})
        harm = profile.get('harmony', {})
        pa = profile.get('pa800Behavior', {})
        conf = profile.get('confidence', {})

        c.execute('INSERT OR REPLACE INTO profiles VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                  (role, ident.get('family', ''), ident.get('subfamily', ''),
                   ident.get('instrumentRole', ''), pa.get('trackType', ''),
                   pa.get('ntt', ''), pa.get('guitarMode', ''),
                   vel.get('source', ''), profile.get('timing', {}).get('source', ''),
                   conf.get('overallConfidence', 0), conf.get('goldSampleCount', 0),
                   conf.get('factorySampleCount', 0), profile.get('howItPlays', ''),
                   json.dumps(profile, ensure_ascii=False)))

        c.execute('INSERT OR REPLACE INTO range_data VALUES (?,?,?,?,?,?,?,?,?)',
                  (role, rng.get('absoluteMin', 0), rng.get('absoluteMax', 127),
                   rng.get('practicalMin', 0), rng.get('practicalMax', 127),
                   rng.get('preferredLow', 0), rng.get('preferredMid', 60),
                   rng.get('preferredHigh', 96), rng.get('registerTransition', '')))

        c.execute('INSERT OR REPLACE INTO velocity_data VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                  (role, vel.get('pp', 0), vel.get('p', 0), vel.get('mp', 0),
                   vel.get('mf', 0), vel.get('f', 0), vel.get('ff', 0),
                   vel.get('fff', 0), vel.get('accent', 0), vel.get('ghost', 0),
                   vel.get('phrasePeak', 0), vel.get('source', ''), vel.get('confidence', 0)))

        c.execute('INSERT OR REPLACE INTO harmony_data VALUES (?,?,?,?,?,?,?,?,?,?)',
                  (role, harm.get('rootWeight', 0), harm.get('thirdWeight', 0),
                   harm.get('fifthWeight', 0), harm.get('seventhWeight', 0),
                   harm.get('passingNoteRate', 0), harm.get('approachNoteRate', 0),
                   harm.get('chromaticRate', 0), harm.get('chordChangeBehavior', ''),
                   harm.get('voiceLeading', '')))

    conn.commit()
    conn.close()
    print(f"✅ SQLite sačuvan: {db_path}")


# ── Human-Readable Report (Master Prompt #47, #49.D) ──

def _save_human_report(profiles: dict, report_path: Path):
    """Sačuvaj human-readable izvještaj."""
    lines = [
        '# DNA MIDI Studio 9.30 — Instrument Playing Profile Report',
        '',
        f'**Verzija:** {VERSION}',
        f'**Ukupno profila:** {len(profiles)}',
        f'**Autoritet:** FACTORY=Velocity, GOLD=Timing/Articulation, PA800=Mapping',
        f'**Osnova:** Chord Tracking — svaka funkcija prati Chord',
        '',
        '---',
        '',
    ]

    for role, profile in sorted(profiles.items()):
        ident = profile.get('identity', {})
        vel = profile.get('velocity', {})
        timing = profile.get('timing', {})
        harmony = profile.get('harmony', {})
        note = profile.get('noteBehavior', {})
        artic = profile.get('articulation', {})
        expr = profile.get('expression', {})
        sec = profile.get('sectionBehavior', {})
        pa = profile.get('pa800Behavior', {})
        conf = profile.get('confidence', {})

        lines.append(f'## {role.upper()}')
        lines.append('')
        lines.append(f'- **Family:** {ident.get("family", "?")}')
        lines.append(f'- **Subfamily:** {ident.get("subfamily", "?")}')
        lines.append(f'- **Arrangement Role:** {ident.get("instrumentRole", "?")}')
        lines.append(f'- **Musical Role:** {ident.get("musicalRole", "?")}')
        lines.append(f'- **PA800 Track:** {pa.get("trackType", "?")} | NTT: {pa.get("ntt", "?")}')
        lines.append(f'- **Register:** {ident.get("register", "?")}')
        lines.append('')

        # Velocity table
        lines.append('### Velocity')
        lines.append('')
        lines.append('| Level | Value |')
        lines.append('|---|---|')
        for lvl in ['pp', 'p', 'mp', 'mf', 'f', 'ff', 'fff', 'accent', 'ghost']:
            if lvl in vel:
                lines.append(f'| {lvl} | {vel[lvl]} |')
        lines.append(f'| Source | {vel.get("source", "?")} |')
        lines.append(f'| Confidence | {vel.get("confidence", 0):.2f} |')
        lines.append('')

        # Harmony
        lines.append('### Harmony')
        lines.append('')
        lines.append(f'- Root weight: {harmony.get("rootWeight", 0):.2f}')
        lines.append(f'- Third weight: {harmony.get("thirdWeight", 0):.2f}')
        lines.append(f'- Fifth weight: {harmony.get("fifthWeight", 0):.2f}')
        lines.append(f'- Passing rate: {harmony.get("passingNoteRate", 0):.0%}')
        lines.append(f'- Chromatic rate: {harmony.get("chromaticRate", 0):.0%}')
        lines.append(f'- Chord change: {harmony.get("chordChangeBehavior", "?")}')
        lines.append('')

        # Timing
        lines.append('### Timing')
        lines.append('')
        lines.append(f'- Humanization: {timing.get("humanization", "?")}')
        lines.append(f'- Base offset: {timing.get("baseOffset", 0)}')
        lines.append(f'- Groove profile: {timing.get("grooveProfile", "?")}')
        lines.append(f'- Swing: {timing.get("swing", 0):.2f}')
        lines.append('')

        # HOW IT PLAYS
        lines.append('### How It Plays')
        lines.append('')
        lines.append(f'> {profile.get("howItPlays", "No description generated.")}')
        lines.append('')

        # Confidence
        lines.append('### Confidence')
        lines.append('')
        lines.append(f'- Overall: {conf.get("overallConfidence", 0):.2f}')
        lines.append(f'- Gold samples: {conf.get("goldSampleCount", 0)}')
        lines.append(f'- Factory samples: {conf.get("factorySampleCount", 0)}')
        lines.append(f'- Flags: {", ".join(conf.get("lowConfidenceFlags", [])) or "None"}')
        lines.append('')
        lines.append('---')
        lines.append('')

    report_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f"✅ Human report sačuvan: {report_path} ({len(lines)} lines)")


# ── Alias Integration ──

def load_alias_profiles() -> Optional[dict]:
    """Učitaj alias-resolved profile ako postoje (prioritet nad običnim)."""
    alias_json = DATA_DIR / 'instrument-playing-profiles-9.30-alias.json'
    if alias_json.exists():
        return json.loads(alias_json.read_text(encoding='utf-8'))
    return None


def build_all_profiles_v930(output_dir: Path = None) -> dict:
    """Build svih profila sa alias integracijom.
    
    Ako alias-resolved JSON postoji, koristi njegove profile kao nadogradnju
    nad originalnim profilima — zamjenjujući profile koji su ranije bili
    DEFAULT_ESTIMATED sa alias-resolved podacima iz Factory/Gold rola.
    
    Originalni build_all_profiles() ostaje za fallback.
    """
    # Prvo napravi obične profile
    base = build_all_profiles(output_dir)
    base_profiles = base.get('profiles', {})
    
    # Onda probaj učitati alias-resolved profile
    alias_data = load_alias_profiles()
    if alias_data is None:
        print("⚠️  Alias-resolved profile nisu pronađeni — koristim obične")
        return base
    
    alias_profiles = alias_data.get('profiles', {})
    merged = {}
    
    for inst in INSTRUMENT_FAMILIES:
        bp = base_profiles.get(inst, {})
        ap = alias_profiles.get(inst, {})
        
        if not ap:
            # Nema alias podataka — koristi običan profil
            merged[inst] = bp
            continue
        
        # Alias profil postoji — koristi ga ako je confidence veći
        bp_conf = bp.get('confidence', {}).get('overallConfidence', 0) if isinstance(bp, dict) else 0
        ap_conf = ap.get('confidence', {}).get('overallConfidence', 0) if isinstance(ap, dict) else 0
        
        if ap_conf > bp_conf:
            merged[inst] = ap  # Alias-resolved je bolji
        elif bp_conf > 0 and not ap.get('velocity', {}).get('aliasSource'):
            merged[inst] = bp  # Original je bolji
        else:
            merged[inst] = ap  # Oba slaba — alias ima barem neke podatke
    
    # Sačuvaj merged verziju
    output_dir = output_dir or DATA_DIR
    output = {
        'schema': 'dna-instrument-playing-profiles',
        'version': '9.30.1',
        'totalProfiles': len(merged),
        'authority': {
            'velocity': 'FACTORY_ONLY',
            'timing': 'GOLD_PRIMARY',
            'articulation': 'GOLD_PRIMARY',
            'expression': 'GOLD_PRIMARY',
            'mapping': 'PA800_ENGINE',
            'chordFoundation': 'CHORD_TIMELINE',
            'aliasMapping': 'ROLE_ALIAS_MAP',
        },
        'chordFoundation': 'Mora sve pratit Chord kao osnovno',
        'profiles': merged,
        'aliasSource': 'instrument-playing-profiles-9.30-alias.json',
        'baseSource': 'instrument-playing-profiles-9.30.json',
    }
    
    merged_path = output_dir / 'instrument-playing-profiles-9.30-merged.json'
    merged_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"✅ Merged JSON sačuvan: {merged_path}")
    
    # Coverage izvještaj
    gold_covered = sum(1 for p in merged.values() if isinstance(p, dict) and p.get('timing', {}).get('aliasSource'))
    factory_covered = sum(1 for p in merged.values() if isinstance(p, dict) and p.get('velocity', {}).get('aliasSource'))
    total = len(merged)
    print(f"📊 Gold coverage: {gold_covered}/{total} ({100*gold_covered/total:.0f}%)")
    print(f"📊 Factory coverage: {factory_covered}/{total} ({100*factory_covered/total:.0f}%)")
    
    return output


# ── CLI ──

if __name__ == '__main__':
    print("DNA MIDI Studio 9.30 — Instrument Playing Intelligence Engine")
    print("=" * 60)
    # Pokreni alias-aware build
    result = build_all_profiles_v930()
    print(f"\nUkupno profila: {result['totalProfiles']}")
    print(f"Chord Foundation: {result['chordFoundation']}")
    print(f"\nAutoriteti:")
    for k, v in result['authority'].items():
        print(f"  {k}: {v}")
