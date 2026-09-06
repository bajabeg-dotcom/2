#!/usr/bin/env python3
"""DNA MIDI Studio 9.30 — Role Alias Mapping Engine

Preslikava Gold/Factory role u 20+ instrument familija po Master Prompt specifikaciji.

Problem:
  Gold koristi 6 rola:  accompaniment(3039), bass(2866), drums(1442), 
                        power-riff(4927), riff(566), percussion(78)
  Factory koristi 4 role: bass(51), chords(335), drums(1421), melody(157)
  
  Master Prompt zahtijeva 20+ instrument familija:
    bass, drums, piano, organ, rhythm_guitar, solo_guitar, accordion,
    strings, brass, sax, woodwind, clarinet, violin, synth_lead, pad,
    mallet, choir, percussion, fx, accompaniment

Rješenje:
  Mapiramo Gold/Factory role u instrument familije sa alias težinama:
    Gold accompaniment → piano(0.35), organ(0.15), pad(0.15), accordion(0.15), 
                         strings(0.10), choir(0.10)
    Factory chords    → piano(0.30), rhythm_guitar(0.20), organ(0.15), 
                         accordion(0.15), pad(0.10), strings(0.05), choir(0.05)
    Factory melody    → sax(0.25), clarinet(0.15), violin(0.15), solo_guitar(0.15),
                         synth_lead(0.15), woodwind(0.10), brass(0.05)
    Gold power-riff   → rhythm_guitar(0.80), brass(0.15), mallet(0.05)
    Gold riff         → solo_guitar(0.30), sax(0.25), synth_lead(0.15),
                         brass(0.15), clarinet(0.10), woodwind(0.05)

Autoritet model:
  VELOCITY  → iz Factory role (chords/melody/bass/drums) preslikano sa aliasima
  TIMING    → iz Gold role (accompaniment/power-riff/riff) preslikano sa aliasima
  RANGE     → PA800 + GM spec (nepromijenjeno)
  
  Svaki parametar nosi: value, confidence, source, alias_source, sample_count

Verzija: 9.30.1
Datum: 2026-09-06
"""

import json, math, os, sys, sqlite3
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional, Any

# ── Konstante ──
DATA_DIR = Path(__file__).parent / 'data'
VERSION = '9.30.1'

# ══════════════════════════════════════════════════════════════════
# ROLE ALIAS DEFINICIJA
# ══════════════════════════════════════════════════════════════════

# Gold role → instrument familije sa težinama
# Težina označava koliko Gold podaci za ovu rolu odgovaraju instrumentu
# Viša težina = direktniji preslikak, niža = slabija asocijacija
GOLD_ALIAS_MAP = {
    'accompaniment': {
        # Accompaniment = chordal comping instrumenti
        # Piano je najčešći comping instrument
        # Organ, accordion su chord-pump instrumenti
        # Pad, strings, choir su sustain/harmonic bed instrumenti
        'piano':          {'weight': 0.35, 'evidence': 'CHORDAL_COMPING_PATTERN', 'subfamily': 'piano'},
        'organ':          {'weight': 0.15, 'evidence': 'SUSTAIN_CHORD_COMPING', 'subfamily': 'organ'},
        'pad':            {'weight': 0.15, 'evidence': 'SUSTAIN_HARMONIC_BED', 'subfamily': 'pad'},
        'accordion':      {'weight': 0.15, 'evidence': 'CHORD_PULSE_PATTERN', 'subfamily': 'accordion'},
        'strings':        {'weight': 0.10, 'evidence': 'SUSTAIN_HARMONIC_SUPPORT', 'subfamily': 'ensemble'},
        'choir':          {'weight': 0.10, 'evidence': 'SUSTAIN_VOCAL_TEXTURE', 'subfamily': 'choir'},
    },
    'power-riff': {
        # Power-riff = ritmički akordi sa snagom
        # Rhythm guitar je dominantni (strum/power chords)
        # Brass može biti stab section
        'rhythm_guitar':  {'weight': 0.80, 'evidence': 'STRUM_POWER_CHORD_RIFF', 'subfamily': 'rhythm'},
        'brass':          {'weight': 0.15, 'evidence': 'SECTION_STAB_ACCENT', 'subfamily': 'section'},
        'mallet':         {'weight': 0.05, 'evidence': 'ARTICULATED_RIFF_PATTERN', 'subfamily': 'mallet'},
    },
    'riff': {
        # Riff = kraći melodijski fragment
        # Može biti bilo koji melodijski/solo instrument
        'solo_guitar':    {'weight': 0.28, 'evidence': 'MELODIC_RIFF_SOLO', 'subfamily': 'solo'},
        'sax':            {'weight': 0.22, 'evidence': 'MELODIC_RIFF_PHRASE', 'subfamily': 'saxophone'},
        'synth_lead':     {'weight': 0.13, 'evidence': 'SYNTH_RIFF_PHRASE', 'subfamily': 'lead'},
        'brass':          {'weight': 0.13, 'evidence': 'BRASS_RIFF_STAB', 'subfamily': 'section'},
        'violin':         {'weight': 0.10, 'evidence': 'FOLK_RIFF_VIOLIN', 'subfamily': 'violin_fiddle'},
        'clarinet':       {'weight': 0.07, 'evidence': 'FOLK_RIFF_ORNAMENT', 'subfamily': 'clarinet_folk'},
        'woodwind':       {'weight': 0.04, 'evidence': 'FOLK_RIFF_MELODIC', 'subfamily': 'folk_woodwind'},
    },
    'bass': {
        # Direktan map — bass je bass
        'bass':           {'weight': 1.00, 'evidence': 'DIRECT_MAP', 'subfamily': 'electric_bass'},
    },
    'drums': {
        # Direktan map — drums je drums
        'drums':          {'weight': 1.00, 'evidence': 'DIRECT_MAP', 'subfamily': 'drum_kit'},
    },
    'percussion': {
        # Direktan map — percussion je percussion
        'percussion':     {'weight': 1.00, 'evidence': 'DIRECT_MAP', 'subfamily': 'hand_perc'},
    },
}

# Factory role → instrument familije sa težinama
# Factory je VELOCITY autoritet
FACTORY_ALIAS_MAP = {
    'chords': {
        # Factory chords = bilo koji chordal instrument
        # Piano/organ/accordion = najčešći comping
        # Rhythm guitar = strum chords
        'piano':          {'weight': 0.30, 'evidence': 'VELOCITY_CHORDAL_COMPING', 'subfamily': 'piano'},
        'rhythm_guitar':  {'weight': 0.20, 'evidence': 'VELOCITY_STRUM_CHORDS', 'subfamily': 'rhythm'},
        'organ':          {'weight': 0.15, 'evidence': 'VELOCITY_SUSTAIN_CHORD', 'subfamily': 'organ'},
        'accordion':      {'weight': 0.15, 'evidence': 'VELOCITY_CHORD_PUMP', 'subfamily': 'accordion'},
        'pad':            {'weight': 0.10, 'evidence': 'VELOCITY_SUSTAIN_BED', 'subfamily': 'pad'},
        'strings':        {'weight': 0.05, 'evidence': 'VELOCITY_SUSTAIN_ENSEMBLE', 'subfamily': 'ensemble'},
        'choir':          {'weight': 0.05, 'evidence': 'VELOCITY_VOCAL_TEXTURE', 'subfamily': 'choir'},
    },
    'melody': {
        # Factory melody = bilo koji melodijski instrument
        # Sax, clarinet, violin, solo_guitar su najčešći melodijski
        'sax':            {'weight': 0.25, 'evidence': 'VELOCITY_MELODIC_PHRASE', 'subfamily': 'saxophone'},
        'clarinet':       {'weight': 0.15, 'evidence': 'VELOCITY_FOLK_MELODIC', 'subfamily': 'clarinet_folk'},
        'violin':         {'weight': 0.15, 'evidence': 'VELOCITY_LEGATO_MELODIC', 'subfamily': 'violin_fiddle'},
        'solo_guitar':    {'weight': 0.15, 'evidence': 'VELOCITY_SOLO_PHRASE', 'subfamily': 'solo'},
        'synth_lead':     {'weight': 0.15, 'evidence': 'VELOCITY_SYNTH_LEAD', 'subfamily': 'lead'},
        'woodwind':       {'weight': 0.10, 'evidence': 'VELOCITY_FOLK_WIND', 'subfamily': 'folk_woodwind'},
        'brass':          {'weight': 0.05, 'evidence': 'VELOCITY_BRASS_SOLO', 'subfamily': 'section'},
    },
    'bass': {
        'bass':           {'weight': 1.00, 'evidence': 'DIRECT_MAP', 'subfamily': 'electric_bass'},
    },
    'drums': {
        'drums':          {'weight': 0.90, 'evidence': 'DIRECT_MAP', 'subfamily': 'drum_kit'},
        'percussion':    {'weight': 0.05, 'evidence': 'VELOCITY_PERC_HIT', 'subfamily': 'percussion'},
        'mallet':        {'weight': 0.05, 'evidence': 'VELOCITY_MALLET_HIT', 'subfamily': 'mallet'},
    },
}

# Inverzni map: instrument → [list of (source_role, source_type, weight)]
# Automatski generiran iz GOLD_ALIAS_MAP i FACTORY_ALIAS_MAP
def build_inverse_alias_map() -> Dict[str, List[Dict]]:
    """Napravi inverzni map: instrument → svi izvori podataka."""
    inverse = defaultdict(list)
    
    for gold_role, targets in GOLD_ALIAS_MAP.items():
        for inst, info in targets.items():
            inverse[inst].append({
                'sourceRole': gold_role,
                'sourceType': 'GOLD',
                'weight': info['weight'],
                'evidence': info['evidence'],
                'authority': 'TIMING+ARTICULATION+EXPRESSION',
            })
    
    for factory_role, targets in FACTORY_ALIAS_MAP.items():
        for inst, info in targets.items():
            inverse[inst].append({
                'sourceRole': factory_role,
                'sourceType': 'FACTORY',
                'weight': info['weight'],
                'evidence': info['evidence'],
                'authority': 'VELOCITY',
            })
    
    return dict(inverse)


# ══════════════════════════════════════════════════════════════════
# VELOCITY ALIAS RESOLVER
# ══════════════════════════════════════════════════════════════════

def resolve_velocity_from_aliases(
    instrument: str,
    factory_stats: dict,
    factory_catalog: dict
) -> Dict[str, Any]:
    """Resolve velocity profil za instrument koristeći Factory aliase.
    
    Pravila:
      - FACTORY je jedini VELOCITY autoritet (Master Prompt #24)
      - Ako instrument ima direktan Factory match (bass, drums), koristi direktno
      - Ako nema, koristi alias sa najvećom težinom iz FACTORY_ALIAS_MAP
      - Svaka vrijednost nosi: value, confidence, source, alias_source, sample_count
      - Confidence se modulira sa alias težinom: alias_confidence = base_conf * weight
    """
    inverse = build_inverse_alias_map()
    factory_sources = [s for s in inverse.get(instrument, []) if s['sourceType'] == 'FACTORY']
    
    if not factory_sources:
        return {
            'source': 'NO_FACTORY_ALIAS',
            'confidence': 0.0,
            'aliasChain': [],
            'message': f'Instrument "{instrument}" nema Factory alias — velocity mora biti definisana ručno'
        }
    
    # Sortiraj po težini (najveća prva)
    factory_sources.sort(key=lambda s: s['weight'], reverse=True)
    
    # Uzmi primarni izvor (najveća težina)
    primary = factory_sources[0]
    primary_role = primary['sourceRole']
    primary_weight = primary['weight']
    
    # Dobavi Factory statistiku za tu rolu
    role_stats = factory_stats.get(primary_role, {})
    catalog_data = factory_catalog.get('perRole', {}).get(primary_role, {})
    
    # Izračunaj velocity krivu
    if role_stats:
        base_confidence = role_stats.get('confidence', 0.5)
        vel_curve = {
            'pp':   role_stats.get('velocityFloor', {}).get('p50', 15),
            'p':    role_stats.get('velocitySoft', {}).get('p50', 50),
            'mp':   round((role_stats.get('velocitySoft', {}).get('p50', 50) + 
                          role_stats.get('velocityOptimal', {}).get('p50', 80)) / 2),
            'mf':   role_stats.get('velocityOptimal', {}).get('p50', 80),
            'f':    role_stats.get('velocityStrong', {}).get('p50', 100),
            'ff':   role_stats.get('velocityCeiling', {}).get('p50', 118),
            'fff':  role_stats.get('velocityCeiling', {}).get('p95', 127),
            'accent': role_stats.get('velocityStrong', {}).get('p75', 110),
            'ghost':  role_stats.get('velocityFloor', {}).get('p75', 30),
            'phrasePeak': role_stats.get('velocityStrong', {}).get('p50', 105),
        }
        sample_count = role_stats.get('profileCount', 0)
    elif catalog_data:
        # Fallback na catalog curve7Point
        curve = catalog_data.get('velocity', {}).get('curve7Point', {})
        base_confidence = 0.5
        vel_curve = {
            'pp':   curve.get('pp', 15),
            'p':    curve.get('p', 40),
            'mp':   curve.get('mp', 60),
            'mf':   curve.get('mf', 80),
            'f':    curve.get('f', 105),
            'ff':   curve.get('ff', 120),
            'fff':  127,
            'accent': 110,
            'ghost':  30,
            'phrasePeak': 105,
        }
        sample_count = catalog_data.get('profileCount', 0)
    else:
        base_confidence = 0.3
        vel_curve = {
            'pp': 15, 'p': 45, 'mp': 60, 'mf': 75, 'f': 100,
            'ff': 118, 'fff': 127, 'accent': 110, 'ghost': 30, 'phrasePeak': 105
        }
        sample_count = 0
    
    # Moduliraj confidence sa alias težinom
    alias_confidence = round(base_confidence * primary_weight, 4)
    
    # Dodaj instrument-specifične korekcije na velocity krivu
    VEL_ADJUSTMENTS = {
        'piano':         {'mf_offset': -5,  'accent_offset': +5},
        'organ':         {'mf_offset': 0,   'accent_offset': 0},
        'rhythm_guitar': {'mf_offset': -3,  'accent_offset': +8, 'ghost_offset': -5},
        'solo_guitar':   {'mf_offset': -5,  'accent_offset': +5, 'phrasePeak_offset': +5},
        'accordion':     {'mf_offset': -3,  'accent_offset': +3},
        'strings':       {'mf_offset': -5,  'accent_offset': 0},
        'brass':         {'mf_offset': +5,  'accent_offset': +10},
        'sax':           {'mf_offset': 0,   'accent_offset': +3},
        'clarinet':      {'mf_offset': 0,   'accent_offset': +5},
        'violin':        {'mf_offset': -3,  'accent_offset': +3},
        'synth_lead':    {'mf_offset': 0,   'accent_offset': 0},
        'pad':           {'mf_offset': -10, 'accent_offset': -15, 'f_offset': -10},
        'mallet':        {'mf_offset': +3,  'accent_offset': +8},
        'choir':         {'mf_offset': -8,  'accent_offset': -10, 'f_offset': -8},
    }
    
    adj = VEL_ADJUSTMENTS.get(instrument, {})
    for key, offset in adj.items():
        target_key = key.replace('_offset', '')
        if target_key in vel_curve:
            vel_curve[target_key] = max(1, min(127, vel_curve[target_key] + offset))
    
    # Sačuvaj alias lanac
    alias_chain = [
        {
            'sourceRole': s['sourceRole'],
            'weight': s['weight'],
            'evidence': s['evidence'],
            'contribution': 'PRIMARY' if i == 0 else 'SECONDARY'
        }
        for i, s in enumerate(factory_sources)
    ]
    
    return {
        **vel_curve,
        'source': f'FACTORY_ALIAS({primary_role})',
        'aliasSource': primary_role,
        'aliasWeight': primary_weight,
        'aliasEvidence': primary['evidence'],
        'aliasConfidence': alias_confidence,
        'baseConfidence': base_confidence,
        'confidence': alias_confidence,
        'sampleCount': sample_count,
        'aliasChain': alias_chain,
    }


# ══════════════════════════════════════════════════════════════════
# TIMING ALIAS RESOLVER
# ══════════════════════════════════════════════════════════════════

def resolve_timing_from_aliases(
    instrument: str,
    gold_stats: dict
) -> Dict[str, Any]:
    """Resolve timing profil za instrument koristeći Gold aliase.
    
    Pravila:
      - GOLD je TIMING/ARTICULATION/EXPRESSION autoritet
      - Ako instrument ima direktan Gold match (bass, drums), koristi direktno
      - Ako nema, koristi alias sa najvećom težinom iz GOLD_ALIAS_MAP
      - Confidence se modulira sa alias težinom
    """
    inverse = build_inverse_alias_map()
    gold_sources = [s for s in inverse.get(instrument, []) if s['sourceType'] == 'GOLD']
    
    if not gold_sources:
        return {
            'source': 'NO_GOLD_ALIAS',
            'confidence': 0.0,
            'aliasChain': [],
        }
    
    gold_sources.sort(key=lambda s: s['weight'], reverse=True)
    primary = gold_sources[0]
    primary_role = primary['sourceRole']
    primary_weight = primary['weight']
    
    role_stats = gold_stats.get(primary_role, {})
    if not role_stats:
        return {
            'source': f'GOLD_ALIAS({primary_role})',
            'confidence': 0.0,
            'aliasSource': primary_role,
            'aliasWeight': primary_weight,
            'aliasChain': [{'sourceRole': s['sourceRole'], 'weight': s['weight'], 'contribution': 'PRIMARY' if i == 0 else 'SECONDARY'} for i, s in enumerate(gold_sources)],
        }
    
    base_confidence = role_stats.get('confidence', 0.5)
    alias_confidence = round(base_confidence * primary_weight, 4)
    
    # Izvuci timing podatke
    offset_data = role_stats.get('offset', {})
    duration_data = role_stats.get('duration', {})
    meter_dist = role_stats.get('meterDistribution', {})
    
    # Base offset
    base_offset = offset_data.get('median', 0)
    early_range = abs(offset_data.get('p5', 0))
    late_range = abs(offset_data.get('p95', 0))
    
    # Swing detekcija
    swing = 0.0
    if '7/8' in meter_dist or '9/8' in meter_dist:
        swing = 0.15
    
    # Instrument-specifične timing korekcije
    TIMING_ADJUSTMENTS = {
        'piano':         {'humanization': 'SMALL_SPREAD', 'grooveProfile': 'COMPING'},
        'organ':         {'humanization': 'MINIMAL', 'grooveProfile': 'SUSTAIN_PULSE'},
        'rhythm_guitar': {'humanization': 'STRUM_SPREAD', 'grooveProfile': 'STRUM_PATTERN', 'earlyBias': 2},
        'solo_guitar':   {'humanization': 'EXPRESSIVE', 'grooveProfile': 'PHRASE_FLOW'},
        'accordion':     {'humanization': 'BELLOWS_HUMAN', 'grooveProfile': 'PULSE_PHRASE'},
        'strings':       {'humanization': 'MINIMAL', 'grooveProfile': 'SUSTAIN_FLOW'},
        'brass':         {'humanization': 'ACCENT_DRIVEN', 'grooveProfile': 'STAB_ACCENT'},
        'sax':           {'humanization': 'PHRASE_DRIVEN', 'grooveProfile': 'BREATH_PHRASE'},
        'clarinet':      {'humanization': 'ORNAMENT_DRIVEN', 'grooveProfile': 'FOLK_ORNAMENT'},
        'violin':        {'humanization': 'BOW_DRIVEN', 'grooveProfile': 'BOW_PHRASE'},
        'synth_lead':    {'humanization': 'PHRASE_DRIVEN', 'grooveProfile': 'LEAD_PHRASE'},
        'pad':           {'humanization': 'MINIMAL', 'grooveProfile': 'PAD_MOVEMENT'},
        'mallet':        {'humanization': 'TIGHT_HUMAN', 'grooveProfile': 'ARTICULATED'},
        'choir':         {'humanization': 'MINIMAL', 'grooveProfile': 'SLOW_ARC'},
        'percussion':    {'humanization': 'INTERLOCK', 'grooveProfile': 'INTERLOCK_PATTERN'},
    }
    
    timing_adj = TIMING_ADJUSTMENTS.get(instrument, {
        'humanization': 'MODERATE', 'grooveProfile': 'GENERIC'
    })
    
    # Early bias za rhythm guitar
    early_bias = timing_adj.pop('earlyBias', 0)
    if early_bias:
        base_offset -= early_bias
    
    return {
        'baseOffset': base_offset,
        'earlyLateRange': {'early': -early_range, 'late': late_range},
        'grooveProfile': timing_adj.get('grooveProfile', 'GENERIC'),
        'swing': swing,
        'humanization': timing_adj.get('humanization', 'MODERATE'),
        'phraseTiming': {
            'startOffset': offset_data.get('p25', 0),
            'endOffset': offset_data.get('p75', 0),
        },
        'gateMedian': duration_data.get('median', 0),
        'gateP5': duration_data.get('p5', 0),
        'gateP95': duration_data.get('p95', 0),
        'syncopationMedian': role_stats.get('offset', {}).get('sd', 0),  # SD offseta ≈ syncopation
        'meterDistribution': meter_dist,
        'sectionDistribution': role_stats.get('sectionDistribution', {}),
        'source': f'GOLD_ALIAS({primary_role})',
        'aliasSource': primary_role,
        'aliasWeight': primary_weight,
        'aliasEvidence': primary['evidence'],
        'aliasConfidence': alias_confidence,
        'baseConfidence': base_confidence,
        'confidence': alias_confidence,
        'sampleCount': role_stats.get('patternCount', 0),
        'aliasChain': [
            {'sourceRole': s['sourceRole'], 'weight': s['weight'], 'evidence': s['evidence'], 'contribution': 'PRIMARY' if i == 0 else 'SECONDARY'}
            for i, s in enumerate(gold_sources)
        ],
    }


# ══════════════════════════════════════════════════════════════════
# HARMONY ALIAS RESOLVER
# ══════════════════════════════════════════════════════════════════

def resolve_harmony_from_aliases(
    instrument: str,
    gold_stats: dict
) -> Dict[str, Any]:
    """Resolve harmony parametre koristeći Gold aliase + instrument spec."""
    inverse = build_inverse_alias_map()
    gold_sources = [s for s in inverse.get(instrument, []) if s['sourceType'] == 'GOLD']
    
    # Instrument-specifični harmony parametri (Master Prompt #4)
    HARMONY_WEIGHTS = {
        'bass':          {'root': 0.85, 'third': 0.10, 'fifth': 0.40, 'seventh': 0.08},
        'piano':         {'root': 0.40, 'third': 0.80, 'fifth': 0.70, 'seventh': 0.30},
        'organ':         {'root': 0.50, 'third': 0.70, 'fifth': 0.65, 'seventh': 0.25},
        'rhythm_guitar': {'root': 0.45, 'third': 0.75, 'fifth': 0.70, 'seventh': 0.20},
        'solo_guitar':   {'root': 0.30, 'third': 0.55, 'fifth': 0.45, 'seventh': 0.35},
        'accordion':     {'root': 0.50, 'third': 0.70, 'fifth': 0.65, 'seventh': 0.20},
        'strings':       {'root': 0.50, 'third': 0.70, 'fifth': 0.65, 'seventh': 0.30},
        'brass':         {'root': 0.55, 'third': 0.65, 'fifth': 0.60, 'seventh': 0.25},
        'sax':           {'root': 0.30, 'third': 0.55, 'fifth': 0.45, 'seventh': 0.35},
        'clarinet':      {'root': 0.30, 'third': 0.55, 'fifth': 0.45, 'seventh': 0.30},
        'violin':        {'root': 0.25, 'third': 0.50, 'fifth': 0.40, 'seventh': 0.30},
        'synth_lead':    {'root': 0.30, 'third': 0.50, 'fifth': 0.40, 'seventh': 0.30},
        'pad':           {'root': 0.50, 'third': 0.75, 'fifth': 0.70, 'seventh': 0.30},
        'mallet':        {'root': 0.40, 'third': 0.55, 'fifth': 0.50, 'seventh': 0.15},
        'choir':         {'root': 0.50, 'third': 0.75, 'fifth': 0.70, 'seventh': 0.30},
        'percussion':    {'root': 0.10, 'third': 0.05, 'fifth': 0.05, 'seventh': 0.02},
        'fx':            {'root': 0.10, 'third': 0.05, 'fifth': 0.05, 'seventh': 0.02},
    }
    
    weights = HARMONY_WEIGHTS.get(instrument, {'root': 0.40, 'third': 0.60, 'fifth': 0.55, 'seventh': 0.20})
    
    # Passing/approach/chromatic rate
    PASSING_RATES = {
        'bass': 0.12, 'sax': 0.25, 'clarinet': 0.20, 'violin': 0.18,
        'solo_guitar': 0.22, 'synth_lead': 0.20, 'piano': 0.08, 'rhythm_guitar': 0.05,
        'organ': 0.05, 'accordion': 0.06, 'strings': 0.05, 'brass': 0.08,
        'pad': 0.02, 'choir': 0.02, 'mallet': 0.10, 'woodwind': 0.15,
    }
    
    CHROMATIC_RATES = {
        'bass': 0.05, 'sax': 0.10, 'clarinet': 0.12, 'violin': 0.08,
        'solo_guitar': 0.10, 'synth_lead': 0.08, 'accordion': 0.08,
        'piano': 0.03, 'rhythm_guitar': 0.03, 'brass': 0.05,
    }
    
    # Chord quality distribucija iz Gold ako postoji
    chord_quality = {}
    if gold_sources:
        primary_role = gold_sources[0]['sourceRole']
        role_stats = gold_stats.get(primary_role, {})
        chord_quality = role_stats.get('chordQualityDistribution', {})
    
    return {
        'rootWeight': weights['root'],
        'thirdWeight': weights['third'],
        'fifthWeight': weights['fifth'],
        'seventhWeight': weights['seventh'],
        'chordToneWeight': round((weights['root'] + weights['third'] + weights['fifth']) / 3, 3),
        'passingNoteRate': PASSING_RATES.get(instrument, 0.08),
        'chromaticRate': CHROMATIC_RATES.get(instrument, 0.03),
        'chordQualityDistribution': chord_quality,
        'source': 'GOLD_ALIAS+INSTRUMENT_SPEC',
        'confidence': gold_sources[0]['weight'] * 0.7 if gold_sources else 0.3,
    }


# ══════════════════════════════════════════════════════════════════
# ARTICULATION/EXPRESSION ALIAS RESOLVER
# ══════════════════════════════════════════════════════════════════

def resolve_articulation_from_aliases(
    instrument: str,
    gold_stats: dict
) -> Dict[str, Any]:
    """Resolve articulaciju koristeći Gold gate/syncopation podatke + instrument spec."""
    inverse = build_inverse_alias_map()
    gold_sources = [s for s in inverse.get(instrument, []) if s['sourceType'] == 'GOLD']
    
    # Instrument-specifični articulacijski parametri
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
        'synth_lead':    {'legato': 0.4, 'staccato': 0.2, 'accent': 0.3, 'glide': 0.15, 'grace': 0.05},
        'pad':           {'legato': 0.9, 'staccato': 0.02, 'accent': 0.1, 'ghost': 0.01},
        'mallet':        {'legato': 0.3, 'staccato': 0.3, 'accent': 0.5, 'grace': 0.05},
        'choir':         {'legato': 0.9, 'staccato': 0.02, 'accent': 0.1},
        'drums':         {'legato': 0.0, 'staccato': 0.9, 'accent': 0.5, 'ghost': 0.2, 'flam': 0.05, 'roll': 0.03, 'choke': 0.04},
        'percussion':    {'legato': 0.0, 'staccato': 0.7, 'accent': 0.4, 'ghost': 0.2, 'flam': 0.08},
        'fx':            {'accent': 0.3, 'staccato': 0.5},
    }
    
    art = ARTIC.get(instrument, {'legato': 0.3, 'staccato': 0.2, 'accent': 0.3, 'grace': 0.05})
    
    # Release behavior
    RELEASE = {
        'bass': 'CONTROLLED_DECAY', 'piano': 'NATURAL_DECAY', 'organ': 'SHARP_CUT_OR_SUSTAIN',
        'strings': 'BOW_RELEASE', 'brass': 'BREATH_RELEASE', 'sax': 'BREATH_RELEASE',
        'rhythm_guitar': 'MUTE_OR_DECAY', 'solo_guitar': 'FRET_NOISE_OR_DECAY',
        'accordion': 'BELLOWS_CONTROLLED', 'pad': 'SLOW_FADE', 'choir': 'BREATH_RELEASE',
        'violin': 'BOW_RELEASE', 'clarinet': 'BREATH_RELEASE', 'synth_lead': 'ENVELOPE_DECAY',
        'mallet': 'NATURAL_DECAY',
    }
    
    # Gate evidence iz Gold ako postoji
    gate_evidence = {}
    if gold_sources:
        primary_role = gold_sources[0]['sourceRole']
        role_stats = gold_stats.get(primary_role, {})
        gate_evidence = {
            'gateMedian': role_stats.get('duration', {}).get('median', 0),
            'gateP5': role_stats.get('duration', {}).get('p5', 0),
            'gateP95': role_stats.get('duration', {}).get('p95', 0),
            'aliasSource': primary_role,
            'aliasWeight': gold_sources[0]['weight'],
        }
    
    return {
        **art,
        'releaseBehavior': RELEASE.get(instrument, 'NATURAL_DECAY'),
        'dnC_RX_Aware': instrument in ['solo_guitar', 'rhythm_guitar', 'sax', 'brass', 'strings', 'violin'],
        'gateEvidence': gate_evidence,
        'source': 'GOLD_ALIAS+INSTRUMENT_SPEC',
        'confidence': gold_sources[0]['weight'] * 0.7 if gold_sources else 0.4,
    }


def resolve_expression_from_aliases(instrument: str) -> Dict[str, Any]:
    """Resolve expression (CC11, swell) za instrument."""
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
        'rhythm_guitar': {'cc11_rate': 'LOW', 'swell': 'RARE', 'phraseCurve': 'GROOVE_ALIGNED'},
        'solo_guitar':   {'cc11_rate': 'MEDIUM', 'swell': 'PHRASE_END', 'phraseCurve': 'PHRASE_ARC'},
        'accordion':     {'cc11_rate': 'MEDIUM', 'swell': 'BELLOWS_DRIVEN', 'phraseCurve': 'PULSE_PHRASE'},
        'synth_lead':    {'cc11_rate': 'MEDIUM', 'swell': 'PHRASE_END', 'phraseCurve': 'PHRASE_ARC'},
        'mallet':        {'cc11_rate': 'NONE', 'swell': 'RARE', 'phraseCurve': 'VELOCITY_DRIVEN'},
        'percussion':    {'cc11_rate': 'NONE', 'swell': 'RARE', 'phraseCurve': 'NONE'},
        'drums':         {'cc11_rate': 'NONE', 'swell': 'NONE', 'phraseCurve': 'NONE'},
        'fx':            {'cc11_rate': 'NONE', 'swell': 'NONE', 'phraseCurve': 'EVENT_DRIVEN'},
    }
    
    expr = EXPRESSION_MAP.get(instrument, {'cc11_rate': 'LOW', 'swell': 'RARE', 'phraseCurve': 'DEFAULT'})
    
    return {
        'cc11': expr['cc11_rate'],
        'swell': expr['swell'],
        'phraseCurve': expr['phraseCurve'],
        'accentExpression': 'VELOCITY_BASED' if instrument not in ['organ', 'strings', 'choir', 'pad'] else 'CC11_BASED',
        'dynamicContour': 'PHRASE_ARC',
        'sectionEnergy': {'intro': 0.4, 'body': 0.6, 'transition': 0.75, 'ending': 0.3},
        'source': 'INSTRUMENT_SPEC',
        'confidence': 0.7,
    }


# ══════════════════════════════════════════════════════════════════
# SECTION BEHAVIOR ALIAS RESOLVER
# ══════════════════════════════════════════════════════════════════

def resolve_section_behavior_from_aliases(
    instrument: str,
    gold_stats: dict
) -> Dict[str, Any]:
    """Resolve section behavior koristeći Gold sekcije + instrument spec."""
    inverse = build_inverse_alias_map()
    gold_sources = [s for s in inverse.get(instrument, []) if s['sourceType'] == 'GOLD']
    
    # Instrument-specific section behavior defaults
    SECTION_DEFAULTS = {
        'bass': {'intro': 'ESTABLISH_ROOT', 'variation': 'GROOVE_WITH_VARIATION', 'fill': 'WALK_OR_REST', 'break': 'REST_OR_ACCENT', 'ending': 'DESCEND_OR_SUSTAIN'},
        'drums': {'intro': 'ESTABLISH_GROOVE_OR_PICKUP', 'variation': 'DENSITY_CHANGE', 'fill': 'FILL_PATTERN', 'break': 'BREAK_PATTERN', 'ending': 'FINAL_FILL_OR_CRASH'},
        'piano': {'intro': 'ESTABLISH_CHORD_OR_PICKUP', 'variation': 'COMPING_VARIATION', 'fill': 'ANSWER_OR_REST', 'break': 'SUSTAIN_OR_REST', 'ending': 'FINAL_VOICING'},
        'organ': {'intro': 'SUSTAIN_OR_SILENT', 'variation': 'REGISTRATION_CHANGE', 'fill': 'SUSTAIN_OR_STAB', 'break': 'SUSTAIN', 'ending': 'FADE_OR_SUSTAIN'},
        'rhythm_guitar': {'intro': 'ESTABLISH_CHORD_OR_REST', 'variation': 'PATTERN_CHANGE', 'fill': 'ANSWER_OR_REST', 'break': 'MUTE_OR_REST', 'ending': 'FINAL_STRUM'},
        'solo_guitar': {'intro': 'REST_OR_PICKUP', 'variation': 'SOLO_PHRASE', 'fill': 'LICK_OR_REST', 'break': 'FEATURE_OR_REST', 'ending': 'DESCEND_OR_REST'},
        'accordion': {'intro': 'ESTABLISH_PUMP_OR_REST', 'variation': 'PATTERN_VARIATION', 'fill': 'BELLOWS_FILL', 'break': 'SUSTAIN_OR_REST', 'ending': 'FINAL_CHORD'},
        'strings': {'intro': 'SUSTAIN_OR_SILENT', 'variation': 'SUSTAIN_WITH_MOVEMENT', 'fill': 'SUSTAIN_OR_CREST', 'break': 'SUSTAIN', 'ending': 'FADE_OR_SUSTAIN'},
        'brass': {'intro': 'REST_OR_SUSTAIN', 'variation': 'STAB_ACCENT', 'fill': 'STAB_FILL', 'break': 'REST_OR_ACCENT', 'ending': 'FINAL_STAB_OR_SUSTAIN'},
        'sax': {'intro': 'REST_OR_PICKUP', 'variation': 'PHRASE_COUNTER', 'fill': 'PHRASE_ENDING', 'break': 'REST_OR_LICK', 'ending': 'DESCEND_OR_REST'},
        'clarinet': {'intro': 'REST_OR_PICKUP', 'variation': 'ORNAMENT_PHRASE', 'fill': 'FILL_PHRASE', 'break': 'REST_OR_ORNAMENT', 'ending': 'DESCEND_OR_REST'},
        'violin': {'intro': 'REST_OR_PICKUP', 'variation': 'LEGATO_PHRASE', 'fill': 'FILL_OR_REST', 'break': 'REST_OR_SOLO', 'ending': 'DESCEND_OR_REST'},
        'synth_lead': {'intro': 'REST_OR_PAD', 'variation': 'PHRASE_VARIATION', 'fill': 'FILL_PHRASE', 'break': 'REST_OR_FEATURE', 'ending': 'DESCEND_OR_REST'},
        'pad': {'intro': 'SUSTAIN_OR_SILENT', 'variation': 'HARMONY_MOVEMENT', 'fill': 'SUSTAIN', 'break': 'SUSTAIN', 'ending': 'FADE'},
        'mallet': {'intro': 'REST_OR_PICKUP', 'variation': 'ARPEGGIO_VARIATION', 'fill': 'FILL_PATTERN', 'break': 'REST_OR_FEATURE', 'ending': 'FINAL_HIT'},
        'choir': {'intro': 'SUSTAIN_OR_SILENT', 'variation': 'HARMONY_MOVEMENT', 'fill': 'SUSTAIN', 'break': 'SUSTAIN', 'ending': 'FADE_OR_SUSTAIN'},
        'percussion': {'intro': 'PICKUP_OR_REST', 'variation': 'PATTERN_VARIATION', 'fill': 'FILL_PATTERN', 'break': 'BREAK_PATTERN', 'ending': 'FINAL_HIT'},
    }
    
    defaults = SECTION_DEFAULTS.get(instrument, {
        'intro': 'ESTABLISH_OR_REST', 'variation': 'FOLLOW_SECTION',
        'fill': 'ANSWER_OR_REST', 'break': 'REST_OR_SUSTAIN', 'ending': 'RELEASE',
    })
    
    # Gold section evidence
    sec_evidence = {}
    if gold_sources:
        primary_role = gold_sources[0]['sourceRole']
        role_stats = gold_stats.get(primary_role, {})
        sec_evidence = role_stats.get('sectionDistribution', {})
    
    return {
        'intro': defaults.get('intro', 'REST'),
        'variation1': defaults.get('variation', 'FOLLOW_SECTION'),
        'variation2': defaults.get('variation', 'INCREASE_DENSITY'),
        'variation3': defaults.get('variation', 'ADD_ORNAMENTS'),
        'variation4': defaults.get('variation', 'PEAK_ENERGY'),
        'fill': defaults.get('fill', 'ANSWER_OR_REST'),
        'break': defaults.get('break', 'REST_OR_SUSTAIN'),
        'ending': defaults.get('ending', 'RELEASE'),
        'goldSectionEvidence': sec_evidence,
        'source': 'GOLD_ALIAS+INSTRUMENT_SPEC',
        'confidence': gold_sources[0]['weight'] * 0.6 if gold_sources else 0.3,
    }


# ══════════════════════════════════════════════════════════════════
# NOTE BEHAVIOR ALIAS RESOLVER
# ══════════════════════════════════════════════════════════════════

def resolve_note_behavior_from_aliases(
    instrument: str,
    gold_stats: dict
) -> Dict[str, Any]:
    """Resolve note behavior (density, length, rest, overlap, sustain)."""
    inverse = build_inverse_alias_map()
    gold_sources = [s for s in inverse.get(instrument, []) if s['sourceType'] == 'GOLD']
    
    # Gold-based density/duration ako postoji
    density_data = {}
    duration_data = {}
    if gold_sources:
        primary_role = gold_sources[0]['sourceRole']
        role_stats = gold_stats.get(primary_role, {})
        density_data = role_stats.get('density', {})
        duration_data = role_stats.get('duration', {})
    
    # Instrument-specific note behavior
    HIGH_REPEAT = ['drums', 'percussion', 'rhythm_guitar', 'bass']
    MED_REPEAT = ['piano', 'organ', 'accordion', 'pad']
    LOW_REPEAT = ['sax', 'violin', 'clarinet', 'solo_guitar', 'brass']
    
    HIGH_OVERLAP = ['organ', 'strings', 'pad', 'choir', 'accordion']
    HIGH_SUST = ['strings', 'pad', 'choir', 'organ']
    MED_SUST = ['bass', 'sax', 'violin', 'synth_lead']
    LOW_SUST = ['drums', 'percussion', 'brass', 'rhythm_guitar', 'mallet']
    
    return {
        'density': {
            'mean': density_data.get('mean', 8),
            'median': density_data.get('median', 8),
            'p5': density_data.get('p5', 2),
            'p95': density_data.get('p95', 20),
        },
        'repetition': 0.6 if instrument in HIGH_REPEAT else (0.4 if instrument in MED_REPEAT else 0.15),
        'restProbability': _estimate_rest_prob(instrument, density_data),
        'noteLength': {
            'short': duration_data.get('p25', 6),
            'medium': duration_data.get('median', 12),
            'long': duration_data.get('p75', 23),
            'distribution': {'shortRatio': 0.3, 'mediumRatio': 0.5, 'longRatio': 0.2},
            'source': 'GOLD_ALIAS_DURATION' if duration_data else 'ESTIMATED',
        },
        'overlap': 0.6 if instrument in HIGH_OVERLAP else 0.15,
        'sustain': 0.8 if instrument in HIGH_SUST else (0.5 if instrument in MED_SUST else 0.2),
        'source': f'GOLD_ALIAS({gold_sources[0]["sourceRole"]})+INSTRUMENT_SPEC' if gold_sources else 'ESTIMATED',
        'confidence': gold_sources[0]['weight'] * 0.7 if gold_sources else 0.3,
    }


def _estimate_rest_prob(instrument: str, density_data: dict) -> float:
    median_density = density_data.get('median', 8)
    REST_DEFAULTS = {
        'bass': max(0.1, 0.5 - median_density * 0.03),
        'pad': 0.05, 'choir': 0.05, 'organ': 0.05, 'strings': 0.05,
        'drums': max(0.05, 0.3 - median_density * 0.02),
    }
    return REST_DEFAULTS.get(instrument, 0.25)


# ══════════════════════════════════════════════════════════════════
# INTERACTION ALIAS RESOLVER
# ══════════════════════════════════════════════════════════════════

def resolve_interaction_from_aliases(instrument: str) -> Dict[str, Any]:
    """Resolve interakcije sa drugim instrumentima."""
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
        'organ': {
            'chordRelationship': {'with': 'chord', 'type': 'SUSTAIN_VOICING', 'priority': 'HIGH'},
            'bassRelationship': {'with': 'bass', 'type': 'REGISTER_AVOID', 'priority': 'HIGH'},
        },
        'accordion': {
            'chordRelationship': {'with': 'chord', 'type': 'PUMP_VOICING', 'priority': 'HIGH'},
            'bassRelationship': {'with': 'bass', 'type': 'REGISTER_AVOID', 'priority': 'MEDIUM'},
        },
        'strings': {
            'chordRelationship': {'with': 'chord', 'type': 'HARMONIC_BED', 'priority': 'HIGH'},
            'vocalSpace': {'type': 'FREQ_AVOID', 'priority': 'MEDIUM'},
        },
        'brass': {
            'chordRelationship': {'with': 'chord', 'type': 'STAB_ACCENT', 'priority': 'MEDIUM'},
            'drumRelationship': {'with': 'drums', 'type': 'ACCENT_ALIGN', 'priority': 'MEDIUM'},
        },
        'sax': {
            'vocalSpace': {'type': 'MELODY_AVOID', 'priority': 'HIGH'},
            'chordRelationship': {'with': 'chord', 'type': 'COUNTER_MELODY', 'priority': 'MEDIUM'},
        },
        'clarinet': {
            'vocalSpace': {'type': 'MELODY_AVOID', 'priority': 'HIGH'},
            'chordRelationship': {'with': 'chord', 'type': 'COUNTER_MELODY', 'priority': 'MEDIUM'},
        },
        'violin': {
            'vocalSpace': {'type': 'MELODY_AVOID', 'priority': 'HIGH'},
            'chordRelationship': {'with': 'chord', 'type': 'MELODIC_COUNTER', 'priority': 'MEDIUM'},
        },
        'solo_guitar': {
            'vocalSpace': {'type': 'MELODY_AVOID', 'priority': 'MEDIUM'},
            'chordRelationship': {'with': 'chord', 'type': 'SOLO_OVER', 'priority': 'HIGH'},
        },
        'synth_lead': {
            'vocalSpace': {'type': 'MELODY_AVOID', 'priority': 'MEDIUM'},
            'chordRelationship': {'with': 'chord', 'type': 'MELODIC_COUNTER', 'priority': 'MEDIUM'},
        },
        'pad': {
            'chordRelationship': {'with': 'chord', 'type': 'HARMONIC_BED', 'priority': 'HIGH'},
        },
        'choir': {
            'chordRelationship': {'with': 'chord', 'type': 'HARMONIC_BED', 'priority': 'HIGH'},
        },
        'mallet': {
            'chordRelationship': {'with': 'chord', 'type': 'ARPEGGIATED_ACCENT', 'priority': 'MEDIUM'},
            'drumRelationship': {'with': 'drums', 'type': 'ACCENT_ALIGN', 'priority': 'MEDIUM'},
        },
        'percussion': {
            'drumRelationship': {'with': 'drums', 'type': 'INTERLOCK', 'priority': 'HIGH'},
        },
        'fx': {
            'sectionRelationship': {'with': 'section', 'type': 'EVENT_TRIGGER', 'priority': 'HIGH'},
        },
    }
    
    interaction = INTERACTIONS.get(instrument, {
        'chordRelationship': {'with': 'chord', 'type': 'FOLLOW', 'priority': 'MEDIUM'},
    })
    
    FREQ_MAP = {
        'bass': '20-250Hz', 'drums': '50-5000Hz', 'piano': '80-4000Hz',
        'rhythm_guitar': '100-2500Hz', 'strings': '200-8000Hz', 'brass': '200-3000Hz',
        'sax': '200-1500Hz', 'violin': '300-5000Hz', 'pad': '100-4000Hz',
        'organ': '80-6000Hz', 'accordion': '100-4000Hz', 'clarinet': '200-2000Hz',
        'solo_guitar': '200-3000Hz', 'synth_lead': '100-5000Hz', 'mallet': '200-5000Hz',
        'choir': '200-4000Hz', 'percussion': '100-5000Hz', 'fx': '20-20000Hz',
    }
    
    interaction['frequencyCompetition'] = FREQ_MAP.get(instrument, '100-3000Hz')
    interaction['source'] = 'INSTRUMENT_SPEC'
    interaction['confidence'] = 0.7
    return interaction


# ══════════════════════════════════════════════════════════════════
# CONFIDENCE ALIAS RESOLVER
# ══════════════════════════════════════════════════════════════════

def resolve_confidence_from_aliases(
    instrument: str,
    gold_stats: dict,
    factory_stats: dict
) -> Dict[str, Any]:
    """Resolve confidence report za instrument sa alias informacijama."""
    inverse = build_inverse_alias_map()
    gold_sources = [s for s in inverse.get(instrument, []) if s['sourceType'] == 'GOLD']
    factory_sources = [s for s in inverse.get(instrument, []) if s['sourceType'] == 'FACTORY']
    
    # Gold sample count
    gold_n = 0
    gold_role = None
    if gold_sources:
        gold_role = gold_sources[0]['sourceRole']
        gold_n = gold_stats.get(gold_role, {}).get('patternCount', 0)
    
    # Factory sample count
    factory_n = 0
    factory_role = None
    if factory_sources:
        factory_role = factory_sources[0]['sourceRole']
        factory_n = factory_stats.get(factory_role, {}).get('profileCount', 0)
    
    # Overall confidence — modulirano sa alias težinama
    gold_weight = gold_sources[0]['weight'] if gold_sources else 0
    factory_weight = factory_sources[0]['weight'] if factory_sources else 0
    
    gold_base = _conf(gold_n) if gold_n > 0 else 0.0
    factory_base = _conf(factory_n, k=100) if factory_n > 0 else 0.0
    
    overall = round(
        max(gold_base * gold_weight, factory_base * factory_weight),
        4
    )
    
    # Per-section confidence
    vel_conf = round(factory_base * factory_weight, 4) if factory_sources else 0.0
    time_conf = round(gold_base * gold_weight, 4) if gold_sources else 0.0
    
    flags = []
    if gold_n < 50:
        flags.append('LOW_GOLD_SAMPLES')
    if factory_n < 30:
        flags.append('LOW_FACTORY_SAMPLES')
    if gold_weight < 0.5:
        flags.append('WEAK_GOLD_ALIAS')
    if factory_weight < 0.5:
        flags.append('WEAK_FACTORY_ALIAS')
    if not gold_sources and not factory_sources:
        flags.append('NO_ALIAS_DATA')
    
    return {
        'overallConfidence': overall,
        'goldSampleCount': gold_n,
        'factorySampleCount': factory_n,
        'goldAliasSource': gold_role,
        'goldAliasWeight': gold_weight,
        'factoryAliasSource': factory_role,
        'factoryAliasWeight': factory_weight,
        'perSection': {
            'identity': {'confidence': 0.95, 'source': 'BEHAVIOR+SPEC'},
            'range': {'confidence': 0.85, 'source': 'PA800+GM_SPEC'},
            'velocity': {'confidence': vel_conf, 'source': f'FACTORY_ALIAS({factory_role})' if factory_role else 'NONE'},
            'timing': {'confidence': time_conf, 'source': f'GOLD_ALIAS({gold_role})' if gold_role else 'NONE'},
            'noteBehavior': {'confidence': round(time_conf * 0.8, 4), 'source': f'GOLD_ALIAS({gold_role})' if gold_role else 'ESTIMATED'},
            'harmony': {'confidence': round(max(time_conf * 0.7, 0.3), 4), 'source': 'GOLD_ALIAS+SPEC'},
            'rhythm': {'confidence': round(time_conf * 0.8, 4), 'source': 'GOLD_ALIAS+INFERENCE'},
            'articulation': {'confidence': round(time_conf * 0.7, 4), 'source': 'GOLD_ALIAS+SPEC'},
            'expression': {'confidence': 0.6, 'source': 'INSTRUMENT_SPEC'},
            'sectionBehavior': {'confidence': round(time_conf * 0.6, 4), 'source': 'GOLD_ALIAS+DEFAULTS'},
            'interaction': {'confidence': 0.7, 'source': 'INSTRUMENT_SPEC'},
            'pa800Behavior': {'confidence': 0.85, 'source': 'PA800_SPEC+GENERAL_RULES'},
        },
        'lowConfidenceFlags': flags,
    }


def _conf(n, min_c=0.1, max_c=0.99, k=50):
    """Confidence iz broja uzoraka."""
    if n == 0:
        return 0.0
    return round(min_c + (max_c - min_c) * (1 - math.exp(-n / k)), 4)


# ══════════════════════════════════════════════════════════════════
# COMPLETE ALIAS-RESOLVED PROFILE BUILDER
# ══════════════════════════════════════════════════════════════════

def build_alias_resolved_profile(
    instrument: str,
    gold_stats: dict,
    factory_stats: dict,
    factory_catalog: dict,
    general_rules: dict,
    instrument_families: dict,
    pa800_track_map: dict,
) -> Dict[str, Any]:
    """Napravi kompletan profil sa alias-resolved podacima.
    
    Ovo je GLAVNA funkcija — zamjenjuje stari build_instrument_profile
    sa alias-aware verzijom koja koristi sve raspoložive podatke.
    """
    family_info = instrument_families.get(instrument, {
        'family': 'unknown', 'subfamily': 'unknown',
        'priority_order': ['chord_voicing', 'rhythm', 'velocity', 'timing']
    })
    
    pa8 = pa800_track_map.get(instrument, {'trackType': 'ACC5', 'ntt': 'Chord', 'guitarMode': None})
    
    # ── 1. IDENTITY ──
    identity = {
        'family': family_info['family'],
        'subfamily': family_info['subfamily'],
        'instrumentRole': _map_arrangement_role(instrument),
        'musicalRole': _describe_musical_role(instrument),
        'pa800SoundClass': pa8['trackType'],
        'register': _register_label(instrument),
        'priority': family_info['priority_order'],
        'playerModel': f'{instrument}_player',
    }
    
    # ── 2. RANGE ──
    range_data = _build_range(instrument)
    
    # ── 3. VELOCITY (FACTORY ALIAS) ──
    velocity_data = resolve_velocity_from_aliases(instrument, factory_stats, factory_catalog)
    
    # ── 4. TIMING (GOLD ALIAS) ──
    timing_data = resolve_timing_from_aliases(instrument, gold_stats)
    
    # ── 5. NOTE_BEHAVIOR (GOLD ALIAS) ──
    note_data = resolve_note_behavior_from_aliases(instrument, gold_stats)
    
    # ── 6. HARMONY (GOLD ALIAS + SPEC) ──
    harmony_data = resolve_harmony_from_aliases(instrument, gold_stats)
    
    # ── 7. RHYTHM (GOLD ALIAS) ──
    rhythm_data = _build_rhythm(instrument, gold_stats)
    
    # ── 8. ARTICULATION (GOLD ALIAS + SPEC) ──
    articulation_data = resolve_articulation_from_aliases(instrument, gold_stats)
    
    # ── 9. EXPRESSION (SPEC) ──
    expression_data = resolve_expression_from_aliases(instrument)
    
    # ── 10. SECTION_BEHAVIOR (GOLD ALIAS + SPEC) ──
    section_data = resolve_section_behavior_from_aliases(instrument, gold_stats)
    
    # ── 11. INTERACTION (SPEC) ──
    interaction_data = resolve_interaction_from_aliases(instrument)
    
    # ── 12. PA800_BEHAVIOR ──
    pa800_data = _build_pa800(instrument, pa8, general_rules)
    
    # ── 13. CONFIDENCE_REPORT (ALIAS-RESOLVED) ──
    confidence_data = resolve_confidence_from_aliases(instrument, gold_stats, factory_stats)
    
    profile = {
        'schema': 'dna-instrument-playing-profile',
        'version': VERSION,
        'role': instrument,
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
        'confidence': confidence_data,
    }
    
    # Human-readable opis
    profile['howItPlays'] = _generate_how_it_plays(profile)
    
    return profile


# ── Helper funkcije (identične originalnom engineu) ──

def _map_arrangement_role(role):
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


def _build_range(role):
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
        'absoluteMin': r['min'], 'absoluteMax': r['max'],
        'practicalMin': r['pracMin'], 'practicalMax': r['pracMax'],
        'preferredLow': r['prefLow'], 'preferredMid': r['prefMid'], 'preferredHigh': r['prefHigh'],
        'source': 'FACTORY+GM_SPEC' if role in ABS_RANGES else 'ESTIMATED',
        'confidence': 0.85,
    }


def _build_rhythm(role, gold_stats):
    inverse = build_inverse_alias_map()
    gold_sources = [s for s in inverse.get(role, []) if s['sourceType'] == 'GOLD']
    
    PATTERN_TYPES = {
        'bass': 'ROOT_PULSE', 'drums': 'GROOVE_PATTERN', 'piano': 'COMPING',
        'rhythm_guitar': 'STRUM_PATTERN', 'accordion': 'CHORD_PULSE',
        'organ': 'CHORD_PULSE', 'strings': 'SUSTAIN', 'brass': 'STAB',
        'sax': 'PHRASE', 'clarinet': 'ORNAMENT_PHRASE', 'violin': 'BOW_PHRASE',
        'pad': 'SUSTAIN', 'mallet': 'ARPEGGIATED',
    }
    
    SYNCOPATION = {
        'bass': 0.15, 'drums': 0.20, 'piano': 0.25, 'rhythm_guitar': 0.30,
        'sax': 0.20, 'clarinet': 0.15, 'violin': 0.10, 'solo_guitar': 0.25,
    }
    
    SUBDIVISION = {
        'bass': 'QUARTER_EIGHTH', 'drums': 'SIXTEENTH', 'piano': 'EIGHTH',
        'rhythm_guitar': 'SIXTEENTH', 'accordion': 'EIGHTH_SIXTEENTH',
        'sax': 'EIGHTH_TRIPLET', 'clarinet': 'SIXTEENTH_ORNAMENT',
    }
    
    OFFBEAT = {
        'rhythm_guitar': 0.45, 'piano': 0.25, 'drums': 0.30,
        'percussion': 0.40, 'bass': 0.10,
    }
    
    meter_dist = {}
    if gold_sources:
        primary_role = gold_sources[0]['sourceRole']
        role_data = gold_stats.get(primary_role, {})
        meter_dist = role_data.get('meterDistribution', {})
    
    return {
        'patternType': PATTERN_TYPES.get(role, 'GENERIC'),
        'syncopation': SYNCOPATION.get(role, 0.10),
        'accentMap': _default_accent_map(role),
        'subdivisionPreference': SUBDIVISION.get(role, 'QUARTER'),
        'offbeatProbability': OFFBEAT.get(role, 0.10),
        'pickupProbability': 0.10 if role in ['bass', 'sax', 'violin'] else 0.05,
        'restPlacement': 'WEAK_BEATS' if role == 'bass' else 'PHRASE_END',
        'meterDistribution': meter_dist,
        'source': f'GOLD_ALIAS+INFERENCE' if gold_sources else 'INFERENCE',
        'confidence': gold_sources[0]['weight'] * 0.6 if gold_sources else 0.3,
    }


def _default_accent_map(role):
    if role == 'bass':
        return {'beat1': 1.0, 'beat2': 0.5, 'beat3': 0.8, 'beat4': 0.4}
    elif role == 'drums':
        return {'beat1': 1.0, 'beat2': 0.3, 'beat3': 0.3, 'beat4': 0.9}
    elif role == 'rhythm_guitar':
        return {'beat1': 0.8, 'and1': 0.6, 'beat2': 0.4, 'and2': 0.5, 'beat3': 0.7, 'beat4': 0.4}
    return {'beat1': 0.8, 'beat2': 0.5, 'beat3': 0.7, 'beat4': 0.5}


def _build_pa800(role, pa8_info, general_rules):
    NTT_TYPES = {'Parallel': 'MELODIC_TRANSPOSITION', 'Fixed': 'MINIMAL_MOVEMENT',
                'Chord': 'CHORD_TONE_FOLLOW', 'Root': 'ROOT_ANCHOR', 'Fifth': 'POWER_CHORD'}
    ntt_rec = pa8_info.get('ntt', 'Chord')
    RX_DNC = ['solo_guitar', 'rhythm_guitar', 'sax', 'brass', 'strings', 'violin']
    rx_dnc = role in RX_DNC
    return {
        'trackType': pa8_info['trackType'],
        'ntt': ntt_rec,
        'chordVariation': NTT_TYPES.get(ntt_rec, 'DEFAULT'),
        'guitarMode': pa8_info.get('guitarMode'),
        'rx': rx_dnc, 'dnc': rx_dnc,
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


def _generate_how_it_plays(profile: dict) -> str:
    role = profile['role']
    identity = profile['identity']
    velocity = profile['velocity']
    timing = profile['timing']
    harmony = profile['harmony']
    articulation = profile['articulation']
    section = profile['sectionBehavior']
    interaction = profile['interaction']
    
    parts = [f"{identity['musicalRole']}."]
    
    # Alias info
    vel_src = velocity.get('source', '?')
    tim_src = timing.get('source', '?')
    if 'ALIAS' in vel_src:
        parts.append(f'velocity inherited from {velocity.get("aliasSource", "?")} role (weight {velocity.get("aliasWeight", 0):.0%})')
    if 'ALIAS' in tim_src:
        parts.append(f'timing inherited from {timing.get("aliasSource", "?")} role (weight {timing.get("aliasWeight", 0):.0%})')
    
    # Harmony
    if harmony.get('rootWeight', 0) > 0.6:
        parts.append(f"strongly anchors root (weight {harmony.get('rootWeight', 0):.2f})")
    elif harmony.get('chordToneWeight', 0) > 0.5:
        parts.append(f"follows chord tones (weight {harmony.get('chordToneWeight', 0):.2f})")
    
    # Timing
    hum = timing.get('humanization', 'MODERATE')
    if hum != 'MINIMAL':
        parts.append(f"{hum.replace('_', ' ').lower()} timing")
    
    # Velocity
    pp = velocity.get('pp', '?')
    ff = velocity.get('ff', '?')
    parts.append(f'dynamic range {pp}-{ff}')
    
    # Articulation
    top_artic = sorted(
        [(k, v) for k, v in articulation.items()
         if isinstance(v, (int, float)) and v > 0.1 and k not in ('confidence', 'dnC_RX_Aware')],
        key=lambda x: -x[1]
    )[:3]
    if top_artic:
        art_str = ', '.join(f"{k} ({v:.0%})" for k, v in top_artic)
        parts.append(f'primary articulation: {art_str}')
    
    return ' '.join(parts).capitalize() + '.'


# ══════════════════════════════════════════════════════════════════
# MAIN: BUILD ALL ALIAS-RESOLVED PROFILES
# ══════════════════════════════════════════════════════════════════

def build_all_alias_profiles(output_dir: Path = None) -> Dict[str, Any]:
    """Napravi sve Instrument Playing Profile koristeći Role Alias Mapping.
    
    Ovo je GLAVNA funkcija — zamjenjuje build_all_profiles() sa alias-aware verzijom.
    """
    output_dir = output_dir or DATA_DIR
    
    # Učitaj podatke
    factory_profiles_raw = _load_json('factory-velocity-profiles.json').get('profiles', [])
    factory_catalog = _load_json('factory-velocity-catalog-9.30.json')
    gold_patterns_raw = _load_json('gold-performance-patterns.json').get('patterns', [])
    general_rules = _load_json('general-rules-9.30.json')
    
    # Izračunaj statistike po originalnim rolama
    gold_stats = _extract_gold_role_stats(gold_patterns_raw)
    factory_stats = _extract_factory_role_stats(factory_profiles_raw, factory_catalog)
    
    # Master Prompt: 20 instrument familija
    INSTRUMENT_FAMILIES = {
        'bass': {'family': 'bass', 'subfamily': 'electric_bass', 'priority_order': ['harmony','groove','root','timing','note_length','passing','velocity','expression','ornament']},
        'drums': {'family': 'drums', 'subfamily': 'drum_kit', 'priority_order': ['groove','pattern','accent','timing','element_rel','velocity','fill','density','articulation']},
        'piano': {'family': 'keyboard', 'subfamily': 'piano', 'priority_order': ['chord_voicing','rhythm','register','velocity','timing','note_length','phrase']},
        'organ': {'family': 'keyboard', 'subfamily': 'organ', 'priority_order': ['sustain','rhythm','expression','register','velocity','timing']},
        'rhythm_guitar': {'family': 'guitar', 'subfamily': 'rhythm', 'priority_order': ['strum','voicing','timing','mute','accent','harmony','articulation','velocity']},
        'solo_guitar': {'family': 'guitar', 'subfamily': 'solo', 'priority_order': ['phrase','articulation','microtiming','expression','ornaments','velocity','note_length']},
        'accordion': {'family': 'free_reed', 'subfamily': 'accordion', 'priority_order': ['chord_pulse','melody','ornament','rhythm','expression','timing','velocity']},
        'strings': {'family': 'bowed_strings', 'subfamily': 'ensemble', 'priority_order': ['sustain','harmony','voice_leading','expression','attack','release','density']},
        'brass': {'family': 'brass', 'subfamily': 'section', 'priority_order': ['attack','accent','rhythm','note_length','phrase','articulation','velocity']},
        'sax': {'family': 'wind', 'subfamily': 'saxophone', 'priority_order': ['phrase','articulation','expression','timing','ornaments','note_length','velocity']},
        'woodwind': {'family': 'wind', 'subfamily': 'folk_woodwind', 'priority_order': ['phrase','ornament','expression','timing','grace','breath','microtiming','velocity']},
        'clarinet': {'family': 'wind', 'subfamily': 'clarinet_folk', 'priority_order': ['phrase','ornament','expression','timing','trill','grace','breath','microtiming']},
        'violin': {'family': 'bowed_strings', 'subfamily': 'violin_fiddle', 'priority_order': ['legato','bow','grace','slide','ornament','sustain','accent','phrase']},
        'synth_lead': {'family': 'synth', 'subfamily': 'lead', 'priority_order': ['density','phrase','repetition','variation','glide','accent','sustain']},
        'pad': {'family': 'synth', 'subfamily': 'pad', 'priority_order': ['sustain','harmony','voice_leading','expression','attack','release','density']},
        'mallet': {'family': 'percussion', 'subfamily': 'mallet', 'priority_order': ['attack','repetition','alternation','arpeggio','sustain','accent','velocity']},
        'choir': {'family': 'vocal', 'subfamily': 'choir', 'priority_order': ['sustain','harmony','voice_leading','expression','attack','release','density']},
        'percussion': {'family': 'percussion', 'subfamily': 'hand_perc', 'priority_order': ['interlock','ghost','rhythm','accent','microtiming','density']},
        'fx': {'family': 'fx', 'subfamily': 'special', 'priority_order': ['trigger','section','duration','impact','repeatability']},
        'accompaniment': {'family': 'keyboard', 'subfamily': 'generic_comp', 'priority_order': ['chord_voicing','rhythm','register','velocity','timing','note_length']},
    }
    
    PA800_TRACK_MAP = {
        'bass': {'trackType': 'BASS', 'ntt': None, 'guitarMode': None},
        'drums': {'trackType': 'DRUM', 'ntt': None, 'guitarMode': None},
        'percussion': {'trackType': 'PERC', 'ntt': None, 'guitarMode': None},
        'rhythm_guitar': {'trackType': 'ACC1', 'ntt': 'Chord', 'guitarMode': 'NORM/FINGER/PICK'},
        'piano': {'trackType': 'ACC2', 'ntt': 'Chord/Fixed', 'guitarMode': None},
        'organ': {'trackType': 'ACC3', 'ntt': 'Fixed', 'guitarMode': None},
        'strings': {'trackType': 'ACC4', 'ntt': 'Fixed/Parallel', 'guitarMode': None},
        'brass': {'trackType': 'ACC5', 'ntt': 'Parallel', 'guitarMode': None},
        'accordion': {'trackType': 'ACC1', 'ntt': 'Chord/Fixed', 'guitarMode': None},
        'sax': {'trackType': 'ACC3', 'ntt': 'Parallel', 'guitarMode': None},
        'woodwind': {'trackType': 'ACC3', 'ntt': 'Parallel', 'guitarMode': None},
        'clarinet': {'trackType': 'ACC2', 'ntt': 'Parallel', 'guitarMode': None},
        'violin': {'trackType': 'ACC4', 'ntt': 'Parallel', 'guitarMode': None},
        'synth_lead': {'trackType': 'ACC3', 'ntt': 'Parallel', 'guitarMode': None},
        'pad': {'trackType': 'ACC4', 'ntt': 'Fixed', 'guitarMode': None},
        'mallet': {'trackType': 'ACC2', 'ntt': 'Chord/Parallel', 'guitarMode': None},
        'choir': {'trackType': 'ACC5', 'ntt': 'Fixed', 'guitarMode': None},
        'fx': {'trackType': 'ACC5', 'ntt': None, 'guitarMode': None},
        'accompaniment': {'trackType': 'ACC2', 'ntt': 'Chord/Fixed', 'guitarMode': None},
    }
    
    # Gradi profile za svih 20 instrumenata
    profiles = {}
    for inst in sorted(INSTRUMENT_FAMILIES.keys()):
        profiles[inst] = build_alias_resolved_profile(
            instrument=inst,
            gold_stats=gold_stats,
            factory_stats=factory_stats,
            factory_catalog=factory_catalog,
            general_rules=general_rules,
            instrument_families=INSTRUMENT_FAMILIES,
            pa800_track_map=PA800_TRACK_MAP,
        )
    
    # ── Sačuvaj JSON ──
    output = {
        'schema': 'dna-instrument-playing-profiles',
        'version': VERSION,
        'roleAliasMap': {
            'goldAliases': {k: {inst: w['weight'] for inst, w in v.items()} for k, v in GOLD_ALIAS_MAP.items()},
            'factoryAliases': {k: {inst: w['weight'] for inst, w in v.items()} for k, v in FACTORY_ALIAS_MAP.items()},
        },
        'coverageReport': _build_coverage_report(profiles),
        'totalProfiles': len(profiles),
        'authority': {
            'velocity': 'FACTORY_ONLY',
            'timing': 'GOLD_PRIMARY',
            'articulation': 'GOLD_PRIMARY',
            'expression': 'GOLD_PRIMARY',
            'mapping': 'PA800_ENGINE',
            'chordFoundation': 'CHORD_TIMELINE',
        },
        'chordFoundation': 'Sve funkcije prate Chord kao osnovu',
        'profiles': profiles,
        'goldStatistics': gold_stats,
        'factoryStatistics': factory_stats,
    }
    
    json_path = output_dir / 'instrument-playing-profiles-9.30-alias.json'
    json_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'✅ JSON sačuvan: {json_path} ({len(json.dumps(output)) // 1024} KB)')
    
    # ── Sačuvaj SQLite ──
    db_path = output_dir / 'instrument-profiles-9.30-alias.db'
    _save_to_sqlite_alias(profiles, db_path)
    
    # ── Sačuvaj human-readable izvještaj ──
    report_path = output_dir / 'role-alias-mapping-report-9.30.md'
    _save_alias_report(profiles, report_path)
    
    return output


# ══════════════════════════════════════════════════════════════════
# DATA LOADING HELPERS
# ══════════════════════════════════════════════════════════════════

def _load_json(filename: str) -> dict:
    path = DATA_DIR / filename
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def _extract_gold_role_stats(gold_patterns: list) -> dict:
    """Izvuci Gold statistiku po originalnim rolama."""
    by_role = defaultdict(list)
    for p in gold_patterns:
        by_role[p['role']].append(p)
    
    result = {}
    for role, rpatterns in by_role.items():
        n = len(rpatterns)
        densities = [p['density'] for p in rpatterns]
        lengths = [p['lengthBars'] for p in rpatterns]
        
        all_offsets, all_durations, all_pitches = [], [], []
        event_counts = []
        
        for p in rpatterns[:min(500, len(rpatterns))]:
            events = p.get('events', [])
            event_counts.append(len(events))
            for e in events:
                if len(e) >= 3:
                    all_pitches.append(e[0])
                    all_durations.append(e[1])
                    all_offsets.append(e[2])
        
        sec_dist = Counter(p.get('sourceSection', '?') for p in rpatterns)
        meter_dist = Counter(p.get('meter', '?') for p in rpatterns)
        
        tempos = []
        for p in rpatterns:
            tr = p.get('tempoRange', [])
            if tr:
                tempos.append((tr[0] + tr[1]) / 2)
        
        reg_lows = [p.get('register', {}).get('low', 0) for p in rpatterns]
        reg_highs = [p.get('register', {}).get('high', 0) for p in rpatterns]
        
        qualities = Counter()
        for p in rpatterns:
            ha = p.get('harmonicAnchor', {})
            if ha:
                qualities[ha.get('quality', '?')] += 1
        
        result[role] = {
            'patternCount': n,
            'density': _stats(densities),
            'lengthBars': _stats(lengths),
            'eventsPerPattern': _stats(event_counts),
            'pitchFromRoot': _stats(all_pitches),
            'duration': _stats(all_durations),
            'offset': _stats(all_offsets),
            'registerLow': _stats(reg_lows),
            'registerHigh': _stats(reg_highs),
            'tempo': _stats(tempos),
            'sectionDistribution': dict(sec_dist),
            'meterDistribution': dict(meter_dist),
            'chordQualityDistribution': dict(qualities),
            'confidence': _conf(n),
        }
    return result


def _extract_factory_role_stats(factory_profiles: list, factory_catalog: dict) -> dict:
    """Izvuci Factory statistiku po originalnim rolama."""
    by_role = defaultdict(list)
    for p in factory_profiles:
        by_role[p.get('role', 'unknown')].append(p)
    
    result = {}
    for role, profiles in by_role.items():
        n = len(profiles)
        vel_mins = [p.get('velocity', {}).get('min', 1) for p in profiles]
        vel_maxs = [p.get('velocity', {}).get('max', 127) for p in profiles]
        vel_opts = [p.get('velocity', {}).get('optimal', 80) for p in profiles]
        vel_floors = [p.get('velocity', {}).get('floor', 1) for p in profiles]
        vel_softs = [p.get('velocity', {}).get('soft', 40) for p in profiles]
        vel_strongs = [p.get('velocity', {}).get('strong', 100) for p in profiles]
        vel_ceilings = [p.get('velocity', {}).get('ceiling', 127) for p in profiles]
        
        result[role] = {
            'profileCount': n,
            'velocityMin': _stats(vel_mins),
            'velocityMax': _stats(vel_maxs),
            'velocityOptimal': _stats(vel_opts),
            'velocityFloor': _stats(vel_floors),
            'velocitySoft': _stats(vel_softs),
            'velocityStrong': _stats(vel_strongs),
            'velocityCeiling': _stats(vel_ceilings),
            'confidence': _conf(n, k=100),
        }
    
    # Dodaj perRole iz cataloga
    per_role = factory_catalog.get('perRole', {})
    for rn, rd in per_role.items():
        if rn not in result:
            result[rn] = {'profileCount': 0, 'confidence': _conf(0)}
        result[rn]['catalogData'] = rd
    
    return result


def _stats(data):
    """Brza statistika."""
    if not data:
        return {'n': 0, 'mean': 0, 'median': 0, 'p5': 0, 'p25': 0, 'p50': 0, 'p75': 0, 'p95': 0, 'sd': 0}
    s = sorted(data)
    n = len(s)
    m = sum(s) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in s) / n) if n > 1 else 0
    return {
        'n': n, 'mean': round(m, 3), 'median': s[n // 2],
        'p5': s[max(0, n // 20)], 'p25': s[n // 4], 'p50': s[n // 2],
        'p75': s[3 * n // 4], 'p95': s[min(n - 1, 19 * n // 20)],
        'sd': round(sd, 3),
    }


# ══════════════════════════════════════════════════════════════════
# COVERAGE REPORT
# ══════════════════════════════════════════════════════════════════

def _build_coverage_report(profiles: dict) -> dict:
    """Izvještaj o pokrivenosti — prije i poslije alias mappinga."""
    inverse = build_inverse_alias_map()
    
    direct_gold = 0
    alias_gold = 0
    no_gold = 0
    direct_factory = 0
    alias_factory = 0
    no_factory = 0
    
    details = []
    
    for inst in sorted(profiles.keys()):
        conf = profiles[inst].get('confidence', {})
        vel = profiles[inst].get('velocity', {})
        tim = profiles[inst].get('timing', {})
        
        # Gold coverage
        gs = [s for s in inverse.get(inst, []) if s['sourceType'] == 'GOLD']
        if gs:
            primary = gs[0]
            if primary['weight'] == 1.0:
                direct_gold += 1
                gold_status = 'DIRECT'
            else:
                alias_gold += 1
                gold_status = f'ALIAS({primary["sourceRole"]}, w={primary["weight"]:.0%})'
        else:
            no_gold += 1
            gold_status = 'NONE'
        
        # Factory coverage
        fs = [s for s in inverse.get(inst, []) if s['sourceType'] == 'FACTORY']
        if fs:
            primary = fs[0]
            if primary['weight'] == 1.0:
                direct_factory += 1
                factory_status = 'DIRECT'
            else:
                alias_factory += 1
                factory_status = f'ALIAS({primary["sourceRole"]}, w={primary["weight"]:.0%})'
        else:
            no_factory += 1
            factory_status = 'NONE'
        
        details.append({
            'instrument': inst,
            'overallConfidence': conf.get('overallConfidence', 0),
            'goldStatus': gold_status,
            'factoryStatus': factory_status,
            'velocitySource': vel.get('source', '?'),
            'timingSource': tim.get('source', '?'),
            'flags': conf.get('lowConfidenceFlags', []),
        })
    
    total = len(profiles)
    gold_coverage = (direct_gold + alias_gold) / total
    factory_coverage = (direct_factory + alias_factory) / total
    
    return {
        'totalInstruments': total,
        'goldCoverage': {
            'directCount': direct_gold,
            'aliasCount': alias_gold,
            'noneCount': no_gold,
            'coveragePercent': round(gold_coverage * 100, 1),
            'beforeAlias': round(direct_gold / total * 100, 1),
            'afterAlias': round(gold_coverage * 100, 1),
        },
        'factoryCoverage': {
            'directCount': direct_factory,
            'aliasCount': alias_factory,
            'noneCount': no_factory,
            'coveragePercent': round(factory_coverage * 100, 1),
            'beforeAlias': round(direct_factory / total * 100, 1),
            'afterAlias': round(factory_coverage * 100, 1),
        },
        'details': details,
    }


# ══════════════════════════════════════════════════════════════════
# SQLITE SAVER
# ══════════════════════════════════════════════════════════════════

def _save_to_sqlite_alias(profiles: dict, db_path: Path):
    """Sačuvaj profile u SQLite sa alias kolonama."""
    if db_path.exists():
        db_path.unlink()
    
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS profiles (
        role TEXT PRIMARY KEY,
        family TEXT,
        subfamily TEXT,
        arrangement_role TEXT,
        pa800_track_type TEXT,
        ntt TEXT,
        guitar_mode TEXT,
        velocity_source TEXT,
        velocity_alias TEXT,
        velocity_alias_weight REAL,
        timing_source TEXT,
        timing_alias TEXT,
        timing_alias_weight REAL,
        overall_confidence REAL,
        gold_samples INTEGER,
        factory_samples INTEGER,
        how_it_plays TEXT,
        profile_json TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS alias_map (
        instrument TEXT,
        source_role TEXT,
        source_type TEXT,
        weight REAL,
        evidence TEXT,
        authority TEXT,
        contribution TEXT,
        PRIMARY KEY (instrument, source_role, source_type)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS range_data (
        role TEXT PRIMARY KEY,
        absolute_min INTEGER, absolute_max INTEGER,
        practical_min INTEGER, practical_max INTEGER,
        preferred_low INTEGER, preferred_mid INTEGER, preferred_high INTEGER,
        FOREIGN KEY (role) REFERENCES profiles(role)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS velocity_data (
        role TEXT PRIMARY KEY,
        pp INTEGER, p INTEGER, mp INTEGER, mf INTEGER,
        f INTEGER, ff INTEGER, fff INTEGER,
        accent INTEGER, ghost INTEGER, phrase_peak INTEGER,
        source TEXT, alias_source TEXT, alias_weight REAL, confidence REAL,
        FOREIGN KEY (role) REFERENCES profiles(role)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS timing_data (
        role TEXT PRIMARY KEY,
        base_offset REAL, early_range REAL, late_range REAL,
        groove_profile TEXT, humanization TEXT, swing REAL,
        source TEXT, alias_source TEXT, alias_weight REAL, confidence REAL,
        FOREIGN KEY (role) REFERENCES profiles(role)
    )''')
    
    for role, profile in profiles.items():
        ident = profile.get('identity', {})
        vel = profile.get('velocity', {})
        tim = profile.get('timing', {})
        rng = profile.get('range', {})
        pa = profile.get('pa800Behavior', {})
        conf = profile.get('confidence', {})
        
        c.execute('INSERT OR REPLACE INTO profiles VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                  (role, ident.get('family', ''), ident.get('subfamily', ''),
                   ident.get('instrumentRole', ''), pa.get('trackType', ''),
                   pa.get('ntt', ''), pa.get('guitarMode', ''),
                   vel.get('source', ''), vel.get('aliasSource', ''), vel.get('aliasWeight', 0),
                   tim.get('source', ''), tim.get('aliasSource', ''), tim.get('aliasWeight', 0),
                   conf.get('overallConfidence', 0), conf.get('goldSampleCount', 0),
                   conf.get('factorySampleCount', 0), profile.get('howItPlays', ''),
                   json.dumps(profile, ensure_ascii=False)))
        
        c.execute('INSERT OR REPLACE INTO range_data VALUES (?,?,?,?,?,?,?,?)',
                  (role, rng.get('absoluteMin', 0), rng.get('absoluteMax', 127),
                   rng.get('practicalMin', 0), rng.get('practicalMax', 127),
                   rng.get('preferredLow', 0), rng.get('preferredMid', 60),
                   rng.get('preferredHigh', 96)))
    
        c.execute('INSERT OR REPLACE INTO velocity_data VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                  (role, vel.get('pp', 0), vel.get('p', 0), vel.get('mp', 0),
                   vel.get('mf', 0), vel.get('f', 0), vel.get('ff', 0),
                   vel.get('fff', 0), vel.get('accent', 0), vel.get('ghost', 0),
                   vel.get('phrasePeak', 0), vel.get('source', ''),
                   vel.get('aliasSource', ''), vel.get('aliasWeight', 0),
                   vel.get('confidence', 0)))
        
        c.execute('INSERT OR REPLACE INTO timing_data VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                  (role, tim.get('baseOffset', 0), 
                   tim.get('earlyLateRange', {}).get('early', 0),
                   tim.get('earlyLateRange', {}).get('late', 0),
                   tim.get('grooveProfile', ''), tim.get('humanization', ''),
                   tim.get('swing', 0), tim.get('source', ''),
                   tim.get('aliasSource', ''), tim.get('aliasWeight', 0),
                   tim.get('confidence', 0)))
    
    # Sačuvaj alias map
    inverse = build_inverse_alias_map()
    for inst, sources in inverse.items():
        sources_sorted = sorted(sources, key=lambda s: s['weight'], reverse=True)
        for i, s in enumerate(sources_sorted):
            c.execute('INSERT OR REPLACE INTO alias_map VALUES (?,?,?,?,?,?,?)',
                      (inst, s['sourceRole'], s['sourceType'], s['weight'],
                       s['evidence'], s['authority'],
                       'PRIMARY' if i == 0 else 'SECONDARY'))
    
    conn.commit()
    conn.close()
    print(f'✅ SQLite sačuvan: {db_path}')


# ══════════════════════════════════════════════════════════════════
# HUMAN-READABLE REPORT
# ══════════════════════════════════════════════════════════════════

def _save_alias_report(profiles: dict, report_path: Path):
    """Sačuvaj detaljni human-readable izvještaj sa alias informacijama."""
    lines = [
        '# DNA MIDI Studio 9.30 — Role Alias Mapping Report',
        '',
        f'**Verzija:** {VERSION}',
        f'**Ukupno profila:** {len(profiles)}',
        '',
        '## Alias Mapiranje',
        '',
        '### Gold Role → Instrument Aliases',
        '',
    ]
    
    for gold_role, targets in GOLD_ALIAS_MAP.items():
        lines.append(f'**{gold_role}** →')
        for inst, info in sorted(targets.items(), key=lambda x: -x[1]['weight']):
            lines.append(f'  - {inst}: weight={info["weight"]:.0%}, evidence={info["evidence"]}')
        lines.append('')
    
    lines.append('### Factory Role → Instrument Aliases')
    lines.append('')
    for factory_role, targets in FACTORY_ALIAS_MAP.items():
        lines.append(f'**{factory_role}** →')
        for inst, info in sorted(targets.items(), key=lambda x: -x[1]['weight']):
            lines.append(f'  - {inst}: weight={info["weight"]:.0%}, evidence={info["evidence"]}')
        lines.append('')
    
    lines.append('---')
    lines.append('')
    lines.append('## Profili po instrumentu')
    lines.append('')
    
    for inst in sorted(profiles.keys()):
        profile = profiles[inst]
        ident = profile.get('identity', {})
        vel = profile.get('velocity', {})
        tim = profile.get('timing', {})
        harm = profile.get('harmony', {})
        artic = profile.get('articulation', {})
        conf = profile.get('confidence', {})
        pa = profile.get('pa800Behavior', {})
        
        lines.append(f'### {inst.upper()}')
        lines.append('')
        lines.append(f'- **Family:** {ident.get("family", "?")}')
        lines.append(f'- **Subfamily:** {ident.get("subfamily", "?")}')
        lines.append(f'- **Arrangement Role:** {ident.get("instrumentRole", "?")}')
        lines.append(f'- **PA800 Track:** {pa.get("trackType", "?")} | NTT: {pa.get("ntt", "?")}')
        lines.append('')
        
        # Alias info
        lines.append('#### Alias Sources')
        lines.append('')
        if 'ALIAS' in vel.get('source', ''):
            lines.append(f'- **Velocity:** inherited from Factory `{vel.get("aliasSource", "?")}` role (weight {vel.get("aliasWeight", 0):.0%}, confidence {vel.get("confidence", 0):.2f})')
        else:
            lines.append(f'- **Velocity:** {vel.get("source", "?")} (confidence {vel.get("confidence", 0):.2f})')
        
        if 'ALIAS' in tim.get('source', ''):
            lines.append(f'- **Timing:** inherited from Gold `{tim.get("aliasSource", "?")}` role (weight {tim.get("aliasWeight", 0):.0%}, confidence {tim.get("confidence", 0):.2f})')
        else:
            lines.append(f'- **Timing:** {tim.get("source", "?")} (confidence {tim.get("confidence", 0):.2f})')
        
        lines.append('')
        
        # Velocity table
        lines.append('#### Velocity Curve')
        lines.append('')
        lines.append('| Level | Value |')
        lines.append('|---|---|')
        for lvl in ['pp', 'p', 'mp', 'mf', 'f', 'ff', 'fff', 'accent', 'ghost']:
            if lvl in vel:
                lines.append(f'| {lvl} | {vel[lvl]} |')
        lines.append(f'| Source | {vel.get("source", "?")} |')
        lines.append(f'| Confidence | {vel.get("confidence", 0):.3f} |')
        lines.append('')
        
        # Timing
        lines.append('#### Timing')
        lines.append('')
        lines.append(f'- Humanization: {tim.get("humanization", "?")}')
        lines.append(f'- Groove profile: {tim.get("grooveProfile", "?")}')
        lines.append(f'- Base offset: {tim.get("baseOffset", 0)}')
        lines.append(f'- Swing: {tim.get("swing", 0):.2f}')
        lines.append('')
        
        # Harmony
        lines.append('#### Harmony')
        lines.append('')
        lines.append(f'- Root weight: {harm.get("rootWeight", 0):.2f}')
        lines.append(f'- Third weight: {harm.get("thirdWeight", 0):.2f}')
        lines.append(f'- Passing rate: {harm.get("passingNoteRate", 0):.0%}')
        lines.append(f'- Chromatic rate: {harm.get("chromaticRate", 0):.0%}')
        lines.append('')
        
        # How It Plays
        lines.append('#### How It Plays')
        lines.append('')
        lines.append(f'> {profile.get("howItPlays", "No description.")}')
        lines.append('')
        
        # Confidence
        lines.append('#### Confidence')
        lines.append('')
        lines.append(f'- Overall: {conf.get("overallConfidence", 0):.3f}')
        lines.append(f'- Gold samples: {conf.get("goldSampleCount", 0)}')
        lines.append(f'- Factory samples: {conf.get("factorySampleCount", 0)}')
        lines.append(f'- Flags: {", ".join(conf.get("lowConfidenceFlags", [])) or "None"}')
        lines.append('')
        lines.append('---')
        lines.append('')
    
    # Coverage summary
    cov = _build_coverage_report(profiles)
    lines.append('## Coverage Summary')
    lines.append('')
    lines.append(f'| Metric | Before Alias | After Alias |')
    lines.append(f'|---|---|---|')
    lines.append(f'| Gold (timing/articulation) | {cov["goldCoverage"]["beforeAlias"]:.1f}% | {cov["goldCoverage"]["afterAlias"]:.1f}% |')
    lines.append(f'| Factory (velocity) | {cov["factoryCoverage"]["beforeAlias"]:.1f}% | {cov["factoryCoverage"]["afterAlias"]:.1f}% |')
    lines.append('')
    
    report_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f'✅ Report sačuvan: {report_path} ({len(lines)} lines)')


# ══════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print('DNA MIDI Studio 9.30 — Role Alias Mapping Engine')
    print('=' * 60)
    print()
    
    # Prikaži alias mapu
    print('GOLD ALIAS MAP:')
    for role, targets in GOLD_ALIAS_MAP.items():
        top = sorted(targets.items(), key=lambda x: -x[1]['weight'])[:3]
        top_str = ', '.join(f'{inst}({w["weight"]:.0%})' for inst, w in top)
        print(f'  {role} → {top_str}')
    
    print()
    print('FACTORY ALIAS MAP:')
    for role, targets in FACTORY_ALIAS_MAP.items():
        top = sorted(targets.items(), key=lambda x: -x[1]['weight'])[:3]
        top_str = ', '.join(f'{inst}({w["weight"]:.0%})' for inst, w in top)
        print(f'  {role} → {top_str}')
    
    print()
    result = build_all_alias_profiles()
    
    cov = result.get('coverageReport', {})
    print(f'\n{"=" * 60}')
    print(f'REZULTAT:')
    print(f'  Ukupno profila: {result["totalProfiles"]}')
    print(f'  Gold coverage: {cov["goldCoverage"]["beforeAlias"]:.1f}% → {cov["goldCoverage"]["afterAlias"]:.1f}%')
    print(f'  Factory coverage: {cov["factoryCoverage"]["beforeAlias"]:.1f}% → {cov["factoryCoverage"]["afterAlias"]:.1f}%')
