from pathlib import Path
from collections import defaultdict, Counter
import json,sys
sys.path.insert(0,'/mnt/data/proj880/src')
from dna_midi_studio.midi import MidiFile
from dna_midi_studio.role_first_song_optimizer import optimize_role_first
start=int(sys.argv[1]); end=int(sys.argv[2])
root=Path('/mnt/data/valja602/VALJA_RECONSTRUCTION_6.02/RECONSTRUCTED/Valja')
files=sorted([p for p in root.rglob('*') if p.suffix.lower() in {'.mid','.midi','.kar'}])[start:end]
rows=[]; errors=[]
for p in files:
    try:
        m=MidiFile.from_bytes(p.read_bytes()); m.notes(); _,rep=optimize_role_first(m)
        for r in rep['passes']:
            rows.append({'file':p.name,'role':r['role'],'action':r['action'],'notes':int(r['note_count']),'changed':int(r['changed_notes']),'reasons':r['reasons']})
    except Exception as e: errors.append({'file':p.name,'error':str(e)})
out={'start':start,'end':end,'count':len(files),'rows':rows,'errors':errors}
p=Path(f'/mnt/data/proj880/calibration/corpus_880_{start:03d}_{end:03d}.json'); p.parent.mkdir(exist_ok=True); p.write_text(json.dumps(out,ensure_ascii=False),encoding='utf-8')
print(start,end,len(files),len(rows),len(errors))
