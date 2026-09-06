#!/usr/bin/env python3
"""DNA MIDI Studio 9.30 — Drum Element Sub-Profile Engine

Gradi detaljne sub-profile za svaki drum element (kick, snare, hihat, etc.)
koristeći Gold pattern podatke i Factory velocity reference.

Autoritet model:
  FACTORY  → velocity po elementu (iz drum kit GM mapa)
  GOLD     → timing, gate, density, groove po elementu (iz absolute-drum-note pitchova)
  CHORD    → interakcija kick/bass, hihat/ride sa promjenama

GM Drum Map (Channel 10):
  36=Bass Drum, 38=Snare, 42=Closed HH, 46=Open HH,
  49=Crash, 51=Ride, 47=Tom Low, 48=Tom Mid, 50=Tom High
"""

import json, sqlite3, math
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional, Any

DATA_DIR = Path(__file__).parent / 'data'
VERSION = '9.30.1'

# ── GM Drum Map ──
GM_DRUM_MAP = {
    36: {'name': 'kick',       'family': 'bass_drum',   'category': 'kick'},
    38: {'name': 'snare',      'family': 'snare',       'category': 'snare'},
    40: {'name': 'snare_ghost', 'family': 'snare',      'category': 'snare_ghost'},
    42: {'name': 'closed_hat', 'family': 'hihat',       'category': 'hihat_closed'},
    44: {'name': 'pedal_hat',  'family': 'hihat',       'category': 'hihat_pedal'},
    46: {'name': 'open_hat',   'family': 'hihat',       'category': 'hihat_open'},
    49: {'name': 'crash',      'family': 'cymbal',      'category': 'crash'},
    51: {'name': 'ride',       'family': 'cymbal',      'category': 'ride'},
    59: {'name': 'ride_bell',  'family': 'cymbal',      'category': 'ride_bell'},
    47: {'name': 'tom_low',    'family': 'tom',         'category': 'tom_low'},
    48: {'name': 'tom_mid',    'family': 'tom',         'category': 'tom_mid'},
    50: {'name': 'tom_high',   'family': 'tom',         'category': 'tom_high'},
    56: {'name': 'cowbell',    'family': 'percussion',  'category': 'cowbell'},
    37: {'name': 'side_stick', 'family': 'snare',       'category': 'side_stick'},
    39: {'name': 'clap',       'family': 'percussion',  'category': 'clap'},
}

# Inverzni map za prepoznavanje
PITCH_TO_ELEMENT = {k: v['name'] for k, v in GM_DRUM_MAP.items()}

# ── Element velocity reference (Factory drums kalibracija) ──
# Iz factory-velocity-catalog-9.30.json + drum kalibracija
ELEMENT_VELOCITY_REF = {
    'kick':       {'pp': 40, 'p': 65, 'mp': 80, 'mf': 95, 'f': 110, 'ff': 120, 'floor': 30, 'optimal': 95},
    'snare':      {'pp': 35, 'p': 60, 'mp': 78, 'mf': 98, 'f': 115, 'ff': 127, 'floor': 25, 'optimal': 98},
    'snare_ghost':{'pp': 20, 'p': 40, 'mp': 55, 'mf': 68, 'f': 82,  'ff': 95,  'floor': 15, 'optimal': 65},
    'closed_hat': {'pp': 30, 'p': 55, 'mp': 72, 'mf': 85, 'f': 100, 'ff': 115, 'floor': 25, 'optimal': 85},
    'pedal_hat':  {'pp': 25, 'p': 48, 'mp': 65, 'mf': 78, 'f': 92,  'ff': 105, 'floor': 20, 'optimal': 75},
    'open_hat':   {'pp': 35, 'p': 58, 'mp': 75, 'mf': 88, 'f': 105, 'ff': 118, 'floor': 28, 'optimal': 88},
    'crash':      {'pp': 50, 'p': 72, 'mp': 88, 'mf': 105,'f': 118, 'ff': 127, 'floor': 40, 'optimal': 108},
    'ride':       {'pp': 35, 'p': 58, 'mp': 74, 'mf': 88, 'f': 102, 'ff': 115, 'floor': 28, 'optimal': 88},
    'ride_bell':  {'pp': 40, 'p': 62, 'mp': 78, 'mf': 92, 'f': 108, 'ff': 120, 'floor': 32, 'optimal': 92},
    'tom_low':    {'pp': 40, 'p': 62, 'mp': 78, 'mf': 95, 'f': 110, 'ff': 122, 'floor': 30, 'optimal': 95},
    'tom_mid':    {'pp': 42, 'p': 65, 'mp': 80, 'mf': 98, 'f': 112, 'ff': 124, 'floor': 32, 'optimal': 98},
    'tom_high':   {'pp': 45, 'p': 68, 'mp': 83, 'mf': 100,'f': 114, 'ff': 126, 'floor': 35, 'optimal': 100},
    'cowbell':    {'pp': 40, 'p': 60, 'mp': 78, 'mf': 92, 'f': 108, 'ff': 120, 'floor': 30, 'optimal': 92},
    'side_stick': {'pp': 35, 'p': 55, 'mp': 72, 'mf': 85, 'f': 100, 'ff': 115, 'floor': 28, 'optimal': 85},
    'clap':       {'pp': 40, 'p': 62, 'mp': 80, 'mf': 98, 'f': 112, 'ff': 127, 'floor': 30, 'optimal': 98},
}

# ── Element timing reference ──
# Svaki element ima karakteristični timing offset i gate
ELEMENT_TIMING_REF = {
    'kick':       {'baseOffset': 0,  'earlyBias': 1,  'gateTypical': 8,  'grooveRole': 'ANCHOR'},
    'snare':      {'baseOffset': 0,  'earlyBias': 2,  'gateTypical': 6,  'grooveRole': 'BACKBEAT'},
    'snare_ghost':{'baseOffset': 0,  'earlyBias': 0,  'gateTypical': 4,  'grooveRole': 'GHOST_FILL'},
    'closed_hat': {'baseOffset': 0,  'earlyBias': -1, 'gateTypical': 3,  'grooveRole': 'PULSE'},
    'pedal_hat':  {'baseOffset': 0,  'earlyBias': 0,  'gateTypical': 5,  'grooveRole': 'PULSE_ALT'},
    'open_hat':   {'baseOffset': 0,  'earlyBias': 0,  'gateTypical': 8,  'grooveRole': 'ACCENT'},
    'crash':      {'baseOffset': -1, 'earlyBias': -2, 'gateTypical': 15, 'grooveRole': 'SECTION_MARK'},
    'ride':       {'baseOffset': 0,  'earlyBias': -1, 'gateTypical': 10, 'grooveRole': 'SWING_PULSE'},
    'ride_bell':  {'baseOffset': 0,  'earlyBias': -1, 'gateTypical': 8,  'grooveRole': 'ACCENT_PULSE'},
    'tom_low':    {'baseOffset': 0,  'earlyBias': 0,  'gateTypical': 8,  'grooveRole': 'FILL_VOICE'},
    'tom_mid':    {'baseOffset': 0,  'earlyBias': 0,  'gateTypical': 6,  'grooveRole': 'FILL_VOICE'},
    'tom_high':   {'baseOffset': 0,  'earlyBias': 0,  'gateTypical': 5,  'grooveRole': 'FILL_VOICE'},
    'cowbell':    {'baseOffset': 0,  'earlyBias': 0,  'gateTypical': 6,  'grooveRole': 'PATTERN_ACCENT'},
    'side_stick': {'baseOffset': 0,  'earlyBias': 1,  'gateTypical': 3,  'grooveRole': 'BACKBEAT_ALT'},
    'clap':       {'baseOffset': 0,  'earlyBias': 0,  'gateTypical': 5,  'grooveRole': 'ACCENT'},
}

# ── Element interaction rules ──
# Kako elementi komuniciraju jedni s drugima
ELEMENT_INTERACTIONS = {
    'kick_bass_coupling': {
        'description': 'Kick i Bass moraju sinhrono — kick je temporal anchor za bass',
        'rule': 'BLOCK_KICK_WITHOUT_BASS_ON_BEAT_1',
        'tolerance': 5,  # ticks
    },
    'snare_backbeat': {
        'description': 'Snare na 2 i 4 — standardni backbeat',
        'rule': 'SNARE_ON_BEATS_2_4',
        'accentLevel': 0.85,
    },
    'hihat_groove': {
        'description': 'Closed hat je osnova groova — 8th ili 16th pulse',
        'rule': 'HIHAT_STEADY_PULSE',
        'swingAffects': True,
    },
    'crash_section': {
        'description': 'Crash označava početak sekcije — intro/chorus/bridge',
        'rule': 'CRASH_ON_SECTION_CHANGE',
        'allowMultiple': False,
    },
    'ride_vs_hat': {
        'description': 'Ride zamjenjuje closed hat u swing/latin patternima',
        'rule': 'MUTUAL_EXCLUSION',
        'priority': 'ride',
    },
    'tom_fill': {
        'description': 'Tomovi se koriste samo u fill kontekstu',
        'rule': 'TOMS_ONLY_IN_FILL',
        'maxBars': 2,
    },
}


def load_gold_drum_patterns() -> list:
    """Učitaj Gold drum patterne."""
    gp = json.loads((DATA_DIR / 'gold-patterns.json').read_text(encoding='utf-8'))
    return [p for p in gp.get('patterns', []) if p.get('role') == 'drums']


def extract_element_stats(drum_patterns: list) -> Dict[str, Dict]:
    """Izvuci statistike po elementu iz Gold drum patterna."""
    element_data = defaultdict(lambda: {
        'velocities': [], 'gates': [], 'densities': [],
        'offsets': [], 'meters': [], 'sections': [],
        'beatPositions': [], 'syncopations': [],
        'totalNotes': 0, 'patternCount': 0,
    })
    
    for pat in drum_patterns:
        notes = pat.get('notes', [])
        meter = pat.get('meter', '4/4')
        density = pat.get('density', 0)
        section = pat.get('sourceSection', 'body')
        grid = pat.get('grid', '1/16')
        ticks_per_grid = 1  # u grid jedinicama
        
        for note in notes:
            if len(note) < 3:
                continue
            start, dur, pitch = note[0], note[1], note[2]
            
            elem_name = PITCH_TO_ELEMENT.get(pitch)
            if elem_name is None:
                # Nepoznat pitch — preskoči
                continue
            
            ed = element_data[elem_name]
            ed['totalNotes'] += 1
            ed['patternCount'] += 1 if start == 0 else 0  # count unique patterns
            ed['velocities'].append(pitch)  # placeholder — Gold nema velocity
            ed['gates'].append(dur)
            ed['densities'].append(density)
            ed['offsets'].append(start)
            ed['meters'].append(meter)
            ed['sections'].append(section)
            
            # Beat position analiza
            # 1/16 grid: beat=0, 4=1, 8=2, 12=3
            beat = start / 4 if grid == '1/16' else start / (pat.get('lengthBars', 1) * 16)
            ed['beatPositions'].append(beat)
            
            # Syncopacija: off-beat note
            if grid == '1/16':
                is_offbeat = start % 4 != 0
                ed['syncopations'].append(1 if is_offbeat else 0)
    
    # Agregiraj statistike
    stats = {}
    for elem, data in element_data.items():
        if data['totalNotes'] == 0:
            continue
        
        gates = sorted(data['gates'])
        offsets = sorted(data['offsets'])
        
        # Beat position distribucija
        beat_counts = Counter()
        for b in data['beatPositions']:
            beat_bucket = int(b) % 4  # beat 0,1,2,3
            beat_counts[beat_bucket] += 1
        total_beats = sum(beat_counts.values()) or 1
        beat_dist = {f'beat_{i}': beat_counts.get(i, 0) / total_beats for i in range(4)}
        
        # Meter distribucija
        meter_counts = Counter(data['meters'])
        total_m = sum(meter_counts.values()) or 1
        meter_dist = {k: v / total_m for k, v in meter_counts.most_common(5)}
        
        # Section distribucija
        sec_counts = Counter(data['sections'])
        total_s = sum(sec_counts.values()) or 1
        sec_dist = {k: v / total_s for k, v in sec_counts.most_common()}
        
        # Syncopation rate
        sync_rate = sum(data['syncopations']) / len(data['syncopations']) if data['syncopations'] else 0
        
        stats[elem] = {
            'totalNotes': data['totalNotes'],
            'patternCount': data['patternCount'],
            'gateMedian': gates[len(gates)//2] if gates else 0,
            'gateP5': gates[int(len(gates)*0.05)] if len(gates) > 5 else (gates[0] if gates else 0),
            'gateP95': gates[int(len(gates)*0.95)] if len(gates) > 5 else (gates[-1] if gates else 0),
            'avgDensity': sum(data['densities']) / len(data['densities']) if data['densities'] else 0,
            'syncopationRate': sync_rate,
            'beatDistribution': beat_dist,
            'meterDistribution': meter_dist,
            'sectionDistribution': sec_dist,
            'dominantBeat': max(beat_dist, key=beat_dist.get) if beat_dist else 'beat_0',
            'offBeatRatio': sync_rate,
        }
    
    return stats


def build_element_profile(elem_name: str, gold_stats: dict) -> dict:
    """Napravi sub-profil za jedan drum element."""
    gs = gold_stats.get(elem_name, {})
    vel_ref = ELEMENT_VELOCITY_REF.get(elem_name, ELEMENT_VELOCITY_REF['snare'])
    tim_ref = ELEMENT_TIMING_REF.get(elem_name, ELEMENT_TIMING_REF['snare'])
    gm_info = None
    for pitch, info in GM_DRUM_MAP.items():
        if info['name'] == elem_name:
            gm_info = info
            break
    
    confidence = min(1.0, gs.get('totalNotes', 0) / 500) if gs else 0
    
    return {
        'identity': {
            'element': elem_name,
            'gmPitch': next((p for p, v in GM_DRUM_MAP.items() if v['name'] == elem_name), 0),
            'family': gm_info['family'] if gm_info else 'unknown',
            'category': gm_info['category'] if gm_info else 'unknown',
            'grooveRole': tim_ref['grooveRole'],
        },
        'velocity': {
            'pp': vel_ref['pp'], 'p': vel_ref['p'], 'mp': vel_ref['mp'],
            'mf': vel_ref['mf'], 'f': vel_ref['f'], 'ff': vel_ref['ff'],
            'floor': vel_ref['floor'], 'optimal': vel_ref['optimal'],
            'source': 'FACTORY_DRUM_KIT',
            'authority': 'FACTORY_ONLY',
            'confidence': 0.90,  # Factory drums su visoko pouzdani
        },
        'timing': {
            'baseOffset': tim_ref['baseOffset'],
            'earlyBias': tim_ref['earlyBias'],
            'gateTypical': tim_ref['gateTypical'],
            'gateMedian': gs.get('gateMedian', tim_ref['gateTypical']),
            'gateP5': gs.get('gateP5', 1),
            'gateP95': gs.get('gateP95', tim_ref['gateTypical'] * 2),
            'syncopationRate': gs.get('syncopationRate', 0),
            'source': 'GOLD_PATTERN' if gs else 'REFERENCE_ESTIMATE',
            'authority': 'GOLD_PRIMARY_FACTORY_REFERENCE',
            'confidence': confidence,
        },
        'density': {
            'average': gs.get('avgDensity', 8),
            'beatDistribution': gs.get('beatDistribution', {'beat_0': 0.5, 'beat_1': 0.1, 'beat_2': 0.3, 'beat_3': 0.1}),
            'dominantBeat': gs.get('dominantBeat', 'beat_0'),
            'offBeatRatio': gs.get('offBeatRatio', 0),
        },
        'meter': {
            'distribution': gs.get('meterDistribution', {'4/4': 1.0}),
            'balkanMeters': {k: v for k, v in gs.get('meterDistribution', {}).items() if '/' in k and k != '4/4'},
        },
        'section': {
            'distribution': gs.get('sectionDistribution', {'body': 0.8, 'intro': 0.1, 'ending': 0.1}),
        },
        'interaction': _get_element_interactions(elem_name),
        'confidence': {
            'overall': confidence,
            'goldNoteCount': gs.get('totalNotes', 0),
            'factoryReference': True,
        },
    }


def _get_element_interactions(elem_name: str) -> dict:
    """Vrati relevantne interakcije za element."""
    interactions = {}
    
    if elem_name == 'kick':
        interactions['bassCoupling'] = ELEMENT_INTERACTIONS['kick_bass_coupling']
    elif elem_name == 'snare':
        interactions['backbeat'] = ELEMENT_INTERACTIONS['snare_backbeat']
    elif elem_name in ('closed_hat', 'pedal_hat'):
        interactions['groovePulse'] = ELEMENT_INTERACTIONS['hihat_groove']
    elif elem_name == 'crash':
        interactions['sectionMark'] = ELEMENT_INTERACTIONS['crash_section']
    elif elem_name == 'ride':
        interactions['hatExclusion'] = ELEMENT_INTERACTIONS['ride_vs_hat']
    elif elem_name in ('tom_low', 'tom_mid', 'tom_high'):
        interactions['fillRule'] = ELEMENT_INTERACTIONS['tom_fill']
    
    return interactions


def build_all_drum_element_profiles(output_dir: Path = None) -> dict:
    """Napravi sve drum element sub-profile."""
    output_dir = output_dir or DATA_DIR
    
    # Učitaj Gold podatke
    drum_patterns = load_gold_drum_patterns()
    print(f"  Učitano {len(drum_patterns)} Gold drum patterna")
    
    # Izvuci statistike
    element_stats = extract_element_stats(drum_patterns)
    print(f"  Pronađeno {len(element_stats)} elemenata sa podacima")
    for elem, stats in sorted(element_stats.items(), key=lambda x: -x[1]['totalNotes']):
        print(f"    {elem:15s}: {stats['totalNotes']:6d} nota, gate={stats['gateMedian']}, sync={stats['syncopationRate']:.2f}")
    
    # Gradi profile za sve poznate elemente
    profiles = {}
    for elem_name in GM_DRUM_MAP.values():
        name = elem_name['name']
        profiles[name] = build_element_profile(name, element_stats)
    
    # Output
    result = {
        'schema': 'dna-drum-element-profiles',
        'version': VERSION,
        'totalElements': len(profiles),
        'authority': {
            'velocity': 'FACTORY_DRUM_KIT',
            'timing': 'GOLD_PATTERN',
            'interaction': 'RULE_BASED',
            'chordFoundation': 'KICK_BASS_COUPLING',
        },
        'elements': profiles,
        'goldStatistics': element_stats,
        'drumEvidence': json.loads((DATA_DIR / 'drum-element-evidence-4.46.json').read_text()) if (DATA_DIR / 'drum-element-evidence-4.46.json').exists() else {},
    }
    
    # Sačuvaj JSON
    json_path = output_dir / 'drum-element-profiles-9.30.json'
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\n✅ Drum element JSON: {json_path}")
    
    # Sačuvaj SQLite
    db_path = output_dir / 'drum-element-profiles-9.30.db'
    _save_drum_sqlite(profiles, db_path)
    
    # Human report
    report_path = output_dir / 'drum-element-report-9.30.md'
    _save_drum_report(profiles, element_stats, report_path)
    
    return result


def _save_drum_sqlite(profiles: dict, db_path: Path):
    """Sačuvaj drum element profile u SQLite."""
    if db_path.exists():
        db_path.unlink()
    
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS elements (
        element TEXT PRIMARY KEY,
        gm_pitch INTEGER,
        family TEXT,
        category TEXT,
        groove_role TEXT,
        vel_pp INTEGER, vel_p INTEGER, vel_mp INTEGER,
        vel_mf INTEGER, vel_f INTEGER, vel_ff INTEGER,
        vel_floor INTEGER, vel_optimal INTEGER,
        base_offset REAL, early_bias REAL, gate_typical REAL,
        syncopation_rate REAL,
        gold_note_count INTEGER,
        confidence REAL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS beat_distribution (
        element TEXT, beat TEXT, ratio REAL,
        PRIMARY KEY (element, beat)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS meter_distribution (
        element TEXT, meter TEXT, ratio REAL,
        PRIMARY KEY (element, meter)
    )''')
    
    for elem, prof in profiles.items():
        ident = prof.get('identity', {})
        vel = prof.get('velocity', {})
        tim = prof.get('timing', {})
        conf = prof.get('confidence', {})
        
        c.execute('INSERT OR REPLACE INTO elements VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                  (elem, ident.get('gmPitch', 0), ident.get('family', ''),
                   ident.get('category', ''), ident.get('grooveRole', ''),
                   vel.get('pp', 0), vel.get('p', 0), vel.get('mp', 0),
                   vel.get('mf', 0), vel.get('f', 0), vel.get('ff', 0),
                   vel.get('floor', 0), vel.get('optimal', 0),
                   tim.get('baseOffset', 0), tim.get('earlyBias', 0),
                   tim.get('gateTypical', 0), tim.get('syncopationRate', 0),
                   conf.get('goldNoteCount', 0), conf.get('overall', 0)))
        
        # Beat distribution
        for beat, ratio in prof.get('density', {}).get('beatDistribution', {}).items():
            c.execute('INSERT OR REPLACE INTO beat_distribution VALUES (?,?,?)', (elem, beat, ratio))
        
        # Meter distribution
        for meter, ratio in prof.get('meter', {}).get('distribution', {}).items():
            c.execute('INSERT OR REPLACE INTO meter_distribution VALUES (?,?,?)', (elem, meter, ratio))
    
    conn.commit()
    conn.close()
    print(f"✅ Drum element SQLite: {db_path}")


def _save_drum_report(profiles: dict, stats: dict, report_path: Path):
    """Sačuvaj human-readable izvještaj."""
    lines = [
        '# DNA MIDI Studio 9.30 — Drum Element Sub-Profiles',
        '',
        f'**Verzija:** {VERSION}',
        f'**Ukupno elemenata:** {len(profiles)}',
        '',
        '## Autoritet Model',
        '',
        '| Domena | Autoritet |',
        '|---|---|',
        '| Velocity | FACTORY_DRUM_KIT |',
        '| Timing/Gate | GOLD_PATTERN |',
        '| Interakcija | RULE_BASED |',
        '| Chord Foundation | KICK_BASS_COUPLING |',
        '',
        '## Element Pregled',
        '',
        '| Element | GM# | Family | Groove Role | Notes | Gate | Sync | Conf |',
        '|---|---|---|---|---|---|---|---|',
    ]
    
    for elem, prof in sorted(profiles.items(), key=lambda x: -x[1].get('confidence', {}).get('goldNoteCount', 0)):
        ident = prof.get('identity', {})
        conf = prof.get('confidence', {})
        tim = prof.get('timing', {})
        lines.append(f"| {elem} | {ident.get('gmPitch',0)} | {ident.get('family','')} | {ident.get('grooveRole','')} | {conf.get('goldNoteCount',0)} | {tim.get('gateMedian',0)} | {tim.get('syncopationRate',0):.2f} | {conf.get('overall',0):.2f} |")
    
    lines.extend(['', '---', ''])
    
    # Detaljni profil po element
    for elem, prof in sorted(profiles.items()):
        ident = prof.get('identity', {})
        vel = prof.get('velocity', {})
        tim = prof.get('timing', {})
        conf = prof.get('confidence', {})
        inter = prof.get('interaction', {})
        
        lines.extend([
            f"## {elem.upper()}",
            '',
            f"- **GM Pitch:** {ident.get('gmPitch', 0)}",
            f"- **Family:** {ident.get('family', '')}",
            f"- **Groove Role:** {ident.get('grooveRole', '')}",
            '',
            '### Velocity',
            '',
            f"| pp | p | mp | mf | f | ff | floor | optimal |",
            f"|---|---|---|---|---|---|---|---|",
            f"| {vel.get('pp',0)} | {vel.get('p',0)} | {vel.get('mp',0)} | {vel.get('mf',0)} | {vel.get('f',0)} | {vel.get('ff',0)} | {vel.get('floor',0)} | {vel.get('optimal',0)} |",
            '',
            '### Timing',
            '',
            f"- Base offset: {tim.get('baseOffset', 0)}",
            f"- Early bias: {tim.get('earlyBias', 0)}",
            f"- Gate typical: {tim.get('gateTypical', 0)}",
            f"- Gate median (Gold): {tim.get('gateMedian', 0)}",
            f"- Syncopation rate: {tim.get('syncopationRate', 0):.2f}",
            '',
            '### Interakcije',
            '',
        ])
        
        for int_name, int_data in inter.items():
            lines.append(f"- **{int_name}:** {int_data.get('description', '')}")
            lines.append(f"  - Rule: `{int_data.get('rule', '')}`")
        
        lines.extend(['', '---', ''])
    
    report_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f"✅ Drum element report: {report_path} ({len(lines)} lines)")


if __name__ == '__main__':
    print("DNA MIDI Studio 9.30 — Drum Element Sub-Profile Engine")
    print("=" * 60)
    result = build_all_drum_element_profiles()
    print(f"\nUkupno elemenata: {result['totalElements']}")
    print(f"Autoriteti:")
    for k, v in result['authority'].items():
        print(f"  {k}: {v}")
