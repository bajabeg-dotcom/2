from pathlib import Path

from dna_midi_studio.full_song_autoregressive import FullSongAutoregressiveReconstructor
from dna_midi_studio.midi import MidiFile, Note

ROOT=Path(__file__).resolve().parents[1]


def _benchmark():
    return ROOT/'artifacts/session19-benchmark/song19-04.mid'


def test_healthy_song_is_not_blindly_regenerated():
    p=_benchmark(); eng=FullSongAutoregressiveReconstructor(ROOT)
    out=eng.reconstruct(p.read_bytes(),p.name,max_auto_regions=6,max_regenerate_regions=1,variants_per_region=5)
    assert out['report']['verification']['passed']
    assert out['report']['summary']['regeneratedRegions']==0


def test_catastrophic_duplicate_drum_region_can_regenerate_with_factory_velocity():
    p=_benchmark(); midi=MidiFile.from_bytes(p.read_bytes())
    drums=[n for n in midi.notes() if n.track==4 and n.channel==9 and n.start<7680]
    bad=[]
    for n in drums:
        for j in range(4):
            bad.append(Note(n.track,n.channel,n.pitch,n.start,min(n.end,n.start+15+j),n.velocity))
    raw=midi.replace_notes(track_index=4,channel=9,start_tick=0,end_tick=7680,new_notes=bad).to_bytes()
    eng=FullSongAutoregressiveReconstructor(ROOT)
    out=eng.reconstruct(raw,'corrupt.mid',max_auto_regions=6,max_regenerate_regions=1,variants_per_region=5)
    rep=out['report']
    assert rep['verification']['passed']
    assert rep['summary']['regeneratedRegions']==1
    action=next(a for a in rep['actions'] if a['status']=='REGENERATED')
    assert action['role']=='drums'
    assert action['promotedToRegenerate'] is True
    assert action['factoryVelocityProfileIds']
    assert action['chosenVariant'] in {'A','B','C'}
