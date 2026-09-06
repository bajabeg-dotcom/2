import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import special_track_engine as s


def N(p,t,d=240,v=90):
    on={'tick':t,'data':[p,v],'remove':False}
    off={'tick':t+d,'data':[p,0],'remove':False}
    return {'pitch':p,'on':on,'off':off}


def test_echo_source_selection_is_sparse_and_phrase_weighted():
    notes=[N(60,i*240,120 if i%2 else 300,70+i*3) for i in range(8)]
    chosen=s._select_echo_sources(notes,480,240,.40)
    assert 1 <= len(chosen) <= 4
    assert len(chosen) < len(notes)


def test_third_sequence_uses_voice_leading_and_allows_rest():
    notes=[N(60,0),N(62,480),N(64,960),N(65,1440)]
    harmony={i:{'confidence':.9,'pitchClasses':{0,4,7},'root':0,'quality':'major'} for i in range(4)}
    plan=s._plan_third_sequence(notes,harmony,480,{'low':48,'high':76})
    assert len(plan)==4
    pitches=[x[0] for x in plan if x[0] is not None]
    assert all(48<=p<=76 for p in pitches)
    assert all(kind in {'third-above','third-below','sixth-below','rest'} for _,kind,_ in plan)
