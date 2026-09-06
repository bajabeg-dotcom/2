import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import performance_gesture_engine as g


def note(p,s,e,v=90):
    return {'pitch':p,'on':{'tick':s,'data':[p,v],'remove':False},'off':{'tick':e,'data':[p,0],'remove':False}}


def test_plan_only_without_explicit_bend_range():
    notes=[note(40,0,450),note(42,460,900),note(47,910,1400)]
    group={'role':'bass','notes':notes,'track':{'index':0,'events':[]},'channel':0}
    parsed={'division':480,'tracks':[group['track']]}
    report=g.apply_gestures(parsed,[group],480,{'performanceGestures':True},Counter())
    assert report['applied']==0
    assert 'not explicitly configured' in report['reason']


def test_explicit_bend_has_reset_and_monophonic_guard():
    notes=[note(40,0,450),note(42,460,900),note(47,910,1400)]
    track={'index':0,'events':[]}
    group={'role':'bass','notes':notes,'track':track,'channel':0}
    parsed={'division':480,'tracks':[track]}
    stats=Counter()
    report=g.apply_gestures(parsed,[group],480,{'performanceGestures':True,'pitchBendSemitones':7,'gestureConfidence':.5},stats)
    assert report['applied']>=1
    bends=[e for e in track['events'] if e.get('command')==14]
    assert bends
    assert any(e['data']==[0,64] for e in bends)  # centered bend
