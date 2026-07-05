"""Tests for monster emoji lookup."""
import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.presentation.monster_emoji import get_monster_emoji, MONSTER_EMOJI_MAP


class TestMonsterEmoji(unittest.TestCase):

    def test_spider(self):
        self.assertEqual(get_monster_emoji("giant_spider"), "🕸️")

    def test_rat(self):
        self.assertEqual(get_monster_emoji("cave_rat"), "🐀")

    def test_dragon(self):
        self.assertEqual(get_monster_emoji("dragon"), "🐉")

    def test_goblin(self):
        self.assertEqual(get_monster_emoji("goblin"), "👺")

    def test_unknown_fallback(self):
        self.assertEqual(get_monster_emoji("unknown_monster"), "❓")

    def test_case_insensitive(self):
        self.assertEqual(get_monster_emoji("DRAGON"), "🐉")
        self.assertEqual(get_monster_emoji("Cave_Rat"), "🐀")

    def test_all_floor1_monsters_have_emoji(self):
        """All floor 1 monster types should have an emoji."""
        floor1_types = [
            "dungeon_guard", "guard_sergeant", "giant_spider", "spider_queen",
            "cave_rat", "rat_king", "troll_scavenger", "fungal_creeper", "cave_bat"
        ]
        for mob_type in floor1_types:
            emoji = get_monster_emoji(mob_type)
            self.assertNotEqual(emoji, "❓Missing emoji for {mob_type}")


if __name__ == "__main__":
    unittest.main()