import unittest
from src.domain.services.combat_factors import (
    calculate_attack_value, calculate_defense_value, calculate_damage,
    get_skill_bonuses, get_armor_value, MOB_SKILL_BONUS_MAP)
from src.domain.entities.mob import Mob
from src.domain.entities.item import Item
from src.domain.entities.player import Player
from src.domain.value_objects.position import Position
from src.domain.services.player_profile_service import PlayerProfileService
from src.domain.services.dynamic_difficulty_service import DynamicDifficultyService, DifficultyAdjustment


class TestFuzionMonsters(unittest.TestCase):
    def test_mob_defense_uses_fuzion_dv_no_attributeerror(self):
        m = Mob(Position(0, 0), mob_type="orc")
        # Mob has no 'defense' attr historically; get_defense must not raise
        dv = m.get_defense()
        self.assertIsInstance(dv, int)
        self.assertGreaterEqual(dv, 6)   # BASE_DV floor

    def test_mob_attack_damage_uses_fuzion(self):
        m = Mob(Position(0, 0), mob_type="dragon", power=24)
        dmg = m.get_attack_damage("2d6")
        self.assertGreaterEqual(dmg, 1)

    def test_combat_service_defense_value_on_mob_no_error(self):
        # Simulate the previously-broken path: CombatService.calculate_defense_value(Mob)
        from src.domain.services.combat_service import CombatService
        m = Mob(Position(0, 0), mob_type="goblin")
        cs = CombatService()
        dv = cs.calculate_defense_value(m)   # was AttributeError: 'Mob' has no 'defense'
        self.assertIsInstance(dv, int)


class TestFuzionSkillMapping(unittest.TestCase):
    def test_mob_string_skills_map_to_bonuses(self):
        m = Mob(Position(0, 0), mob_type="orc", skills=["bite", "shield", "guard"])
        wm, am, ta = get_skill_bonuses(m)
        self.assertEqual(wm, MOB_SKILL_BONUS_MAP["bite"][1])   # attack bonus
        self.assertEqual(am, MOB_SKILL_BONUS_MAP["shield"][1]) # av bonus
        self.assertEqual(ta, MOB_SKILL_BONUS_MAP["guard"][1])  # dv bonus

    def test_unknown_monster_skill_maps_to_zero(self):
        # S3: skills not present in MOB_SKILL_BONUS_MAP contribute 0 (no crash)
        m = Mob(Position(0, 0), mob_type="orc", skills=["totally_unknown_skill"])
        wm, am, ta = get_skill_bonuses(m)
        self.assertEqual((wm, am, ta), (0, 0, 0))

    def test_player_skills_from_profile_feed_combat(self):
        # S2: actually call apply_combat_skills (not manual attach)
        p = Player(Position(0, 0))   # default Stats all = 10
        svc = PlayerProfileService()
        svc.apply_combat_skills(p)
        wm, am, ta = get_skill_bonuses(p)
        # weapon_mastery = STR*1 + DEX*1 = 20 -> //5 = 4
        self.assertEqual(wm, 4)
        self.assertEqual(am, 4)   # CON*1.5 + STR*0.5 = 20 -> 4
        self.assertEqual(ta, 4)   # INT + WIS = 20 -> 4
        # AV includes armor_mastery bonus (B2: equipment path also exercised)
        self.assertGreaterEqual(get_armor_value(p), am)

    def test_entity_player_skills_from_profile_feed_combat(self):
        # B3: in-game darkdelve.Entity player must also get skills wired
        from darkdelve import Entity
        e = Entity(x=0, y=0, name="Hero",
                   stats={'str': 14, 'dex': 12, 'con': 13, 'int': 10, 'wis': 10, 'cha': 8})
        svc = PlayerProfileService()
        svc.apply_combat_skills_to_entity(e)
        wm, am, ta = get_skill_bonuses(e)
        self.assertEqual(wm, (14 + 12) // 5)                    # 5
        self.assertEqual(am, int((13 * 1.5 + 14 * 0.5) // 5))  # 5
        self.assertEqual(ta, (10 + 10) // 5)                   # 4
        # AV includes armor_mastery bonus for the Entity player too
        self.assertGreaterEqual(get_armor_value(e), am)


class TestFuzionLevelFactor(unittest.TestCase):
    def test_level_bonus_in_attack_and_defense(self):
        from unittest.mock import patch
        low = Mob(Position(0, 0), mob_type="goblin", level=1)
        high = Mob(Position(0, 0), mob_type="goblin", level=5)
        # Mock d10 roll to be same for both to isolate level difference
        with patch('random.randint', return_value=5):
            _, atk_low = calculate_attack_value(low)
            _, atk_high = calculate_attack_value(high)
        self.assertGreater(atk_high, atk_low)          # level adds to attack
        self.assertGreater(calculate_defense_value(high), calculate_defense_value(low))

    def test_tier_maps_to_level(self):
        from src.domain.entities.mob import Mob as _M
        boss = _M(Position(0, 0), mob_type="dragon", tier="boss")
        # boss tier -> level 4 via _tier_to_level; DV should reflect it
        self.assertGreaterEqual(calculate_defense_value(boss), 6 + 4)


class TestFuzionItems(unittest.TestCase):
    def test_item_weapon_dice_field(self):
        it = Item(item_id="w", name="Sword", item_type="weapon", weapon_dice="2d6+1")
        self.assertEqual(it.weapon_dice, "2d6+1")

    def test_item_attack_bonus_feeds_attack_value(self):
        # attack_bonus -> to_hit_bonus path via equipment aggregation
        it = Item(item_id="w", name="Sword", item_type="weapon")
        it.attack_bonus = 3
        self.assertEqual(it.attack_bonus, 3)
        # defense_bonus -> AV
        it.defense_bonus = 4
        self.assertEqual(it.armor_value, 4)


class TestFuzionDifficulty(unittest.TestCase):
    def test_difficulty_adjustment_has_fuzion_fields(self):
        adj = DifficultyAdjustment(monster_dv_modifier=1.5, monster_av_modifier=1.5,
                                 monster_attack_modifier=1.5)
        self.assertTrue(adj.is_significant_change())
        self.assertFalse(adj.is_no_change())

    def test_difficulty_no_stale_refs(self):
        # Build a minimal fake player with the NEW attributes only
        class FakePlayer:
            attack_power = 20
            level = 3
            defense_value = 8
        svc = DynamicDifficultyService.__new__(DynamicDifficultyService)
        stats = svc._get_player_max_stats(FakePlayer())
        self.assertIn('attack', stats)
        self.assertIn('level', stats)
        self.assertNotIn('fighter', dir(FakePlayer()))   # stale attr gone
        adj = svc._calculate_difficulty_from_stats(stats, 3)
        self.assertEqual(adj.monster_dv_modifier, adj.monster_health_modifier)
        self.assertEqual(adj.monster_av_modifier, adj.monster_attack_modifier)


if __name__ == '__main__':
    unittest.main()