from pathlib import Path
from dna_midi_studio.candidate_preference_brain import CandidatePreferenceBrain
from dna_midi_studio.midi import MidiFile, MidiTrack, MidiEvent

ROOT=Path(__file__).resolve().parents[1]

def mk(good=True):
    # format1, ppq480: bass on track0/ch0 + drums track1/ch9
    tr0=[]; tr1=[]
    for i,t in enumerate(range(0,1920,480)):
        pitch=36+(i%2)*2
        tr0 += [MidiEvent(t,0,'channel',0x90,bytes([pitch,80])), MidiEvent(t+360,1,'channel',0x80,bytes([pitch,0]))]
        tr1 += [MidiEvent(t,0,'channel',0x99,bytes([36,100])), MidiEvent(t+120,1,'channel',0x89,bytes([36,0]))]
    m=MidiFile(1,480,[MidiTrack(tr0),MidiTrack(tr1)])
    if good: return m
    # pathological candidate: clustered duplicate bass notes off groove
    ev=[]
    for k in range(12):
        t=100+k*7; p=50
        ev += [MidiEvent(t,0,'channel',0x90,bytes([p,70])), MidiEvent(t+2,1,'channel',0x80,bytes([p,0]))]
    return MidiFile(1,480,[MidiTrack(ev),MidiTrack(tr1)])

def test_preference_prefers_musical_candidate():
    b=mk(True).to_bytes(); good=mk(True).to_bytes(); bad=mk(False).to_bytes()
    brain=CandidatePreferenceBrain(ROOT)
    gs=brain.score(b,good,track_index=0,channel=0,role='bass',start_tick=0,end_tick=1920)
    bs=brain.score(b,bad,track_index=0,channel=0,role='bass',start_tick=0,end_tick=1920)
    assert gs.total > bs.total
    assert gs.safety == 1.0
    assert 0 <= gs.total <= 1
