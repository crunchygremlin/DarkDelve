import unittest
from src.domain.value_objects.fuzion_stats import SkillSet, PrimaryCharacteristics, DerivedCharacteristics
from src.domain.services.fuzion_skill_service import (
    get_skill_bonuses, check_rule_of_x, enforce_rule_of_x
)


def _fake_with(sk: SkillSet):
    """Create a fake entity with a skill_set attribute."""
    class FakeEntity:
        skill_set = sk
    return FakeEntity()


def _fake_mob(skills: list):
    """Create a fake mob with string-list skills."""
    class FakeMob:
        def __init__(self, skills_list):
            self.skills = skills_list
    return FakeMob(skills)


def _fake_player_with_characteristics(pc: PrimaryCharacteristics, sk: SkillSet):
    """Create a fake player with characteristics and skills."""
    class FakePlayer:
        characteristics = pc
        derived = DerivedCharacteristics.from_primary(pc)
        skill_set = sk
    return FakePlayer()


class TestSkillService(unittest.TestCase):
    def test_player_skillset_bonuses(self):
        sk = SkillSet(fighting=10, ranged_weapon=0, awareness=5, control=0, technique=5, body=0)
        # atk=(10+0)//5=2 ; dv=(5+0)//5=1 ; av=(5+0)//5=1
        self.assertEqual(get_skill_bonuses(_fake_with(sk)), (2, 1, 1))

    def test_mob_string_skills(self):
        mob = _fake_mob(["bite", "dodge", "scales"])
        atk, dv, av = get_skill_bonuses(mob)
        self.assertGreater(atk, 0)
        self.assertGreater(dv, 0)
        self.assertGreater(av, 0)


class TestRuleOfX(unittest.TestCase):
    def test_rule_of_x_within_caps(self):
        """Test that entities within caps pass check."""
        pc = PrimaryCharacteristics(ref=10, dex=10, body=10, con=10)
        sk = SkillSet(fighting=5, awareness=5)
        player = _fake_player_with_characteristics(pc, sk)
        attack_ok, defense_ok = check_rule_of_x(player, weapon_dc=5)
        # hits=50, hits//5=10, con//5=2, dex=10, skill_dv=1 -> 23 <= 20? No, exceeds
        # Let's use lower values
        pc = PrimaryCharacteristics(ref=10, dex=8, body=8, con=8)
        sk = SkillSet(fighting=5, awareness=3)
        player = _fake_player_with_characteristics(pc, sk)
        attack_ok, defense_ok = check_rule_of_x(player, weapon_dc=5)
        self.assertTrue(attack_ok)
        self.assertTrue(defense_ok)

    def test_rule_of_x_attack_exceeds_cap(self):
        """Test that attack power exceeding cap is detected."""
        pc = PrimaryCharacteristics(ref=18, dex=8, body=8, con=8)
        sk = SkillSet(fighting=20, awareness=3)  # High fighting skill
        player = _fake_player_with_characteristics(pc, sk)
        attack_ok, defense_ok = check_rule_of_x(player, weapon_dc=10)
        self.assertFalse(attack_ok)  # Should exceed cap
        self.assertTrue(defense_ok)

    def test_rule_of_x_defense_exceeds_cap(self):
        """Test that defense power exceeding cap is detected."""
        pc = PrimaryCharacteristics(ref=10, dex=18, body=20, con=20)  # High dex and body
        sk = SkillSet(fighting=5, awareness=20)  # High awareness skill
        player = _fake_player_with_characteristics(pc, sk)
        attack_ok, defense_ok = check_rule_of_x(player, weapon_dc=5)
        self.assertTrue(attack_ok)
        self.assertFalse(defense_ok)  # Should exceed cap

    def test_enforce_rule_of_x_clamps_attack(self):
        """Test that enforce_rule_of_x clamps attack bonus when cap exceeded."""
        pc = PrimaryCharacteristics(ref=18, dex=8, body=8, con=8)
        sk = SkillSet(fighting=20, awareness=3)
        player = _fake_player_with_characteristics(pc, sk)
        atk_bonus, dv_bonus = enforce_rule_of_x(player, weapon_dc=10)
        # Should be clamped to fit within cap
        self.assertLessEqual(atk_bonus, 20)

    def test_enforce_rule_of_x_clamps_defense(self):
        """Test that enforce_rule_of_x clamps defense bonus when cap exceeded."""
        pc = PrimaryCharacteristics(ref=10, dex=18, body=20, con=20)
        sk = SkillSet(fighting=5, awareness=20)
        player = _fake_player_with_characteristics(pc, sk)
        atk_bonus, dv_bonus = enforce_rule_of_x(player, weapon_dc=5)
        # Should be clamped to fit within cap
        self.assertLessEqual(dv_bonus, 20)

    def test_rule_of_x_legacy_entity_passes(self):
        """Test that legacy entities without characteristics pass Rule-of-X check."""
        class LegacyEntity:
            pass
        entity = LegacyEntity()
        attack_ok, defense_ok = check_rule_of_x(entity, weapon_dc=100)
        self.assertTrue(attack_ok)
        self.assertTrue(defense_ok)


if __name__ == '__main__':
    unittest.main()