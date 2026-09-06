from pathlib import Path
from dna_midi_studio.midi import Note
from dna_midi_studio.pattern_ir import extract_pattern_dna
from dna_midi_studio.evidence_index import PatternEvidenceIndex
from dna_midi_studio.pattern_retrieval import PatternQuery, retrieve
from dna_midi_studio.global_section_planner import plan_section_path, PlannerPolicy
from dna_midi_studio.style_track_mapper import RoleCandidate, optimize_style_track_map
from dna_midi_studio.styleworks_mapping import build_styleworks_mapping_report

PPQ=96

def n(start,pitch=48,vel=88,dur=72,ch=12): return Note(0,ch,pitch,start,start+dur,vel)

def pattern(role='power-riff',section='chorus',source='GOLD',phase=0,energy_vel=90):
    notes=[]
    for beat in range(8):
        s=phase+beat*(PPQ//2)
        notes += [n(s,48,energy_vel),n(s,55,max(1,energy_vel-3))]
    return extract_pattern_dna(notes,source_kind=source,source_hash=('a' if source=='GOLD' else 'b')*64,
      role=role,section_label=section,ppq=PPQ,start_tick=0,end_tick=4*PPQ,instrument_family='guitar',
      quality=.92 if source=='GOLD' else .88,confidence=.9,entry_behavior='section-start',exit_behavior='section-end')

def test_pattern_dna_is_deterministic_and_structured():
    p1=pattern(); p2=pattern()
    assert p1.pattern_id==p2.pattern_id
    assert p1.role=='power-riff'
    assert len(p1.onset_vector)==16
    assert p1.note_count==16
    assert p1.velocity_mean>80

def test_evidence_index_and_retrieval_rank_matching_pattern(tmp_path:Path):
    db=PatternEvidenceIndex(tmp_path/'patterns.sqlite')
    gold=pattern(source='GOLD',section='chorus',energy_vel=96)
    factory=pattern(source='FACTORY',section='body',energy_vel=72)
    db.add_many([factory,gold])
    q=PatternQuery(role='power-riff',section_label='chorus',meter_num=4,meter_den=4,tempo_bpm=120,
                   energy=gold.energy,density=gold.density,register_center=gold.register_center,onset_vector=gold.onset_vector)
    ranked=retrieve(db,q,top_k=2)
    assert db.count()==2
    assert ranked[0].pattern_id==gold.pattern_id
    assert ranked[0].score>ranked[-1].score
    db.close()

def test_global_section_planner_prefers_coherent_full_section_path(tmp_path:Path):
    db=PatternEvidenceIndex(tmp_path/'patterns.sqlite')
    a=pattern(source='GOLD',energy_vel=94); b=pattern(source='FACTORY',energy_vel=88)
    db.add_many([a,b])
    q=PatternQuery(role='power-riff',section_label='chorus',energy=a.energy,density=a.density,register_center=a.register_center,onset_vector=a.onset_vector)
    ranked=retrieve(db,q,top_k=2)
    bars=[ranked for _ in range(8)]
    path=plan_section_path(role='power-riff',section_label='chorus',bar_candidates=bars)
    assert path.pass_continuity
    assert path.coverage==1.0
    assert all(c.active for c in path.cells)
    assert path.switches==0

def test_required_role_cannot_have_mid_section_hole():
    # Planner is offered no musical candidate at bar 4, but continuity policy still exposes the failure.
    p=pattern()
    from dna_midi_studio.pattern_retrieval import RankedPattern
    rp=RankedPattern(p.pattern_id,.9,p.source_kind,{},p)
    bars=[[rp],[rp],[rp],[],[rp],[rp],[rp],[rp]]
    path=plan_section_path(role='power-riff',section_label='chorus',bar_candidates=bars,policy=PlannerPolicy(required_role=True))
    assert not path.pass_continuity
    assert 'UNEXPLAINED_MID_SECTION_HOLE' in path.reasons or 'SECTION_COVERAGE_TOO_LOW' in path.reasons

def test_style_track_mapper_keeps_only_five_acc_roles_and_fixed_channels():
    roles=[
      RoleCandidate('bass',1,1,1,1,1),RoleCandidate('drums',1,1,1,1,1),RoleCandidate('perc',.5,.8,.5,.8,.5),
      RoleCandidate('rhythm-guitar',.95,1,.95,.9,.9,preferred_acc=12),
      RoleCandidate('power-riff',.94,.95,.98,.95,1,preferred_acc=13),
      RoleCandidate('keys',.8,.9,.7,.8,.7),RoleCandidate('strings',.7,.75,.75,.85,.7),
      RoleCandidate('brass',.72,.6,.9,.8,.8),RoleCandidate('organ',.3,.4,.2,.5,.3, redundancy=.8),
    ]
    m=optimize_style_track_map(roles)
    mapping={a.role:a.channel for a in m.assignments}
    assert mapping['bass']==9 and mapping['drums']==10 and mapping['perc']==11
    assert mapping['rhythm-guitar']==12 and mapping['power-riff']==13
    assert len([a for a in m.assignments if a.channel>=12])==5
    assert 'organ' in m.dropped_roles

def test_styleworks_report_flags_no_problem_for_valid_map():
    m=optimize_style_track_map([RoleCandidate('bass',1,1,1,1,1),RoleCandidate('drums',1,1,1,1,1),RoleCandidate('rhythm-guitar',1,1,1,1,1)])
    r=build_styleworks_mapping_report(style_element='V4',chord_variation='CV1',bars=8,track_map=m)
    assert not r.warnings
