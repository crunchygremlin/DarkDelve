import unittest
from unittest.mock import patch
from src.domain.value_objects.fuzion_damage import FuzionDamageCalculator


class FakeTarget:
    killing_defense = 5
    stun_defense = 5
    energy_defense = 0
    characteristics = type('PC', (), {'str': 10})()


class TestFuzionDamage(unittest.TestCase):
    def test_dc_subtracts_kd(self):
        calc = FuzionDamageCalculator()
        with patch('src.domain.value_objects.fuzion_damage.random.randint', return_value=4):   # 3d6 -> 12
            r = calc.calculate(FakeTarget(), FakeTarget(), weapon_dc=3)
        self.assertEqual(r.hits, 12 - 5)
        self.assertEqual(r.stun, 12 - 5)

    def test_crit_adds_dc(self):
        calc = FuzionDamageCalculator()
        with patch('src.domain.value_objects.fuzion_damage.random.randint', return_value=3):
            r = calc.calculate(FakeTarget(), FakeTarget(), weapon_dc=2, is_critical=True)
        # 2d6=6, crit +1d6=3 -> 9
        self.assertEqual(r.hits, 9 - 5)

    def test_aimed_head_double(self):
        calc = FuzionDamageCalculator()
        with patch('src.domain.value_objects.fuzion_damage.random.randint', return_value=3):
            r = calc.calculate(FakeTarget(), FakeTarget(), weapon_dc=2, aimed_location="head")
        # 2d6=6, head x2 -> 12
        self.assertEqual(r.hits, int(6 * 2) - 5)


if __name__ == '__main__':
    unittest.main()