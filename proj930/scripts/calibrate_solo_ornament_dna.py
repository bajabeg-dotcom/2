from __future__ import annotations
import json, hashlib, statistics, zipfile
from collections import Counter, defaultdict
from pathlib import Path
import mido

ROOT=Path(__file__).resolve().parents[1]
GOLD=ROOT/'calibration/raw/gold/Gold DNA'
OUT=ROOT/'data/dna-solo-ornament-calibration-8.30.json'

def ensure_sources():
    if GOLD.exists() and any(GOLD.glob('*.[Mm][Ii][Dd]')): return
    raw=ROOT/'calibration/raw'; raw.mkdir(parents=True,exist_ok=True)
    dna=ROOT/'prism-uploads/DNA.zip'
    with zipfile.ZipFile(dna) as z: z.extract('Gold DNA.zip',raw)
    with zipfile.ZipFile(raw/'Gold DNA.zip') as z: z.extractall(raw/'gold')

def phrase_bin(i,n):
    if n<=1:return 'single'
    p=i/max(1,n-1)
    if p<.15:return 'start'
    if p>.85:return 'cadence'
    return 'body'

def parse(path):
    mf=mido.MidiFile(path); ppq=int(mf.ticks_per_beat or 480)
    groups=defaultdict(list); bends=defaultdict(list); invalid=0; names={}
    for ti,tr in enumerate(mf.tracks):
        tick=0; active=defaultdict(list); name=''
        for msg in tr:
            tick += int(msg.time)
            if msg.type=='track_name': name=str(msg.name or '')
            if not hasattr(msg,'channel'): continue
            ch=int(msg.channel)
            if msg.type=='note_on' and int(msg.velocity)>0:
                active[(ch,int(msg.note))].append((tick,int(msg.velocity)))
            elif msg.type in {'note_off','note_on'}:
                key=(ch,int(msg.note)); stack=active.get(key)
                if stack:
                    st,vel=stack.pop(0)
                    if tick>st: groups[(ti,ch)].append({'start':st,'end':tick,'pitch':int(msg.note)})
                    else: invalid+=1
                else: invalid+=1
            elif msg.type=='pitchwheel':
                bends[(ti,ch)].append((tick,int(msg.pitch)))
        invalid += sum(len(v) for v in active.values()); names[ti]=name
    return ppq,groups,bends,names,invalid

def max_poly(notes):
    pts=[]
    for n in notes: pts += [(n['start'],1),(n['end'],-1)]
    a=m=0
    for _,d in sorted(pts,key=lambda x:(x[0],x[1])): a+=d; m=max(m,a)
    return m

def melodic(notes, key, name):
    if len(notes)<12 or key[1]==9:return False
    on=Counter(n['start'] for n in notes); poly=sum(v>1 for v in on.values())/max(1,len(on))
    med=statistics.median(n['pitch'] for n in notes)
    return med>=44 and poly<.20 and max_poly(notes)<=3

def detect(notes,bends,ppq):
    notes=sorted(notes,key=lambda n:(n['start'],n['pitch'],n['end']))
    ev=[]; used_trill=set()
    # trills: at least 4 short alternating notes between two close pitches.
    i=0
    while i<=len(notes)-4:
        run=[notes[i]]; j=i+1
        while j<len(notes) and len(run)<8:
            prev=run[-1]; cur=notes[j]
            if cur['start']-prev['start']>ppq*.28: break
            if cur['end']-cur['start']>ppq*.32: break
            run.append(cur); j+=1
        best=None
        for L in range(min(8,len(run)),3,-1):
            r=run[:L]; ps=[x['pitch'] for x in r]
            uniq=sorted(set(ps))
            if len(uniq)==2 and 1<=abs(uniq[1]-uniq[0])<=3 and all(ps[k]==ps[k%2] for k in range(len(ps))): best=r; break
        if best:
            ev.append({'kind':'trill','index':i,'interval':best[1]['pitch']-best[0]['pitch'],'durationQn':(best[-1]['end']-best[0]['start'])/ppq,'noteCount':len(best)})
            used_trill.update(range(i,i+len(best))); i+=len(best); continue
        i+=1
    # grace: short approach immediately before a longer target, excluding trill members.
    for i in range(len(notes)-1):
        a,b=notes[i],notes[i+1]; dur=(a['end']-a['start'])/ppq; gap=(b['start']-a['end'])/ppq; iv=b['pitch']-a['pitch']
        if i in used_trill: continue
        if dur<=.20 and -.08<=gap<=.14 and 1<=abs(iv)<=4 and (b['end']-b['start']) >= (a['end']-a['start'])*1.5:
            ev.append({'kind':'grace','index':i,'interval':iv,'durationQn':dur,'gapQn':gap})
    # real bend evidence inside note spans. Magnitude > 512 avoids tiny wheel noise.
    if bends:
        bi=0; bs=sorted(bends)
        for i,n in enumerate(notes):
            vals=[v for t,v in bs if n['start']<=t<n['end'] and abs(v)>=512]
            if vals:
                ev.append({'kind':'bend','index':i,'peak':max(vals,key=abs),'durationQn':(n['end']-n['start'])/ppq})
                # nearby next note makes this a slide context as well.
                if i+1<len(notes):
                    nx=notes[i+1]; gap=(nx['start']-n['end'])/ppq; iv=nx['pitch']-n['pitch']
                    if -.12<=gap<=.12 and 1<=abs(iv)<=7:
                        ev.append({'kind':'slide','index':i,'interval':iv,'gapQn':gap})
    return ev,notes

def summarize(rows, total_gaps, total_notes):
    bykind=Counter(r['kind'] for r in rows); phrase=defaultdict(Counter); intervals=defaultdict(Counter); durs=defaultdict(list); steps=defaultdict(list); gaps=defaultdict(list)
    for r in rows:
        phrase[r['kind']][r['phrase']]+=1
        if 'interval' in r: intervals[r['kind']][str(int(r['interval']))]+=1
        if 'durationQn' in r:
            durs[r['kind']].append(float(r['durationQn']))
            if r['kind']=='trill' and r.get('noteCount'): steps[r['kind']].append(float(r['durationQn'])/max(1,int(r['noteCount'])))
        if 'gapQn' in r:gaps[r['kind']].append(float(r['gapQn']))
    out={}
    for k in ('grace','trill','slide','bend'):
        c=bykind[k]; pc=phrase[k]; z=sum(pc.values()) or 1
        out[k]={
            'events':c,
            'eventRatePer100Notes':round(100*c/max(1,total_notes),4),
            'phraseProbabilities':{p:round(pc[p]/z,4) for p in ('start','body','cadence','single')},
            'intervalCounts':dict(intervals[k]),
            'medianDurationQn':round(statistics.median(durs[k]),4) if durs[k] else 0.0,
            'medianStepDurationQn':round(statistics.median(steps[k]),4) if steps[k] else 0.0,
            'medianGapQn':round(statistics.median(gaps[k]),4) if gaps[k] else 0.0,
            'velocityUsed':False,
        }
    return out

def main():
    ensure_sources(); rows=[]; parsed=invalid=mel_groups=notes_total=gaps_total=0; sources=[]; failures=[]
    mids=sorted([p for p in GOLD.iterdir() if p.suffix.lower() in {'.mid','.midi','.kar'}])
    for p in mids:
        try:
            ppq,groups,bends,names,bad=parse(p); parsed+=1;invalid+=bad; file_events=0
            for key,ns in groups.items():
                if not melodic(ns,key,names.get(key[0],'')): continue
                mel_groups+=1; ev,ordered=detect(ns,bends.get(key,()),ppq); notes_total+=len(ordered);gaps_total+=max(0,len(ordered)-1)
                for e in ev:
                    e=dict(e);e['file']=p.name;e['track']=key[0];e['channel']=key[1];e['phrase']=phrase_bin(int(e['index']),len(ordered));rows.append(e);file_events+=1
            if file_events:sources.append({'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'events':file_events})
        except Exception as exc: failures.append({'file':p.name,'error':type(exc).__name__+': '+str(exc)})
    kinds=summarize(rows,gaps_total,notes_total)
    out={
      'schema':'dna-solo-ornament-calibration','version':'8.30',
      'authority':'GOLD_SOURCE_MIDI_ORNAMENT_PLACEMENT',
      'source':{'archive':'prism-uploads/DNA.zip -> Gold DNA.zip','midiCount':len(mids),'parsedMidiCount':parsed,'melodicGroups':mel_groups,'analyzedNotes':notes_total,'ignoredInvalidNotePairs':invalid,'filesWithEvidence':len(sources),'failures':failures},
      'ornaments':kinds,
      'global':{'totalEvents':len(rows),'eventRatePer100Notes':round(100*len(rows)/max(1,notes_total),4)},
      'policy':{'velocityAuthority':'FACTORY_ONLY','goldVelocityUsed':False,'originalMidiMutated':False,'pitchBendIsEvidenceNotDirectCopy':True,'mainSoloPreserved':True},
      'sourceFiles':sources,
    }
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
