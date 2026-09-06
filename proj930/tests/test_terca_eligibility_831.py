from dna_midi_studio.midi import MidiFile, MidiTrack, MidiEvent, Note
from dna_midi_studio.ai_learning.melodic_relationship import MelodicRelationshipEngine, MelodicRelationshipRequest


def test_vocal_name_blocks_terca_source_helper(tmp_path):
    events=[
        MidiEvent(0,0,'meta',data=b'Lead Vocal',meta_type=0x03),
        MidiEvent(0,1,'channel',status=0x90,data=bytes([60,90])),
        MidiEvent(240,2,'channel',status=0x80,data=bytes([60,0])),
        MidiEvent(0,3,'meta',data=b'hello',meta_type=0x05),
        MidiEvent(240,4,'meta',data=b'',meta_type=0x2F),
    ]
    midi=MidiFile(1,480,[MidiTrack(events),MidiTrack([])])
    req=MelodicRelationshipRequest(0,0,1,1,1,1,'third')
    source=[Note(0,0,60,0,240,90)]
    ev=MelodicRelationshipEngine._source_vocal_evidence(midi,req,source,0,1920)
    assert ev['isVocalLike'] is True
    assert ev['explicitNameHint'] is True
