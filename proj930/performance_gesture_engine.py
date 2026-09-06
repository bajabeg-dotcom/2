#!/usr/bin/env python3
"""Deterministic instrument-performance gesture planner/applicator.

Design goals:
- Phrase-aware, not random.
- No GOLD velocity authority.
- No pitch-bend emission unless the caller explicitly supplies the bend range.
- Channel pitch-bend is emitted only inside a monophonic window.
- Every bend is reset to center before another unrelated note can be affected.
"""
from __future__ import annotations

from collections import defaultdict


def _active_overlap(notes, target):
    return [n for n in notes if n is not target and not n['on'].get('remove')
            and n['on']['tick'] < target['off']['tick'] and n['off']['tick'] > target['on']['tick']]


def _pb_bytes(value: int):
    value=max(-8192,min(8191,int(value)))+8192
    return [value & 0x7F, (value >> 7) & 0x7F]


def _add_pitchbend(track, channel, tick, value, order):
    data=_pb_bytes(value)
    track['events'].append({'tick':int(tick),'order':order,'status':0xE0|channel,
                           'kind':'channel','command':14,'channel':channel,'data':data,'remove':False})
    return order+1


def _phrase_position(index, size):
    if size <= 1: return 'single'
    ratio=index/(size-1)
    if ratio < .18: return 'start'
    if ratio > .82: return 'end'
    if .42 <= ratio <= .68: return 'peak'
    return 'body'


def _bass_slide_candidates(notes, ppq):
    ordered=sorted([n for n in notes if not n['on'].get('remove')], key=lambda n:(n['on']['tick'],n['pitch']))
    out=[]
    for i,(a,b) in enumerate(zip(ordered,ordered[1:])):
        gap=b['on']['tick']-a['off']['tick']
        interval=b['pitch']-a['pitch']
        if interval == 0 or abs(interval) > 7: continue
        if gap > ppq//8: continue
        # structural candidates: phrase pickup/end or strong semitone/tone/fourth/fifth motion
        pos=_phrase_position(i,len(ordered))
        score=.35
        score += .20 if abs(interval) in (1,2) else .10
        score += .15 if abs(interval) in (5,7) else 0
        score += .15 if pos in ('end','peak') else 0
        score += .10 if gap <= 0 else 0
        if score >= .55:
            out.append({'source':a,'target':b,'interval':interval,'score':round(score,4),'position':pos})
    return out


def plan_gestures(groups, ppq, options):
    report=[]
    for group in groups:
        role=group.get('role')
        notes=group.get('notes',[])
        if role == 'bass':
            for c in _bass_slide_candidates(notes,ppq):
                report.append({'role':'bass','gesture':'slide','track':group['track']['index'],
                               'channel':group['channel']+1,'sourceTick':c['source']['on']['tick'],
                               'targetTick':c['target']['on']['tick'],'interval':c['interval'],
                               'score':c['score'],'phrasePosition':c['position'],
                               'emit':'pitchbend' if options.get('pitchBendSemitones') else 'plan-only'})
    return report


def apply_gestures(parsed, groups, ppq, options, stats):
    plans=plan_gestures(groups,ppq,options)
    bend_range=options.get('pitchBendSemitones')
    if not bend_range:
        return {'enabled':bool(options.get('performanceGestures',False)),'plans':plans,'applied':0,
                'reason':'pitch-bend range not explicitly configured','safety':{'channelBend':False}}
    try: bend_range=float(bend_range)
    except Exception: bend_range=0
    if bend_range <= 0:
        return {'enabled':True,'plans':plans,'applied':0,'reason':'invalid pitch-bend range','safety':{'channelBend':False}}
    applied=0
    max_per_track=int(options.get('maxPitchGesturesPerTrack',12) or 12)
    grouped_notes={(g['track']['index'],g['channel']):g['notes'] for g in groups}
    per_track=defaultdict(int)
    for plan in sorted(plans,key=lambda x:(-x['score'],x['track'],x['sourceTick'])):
        if plan['score'] < float(options.get('gestureConfidence',.65)): continue
        key=(plan['track'],plan['channel']-1)
        if per_track[key]>=max_per_track: continue
        notes=grouped_notes.get(key,[])
        source=next((n for n in notes if n['on']['tick']==plan['sourceTick']),None)
        target=next((n for n in notes if n['on']['tick']==plan['targetTick']),None)
        if not source or not target: continue
        # Pitch bend is channel-wide: require no other sounding note in gesture window.
        window={'on':{'tick':source['on']['tick'],'remove':False},'off':{'tick':target['on']['tick']},'pitch':source['pitch']}
        overlaps=[n for n in notes if n not in (source,target) and not n['on'].get('remove')
                  and n['on']['tick'] < target['on']['tick'] and n['off']['tick'] > source['on']['tick']]
        if overlaps:
            stats['pitchGesturePolyphonyRejected']+=1; continue
        semitones=plan['interval']
        if abs(semitones) > bend_range:
            stats['pitchGestureRangeRejected']+=1; continue
        track=parsed['tracks'][plan['track']]
        order=max((e['order'] for e in track['events']),default=0)+1
        start=max(source['on']['tick'],source['off']['tick']-max(2,round(ppq/10)))
        end=max(start+1,target['on']['tick']-1)
        peak=int(round(8191*(semitones/bend_range)))
        order=_add_pitchbend(track,key[1],start,0,order)
        order=_add_pitchbend(track,key[1],start+(end-start)//2,round(peak*.55),order)
        order=_add_pitchbend(track,key[1],end,peak,order)
        order=_add_pitchbend(track,key[1],target['on']['tick'],0,order)
        applied+=1; per_track[key]+=1; stats['bassPitchSlidesApplied']+=1
    return {'enabled':True,'plans':plans,'applied':applied,
            'safety':{'explicitBendRange':bend_range,'monophonicOnly':True,'resetToZero':True,'goldVelocity':False}}
