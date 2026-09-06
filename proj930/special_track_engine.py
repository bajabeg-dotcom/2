#!/usr/bin/env python3
"""Deterministički FX, Solo, Delay i Terca sloj bez GOLD dinamike/programa."""

from __future__ import annotations

import math
import statistics
from collections import Counter, defaultdict

import factory_velocity


FX_ROLE_TARGETS = {
    "drums": {91: 16, 93: 0},
    "bass": {91: 7, 93: 0},
    "rhythm-guitar": {91: 17, 93: 9},
    "solo": {91: 25, 93: 7},
    "echo": {91: 18, 93: 5},
    "third": {91: 21, 93: 6},
    "pad": {91: 34, 93: 15},
    "chords": {91: 22, 93: 11},
    "accompaniment": {91: 18, 93: 6},
}


def _track_name(track):
    for event in track["events"]:
        if event["kind"] == "meta" and event["metaType"] == 3:
            return event["payload"].decode("utf-8", "replace").strip("\0 ")
    return ""


def _max_polyphony(notes):
    sweep = []
    for note in notes:
        sweep.append((note["on"]["tick"], 1))
        sweep.append((note["off"]["tick"], -1))
    active = maximum = 0
    for _, change in sorted(sweep, key=lambda item: (item[0], item[1])):
        active += change
        maximum = max(maximum, active)
    return maximum


def _classify_role(channel, notes, name, ppq):
    pitches = sorted(note["pitch"] for note in notes)
    median_pitch = statistics.median(pitches) if pitches else 60
    durations = [max(1, note["off"]["tick"] - note["on"]["tick"]) for note in notes]
    median_duration = statistics.median(durations) if durations else 0
    programs = Counter(note.get("program", 0) for note in notes)
    program = programs.most_common(1)[0][0] if programs else 0
    onsets = defaultdict(int)
    for note in notes:
        onsets[note["on"]["tick"]] += 1
    polyphonic_onsets = sum(value > 1 for value in onsets.values()) / max(1, len(onsets))
    maximum_polyphony = _max_polyphony(notes)
    lowered = name.lower()
    if channel == 9:
        role, confidence = "drums", 1.0
    elif 32 <= program <= 39 or median_pitch < 48:
        role, confidence = "bass", .9
    elif any(word in lowered for word in ("echo", "delay", "odjek")):
        role, confidence = "echo", .99
    elif any(word in lowered for word in ("terca", "third", "2nd voice", "second voice", "harmony solo")):
        role, confidence = "third", .99
    elif any(word in lowered for word in ("solo", "lead", "melody", "sax", "trumpet")):
        role, confidence = "solo", .95
    elif 24 <= program <= 31 and polyphonic_onsets >= .12:
        role, confidence = "rhythm-guitar", .88
    elif maximum_polyphony <= 2 and polyphonic_onsets < .12 and median_pitch >= 52:
        role, confidence = "solo", .78
    elif median_duration >= ppq and maximum_polyphony >= 3:
        role, confidence = "pad", .72
    elif polyphonic_onsets >= .2 or maximum_polyphony >= 3:
        role, confidence = "chords", .8
    else:
        role, confidence = "accompaniment", .62
    return {
        "role": role, "confidence": confidence, "program": program,
        "medianPitch": round(median_pitch, 2), "medianDurationTicks": round(median_duration, 2),
        "maximumPolyphony": maximum_polyphony,
        "polyphonicOnsetRatio": round(polyphonic_onsets, 4),
    }


def analyze_roles(parsed, notes_by_track, ppq):
    internal, public = [], []
    for track in parsed["tracks"]:
        grouped = defaultdict(list)
        for note in notes_by_track.get(track["index"], []):
            if not note["on"].get("remove"):
                grouped[note["channel"]].append(note)
        name = _track_name(track)
        for channel, notes in sorted(grouped.items()):
            evidence = _classify_role(channel, notes, name, ppq)
            record = {"track": track, "channel": channel, "notes": notes, "trackName": name, **evidence}
            internal.append(record)
            public.append({"track": track["index"], "channel": channel + 1,
                           "trackName": name or f"Track {track['index'] + 1}",
                           "noteCount": len(notes), **evidence})
    return internal, public


def _first_meter_bar_ticks(parsed, ppq):
    for track in parsed["tracks"]:
        for event in track["events"]:
            if event["kind"] == "meta" and event["metaType"] == 88 and len(event["payload"]) >= 2:
                numerator = max(1, event["payload"][0])
                denominator = 2 ** event["payload"][1]
                return max(1, round(ppq * numerator * 4 / denominator))
    return ppq * 4


def _harmonic_map(groups, bar_ticks):
    histograms = defaultdict(Counter)
    for group in groups:
        if group["role"] == "drums":
            continue
        for note in group["notes"]:
            histograms[note["on"]["tick"] // bar_ticks][note["pitch"] % 12] += 1
    output = {}
    for bar, histogram in histograms.items():
        total = sum(histogram.values())
        candidates = []
        for root in range(12):
            for quality, intervals in (("major", (0, 4, 7)), ("minor", (0, 3, 7))):
                pcs = {(root + interval) % 12 for interval in intervals}
                support = sum(histogram[pitch] for pitch in pcs)
                outside = total - support
                score = support - outside * .18
                candidates.append((score, support / max(1, total), root, quality, pcs))
        score, confidence, root, quality, pcs = max(candidates)
        output[bar] = {"root": root, "quality": quality, "pitchClasses": pcs,
                       "confidence": round(confidence, 4), "score": round(score, 4)}
    return output


def _existing_delay(notes, delay_ticks, tolerance, name):
    if any(word in name.lower() for word in ("delay", "echo")):
        return True
    onsets = defaultdict(set)
    for note in notes:
        onsets[note["pitch"]].add(note["on"]["tick"])
    matches = 0
    for note in notes:
        target = note["on"]["tick"] + delay_ticks
        if any(abs(candidate - target) <= tolerance for candidate in onsets[note["pitch"]]):
            matches += 1
    return matches >= 3 and matches / max(1, len(notes)) >= .18


def _existing_third(notes, tolerance, name):
    if any(word in name.lower() for word in ("terca", "third", "harmony")):
        return True
    buckets, onset_pitches = defaultdict(list), defaultdict(list)
    width = max(1, tolerance + 1)
    for note in notes:
        buckets[note["on"]["tick"] // width].append((note["on"]["tick"], note["pitch"]))
        onset_pitches[note["on"]["tick"]].append(note["pitch"])
    matches = 0
    for tick, pitches in onset_pitches.items():
        bucket = tick // width
        nearby = [pitch for candidate in (bucket - 1, bucket, bucket + 1)
                  for other_tick, pitch in buckets[candidate] if abs(other_tick - tick) <= tolerance]
        if any(abs(one - two) in (3, 4, 8, 9) for one in pitches for two in nearby if one != two):
            matches += 1
    return matches >= 3 and matches / max(1, len(onset_pitches)) >= .2



def _nearest_note(notes, tick, *, pitch=None, tolerance=12):
    candidates = [note for note in notes
                  if (pitch is None or note["pitch"] == pitch)
                  and abs(note["on"]["tick"] - tick) <= tolerance
                  and not note["on"].get("remove")]
    if not candidates:
        return None
    return min(candidates, key=lambda note: (abs(note["on"]["tick"] - tick), abs(note["pitch"] - (pitch if pitch is not None else note["pitch"]))))


def _echo_similarity(main_notes, aux_notes, ppq):
    if not main_notes or not aux_notes:
        return {"score": 0.0, "delayTicks": round(ppq / 2), "matched": []}
    tolerance = max(2, round(ppq / 32))
    candidate_delays = sorted(set([round(ppq * ratio) for ratio in (.25, .5, .75, 1.0)] +
                                  [max(1, aux["on"]["tick"] - main["on"]["tick"])
                                   for main in main_notes[:32] for aux in aux_notes[:32]
                                   if main["pitch"] == aux["pitch"] and 0 < aux["on"]["tick"] - main["on"]["tick"] <= ppq * 2]))
    best = (0.0, round(ppq / 2), [])
    for delay in candidate_delays[:256]:
        matches=[]
        used=set()
        for mi, main in enumerate(main_notes):
            target=main["on"]["tick"]+delay
            candidates=[(ai, aux) for ai, aux in enumerate(aux_notes) if ai not in used and aux["pitch"]==main["pitch"] and abs(aux["on"]["tick"]-target)<=tolerance]
            if candidates:
                ai, aux=min(candidates, key=lambda item: abs(item[1]["on"]["tick"]-target))
                used.add(ai); matches.append((mi, ai))
        coverage=len(matches)/max(1, min(len(main_notes), len(aux_notes)))
        density=min(len(main_notes),len(aux_notes))/max(len(main_notes),len(aux_notes))
        score=coverage*(.85+.15*density)
        if score>best[0]: best=(score,delay,matches)
    return {"score": round(best[0],4), "delayTicks": int(best[1]), "matched": best[2], "tolerance": tolerance}


def _third_similarity(main_notes, aux_notes, ppq):
    if not main_notes or not aux_notes:
        return {"score": 0.0, "matched": []}
    tolerance=max(2,round(ppq/48)); matches=[]; used=set()
    for mi, main in enumerate(main_notes):
        candidates=[(ai,aux) for ai,aux in enumerate(aux_notes) if ai not in used and abs(aux["on"]["tick"]-main["on"]["tick"])<=tolerance and abs(aux["pitch"]-main["pitch"]) in (3,4,8,9)]
        if candidates:
            ai,aux=min(candidates,key=lambda item:(abs(item[1]["on"]["tick"]-main["on"]["tick"]),abs(item[1]["pitch"]-main["pitch"])))
            used.add(ai); matches.append((mi,ai))
    coverage=len(matches)/max(1,min(len(main_notes),len(aux_notes)))
    density=min(len(main_notes),len(aux_notes))/max(len(main_notes),len(aux_notes))
    return {"score": round(coverage*(.85+.15*density),4), "matched": matches, "tolerance": tolerance}




def _note_importance(notes, index, ppq):
    note=notes[index]
    dur=max(1,note["off"]["tick"]-note["on"]["tick"])
    prev_gap=note["on"]["tick"]-(notes[index-1]["off"]["tick"] if index else note["on"]["tick"]-ppq)
    next_gap=(notes[index+1]["on"]["tick"]-note["off"]["tick"] if index+1<len(notes) else ppq)
    score=.25+min(.35,dur/max(1,ppq)*.22)
    if prev_gap>=ppq/8: score+=.12
    if next_gap>=ppq/8: score+=.18
    if index in (0,len(notes)-1): score+=.10
    vel=note["on"]["data"][1]
    score+=min(.15,max(0,(vel-64)/63)*.15)
    return round(min(1.0,score),4)

def _select_echo_sources(notes, ppq, delay_ticks, max_density=.55):
    if not notes: return []
    ranked=[]
    for i,n in enumerate(notes):
        dur=max(1,n["off"]["tick"]-n["on"]["tick"])
        if dur<ppq/10: continue
        imp=_note_importance(notes,i,ppq)
        # Echo must not land on top of the next strong main-note attack.
        landing=n["on"]["tick"]+delay_ticks
        collision=any(abs(other["on"]["tick"]-landing)<=max(2,ppq//32) and j!=i
                      for j,other in enumerate(notes))
        if collision: imp-=.22
        ranked.append((imp,i,n))
    keep=max(1,round(len(notes)*max(0.15,min(.75,max_density))))
    chosen=sorted(ranked,key=lambda x:(-x[0],x[2]["on"]["tick"]))[:keep]
    return [n for score,i,n in sorted(chosen,key=lambda x:x[2]["on"]["tick"]) if score>=.35]

def _third_candidates(pitch, chord):
    if not chord or chord.get("confidence",0)<.55: return []
    pcs=chord["pitchClasses"]
    candidates=[]
    for delta,kind in ((4,"third-above"),(3,"third-above"),(-3,"third-below"),(-4,"third-below"),(8,"sixth-above"),(9,"sixth-above"),(-8,"sixth-below"),(-9,"sixth-below")):
        q=pitch+delta
        if 0<=q<=127 and q%12 in pcs: candidates.append((q,kind))
    candidates.append((None,"rest"))
    return candidates

def _plan_third_sequence(notes, harmony, bar_ticks, register=None):
    """Dynamic-programming harmony path with voice-leading and optional rests."""
    if not notes: return []
    states=[]
    for n in notes:
        chord=harmony.get(n["on"]["tick"]//bar_ticks)
        row=[]
        for pitch,kind in _third_candidates(n["pitch"],chord):
            if pitch is not None and register:
                pitch=_fold_same_pitch_class(pitch,register)
                if pitch is None: continue
            local=.0
            if kind=="third-above": local=.72
            elif kind=="third-below": local=.64
            elif kind=="sixth-below": local=.58
            else: local=.16
            row.append((pitch,kind,local))
        states.append(row or [(None,"rest",.1)])
    dp=[]; back=[]
    for i,row in enumerate(states):
        drow=[]; brow=[]
        for j,(pitch,kind,local) in enumerate(row):
            if i==0: drow.append(local); brow.append(-1); continue
            best=(-10**9,-1)
            for k,(ppitch,pkind,_) in enumerate(states[i-1]):
                trans=0.0
                if pitch is None or ppitch is None: trans-=.08
                else:
                    leap=abs(pitch-ppitch)
                    trans-=min(.38,leap*.025)
                    if leap<=5: trans+=.10
                    if pitch==ppitch: trans+=.04
                value=dp[i-1][k]+local+trans
                if value>best[0]: best=(value,k)
            drow.append(best[0]); brow.append(best[1])
        dp.append(drow); back.append(brow)
    j=max(range(len(dp[-1])),key=lambda x:dp[-1][x]); out=[]
    for i in range(len(states)-1,-1,-1):
        out.append(states[i][j]); j=back[i][j]
    out.reverse(); return out

def _factory_layer_velocity(main_note, profiles_by_key, *, drop):
    profile=profiles_by_key.get(main_note.get("instrumentKey"))
    if not profile or int(profile.get("samples",0)) < 32:
        return None
    intensity=(main_note["on"]["data"][1]-1)*100/126
    return factory_velocity.velocity_at(profile,max(0,intensity-drop))


def _set_note(note, *, pitch=None, start=None, end=None, velocity=None):
    if pitch is not None:
        note["pitch"]=int(pitch); note["on"]["data"][0]=int(pitch); note["off"]["data"][0]=int(pitch)
    if start is not None: note["on"]["tick"]=int(start)
    if end is not None: note["off"]["tick"]=max(note["on"]["tick"]+1,int(end))
    if velocity is not None: note["on"]["data"][1]=max(1,min(127,int(velocity)))


def _remove_note(note):
    note["on"]["remove"]=True; note["off"]["remove"]=True


def _diatonic_third_target(pitch, chord, current_pitch=None):
    """Choose a scale-valid 3rd/6th voice; preserve existing voicing when repairing."""
    if not chord or chord.get("confidence",0) < .55:
        return None
    intervals=(0,2,4,5,7,9,11) if chord.get("quality")=="major" else (0,2,3,5,7,8,10)
    root=int(chord.get("root",0)); candidates=[]
    for delta in (3,4,-3,-4,8,9,-8,-9):
        q=pitch+delta
        if 0<=q<=127 and ((q-root)%12 in intervals):
            candidates.append(q)
    if not candidates:return None
    if current_pitch is not None:
        return min(candidates,key=lambda q:(abs(q-current_pitch),abs(q-pitch),q))
    close=[q for q in candidates if abs(q-pitch) in (3,4)]
    return min(close,key=lambda q:(abs(q-pitch),q)) if close else min(candidates,key=lambda q:(abs(q-pitch),q))

def optimize_existing_echo_terca(groups, harmony, bar_ticks, ppq, profiles_by_key, options, stats):
    """Repair/rebuild existing Echo and Terca tracks against a protected MAIN SOLO.

    MAIN SOLO is melodic authority. GOLD-style relationships may influence delay/gate/density,
    while generated/adjusted velocity remains Factory-only. Existing auxiliary tracks are allowed
    to change notes; the MAIN SOLO group is never mutated here.
    """
    solos=[g for g in groups if g["role"]=="solo" and g["confidence"]>=.7]
    named_aux=[g for g in groups if g["role"] in ("echo","third")]
    report=[]
    if not solos:
        return report
    # MAIN SOLO: prefer explicit solo/lead/melody naming, then confidence and note coverage.
    def main_rank(g):
        name=g.get("trackName","").lower()
        explicit=1 if any(w in name for w in ("solo","lead","melody")) else 0
        return (explicit,g["confidence"],len(g["notes"]))
    primary=max(solos,key=main_rank)
    auxiliaries=list(named_aux)
    # Legacy MIDI often names tracks generically. Infer Echo/Terca only when a second melodic
    # group has a strong relational fingerprint against MAIN SOLO.
    for candidate in solos:
        if candidate is primary: continue
        main_notes=sorted(primary["notes"],key=lambda n:(n["on"]["tick"],n["pitch"]))
        aux_notes=sorted(candidate["notes"],key=lambda n:(n["on"]["tick"],n["pitch"]))
        echo=_echo_similarity(main_notes,aux_notes,ppq)
        third=_third_similarity(main_notes,aux_notes,ppq)
        kind,score=("echo",echo["score"]) if echo["score"]>=third["score"] else ("third",third["score"])
        name=(candidate.get("trackName") or "").lower()
        explicit_third_hint=any(tok in name for tok in ("terca","third","2nd voice","second voice","harmony solo","harm solo"))
        # 8.31: never reinterpret an ordinary second solo as terca merely because
        # intervals happen to line up. Echo remains relationship-inferable; terca
        # requires an explicit auxiliary-harmony identity.
        eligible=(kind=="echo" and score>=.72) or (kind=="third" and explicit_third_hint and score>=.72)
        if eligible:
            inferred=dict(candidate); inferred["role"]=kind; inferred["inferredAuxRole"]=True
            auxiliaries.append(inferred)
    if not auxiliaries:
        return report
    for aux in auxiliaries:
        kind=aux["role"]
        scorer=_echo_similarity if kind=="echo" else _third_similarity
        candidates=[]
        for main in solos:
            if aux.get("inferredAuxRole") and main is not primary:
                continue
            if main["track"]["index"]==aux["track"]["index"] and main["channel"]==aux["channel"]:
                continue
            sim=scorer(sorted(main["notes"],key=lambda n:(n["on"]["tick"],n["pitch"])), sorted(aux["notes"],key=lambda n:(n["on"]["tick"],n["pitch"])), ppq)
            candidates.append((sim["score"],main,sim))
        if not candidates: continue
        score,main,sim=max(candidates,key=lambda x:x[0])
        main_notes=sorted(main["notes"],key=lambda n:(n["on"]["tick"],n["pitch"]))
        aux_notes=sorted(aux["notes"],key=lambda n:(n["on"]["tick"],n["pitch"]))
        explicit=not aux.get("inferredAuxRole",False)
        mode="PRESERVE" if score>=.88 else ("REPAIR" if score>=.58 else ("REBUILD" if explicit else "MANUAL_REVIEW"))
        if mode=="REBUILD" and main["confidence"]<.85:
            mode="MANUAL_REVIEW"
        matched_map={ai:mi for mi,ai in sim.get("matched",[])}
        changed=removed=generated=0
        next_order=max((e["order"] for e in aux["track"]["events"]),default=0)+1
        if mode in ("PRESERVE","REPAIR"):
            for ai,mi in matched_map.items():
                source=main_notes[mi]; note=aux_notes[ai]
                if kind=="echo":
                    target_start=source["on"]["tick"]+sim["delayTicks"]
                    source_dur=max(1,source["off"]["tick"]-source["on"]["tick"])
                    ratio=.72 if mode=="PRESERVE" else .66
                    target_end=target_start+max(1,round(source_dur*ratio))
                    vel=_factory_layer_velocity(source,profiles_by_key,drop=30)
                    before=(note["on"]["tick"],note["off"]["tick"],note["pitch"],note["on"]["data"][1])
                    _set_note(note,start=target_start,end=target_end,velocity=vel)
                else:
                    chord=harmony.get(source["on"]["tick"]//bar_ticks); target_pitch=_diatonic_third_target(source["pitch"],chord,note["pitch"])
                    if target_pitch is None: continue
                    source_dur=max(1,source["off"]["tick"]-source["on"]["tick"])
                    vel=_factory_layer_velocity(source,profiles_by_key,drop=12)
                    before=(note["on"]["tick"],note["off"]["tick"],note["pitch"],note["on"]["data"][1])
                    _set_note(note,pitch=target_pitch,start=source["on"]["tick"],end=source["on"]["tick"]+round(source_dur*.9),velocity=vel)
                after=(note["on"]["tick"],note["off"]["tick"],note["pitch"],note["on"]["data"][1])
                if after!=before: changed+=1
            if mode=="REPAIR" and score>=.7:
                for ai,note in enumerate(aux_notes):
                    if ai not in matched_map:
                        _remove_note(note); removed+=1
        elif mode=="REBUILD":
            for note in aux_notes: _remove_note(note); removed+=1
            limit=min(512,max(8,round(len(main_notes)*(.7 if kind=="echo" else .9))))
            previous_source=-10**12
            source_iter = (_select_echo_sources(main_notes,ppq,sim.get("delayTicks") or round(ppq/2),.48)
                           if kind=="echo" else main_notes)
            third_plan = (_plan_third_sequence(main_notes,harmony,bar_ticks,
                          (profiles_by_key.get(main_notes[0].get("instrumentKey")) or {}).get("register"))
                          if kind=="third" else None)
            for source_index,source in enumerate(source_iter):
                if generated>=limit: break
                dur=max(1,source["off"]["tick"]-source["on"]["tick"])
                if kind=="echo":
                    delay=sim.get("delayTicks") or round(ppq/2)
                    if dur<ppq/10 or source["on"]["tick"]-previous_source<ppq/4: continue
                    start=source["on"]["tick"]+delay; end=start+max(1,min(round(dur*.62),round(delay*.82)))
                    pitch=source["pitch"]; vel=_factory_layer_velocity(source,profiles_by_key,drop=34)
                    previous_source=source["on"]["tick"]
                else:
                    # Find original index because source_iter is main_notes for thirds.
                    pitch,kind_name,_ = third_plan[source_index]
                    if pitch is None: continue
                    start=source["on"]["tick"]; end=start+max(1,round(dur*.88)); vel=_factory_layer_velocity(source,profiles_by_key,drop=14)
                if vel is None: continue
                next_order=_add_note(aux["track"],aux["channel"],pitch,start,end,vel,next_order); generated+=1
        stats[f"{kind}ExistingNotesChanged"] += changed
        stats[f"{kind}ExistingNotesRemoved"] += removed
        stats[f"{kind}RebuiltNotesGenerated"] += generated
        report.append({"kind":kind,"track":aux["track"]["index"],"inferred":bool(aux.get("inferredAuxRole",False)),"channel":aux["channel"]+1,"mainSoloTrack":main["track"]["index"],"mainSoloChannel":main["channel"]+1,"confidence":round(score,4),"mode":mode,"matched":len(sim.get("matched",[])),"sourceNotes":len(main_notes),"auxNotes":len(aux_notes),"changed":changed,"removed":removed,"generated":generated,"delayTicks":sim.get("delayTicks") if kind=="echo" else None,"authority":{"melody":"main-solo","velocity":"factory-only","relationship":"gold-compatible"}})
    return report

def _fold_same_pitch_class(pitch, register):
    if not register:
        return pitch if 0 <= pitch <= 127 else None
    low, high = int(register["low"]), int(register["high"])
    candidates = [pitch + octave * 12 for octave in range(-10, 11)
                  if low <= pitch + octave * 12 <= high and 0 <= pitch + octave * 12 <= 127]
    return min(candidates, key=lambda value: (abs(value - pitch), value)) if candidates else None


def _add_note(track, channel, pitch, start, end, velocity, order):
    on = {"tick": start, "order": order, "status": 0x90 | channel, "kind": "channel",
          "command": 9, "channel": channel, "data": [pitch, velocity], "remove": False}
    off = {"tick": max(start + 1, end), "order": order + 1, "status": 0x80 | channel,
           "kind": "channel", "command": 8, "channel": channel,
           "data": [pitch, 0], "remove": False}
    track["events"].extend((on, off))
    track["endTick"] = max(track["endTick"], off["tick"])
    return order + 2


def _apply_fx(groups, strength, stats):
    ratio = max(0, min(100, int(strength))) / 100
    decisions = []
    if ratio <= 0:
        return decisions
    for group in groups:
        track, channel, role = group["track"], group["channel"], group["role"]
        targets = FX_ROLE_TARGETS[role]
        current = defaultdict(list)
        for event in track["events"]:
            if (event["kind"] == "channel" and event["command"] == 11
                    and event["channel"] == channel and event["data"][0] in (91, 93)):
                current[event["data"][0]].append(event)
        first_note = min(group["notes"], key=lambda note: (note["on"]["tick"], note["on"]["order"]))["on"]
        next_order = max((event["order"] for event in track["events"]), default=0) + 1
        for cc in (91, 93):
            events = current[cc]
            target = targets[cc]
            if events:
                baseline = statistics.median(event["data"][1] for event in events)
                shift = (target - baseline) * ratio
                for event in events:
                    value = max(0, min(127, round(event["data"][1] + shift)))
                    if value != event["data"][1]:
                        event["data"][1] = value
                        stats["fxControllersAdjusted"] += 1
            else:
                event = {"tick": first_note["tick"], "order": next_order,
                         "sortOrder": first_note["order"] - 0.4 + cc / 1000,
                         "status": 0xB0 | channel, "kind": "channel", "command": 11,
                         "channel": channel, "data": [cc, target], "remove": False}
                next_order += 1
                track["events"].append(event)
                stats["fxControllersInserted"] += 1
            decisions.append({"track": track["index"], "channel": channel + 1, "role": role,
                              "controller": cc, "target": target,
                              "authority": "deterministic-engine-policy-not-gold"})
    return decisions


def apply_special_tracks(parsed, notes_by_track, profiles_by_key, options, stats):
    ppq = parsed["division"] if not parsed["division"] & 0x8000 else None
    if not ppq:
        return {"enabled": False, "reason": "SMPTE timebase", "roles": [], "fx": [],
                "delay": [], "third": [], "budgets": {}}
    groups, public_roles = analyze_roles(parsed, notes_by_track, ppq)
    fx_decisions = _apply_fx(groups, options.get("fxStrength", 60), stats) if options.get("fxAuto") else []
    delay_enabled = bool(options.get("autoDelay"))
    third_enabled = bool(options.get("autoThird"))
    delay_division = int(options.get("delayDivision", 8) or 8)
    if delay_division not in (4, 8, 16):
        raise ValueError("Delay division mora biti 1/4, 1/8 ili 1/16")
    delay_ticks = round(ppq * 4 / delay_division)
    tolerance = max(1, round(ppq / 48))
    bar_ticks = _first_meter_bar_ticks(parsed, ppq)
    harmony = _harmonic_map(groups, bar_ticks)
    existing_layer_report = optimize_existing_echo_terca(groups, harmony, bar_ticks, ppq, profiles_by_key, options, stats)
    delay_report, third_report = [], []
    total_source_notes = sum(len(group["notes"]) for group in groups)
    global_budget = min(4000, max(0, round(total_source_notes * .18)))
    generated_total = 0

    for group in groups:
        if group["role"] != "solo" or group["confidence"] < .7:
            continue
        track, channel, notes = group["track"], group["channel"], sorted(
            group["notes"], key=lambda note: (note["on"]["tick"], note["pitch"]))
        has_delay = _existing_delay(notes, delay_ticks, tolerance, group["trackName"])
        has_third = _existing_third(notes, tolerance, group["trackName"])
        per_layer_budget = min(512, max(1, math.ceil(len(notes) * .25)))
        existing_keys = {(note["channel"], note["pitch"], note["on"]["tick"]) for note in notes}
        next_order = max((event["order"] for event in track["events"]), default=0) + 1

        delay_added, previous_delay_source = 0, -10**12
        if delay_enabled and not has_delay:
            for note in _select_echo_sources(notes,ppq,delay_ticks,float(options.get("echoDensity",.42))):
                if delay_added >= per_layer_budget or generated_total >= global_budget:
                    break
                duration = note["off"]["tick"] - note["on"]["tick"]
                if (duration < ppq / 8 or duration >= delay_ticks * .9
                        or note["on"]["tick"] - previous_delay_source < ppq / 2):
                    continue
                profile = profiles_by_key.get(note.get("instrumentKey"))
                if not profile or int(profile.get("samples", 0)) < 32:
                    continue
                start = note["on"]["tick"] + delay_ticks
                if (channel, note["pitch"], start) in existing_keys:
                    continue
                intensity = (note["on"]["data"][1] - 1) * 100 / 126
                velocity = factory_velocity.velocity_at(profile, max(0, intensity - 20))
                gate = max(1, min(round(duration * .58), round(delay_ticks * .9)))
                next_order = _add_note(track, channel, note["pitch"], start, start + gate, velocity, next_order)
                existing_keys.add((channel, note["pitch"], start))
                delay_added += 1
                generated_total += 1
                previous_delay_source = note["on"]["tick"]
                stats["delayNotesGenerated"] += 1
        delay_report.append({"track": track["index"], "channel": channel + 1,
                             "existingDetected": has_delay, "generated": delay_added,
                             "delayTicks": delay_ticks, "budget": per_layer_budget})

        third_added = 0
        if third_enabled and not has_third:
            register=(profiles_by_key.get(notes[0].get("instrumentKey")) or {}).get("register") if notes else None
            third_plan=_plan_third_sequence(notes,harmony,bar_ticks,register)
            for note,(pitch,harmony_kind,path_score) in zip(notes,third_plan):
                if third_added >= per_layer_budget or generated_total >= global_budget:
                    break
                if pitch is None:
                    continue
                profile = profiles_by_key.get(note.get("instrumentKey"))
                if not profile or int(profile.get("samples", 0)) < 32:
                    continue
                start = note["on"]["tick"]
                if (channel, pitch, start) in existing_keys:
                    continue
                intensity = (note["on"]["data"][1] - 1) * 100 / 126
                velocity = factory_velocity.velocity_at(profile, max(0, intensity - 12))
                end = note["on"]["tick"] + max(1, round((note["off"]["tick"] - note["on"]["tick"]) * .88))
                next_order = _add_note(track, channel, pitch, start, end, velocity, next_order)
                existing_keys.add((channel, pitch, start))
                third_added += 1
                generated_total += 1
                stats["thirdNotesGenerated"] += 1
                stats[f"thirdPath_{harmony_kind}"] += 1
        third_report.append({"track": track["index"], "channel": channel + 1,
                             "existingDetected": has_third, "generated": third_added,
                             "budget": per_layer_budget,
                             "harmonyRule": "phrase-level DP voice-leading over chord-safe third/sixth/rest candidates"})

    return {
        "enabled": bool(options.get("fxAuto") or delay_enabled or third_enabled),
        "roles": public_roles,
        "fx": fx_decisions,
        "delay": delay_report,
        "third": third_report,
        "existingEchoTerca": existing_layer_report,
        "budgets": {"sourceNotes": total_source_notes, "globalGeneratedLimit": global_budget,
                    "generated": generated_total, "limitRespected": generated_total <= global_budget},
        "authority": {"fx": "deterministic-engine-policy", "generatedVelocity": "factory-only",
                      "goldVelocity": False, "goldProgramChange": False},
        "safety": {"trackCountChanged": False, "programChangeAdded": False,
                   "unknownSysExChanged": False, "drumNotesTransposed": False},
    }