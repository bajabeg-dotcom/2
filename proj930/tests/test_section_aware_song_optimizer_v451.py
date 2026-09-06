from dna_midi_studio.midi import MidiFile
from dna_midi_studio.section_aware_song_optimizer import optimize_section_aware

def _fixture():
    # format-0, ppq 96; markers Intro@0, Verse@384, Chorus@768; guitar ch0 program25
    import mido, io
    mf=mido.MidiFile(type=0,ticks_per_beat=96); tr=mido.MidiTrack(); mf.tracks.append(tr)
    tr.append(mido.MetaMessage('marker',text='Intro',time=0)); tr.append(mido.Message('program_change',channel=0,program=25,time=0))
    # dense arpeggio notes through three sections
    abs_t=0
    for i in range(36):
        if i==12: tr.append(mido.MetaMessage('marker',text='Verse',time=0))
        if i==24: tr.append(mido.MetaMessage('marker',text='Chorus',time=0))
        tr.append(mido.Message('note_on',channel=0,note=55+(i%3)*4,velocity=90,time=32))
        tr.append(mido.Message('note_off',channel=0,note=55+(i%3)*4,velocity=0,time=6))
    tr.append(mido.MetaMessage('end_of_track',time=1)); b=io.BytesIO(); mf.save(file=b); return b.getvalue()

def test_section_map_precedes_mutation_and_preserves_pitch_velocity():
    m=MidiFile.from_bytes(_fixture()); before=sorted((n.pitch,n.velocity) for n in m.notes())
    out,rep=optimize_section_aware(m,'fixture.mid')
    assert rep['policy']['songMapBeforeMutation'] is True
    assert len(rep['songMap']['sections'])>=3
    assert sorted((n.pitch,n.velocity) for n in out.notes())==before

def test_echo_terca_policy_is_protected():
    _,rep=optimize_section_aware(MidiFile.from_bytes(_fixture()),'fixture.mid')
    assert rep['policy']['echoTercaProtected'] is True

def test_section_targets_differ():
    from dna_midi_studio.section_aware_song_optimizer import _section_target
    assert _section_target('rhythm-guitar','verse',96)!=_section_target('rhythm-guitar','chorus',96)
