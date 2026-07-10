import unittest
from src.domain.value_objects.fuzion_stats import (
    PrimaryCharacteristics, DerivedCharacteristics, SkillSet)


class TestFuzionStats(unittest.TestCase):
    def test_derived_from_primary(self):
        pc = PrimaryCharacteristics(body=10, con=10, str=10, ref=10, move=10, will=10)
        d = DerivedCharacteristics.from_primary(pc)
        self.assertEqual(d.hits, 50)
        self.assertEqual(d.stun, 50)
        self.assertEqual(d.sd, 20)
        self.assertEqual(d.rec, 20)
        self.assertEqual(d.run, 20)
        self.assertEqual(d.sprint, 30)

    def test_modifier_backward_compat(self):
        pc = PrimaryCharacteristics(ref=14)
        self.assertEqual(pc.modifier('ref'), 2)

    def test_skillset_everyman(self):
        sk = SkillSet.everyman()
        self.assertEqual(sk.awareness, 2)

    def test_round_trip_dict(self):
        pc = PrimaryCharacteristics(int=12)
        self.assertEqual(PrimaryCharacteristics.from_dict(pc.to_dict()).int, 12)


if __name__ == '__main__':
    unittest.main()