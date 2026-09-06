from dna_midi_studio.rx_dnc_articulation_calibration import RxDncArticulationCalibration
from dna_midi_studio.midi import MidiFile, MidiTrack, MidiEvent


def mk(with_pb=True, out_pb=True):
    tr=[]
    tr.append(MidiEvent(tick=0,order=0,kind='channel',status=0xC0,data=bytes([23])))
    if with_pb: tr.append(MidiEvent(tick=10,order=1,kind='channel',status=0xE0,data=bytes([0,80])))
    for t,p in [(0,60),(240,62),(480,64)]:
        tr.append(MidiEvent(tick=t,order=10+t,kind='channel',status=0x90,data=bytes([p,90])))
        tr.append(MidiEvent(tick=t+200,order=20+t,kind='channel',status=0x80,data=bytes([p,0])))
    return MidiFile(format_type=1,ppq=480,tracks=[MidiTrack(events=tr)]).to_bytes()


def test_version(tmp_path):
    assert RxDncArticulationCalibration(tmp_path).VERSION=='9.30'

def test_no_velocity_and_no_trigger_insertion(tmp_path):
    c=RxDncArticulationCalibration(tmp_path)
    r=c.candidate_fit(mk(),mk(),track_index=0,channel=0,role='solo',start_tick=0,end_tick=1000)
    assert r.details['velocityUsed'] is False
    assert r.details['triggerInsertionAllowedByThisModule'] is False

def test_lost_pitchbend_scores_lower(tmp_path):
    c=RxDncArticulationCalibration(tmp_path)
    good=c.candidate_fit(mk(),mk(),track_index=0,channel=0,role='solo',start_tick=0,end_tick=1000)
    # build candidate without pitch bend
    m=MidiFile.from_bytes(mk())
    m.tracks[0].events=[e for e in m.tracks[0].events if e.command!=0xE0]
    bad=c.candidate_fit(mk(),m.to_bytes(),track_index=0,channel=0,role='solo',start_tick=0,end_tick=1000)
    assert bad.score < good.score
    assert any('PITCHBEND' in x for x in bad.conflicts)
