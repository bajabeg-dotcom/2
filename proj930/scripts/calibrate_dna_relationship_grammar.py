from __future__ import annotations
import json, statistics, hashlib, math
from collections import Counter, defaultdict
from pathlib import Path
import mido
import zipfile

ROOT=Path(__file__).resolve().parents[1]
GOLD=ROOT/'calibration/raw/gold/Gold DNA'
OUT=ROOT/'data/dna-relationship-grammar-8.00.json'

def ensure_sources():
    if GOLD.exists() and any(GOLD.glob('*.MID')) or (GOLD.exists() and any(GOLD.glob('*.mid'))):
        return
    raw=ROOT/'calibration/raw'; raw.mkdir(parents=True,exist_ok=True)
    dna=ROOT/'prism-uploads/DNA.zip'
    if not dna.exists(): raise FileNotFoundError(dna)
    with zipfile.ZipFile(dna) as z: z.extract('Gold DNA.zip',raw)
    with zipfile.ZipFile(raw/'Gold DNA.zip') as z: z.extractall(raw/'gold')


ALLOWED_TERC_MOD={3,4,8,9}

def safe_median(xs, default=0.0):
    return float(statistics.median(xs)) if xs else float(default)

def phrase_bin(i,n):
    if n<=1:return 'single'
    p=i/(n-1)
    if p<.15:return 'start'
    if p>.85:return 'cadence'
    return 'body'

def parse_groups(path:Path):
    mf=mido.MidiFile(path)
    ppq=int(mf.ticks_per_beat or 480)
    groups=defaultdict(list); names={}; programs=defaultdict(Counter); invalid=0
    for ti,tr in enumerate(mf.tracks):
        tick=0; active=defaultdict(list); current_program=defaultdict(lambda:0)
        name=''
        for msg in tr:
            tick += int(msg.time)
            if msg.type=='track_name': name=str(msg.name or '')
            if hasattr(msg,'channel'):
                ch=int(msg.channel)
                if msg.type=='program_change': current_program[ch]=int(msg.program)
                elif msg.type=='note_on' and int(msg.velocity)>0:
                    active[(ch,int(msg.note))].append((tick,int(msg.velocity),int(current_program[ch])))
                elif msg.type in {'note_off','note_on'}:
                    key=(ch,int(msg.note)); stack=active.get(key)
                    if stack:
                        st,vel,prog=stack.pop(0)
                        if tick>st:
                            groups[(ti,ch)].append({'start':st,'end':tick,'pitch':int(msg.note),'velocity':vel,'program':prog})
                            programs[(ti,ch)][prog]+=1
                        else: invalid+=1
                    else: invalid+=1
        names[ti]=name
        # close dangling notes conservatively at +1 tick only for parser stats, not relationship evidence
        invalid += sum(len(v) for v in active.values())
    return mf,ppq,groups,names,programs,invalid

def max_poly(notes):
    pts=[]
    for n in notes: pts.append((n['start'],1)); pts.append((n['end'],-1))
    active=mx=0
    for _,d in sorted(pts,key=lambda x:(x[0],x[1])):
        active+=d; mx=max(mx,active)
    return mx

def group_features(key,notes,name,programs,ppq):
    if not notes:return None
    on=Counter(n['start'] for n in notes); poly_on=sum(v>1 for v in on.values())/max(1,len(on))
    medpitch=safe_median([n['pitch'] for n in notes],60)
    prog=programs[key].most_common(1)[0][0] if programs[key] else 0
    melodic=(len(notes)>=12 and medpitch>=45 and poly_on<.20 and max_poly(notes)<=3 and key[1]!=9)
    explicit_terca=any(w in name.lower() for w in ('terca','third','2nd voice','second voice','harmony solo'))
    explicit_echo=any(w in name.lower() for w in ('echo','delay','odjek'))
    explicit_solo=any(w in name.lower() for w in ('solo','lead','melody','sax','trumpet'))
    return {'notes':len(notes),'medianPitch':medpitch,'program':prog,'polyOnset':poly_on,'maxPoly':max_poly(notes),'melodic':melodic,
            'explicitTerca':explicit_terca,'explicitEcho':explicit_echo,'explicitSolo':explicit_solo}

def nearest_terca(src,tgt,ppq):
    tol=max(2,round(ppq*.08)); width=max(1,tol)
    buckets=defaultdict(list)
    for j,a in enumerate(tgt): buckets[a['start']//width].append((j,a))
    used=set(); matched=[]
    for si,s in enumerate(src):
        b=s['start']//width; cand=[]
        for bb in (b-1,b,b+1):
            for j,a in buckets.get(bb,()):
                if j in used: continue
                dt=abs(a['start']-s['start'])
                if dt<=tol and ((a['pitch']-s['pitch'])%12) in ALLOWED_TERC_MOD:
                    cand.append((dt,abs(a['pitch']-s['pitch']),j,a))
        if cand:
            _,_,j,a=min(cand);used.add(j);matched.append((si,j,s,a))
    cov_src=len(matched)/max(1,len(src)); cov_tgt=len(matched)/max(1,len(tgt)); density=min(len(src),len(tgt))/max(len(src),len(tgt))
    ratio=len(matched)/max(1,min(len(src),len(tgt)))
    conf=min(.95,.55+ratio*.4) if len(matched)>=12 and ratio>=.35 else 0.0
    return conf,matched

def echo_relation(src,tgt,ppq):
    if not src or not tgt:return 0.0,0,[]
    from bisect import bisect_left,bisect_right
    tol=max(2,round(ppq*.08)); min_d=round(ppq*.15); max_d=round(ppq*1.6)
    bypitch=defaultdict(list)
    for j,a in enumerate(tgt):bypitch[a['pitch']].append((a['start'],j,a))
    for p in bypitch: bypitch[p].sort()
    hist=Counter()
    # sample source notes for delay discovery; matching pass still uses all notes
    sample=src if len(src)<=96 else src[::max(1,len(src)//96)]
    for s in sample:
        arr=bypitch.get(s['pitch'],())
        starts=[x[0] for x in arr]
        lo=bisect_left(starts,s['start']+min_d); hi=bisect_right(starts,s['start']+max_d)
        for st,_,a in arr[lo:hi]:
            d=st-s['start']; q=round(d/max(1,tol))*tol; hist[q]+=1
    if not hist:return 0.0,0,[]
    delay,_=hist.most_common(1)[0];used=set();matched=[]
    for si,s in enumerate(src):
        arr=bypitch.get(s['pitch'],()); starts=[x[0] for x in arr]; desired=s['start']+delay
        lo=bisect_left(starts,desired-tol); hi=bisect_right(starts,desired+tol); cand=[]
        for st,j,a in arr[lo:hi]:
            if j not in used:cand.append((abs(st-desired),j,a))
        if cand:
            _,j,a=min(cand);used.add(j);matched.append((si,j,s,a))
    cov_src=len(matched)/max(1,len(src));cov_tgt=len(matched)/max(1,len(tgt));density=min(len(src),len(tgt))/max(len(src),len(tgt))
    ratio=len(matched)/max(1,min(len(src),len(tgt)))
    conf=min(.92,.50+ratio*.4) if len(matched)>=12 and ratio>=.30 else 0.0
    return conf,int(delay),matched

def select_relations(groups,features,names,ppq):
    keys=[k for k,f in features.items() if f and f['melodic']]
    candidates=[]
    for tk in keys:
        tf=features[tk]; tgt=sorted(groups[tk],key=lambda n:(n['start'],n['pitch']))
        for sk in keys:
            if sk==tk:continue
            sf=features[sk];src=sorted(groups[sk],key=lambda n:(n['start'],n['pitch']))
            # Prefer a denser/main source unless target is explicitly labelled.
            if not (tf['explicitTerca'] or tf['explicitEcho']) and len(src)<len(tgt)*.88: continue
            tc,tm=nearest_terca(src,tgt,ppq)
            ec,delay,em=echo_relation(src,tgt,ppq)
            if tf['explicitTerca']:tc+=.18
            if tf['explicitEcho']:ec+=.18
            if sf['explicitSolo']:tc+=.05;ec+=.05
            if tc>=.69 and tc>=ec+.01:candidates.append({'kind':'terca','source':sk,'target':tk,'confidence':min(1,tc),'matched':tm,'delay':0})
            if ec>=.62 and ec>tc+.01:candidates.append({'kind':'echo','source':sk,'target':tk,'confidence':min(1,ec),'matched':em,'delay':delay})
    # one strongest relation per target/kind, prevent duplicate reverse pair by target choice
    out=[];seen=set()
    for c in sorted(candidates,key=lambda x:-x['confidence']):
        k=(c['kind'],c['target'])
        if k in seen:continue
        seen.add(k);out.append(c)
    return out

def derive_note_stats(src,tgt,kind,matched,delay,ppq):
    src=sorted(src,key=lambda n:(n['start'],n['pitch'],n['end']));tgt=sorted(tgt,key=lambda n:(n['start'],n['pitch'],n['end']))
    pair_by_src={si:(a,j) for si,j,s,a in matched}
    actions=Counter();phrase=defaultdict(Counter);intervals=Counter();durs=[];delays=[];beat=defaultdict(Counter)
    for i,s in enumerate(src):
        pb=phrase_bin(i,len(src)); b=str(round((s['start']%ppq)/max(1,ppq),2))
        if i in pair_by_src:
            a,_=pair_by_src[i]; act='PLAY'; durs.append((a['end']-a['start'])/max(1,s['end']-s['start']));delays.append((a['start']-s['start'])/max(1,ppq))
            if kind=='terca':
                d=a['pitch']-s['pitch']
                while d>12:d-=12
                while d<-12:d+=12
                intervals[str(d)]+=1
        else:
            desired=s['start']+(delay if kind=='echo' else 0)
            covering=any(a['start']<desired<a['end'] for a in tgt)
            act='HOLD' if covering else 'SKIP'
        actions[act]+=1;phrase[pb][act]+=1;beat[b][act]+=1
    return {'sourceNotes':len(src),'targetNotes':len(tgt),'actions':actions,'phrase':phrase,'beat':beat,'intervals':intervals,'durs':durs,'delays':delays}

def merge(rows,kind):
    actions=Counter();phrase=defaultdict(Counter);beat=defaultdict(Counter);intervals=Counter();durs=[];delays=[];sn=tn=0
    for r in rows:
        sn+=r['stats']['sourceNotes'];tn+=r['stats']['targetNotes'];actions.update(r['stats']['actions']);intervals.update(r['stats']['intervals']);durs+=r['stats']['durs'];delays+=r['stats']['delays']
        for k,v in r['stats']['phrase'].items():phrase[k].update(v)
        for k,v in r['stats']['beat'].items():beat[k].update(v)
    def probs(c):
        z=sum(c.values()) or 1
        return {x:round(c.get(x,0)/z,4) for x in ('PLAY','SKIP','HOLD')}
    ivz=sum(intervals.values()) or 1
    return {'kind':kind,'pairCount':len(rows),'sourceNotes':sn,'targetNotes':tn,'actionCounts':dict(actions),'actionProbabilities':probs(actions),
            'phraseActionProbabilities':{k:probs(v) for k,v in sorted(phrase.items())},
            'intervalCounts':dict(intervals),'intervalProbabilities':{k:round(v/ivz,4) for k,v in intervals.most_common()},
            'medianDelayQn':round(safe_median(delays,0),4),'medianDurationRatio':round(safe_median(durs,1),4),'velocityUsed':False}

def main():
    ensure_sources()
    rows={'terca':[],'echo':[]}; failures=[]; parsed=0;invalid_pairs=0;files_with_rel=set(); source_manifest=[]
    mids=sorted([p for p in GOLD.iterdir() if p.suffix.lower() in {'.mid','.midi','.kar'}])
    for p in mids:
        try:
            mf,ppq,groups,names,programs,invalid=parse_groups(p);parsed+=1;invalid_pairs+=invalid
            feats={k:group_features(k,v,names.get(k[0],''),programs,ppq) for k,v in groups.items()}
            rels=select_relations(groups,feats,names,ppq)
            if rels:
                files_with_rel.add(p.name);source_manifest.append({'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'relationships':len(rels),'ignoredInvalidNotePairs':invalid})
            for c in rels:
                st=derive_note_stats(groups[c['source']],groups[c['target']],c['kind'],c['matched'],c['delay'],ppq)
                rows[c['kind']].append({'file':p.name,'source':list(c['source']),'target':list(c['target']),'confidence':round(c['confidence'],4),'stats':st})
        except Exception as exc:failures.append({'file':p.name,'error':type(exc).__name__+': '+str(exc)})
    out={'schema':'dna-relationship-grammar','version':'8.00','authority':'GOLD_SOURCE_MIDI_RELATIONSHIP_GRAMMAR',
         'source':{'archive':'prism-uploads/DNA.zip -> Gold DNA.zip','midiCount':len(mids),'parsedMidiCount':parsed,'relationshipFiles':len(files_with_rel),'ignoredInvalidNotePairs':invalid_pairs,'failures':failures},
         'terca':merge(rows['terca'],'terca'),'echo':merge(rows['echo'],'echo'),
         'relationshipEvidence':[{'kind':k,'file':r['file'],'source':r['source'],'target':r['target'],'confidence':r['confidence']} for k in ('terca','echo') for r in rows[k]],
         'sourceFiles':source_manifest,
         'policy':{'velocityAuthority':'FACTORY_ONLY','goldVelocityUsed':False,'relationshipOnly':True,'allowedTercaIntervalsSemitones':[3,4,8,9,-3,-4,-8,-9],
                   'originalMidiMutated':False,'invalidNotePairsIgnoredForCalibrationOnly':True}}
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    summary={'out':str(OUT),'source':out['source'],'terca':out['terca'],'echo':out['echo']}
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
