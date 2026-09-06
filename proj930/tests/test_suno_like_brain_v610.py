from __future__ import annotations
import unittest
from pathlib import Path
from dna_midi_studio.session19_fixture import build_benchmark_case
from dna_midi_studio.suno_like_brain import SunoLikeConductor, EvidencePatternMemory
from dna_midi_studio.symbolic_language import encode_remiplus_like

ROOT=Path(__file__).resolve().parents[1]

class SunoLikeBrainV610Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case=build_benchmark_case(3)
        cls.brain=SunoLikeConductor(ROOT/'data')
        cls.plan=cls.brain.deliberate(cls.case.midi,'fixture.mid',candidates_per_role=3,max_retries=1)

    def test_symbolic_language_is_velocity_blind_and_multitrack(self):
        seq=encode_remiplus_like(self.case.midi,'fixture.mid')
        self.assertFalse(seq.metadata['velocityUsed'])
        self.assertTrue(any(t.startswith('ROLE_') for t in seq.tokens))
        self.assertTrue(any(t.startswith('SECTION_') for t in seq.tokens))
        self.assertEqual(seq.tokens[0],'BOS'); self.assertEqual(seq.tokens[-1],'EOS')

    def test_plan_has_hierarchical_music_loop(self):
        p=self.plan
        self.assertEqual(p['schema'],'dna-suno-like-symbolic-brain')
        self.assertTrue(p['sectionIntents'])
        self.assertIn('planner',p['architecture']); self.assertIn('critic',p['architecture'])
        self.assertFalse(p['safety']['autoCommitMidi'])
        self.assertFalse(p['tokenization']['velocityUsed'])

    def test_corpus_memory_is_real_and_retrieves_ranked_candidates(self):
        mem=EvidencePatternMemory(ROOT/'data')
        self.assertGreater(len(mem.gold),1000); self.assertGreater(len(mem.factory),1000)
        rows=mem.retrieve('drums','verse','4/4',4.0,n=3)
        self.assertTrue(rows)
        self.assertEqual(rows,sorted(rows,key=lambda c:(c.score,c.confidence,c.source=='GOLD'),reverse=True))

    def test_audit_trace_is_structured_not_free_text_reasoning(self):
        self.assertIn('candidateAudit',self.plan)
        self.assertIn('retryHistory',self.plan)
        self.assertIn('issues',self.plan['critic'])

if __name__=='__main__': unittest.main()
