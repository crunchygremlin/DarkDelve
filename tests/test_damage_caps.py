"""Tests for damage cap and floor formulas."""
import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.domain.value_objects.damage_caps import (
    compute_monster_damage_cap,
    compute_player_damage_floor,
    clamp_monster_damage,
    clamp_player_damage,
)


class TestMonsterDamageCap(unittest.TestCase):
    """Test that monster damage is capped at 1/5 of player max HP."""

    def test_cap_at_100_hp(self):
        """Player with 100 HP should have cap of 20."""
        self.assertEqual(compute_monster_damage_cap(100), 20)

    def test_cap_at_50_hp(self):
        """Player with 50 HP should have cap of 10."""
        self.assertEqual(compute_monster_damage_cap(50), 10)

    def test_cap_minimum_1(self):
        """Cap should never be less than 1."""
        self.assertEqual(compute_monster_damage_cap(1), 1)
        self.assertEqual(compute_monster_damage_cap(4), 1)

    def test_clamp_reduces_high_damage(self):
        """Damage above cap should be reduced to cap."""
        self.assertEqual(clamp_monster_damage(50, 100), 20)

    def test_clamp_passes_low_damage(self):
        """Damage below cap should pass through unchanged."""
        self.assertEqual(clamp_monster_damage(5, 100), 5)

    def test_clamp_at_boundary(self):
        """Damage equal to cap should pass through."""
        self.assertEqual(clamp_monster_damage(20, 100), 20)


class TestPlayerDamageFloor(unittest.TestCase):
    """Test that player damage is floored so monsters die in ≤4 hits."""

    def test_floor_for_hp_15(self):
        """Monster with 15 HP should have floor of 4 (ceiling division)."""
        self.assertEqual(compute_player_damage_floor(15), 4)

    def test_floor_for_hp_6(self):
        """Monster with 6 HP should have floor of 2 (ceiling division)."""
        self.assertEqual(compute_player_damage_floor(6), 2)

    def test_floor_for_hp_3(self):
        """Monster with 3 HP should have floor of 1 (min)."""
        self.assertEqual(compute_player_damage_floor(3), 1)

    def test_floor_minimum_1(self):
        """Floor should never be less than 1."""
        self.assertEqual(compute_player_damage_floor(1), 1)

    def test_clamp_floor_boosts_low_damage(self):
        """Damage below floor should be boosted to floor."""
        self.assertEqual(clamp_player_damage(1, 15), 4)

    def test_clamp_floor_passes_high_damage(self):
        """Damage above floor should pass through."""
        self.assertEqual(clamp_player_damage(10, 15), 10)

    def test_four_hits_kills(self):
        """With floor damage, any monster should die in ≤4 hits."""
        for hp in [3, 6, 8, 10, 12, 15, 20, 30, 50, 100]:
            floor = compute_player_damage_floor(hp)
            hits_needed = (hp + floor - 1) // floor  # ceiling division
            self.assertLessEqual(hits_needed, 4, f"HP={hp}, floor={floor}, hits={hits_needed}")


class TestFloor1Balance(unittest.TestCase):
    """Verify floor 1 balance is not broken."""

    def test_floor1_monsters_dont_one_shot(self):
        """Floor  1-3) should not one-shot player (100 HP)."""
        player_max_hp = 100
        cap = compute_monster_damage_cap(player_max_hp)
        # Floor 1 max monster power is 3, well under cap of 20
        self.assertGreaterEqual(cap, 3)

    def test_player_kills_floor1_in_four_hits(self):
        """Player should kill any floor 1 monster in ≤4 hits."""
        floor1_hps = [3, 4, 6, 8, 10, 12, 15]  # From floor1_monsters.yaml
        for hp in floor1_hps:
            floor = compute_player_damage_floor(hp)
            hits_needed = hp // floor  # floor division
            self.assertLessEqual(hits_needed, 4, f"HP={hp} needs {hits_needed} hits")


if __name__ == "__main__":
    unittest.main()