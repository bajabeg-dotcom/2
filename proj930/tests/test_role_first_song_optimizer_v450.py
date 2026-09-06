from dna_midi_studio.midi import MidiFile, MidiTrack, MidiEvent
from dna_midi_studio.role_first_song_optimizer import optimize_role_first

def _mid(program=25):
    ev=[MidiEvent(0,0,'channel',0xC3,bytes([program]))]
    o=1
    for k,p in enumerate([60,64,67,60,64,67]):
        s=(k//3)*240
        ev += [MidiEvent(s,o,'channel',0x93,bytes([p,90])), MidiEvent(s+40,o+1,'channel',0x83,bytes([p,0]))]; o+=2
    ev.append(MidiEvent(500,o,'meta',meta_type=0x2F,data=b''))
    return MidiFile(1,480,[MidiTrack(ev)])

def test_guitar_pitch_velocity_invariant():
    m=_mid(); before=sorted((n.pitch,n.velocity) for n in m.notes())
    out,rep=optimize_role_first(m)
    assert sorted((n.pitch,n.velocity) for n in out.notes())==before
    assert rep['policy']['roleMapBeforeMutation']
