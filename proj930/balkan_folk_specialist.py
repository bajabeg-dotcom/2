#!/usr/bin/env python3
"""
DNA MIDI Studio 9.30 — Balkan/Folk Specialization Module
=========================================================
Specijalizacija za balkanske folk metre (7/8, 9/8) i folk instrumente
(harmonika, klarinet, violina, frula, tambura, gusle).

Autoriteti:
  - Gold pattern ekstrakt: 7/8 (634 patterna) + 9/8 (91 patterna)
  - Factory velocity: jedini izvor za dinamiku
  - Folk ornament rules: pravilo-bazirana ekspertiza
  - Chord foundation: OBAVEZNO za sve folk instrumente

Version: 9.30.0
"""

import json
import sqlite3
from pathlib import Path
from collections import Counter, defaultdict

DATA_DIR = Path(__file__).parent / 'data'

# ─── BALKAN METER DEFINITIONS ─────────────────────────────────────────────

BALKAN_METERS = {
    '7/8': {
        'fullName': 'Sedminka (7/8)',
        'subGroups': [
            {'beats': [0,1], 'weight': 'strong',  'label': '2'},
            {'beats': [2,3], 'weight': 'weak',    'label': '2'},
            {'beats': [4,5,6], 'weight': 'medium', 'label': '3'},
        ],
        'commonNames': ['Leskoto', 'Makedonsko', 'Balkan 2+2+3'],
        'altGroupings': ['3+2+2', '2+3+2'],
        'primaryGrouping': '2+2+3',
        'ppqPerBar': 168,  # 7 * 24 PPQ
        'accentPattern': [1.0, 0.5, 0.3, 0.5, 0.6, 0.4, 0.4],
        'typicalTempoRange': [100, 200],
        'danceStyles': ['Leskoto', 'Makedonsko oro', 'Račanik', 'Balkan folk'],
    },
    '9/8': {
        'fullName': 'Devetina (9/8)',
        'subGroups': [
            {'beats': [0,1], 'weight': 'strong',  'label': '2'},
            {'beats': [2,3], 'weight': 'weak',    'label': '2'},
            {'beats': [4,5,6,7,8], 'weight': 'medium', 'label': '5'},  # or 2+3
        ],
        'commonNames': ['Devetinka', 'Aksak 9', 'Balkan 2+2+5'],
        'altGroupings': ['2+2+2+3', '2+3+2+2', '3+2+2+2'],
        'primaryGrouping': '2+2+5',
        'ppqPerBar': 216,  # 9 * 24 PPQ
        'accentPattern': [1.0, 0.5, 0.3, 0.5, 0.6, 0.4, 0.4, 0.3, 0.3],
        'typicalTempoRange': [80, 160],
        'danceStyles': ['Aksak', 'Devetinka', 'Balkan folk 9/8'],
    },
    '6/4': {
        'fullName': 'Šestčetvrtina (6/4)',
        'subGroups': [
            {'beats': [0,1,2], 'weight': 'strong', 'label': '3'},
            {'beats': [3,4,5], 'weight': 'weak',   'label': '3'},
        ],
        'commonNames': ['Dvostruki vals', 'Balkan 6/4'],
        'primaryGrouping': '3+3',
        'ppqPerBar': 144,
        'accentPattern': [1.0, 0.5, 0.3, 0.6, 0.4, 0.3],
        'typicalTempoRange': [60, 120],
        'danceStyles': ['Balkan folk 6/4'],
    },
}

# ─── FOLK INSTRUMENT DEFINITIONS ──────────────────────────────────────────

FOLK_INSTRUMENTS = {
    'harmonika': {
        'fullName': 'Harmonika (Button Accordion)',
        'GM_Patch': 22,  # Accordion
        'family': 'keyboard',
        'role': 'chords',  # chords + melody
        'velocityAuthority': 'FACTORY',
        'timingAuthority': 'GOLD_PATTERN',
        'humanization': 'BELLOW_PHRASE',
        'grooveProfile': 'BELLOW_SUSTAIN',
        'folkOrnaments': {
            'mordent': {'probability': 0.15, 'interval': 2, 'timing': -3},
            'turn': {'probability': 0.08, 'interval': 2, 'timing': -5},
            'glissando': {'probability': 0.05, 'duration': 6, 'timing': 0},
        },
        'bellowsDynamics': {
            'crescendoRate': 0.7,  # per bar
            'diminuendoRate': 0.6,
            'breathPhrase': True,
            'sustainBite': 3,  # PPQ ticks early attack
        },
        'chordRequirement': 'MANDATORY',
        'typicalRange': [48, 84],  # C3-C6
        'articulation': {
            'legato': 0.8,
            'staccato': 0.1,
            'portato': 0.1,
        },
    },
    'klarinet': {
        'fullName': 'Klarinet (Clarinet)',
        'GM_Patch': 72,  # Clarinet
        'family': 'wind',
        'role': 'melody',
        'velocityAuthority': 'FACTORY',
        'timingAuthority': 'GOLD_PATTERN',
        'humanization': 'BREATH_PHRASE',
        'grooveProfile': 'BREATH_PHRASE',
        'folkOrnaments': {
            'mordent': {'probability': 0.25, 'interval': 2, 'timing': -2},
            'trill': {'probability': 0.12, 'interval': 2, 'beats': 2},
            'appoggiatura': {'probability': 0.20, 'interval': 3, 'timing': -4},
            'glissando': {'probability': 0.08, 'duration': 8, 'timing': 0},
            'shake': {'probability': 0.05, 'interval': 2, 'duration': 12},  # Balkan shake
        },
        'breathControl': {
            'phraseLength': [4, 8],  # beats
            'breathGap': 6,  # PPQ ticks
            'vibratoRate': 5.0,  # Hz
            'vibratoDepth': 3,  # cents
        },
        'chordRequirement': 'MANDATORY',
        'typicalRange': [55, 91],  # G3-G6
        'articulation': {
            'legato': 0.7,
            'staccato': 0.15,
            'portato': 0.15,
        },
    },
    'violina': {
        'fullName': 'Violina (Violin)',
        'GM_Patch': 41,  # Violin
        'family': 'strings',
        'role': 'melody',
        'velocityAuthority': 'FACTORY',
        'timingAuthority': 'GOLD_PATTERN',
        'humanization': 'BOW_PHRASE',
        'grooveProfile': 'BOW_PHRASE',
        'folkOrnaments': {
            'mordent': {'probability': 0.20, 'interval': 2, 'timing': -2},
            'trill': {'probability': 0.18, 'interval': 2, 'beats': 2},
            'appoggiatura': {'probability': 0.22, 'interval': 3, 'timing': -3},
            'glissando': {'probability': 0.15, 'duration': 10, 'timing': 0},  # slide
            'grace_note': {'probability': 0.10, 'interval': 2, 'timing': -2},
        },
        'bowControl': {
            'phraseLength': [4, 8],
            'bowChangeGap': 4,  # PPQ ticks
            'vibratoRate': 5.5,
            'vibratoDepth': 8,  # cents — wider than clarinet
            'sulPonticello': 0.05,  # probability
            'colLegno': 0.02,
        },
        'chordRequirement': 'MANDATORY',
        'typicalRange': [55, 96],  # G3-C7
        'articulation': {
            'legato': 0.6,
            'staccato': 0.20,
            'spiccato': 0.15,
            'portato': 0.05,
        },
    },
    'frula': {
        'fullName': 'Frula (Folk Flute/Recorder)',
        'GM_Patch': 75,  # Pan Flute (closest GM)
        'family': 'wind',
        'role': 'melody',
        'velocityAuthority': 'FACTORY',
        'timingAuthority': 'GOLD_PATTERN',
        'humanization': 'BREATH_PHRASE',
        'grooveProfile': 'BREATH_PHRASE',
        'folkOrnaments': {
            'mordent': {'probability': 0.30, 'interval': 2, 'timing': -1},
            'trill': {'probability': 0.15, 'interval': 2, 'beats': 1},
            'appoggiatura': {'probability': 0.18, 'interval': 2, 'timing': -3},
            'flutter': {'probability': 0.08, 'duration': 12},  # flutter tongue
        },
        'breathControl': {
            'phraseLength': [2, 4],  # shorter phrases
            'breathGap': 8,  # PPQ ticks — more breathing
            'vibratoRate': 4.0,
            'vibratoDepth': 2,  # cents
        },
        'chordRequirement': 'MANDATORY',
        'typicalRange': [60, 84],  # C4-C6
        'articulation': {
            'legato': 0.75,
            'staccato': 0.15,
            'portato': 0.10,
        },
    },
    'tambura': {
        'fullName': 'Tambura (Tamburitza)',
        'GM_Patch': 25,  # Acoustic Guitar (steel) closest
        'family': 'strings',
        'role': 'chords',
        'velocityAuthority': 'FACTORY',
        'timingAuthority': 'GOLD_PATTERN',
        'humanization': 'PLECTRUM_PHRASE',
        'grooveProfile': 'PLECTRUM_PHRASE',
        'folkOrnaments': {
            'mordent': {'probability': 0.10, 'interval': 2, 'timing': -2},
            'appoggiatura': {'probability': 0.12, 'interval': 2, 'timing': -2},
        },
        'plectrumControl': {
            'phraseLength': [4, 8],
            'pickAngle': 0.3,  # relative
            'strumDirection': 'alternating',
        },
        'chordRequirement': 'MANDATORY',
        'typicalRange': [48, 77],  # C3-F5
        'articulation': {
            'legato': 0.3,
            'staccato': 0.5,
            'portato': 0.2,
        },
    },
    'gusle': {
        'fullName': 'Gusle (Folk Fiddle)',
        'GM_Patch': 111,  # Fiddle
        'family': 'strings',
        'role': 'melody',
        'velocityAuthority': 'FACTORY',
        'timingAuthority': 'GOLD_PATTERN',
        'humanization': 'BOW_FREE',
        'grooveProfile': 'BOW_FREE_RUBATO',
        'folkOrnaments': {
            'glissando': {'probability': 0.25, 'duration': 16, 'timing': 0},
            'mordent': {'probability': 0.15, 'interval': 1, 'timing': -2},
            'vibrato_wide': {'probability': 0.20, 'depth': 15, 'rate': 4.0},
        },
        'bowControl': {
            'phraseLength': [8, 16],  # long phrases — epic singing
            'bowChangeGap': 6,
            'vibratoRate': 4.0,
            'vibratoDepth': 15,  # cents — very wide
            'rubatoRange': 0.15,  # ±15% tempo
        },
        'chordRequirement': 'MANDATORY',
        'typicalRange': [55, 77],  # G3-F5 — narrow range
        'articulation': {
            'legato': 0.9,
            'portato': 0.1,
        },
    },
}

# ─── BALKAN DRUM PATTERNS (7/8, 9/8) ──────────────────────────────────────

def extract_balkan_drum_patterns(gold_patterns_path: Path = None):
    """Ekstraktuj 7/8 i 9/8 drum patterna iz Gold baze."""
    if gold_patterns_path is None:
        gold_patterns_path = DATA_DIR / 'gold-patterns.json'
    
    with open(gold_patterns_path, 'r') as f:
        gold = json.load(f)
    
    patterns = gold.get('patterns', [])
    
    balkan = {'7/8': [], '9/8': [], '6/4': []}
    
    for p in patterns:
        meter = p.get('meter', '4/4')
        role = p.get('role', 'unknown')
        
        if meter in balkan and role == 'drums':
            balkan[meter].append({
                'id': p.get('id', ''),
                'notes': p.get('notes', []),
                'grid': p.get('grid', 96),
                'density': p.get('density', 0),
                'register': p.get('register', ''),
                'sourceSection': p.get('sourceSection', ''),
                'occurrences': p.get('occurrences', 0),
                'confidence': p.get('confidence', 0),
            })
    
    return balkan


def extract_balkan_performance_patterns(gold_perf_path: Path = None):
    """Ekstraktuj 7/8 i 9/8 performance patterna (sve role)."""
    if gold_perf_path is None:
        gold_perf_path = DATA_DIR / 'gold-performance-patterns.json'
    
    with open(gold_perf_path, 'r') as f:
        gp = json.load(f)
    
    patterns = gp.get('patterns', [])
    
    balkan = defaultdict(list)
    
    for p in patterns:
        meter = p.get('meter', '4/4')
        if meter in BALKAN_METERS:
            balkan[meter].append({
                'id': p.get('id', ''),
                'role': p.get('role', ''),
                'notes': p.get('notes', []),
                'events': p.get('events', []),
                'grid': p.get('timingResolution', 96),
                'density': p.get('density', 0),
                'register': p.get('register', ''),
                'harmonicAnchor': p.get('harmonicAnchor', ''),
                'drumElements': p.get('drumElements', []),
                'articulation': p.get('articulation', {}),
                'sourceSection': p.get('sourceSection', ''),
                'occurrences': p.get('occurrences', 0),
                'confidence': p.get('confidence', 0),
                'qualityScore': p.get('qualityScore', 0),
            })
    
    return dict(balkan)


def analyze_balkan_meter_patterns(balkan_patterns: dict, meter: str):
    """Analiziraj pattern za dati balkanski meter."""
    meter_info = BALKAN_METERS.get(meter, {})
    pats = balkan_patterns.get(meter, [])
    
    if not pats:
        return {'meter': meter, 'patternCount': 0}
    
    # Group by role
    by_role = Counter(p.get('role', 'unknown') for p in pats)
    
    # Analyze density distribution
    densities = [p.get('density', 0) for p in pats if p.get('density')]
    avg_density = sum(densities) / len(densities) if densities else 0
    
    # Analyze note positions (beat map)
    beat_map = Counter()
    for p in pats:
        for n in p.get('notes', []):
            if len(n) >= 1:
                # Calculate which beat this falls on
                ppq = p.get('grid', 96)
                beat_size = ppq // meter_info.get('subGroups', [{}])[0].get('beats', [1]).__len__() if meter_info.get('subGroups') else ppq
                beat_pos = n[0] // 24 if len(n) >= 1 else 0
                beat_map[beat_pos] = beat_map.get(beat_pos, 0) + 1
    
    return {
        'meter': meter,
        'fullName': meter_info.get('fullName', meter),
        'primaryGrouping': meter_info.get('primaryGrouping', ''),
        'patternCount': len(pats),
        'roleDistribution': dict(by_role),
        'avgDensity': round(avg_density, 2),
        'topBeats': dict(beat_map.most_common(10)),
        'typicalTempoRange': meter_info.get('typicalTempoRange', [120, 120]),
        'danceStyles': meter_info.get('danceStyles', []),
    }

# ─── FOLK ORNAMENT ENGINE ─────────────────────────────────────────────────

def generate_ornament_events(instrument: str, chord_root: int, scale_type: str = 'minor',
                             position: int = 0, bar_start: int = 0):
    """
    Generiši MIDI evente za folk ornamenta datog instrumenta.
    
    Args:
        instrument: ključ iz FOLK_INSTRUMENTS
        chord_root: MIDI pitch osnovnog tona akorda
        scale_type: 'minor' ili 'major' (za interval pravila)
        position: PPQ pozicija osnovne note
        bar_start: početak takta
    
    Returns:
        Lista [start, duration, pitch, velocity] eventa
    """
    folk = FOLK_INSTRUMENTS.get(instrument, {})
    ornaments = folk.get('folkOrnaments', {})
    
    if not ornaments:
        return []
    
    events = []
    
    for orn_name, orn_conf in ornaments.items():
        prob = orn_conf.get('probability', 0)
        
        # Deterministic seed: position-based probability
        # Koristimo poziciju kao seed za determinizam
        seed_val = (chord_root * 7 + position * 3 + hash(orn_name)) % 1000
        effective_prob = prob if (seed_val % 1000) < (prob * 1000) else 0.0
        
        if effective_prob <= 0:
            continue
        
        interval = orn_conf.get('interval', 2)
        timing_offset = orn_conf.get('timing', 0)
        duration = orn_conf.get('duration', orn_conf.get('beats', 1) * 24)
        
        if scale_type == 'minor' and orn_name == 'appoggiatura':
            interval = 3  # minor third for minor scale
        
        start = position + timing_offset
        
        if orn_name in ('mordent', 'trill'):
            # Upper neighbor then back
            events.append([start, 3, chord_root + interval, 0])  # velocity set by caller
            events.append([start + 3, 3, chord_root, 0])
            if orn_name == 'trill':
                beats = orn_conf.get('beats', 2)
                for i in range(beats * 4):
                    events.append([start + 6 + i * 6, 3, chord_root + interval, 0])
                    events.append([start + 9 + i * 6, 3, chord_root, 0])
        
        elif orn_name == 'appoggiatura':
            # Grace note before main
            events.append([start, 2, chord_root + interval, 0])
            
        elif orn_name == 'glissando':
            # Chromatic slide
            direction = 1 if chord_root < 72 else -1
            for i in range(duration // 2):
                events.append([start + i * 2, 2, chord_root + i * direction, 0])
        
        elif orn_name in ('shake', 'flutter', 'vibrato_wide'):
            # Rapid alternation
            dur = orn_conf.get('duration', 12)
            for i in range(dur // 3):
                events.append([start + i * 3, 2, chord_root + (1 if i % 2 == 0 else -1), 0])
        
        elif orn_name == 'grace_note':
            events.append([start, 2, chord_root + interval, 0])
    
    return events


# ─── BALKAN ACCENT TIMING ENGINE ──────────────────────────────────────────

def compute_balkan_accent_offsets(meter: str, position_ppq: int, element: str = 'melody'):
    """
    Izračunaj determinističke timing offseta za balkanske metre.
    
    Vraća dict sa:
      - velocity_scale: float (0.0-1.0) — skaliranje Factory velocity
      - timing_offset: int — PPQ offset (- kašnjenje, + ranije)
      - accent_weight: float — težina akcenta na toj poziciji
    
    Autoritet: FACTORY za velocity, GOLD za timing
    """
    meter_info = BALKAN_METERS.get(meter)
    if not meter_info:
        return {'velocity_scale': 1.0, 'timing_offset': 0, 'accent_weight': 0.5}
    
    ppq_per_bar = meter_info.get('ppqPerBar', 168)
    accent_pattern = meter_info.get('accentPattern', [])
    position_in_bar = position_ppq % ppq_per_bar
    beat_index = position_in_bar // 24  # assuming 24 PPQ per beat unit
    
    if beat_index < len(accent_pattern):
        accent = accent_pattern[beat_index]
    else:
        accent = 0.3
    
    # Timing offset: strong beats slightly early, weak beats slightly late
    if accent > 0.7:
        timing_offset = -2  # PPQ ticks early (driving the beat)
    elif accent < 0.4:
        timing_offset = 2   # PPQ ticks late (laying back)
    else:
        timing_offset = 0
    
    # For drums, adjust based on element
    if element == 'kick':
        timing_offset -= 1  # kick always slightly early
    elif element == 'snare':
        timing_offset += 1  # snare on the dot or slightly late
    elif element == 'closed_hat':
        timing_offset = 0   # hi-hat is the timekeeper
    
    # Velocity scale: FACTORY authority, never override
    # We only SCALE the factory velocity, never replace
    velocity_scale = 0.7 + 0.3 * accent  # range 0.7-1.0
    
    return {
        'velocity_scale': velocity_scale,
        'timing_offset': timing_offset,
        'accent_weight': accent,
    }


# ─── MAIN BUILD FUNCTION ──────────────────────────────────────────────────

def build_balkan_folk_profiles():
    """Glavna funkcija: generiši kompletne Balkan/folk profile."""
    print('DNA MIDI Studio 9.30 — Balkan/Folk Specialization')
    print('=' * 56)
    
    # 1. Extract Balkan patterns from Gold
    print('\n  Ekstraktujem balkanske patterne iz Gold baze...')
    balkan_drum = extract_balkan_drum_patterns()
    balkan_perf = extract_balkan_performance_patterns()
    
    for meter in ['7/8', '9/8', '6/4']:
        drum_count = len(balkan_drum.get(meter, []))
        perf_count = len(balkan_perf.get(meter, []))
        print(f'    {meter}: {drum_count} drum + {perf_count} ukupno patterna')
    
    # 2. Analyze each meter
    print('\n  Analiziram metre...')
    meter_analyses = {}
    for meter in BALKAN_METERS:
        analysis = analyze_balkan_meter_patterns(balkan_perf, meter)
        meter_analyses[meter] = analysis
        print(f'    {analysis["fullName"]}: {analysis["patternCount"]} patterna, '
              f'grouping={analysis["primaryGrouping"]}')
    
    # 3. Build complete output structure
    output = {
        'schema': 'dna-balkan-folk-profiles',
        'version': '9.30.0',
        'authority': {
            'velocity': 'FACTORY',
            'timing': 'GOLD_PATTERN',
            'ornaments': 'RULE_BASED',
            'meterAccent': 'BALKAN_METRIC',
            'chordFoundation': 'MANDATORY',
        },
        'balkanMeters': BALKAN_METERS,
        'folkInstruments': FOLK_INSTRUMENTS,
        'balkanPatterns': {
            'drums': {m: pats for m, pats in balkan_drum.items() if pats},
            'performance': {m: pats for m, pats in balkan_perf.items() if pats},
        },
        'meterAnalyses': meter_analyses,
        'ornamentEngine': {
            'description': 'Generiše MIDI evente za folk ornamenta po instrumentu',
            'chordRequired': True,
            'scaleAware': True,
            'deterministicSeed': 'position-based',
        },
        'accentEngine': {
            'description': 'Izračunava timing i velocity skale za balkanske metre',
            'velocityMode': 'SCALE_FACTORY',  # nikad ne zamjenjuje Factory
            'timingMode': 'OFFSET_FROM_GRID',
        },
    }
    
    # 4. Save JSON
    json_path = DATA_DIR / 'balkan-folk-profiles-9.30.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f'\n✅ Balkan/folk JSON: {json_path}')
    
    # 5. Save SQLite
    db_path = DATA_DIR / 'balkan-folk-profiles-9.30.db'
    if db_path.exists():
        db_path.unlink()
    
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    
    # Meters table
    c.execute('''CREATE TABLE IF NOT EXISTS meters (
        meter TEXT PRIMARY KEY,
        full_name TEXT,
        primary_grouping TEXT,
        ppq_per_bar INTEGER,
        accent_pattern TEXT,
        tempo_min INTEGER,
        tempo_max INTEGER,
        pattern_count INTEGER
    )''')
    
    for m, info in BALKAN_METERS.items():
        analysis = meter_analyses.get(m, {})
        c.execute('INSERT OR REPLACE INTO meters VALUES (?,?,?,?,?,?,?,?)',
                  (m, info.get('fullName',''), info.get('primaryGrouping',''),
                   info.get('ppqPerBar',0), json.dumps(info.get('accentPattern',[])),
                   info.get('typicalTempoRange',[0,0])[0],
                   info.get('typicalTempoRange',[0,0])[1],
                   analysis.get('patternCount',0)))
    
    # Folk instruments table
    c.execute('''CREATE TABLE IF NOT EXISTS folk_instruments (
        instrument TEXT PRIMARY KEY,
        full_name TEXT,
        gm_patch INTEGER,
        family TEXT,
        role TEXT,
        velocity_authority TEXT,
        timing_authority TEXT,
        humanization TEXT,
        groove_profile TEXT,
        chord_required TEXT,
        typical_range TEXT,
        articulation TEXT,
        ornaments TEXT
    )''')
    
    for inst, info in FOLK_INSTRUMENTS.items():
        c.execute('INSERT OR REPLACE INTO folk_instruments VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                  (inst, info.get('fullName',''), info.get('GM_Patch',0),
                   info.get('family',''), info.get('role',''),
                   info.get('velocityAuthority',''), info.get('timingAuthority',''),
                   info.get('humanization',''), info.get('grooveProfile',''),
                   info.get('chordRequirement',''),
                   json.dumps(info.get('typicalRange',[])),
                   json.dumps(info.get('articulation',{})),
                   json.dumps(info.get('folkOrnaments',{}))))
    
    # Meter pattern stats
    c.execute('''CREATE TABLE IF NOT EXISTS meter_role_stats (
        meter TEXT,
        role TEXT,
        count INTEGER,
        avg_density REAL,
        PRIMARY KEY (meter, role)
    )''')
    
    for meter, analysis in meter_analyses.items():
        for role, count in analysis.get('roleDistribution', {}).items():
            c.execute('INSERT OR REPLACE INTO meter_role_stats VALUES (?,?,?,?)',
                      (meter, role, count, analysis.get('avgDensity',0)))
    
    conn.commit()
    conn.close()
    print(f'✅ Balkan/folk SQLite: {db_path}')
    
    # 6. Generate report
    report_path = DATA_DIR / 'balkan-folk-report-9.30.md'
    report = generate_balkan_report(output, meter_analyses)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f'✅ Balkan/folk report: {report_path} ({len(report.splitlines())} linija)')
    
    return output


def generate_balkan_report(output: dict, meter_analyses: dict) -> str:
    """Generiši Markdown izvještaj za Balkan/folk specijalizaciju."""
    lines = []
    lines.append('# DNA MIDI Studio 9.30 — Balkan/Folk Specialization Report')
    lines.append('')
    lines.append(f'**Schema:** {output["schema"]}')
    lines.append(f'**Version:** {output["version"]}')
    lines.append('')
    
    lines.append('## Autoriteti')
    lines.append('')
    for auth_key, auth_val in output['authority'].items():
        lines.append(f'- **{auth_key}**: {auth_val}')
    lines.append('')
    
    lines.append('## Balkanski Metri')
    lines.append('')
    for meter, info in output['balkanMeters'].items():
        analysis = meter_analyses.get(meter, {})
        lines.append(f'### {info["fullName"]}')
        lines.append('')
        lines.append(f'- **Grupiranje:** {info["primaryGrouping"]}')
        lines.append(f'- **Alternativna grupiranja:** {", ".join(info.get("altGroupings", []))}')
        lines.append(f'- **PPQ po taktu:** {info["ppqPerBar"]}')
        lines.append(f'- **Tempo raspon:** {info["typicalTempoRange"][0]}–{info["typicalTempoRange"][1]} BPM')
        lines.append(f'- **Patterna u Gold bazi:** {analysis.get("patternCount", 0)}')
        lines.append(f'- **Plesni stilovi:** {", ".join(info.get("danceStyles", []))}')
        lines.append(f'- **Distribucija po rolama:** {analysis.get("roleDistribution", {})}')
        lines.append(f'- **Prosječna gustina:** {analysis.get("avgDensity", 0)}')
        lines.append('')
        lines.append('**Akcent pattern:**')
        lines.append('')
        accent = info.get('accentPattern', [])
        for i, a in enumerate(accent):
            bar = '█' * int(a * 10) + '░' * (10 - int(a * 10))
            lines.append(f'| {i+1} | {a:.2f} | {bar} |')
        lines.append('')
    
    lines.append('## Folk Instrumenti')
    lines.append('')
    for inst, info in output['folkInstruments'].items():
        lines.append(f'### {info["fullName"]}')
        lines.append('')
        lines.append(f'- **GM Patch:** {info["GM_Patch"]}')
        lines.append(f'- **Familija:** {info["family"]}')
        lines.append(f'- **Primarna rola:** {info["role"]}')
        lines.append(f'- **Velocity autoritet:** {info["velocityAuthority"]}')
        lines.append(f'- **Timing autoritet:** {info["timingAuthority"]}')
        lines.append(f'- **Humanizacija:** {info["humanization"]}')
        lines.append(f'- **Chord obavezno:** {info["chordRequirement"]}')
        lines.append(f'- **Raspon:** {info["typicalRange"][0]}–{info["typicalRange"][1]}')
        lines.append('')
        
        ornaments = info.get('folkOrnaments', {})
        if ornaments:
            lines.append('**Ornamenti:**')
            lines.append('')
            lines.append('| Ornament | Vjerovatnost | Interval | Timing offset |')
            lines.append('|----------|-------------|----------|---------------|')
            for orn, conf in ornaments.items():
                prob = conf.get('probability', 0)
                interv = conf.get('interval', '—')
                timing = conf.get('timing', '—')
                lines.append(f'| {orn} | {prob:.0%} | {interv} | {timing} |')
            lines.append('')
    
    lines.append('## Determinizam i Hard Limits')
    lines.append('')
    lines.append('### BLOCK pravila')
    lines.append('- FACTORY velocity se NIKAD ne zamjenjuje — samo skalira (0.7–1.0)')
    lines.append('- Chord foundation je OBAVEZAN za sve folk instrumente')
    lines.append('- Ornament interval mora biti dijatonski (vezan za skalu)')
    lines.append('- Timing offset NIKAD ne prekoračuje ±6 PPQ')
    lines.append('')
    lines.append('### CLAMP pravila')
    lines.append('- Velocity scale: CLAMP(0.7, 1.0)')
    lines.append('- Timing offset: CLAMP(-6, +6) PPQ')
    lines.append('- Ornament probability: CLAMP(0, 1.0)')
    lines.append('- Vibrato depth: CLAMP(0, 20) cents')
    lines.append('')
    
    return '\n'.join(lines)


if __name__ == '__main__':
    build_balkan_folk_profiles()
