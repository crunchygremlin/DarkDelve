"""Tests for item emoji lookup."""
import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.presentation.item_emoji import get_item_emoji, ITEM_EMOJI_MAP


class TestItemEmoji(unittest.TestCase):

    def test_weapon_type(self):
        self.assertEqual(get_item_emoji("weapon"), "⚔️")

    def test_armor_type(self):
        self.assertEqual(get_item_emoji("armor"), "🛡️")

    def test_potion_type(self):
        self.assertEqual(get_item_emoji("potion"), "🧪")

    def test_scroll_type(self):
        self.assertEqual(get_item_emoji("scroll"), "📜")

    def test_accessory_type(self):
        self.assertEqual(get_item_emoji("accessory"), "💍")

    def test_sword_name(self):
        self.assertEqual(get_item_emoji("weapon", "Iron Sword"), "⚔️")

    def test_ring_name(self):
        self.assertEqual(get_item_emoji("accessory", "Ring of Power"), "💍")

    def test_amulet_name(self):
        self.assertEqual(get_item_emoji("accessory", "Amulet of Wisdom"), "📿")

    def test_unknown_fallback(self):
        self.assertEqual(get_item_emoji("unknown_type", "Mystery Item"), "📦")

    def test_gold_name(self):
        self.assertEqual(get_item_emoji("misc", "Gold Coins"), "💰")


if __name__ == "__main__":
    unittest.main()