import unittest
from unittest.mock import Mock, patch
from src.domain.value_objects.combat_config import COMBAT_CONFIG
from src.shared.utils.dice import parse_dice
from darkdelve import Entity, Inventory, Item, ItemType, CombatResolver, HitResult, CombatEvent

class TestFuzionCombat(unittest.TestCase):
    def make_player(self, dex=10, power=6, def_bonus=0, to_hit=0, defense=2):
        # Item constructor signature: Item(item_id, name, item_type, symbol="?", weight=1, value=0, damage_bonus=0, defense_bonus=0, to_hit_bonus=0, ...)
        # => Item("w","wpn",ItemType.WEAPON) sets item_id="w", name="wpn", item_type=ItemType.WEAPON (valid, 3 positional args)
        e = Entity()
        e.stats = {'str':10,'dex':dex,'con':10,'int':10,'wis':10,'cha':10}
        e.power = power
        e.defense = defense
        e.inventory = Inventory()
        if def_bonus or to_hit:
            w = Item("w","wpn",ItemType.WEAPON); w.to_hit_bonus=to_hit; w.defense_bonus=def_bonus
            e.inventory.add_item(w); e.inventory.equip(w.id, __import__('darkdelve').EquipmentSlot.MAIN_HAND)
        return e

    def test_defense_value_baseline(self):
        p = self.make_player(dex=10, power=6)
        self.assertEqual(p.defense_value, 6)
        self.assertEqual(p.armor_class, 6)

    def test_armor_value_from_equipment(self):
        p = self.make_player(def_bonus=5)
        self.assertEqual(p.armor_value, 5)

    def test_hit_probability_range(self):
        atk = self.make_player(dex=14, power=6, to_hit=2)
        dfn = self.make_player(dex=8, defense=2)
        # Mock d10 roll to avoid critical fail (roll of 1)
        with patch('random.randint', return_value=5):
            for _ in range(20):
                ev = CombatResolver.resolve_attack(atk, dfn)
                self.assertIn(ev.result, (HitResult.HIT, HitResult.CRITICAL))

    def test_ac_41_foe_now_hittable(self):
        foe = self.make_player(dex=10, power=6, def_bonus=25)
        foe.defense = 6
        player = self.make_player(dex=14, power=6, to_hit=2)
        hits = 0
        for _ in range(100):
            ev = CombatResolver.resolve_attack(player, foe)
            if ev.result in (HitResult.HIT, HitResult.CRITICAL): hits += 1
        self.assertGreater(hits, 80)

    def test_damage_absorbs_av(self):
        atk = self.make_player(power=10)
        dfn = self.make_player(def_bonus=25)
        # Mock d10 roll to ensure a hit (not critical fail)
        with patch('random.randint', return_value=5):
            ev = CombatResolver.resolve_attack(atk, dfn, weapon_dice="5d6")
            self.assertGreaterEqual(ev.damage, COMBAT_CONFIG.MIN_DMG)

    def test_combat_event_renamed_fields(self):
        # Defect #1: old names remain REAL fields, so populate BOTH pairs and assert equality.
        ev = CombatEvent(target_ac=5, d20_roll=3, target_dv=5, d10_roll=3)
        self.assertEqual(ev.target_ac, 5)
        self.assertEqual(ev.d20_roll, 3)
        self.assertEqual(ev.target_dv, 5)
        self.assertEqual(ev.d10_roll, 3)

    def test_parse_dice(self):
        self.assertEqual(parse_dice("2d6+3"), (2, 6, 3))
        self.assertEqual(parse_dice("1d10"), (1, 10, 0))
        self.assertEqual(parse_dice("4"), (0, 0, 4))

if __name__ == '__main__':
    unittest.main()