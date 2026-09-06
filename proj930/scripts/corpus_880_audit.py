from pathlib import Path
from collections import defaultdict, Counter
import json, sys
sys.path.insert(0, str(Path('/mnt/data/proj880/src')))
from dna_midi_studio.midi import MidiFile
from dna_midi_studio.role_first_song_optimizer import optimize_role_first
root=Path('/mnt/data/valja602/VALJA_RECONSTRUCTION_6.02/RECONSTRUCTED/Valja')
files=sorted([p for p in root.rglob('*') if p.suffix.lower() in {'.mid','.midi','.kar'}])
roles=defaultdict(lambda:{'targets':0,'repaired':0,'notes':0,'changed':0,'ratios':[],'files':Counter()})
errors=[]
for i,p in enumerate(files,1):
    try:
        m=MidiFile.from_bytes(p.read_bytes()); m.notes()
        _, rep=optimize_role_first(m)
        for r in rep['passes']:
            role=r['role']; n=int(r['note_count']); c=int(r['changed_notes'])
            d=roles[role]; d['targets']+=1; d['notes']+=n; d['changed']+=c
            if r['action']=='REPAIR': d['repaired']+=1
            if n: d['ratios'].append(c/n)
            if c: d['files'][p.name]+=c
    except Exception as e: errors.append({'file':p.name,'error':str(e)})
    if i%25==0: print(i, flush=True)
out={'files':len(files),'errors':errors,'roles':{}}
for role,d in roles.items():
    rr=sorted(d['ratios'])
    def q(fr):
        if not rr:return 0
        return rr[min(len(rr)-1,round((len(rr)-1)*fr))]
    out['roles'][role]={
      'targets':d['targets'],'repaired':d['repaired'],'notes':d['notes'],'changed':d['changed'],
      'overallChangeRate':round(d['changed']/max(1,d['notes']),4),'medianTargetChangeRate':round(q(.5),4),
      'p90TargetChangeRate':round(q(.9),4),'maxTargetChangeRate':round(max(rr) if rr else 0,4),
      'topChangedFiles':d['files'].most_common(8)}
Path('/mnt/data/proj880/calibration/corpus_880_audit.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(out['roles'],indent=2,ensure_ascii=False))
print('ERRORS',len(errors))
