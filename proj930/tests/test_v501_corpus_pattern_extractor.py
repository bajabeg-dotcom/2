from pathlib import Path
from dna_midi_studio.midi import MidiFile, MidiTrack, channel_event, meta_event
from dna_midi_studio.corpus_pattern_extractor import extract_file_patterns, ingest_corpus, discover_midis
from dna_midi_studio.evidence_index import PatternEvidenceIndex
from dna_midi_studio.pattern_ir import extract_pattern_dna
from dna_midi_studio.pattern_quality import assess_pattern_quality
from dna_midi_studio.midi import Note

PPQ=96

def make_drum_file(path:Path):
    ev=[]; o=0
    # Track name and tempo (120 BPM)
    ev.append(meta_event(0,o,0x03,b'Drums')); o+=1
    ev.append(meta_event(0,o,0x51,(500000).to_bytes(3,'big'))); o+=1
    # 8 bars, channel 10 == zero-based 9. Kick/snare/hat with non-constant velocities.
    for bar in range(8):
        base=bar*4*PPQ
        for beat in range(4):
            s=base+beat*PPQ
            for pitch,vel,dur in [(36,100+(beat%2)*5,36),(42,62+(beat%3)*5,24)]:
                ev.append(channel_event(s,o,0x99,pitch,min(127,vel))); o+=1
                ev.append(channel_event(s+dur,o,0x89,pitch,0)); o+=1
            if beat in (1,3):
                ev.append(channel_event(s,o,0x99,38,92+(bar%3))); o+=1
                ev.append(channel_event(s+30,o,0x89,38,0)); o+=1
    MidiFile(0,PPQ,[MidiTrack(ev)]).write(path)

def test_quality_gate_rejects_saturated_degenerate_pattern():
    notes=[Note(0,0,60,i*PPQ, i*PPQ+2,127) for i in range(8)]
    p=extract_pattern_dna(notes,source_kind='GOLD',source_hash='a'*64,role='bass',section_label='chorus',
        ppq=PPQ,start_tick=0,end_tick=8*PPQ,quality=.5,confidence=.9)
    q=assess_pattern_quality(p)
    assert not q.accepted
    assert 'VELOCITY_SATURATION' in q.reasons

def test_extractor_segments_real_midi_into_pattern_dna(tmp_path:Path):
    mid=tmp_path/'drums.mid'; make_drum_file(mid)
    items,report=extract_file_patterns(mid,source_kind='FACTORY',phrase_bars=2)
    assert report.status=='PASS'
    assert report.extracted>0
    assert any(x.dna.role=='drums' for x in items)
    assert any(x.quality.accepted for x in items)
    assert all(x.dna.source_kind=='FACTORY' for x in items)

def test_ingest_writes_only_accepted_patterns(tmp_path:Path):
    mid=tmp_path/'drums.mid'; make_drum_file(mid)
    idx=PatternEvidenceIndex(tmp_path/'evidence.sqlite')
    r=ingest_corpus([mid],idx,source_kind='FACTORY')
    assert r['summary']['patterns_extracted']>0
    assert r['summary']['patterns_accepted']==idx.count()
    assert idx.count()>0
    idx.close()

def test_discover_midis_is_recursive_and_deterministic(tmp_path:Path):
    a=tmp_path/'b.mid'; a.write_bytes(b'x')
    sub=tmp_path/'sub'; sub.mkdir(); b=sub/'A.MIDI'; b.write_bytes(b'x')
    got=discover_midis(tmp_path)
    assert set(got)=={a,b}
    assert got==sorted(got,key=lambda x:str(x).lower())


def make_solo_family_file(path:Path, program:int, name:bytes=b'Solo'):
    ev=[]; o=0
    ev.append(meta_event(0,o,0x03,name)); o+=1
    ev.append(channel_event(0,o,0xC0,program)); o+=1
    # Monophonic melodic track, enough notes for solo classifier / evidence.
    for i,pitch in enumerate([60,62,64,67,69,67,64,62,60,64,67,72,71,69,67,64]):
        s=i*PPQ//2
        ev.append(channel_event(s,o,0x90,pitch,76+(i%5)*3)); o+=1
        ev.append(channel_event(s+PPQ//3,o,0x80,pitch,0)); o+=1
    MidiFile(0,PPQ,[MidiTrack(ev)]).write(path)

def test_solo_evidence_keeps_physical_instrument_family(tmp_path:Path):
    mid=tmp_path/'accordion_solo.mid'; make_solo_family_file(mid,21,b'Accordion Solo')
    items,report=extract_file_patterns(mid,source_kind='GOLD',phrase_bars=2)
    assert report.status=='PASS'
    assert any(x.dna.instrument_family=='accordion' for x in items)
