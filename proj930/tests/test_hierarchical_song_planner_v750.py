import unittest
from dna_midi_studio.hierarchical_song_planner import build_hierarchical_song_plan, intent_for_tick
from dna_midi_studio.session19_fixture import build_benchmark_case

class HierarchicalSongPlannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case=build_benchmark_case(0)
        cls.plan=build_hierarchical_song_plan(cls.case.midi, 'fixture.mid')

    def test_plan_is_velocity_blind_and_has_sections(self):
        self.assertFalse(self.plan['velocityUsed'])
        self.assertTrue(self.plan['sections'])
        self.assertTrue(self.plan['policy']['factoryVelocityAuthority'])

    def test_energy_is_bounded_and_lifecycle_exists(self):
        for sec in self.plan['sections']:
            self.assertGreaterEqual(sec['energy'],0.0)
            self.assertLessEqual(sec['energy'],1.0)
            self.assertIn(sec['energy_target'],{'low','medium','high'})
        self.assertIsInstance(self.plan['roleLifecycle'],dict)

    def test_tick_intent_resolves(self):
        sec=self.plan['sections'][0]
        intent=intent_for_tick(self.plan,sec['start_tick'])
        self.assertEqual(intent['section_id'],sec['section_id'])

if __name__=='__main__': unittest.main()
