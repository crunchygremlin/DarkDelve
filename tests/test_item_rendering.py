"""Tests for item rendering on the map.

Verifies that Item entities always have a valid, deterministic symbol
based on item_type, regardless of what the LLM-generated symbol was.
"""
import pytest
from darkdelve import Item, ItemType, Entity, COLORS


class TestItemSymbol:
    """Item symbols must be deterministic based on item_type."""

    def test_potion_symbol(self):
        item = Item(id="p1", name="Healing Potion", item_type=ItemType.POTION, symbol="?")
        assert item.symbol == "!", f"Potion should use '!' symbol, got '{item.symbol}'"

    def test_weapon_symbol(self):
        item = Item(id="w1", name="Iron Sword", item_type=ItemType.WEAPON, symbol="?")
        assert item.symbol == "/", f"Weapon should use '/' symbol, got '{item.symbol}'"

    def test_armor_symbol(self):
        item = Item(id="a1", name="Leather Armor", item_type=ItemType.ARMOR, symbol="?")
        assert item.symbol == "[", f"Armor should use '[' symbol, got '{item.symbol}'"

    def test_scroll_symbol(self):
        item = Item(id="s1", name="Scroll of Fire", item_type=ItemType.SCROLL, symbol="?")
        assert item.symbol == "?", f"Scroll should use '?' symbol, got '{item.symbol}'"

    def test_food_symbol(self):
        item = Item(id="f1", name="Bread", item_type=ItemType.FOOD, symbol="?")
        assert item.symbol == ",", f"Food should use ',' symbol, got '{item.symbol}'"

    def test_misc_symbol(self):
        item = Item(id="m1", name="Rock", item_type=ItemType.MISC, symbol="?")
        assert item.symbol == "*", f"Misc should use '*' symbol, got '{item.symbol}'"

    def test_item_entity_renders_correctly(self):
        """An Entity created from an item should use the item's symbol."""
        item = Item(id="p1", name="Healing Potion", item_type=ItemType.POTION, symbol="?")
        entity = Entity(
            x=5, y=5,
            char=item.symbol, color=COLORS['item'],
            name=item.name, blocks=False,
            hp=1, max_hp=1, power=0, defense=0,
            speed=0, intel_tier=0, is_commander=False,
        )
        assert entity.char == "!"

    def test_item_symbol_overrides_llm_output(self):
        """Even if LLM generated a weird symbol like '%', post_init should fix it."""
        item = Item(id="bad1", name="Weird Potion", item_type=ItemType.POTION, symbol="%")
        assert item.symbol == "!", f"Should override LLM symbol '%' with '!'"

    def test_item_has_color(self):
        """Items must have a color for rendering."""
        item = Item(id="p1", name="Healing Potion", item_type=ItemType.POTION, symbol="?")
        assert item.color is not None
        assert len(item.color) == 3

    def test_glyph_override_takes_precedence(self):
        """If glyph is explicitly set, it should override the type-based symbol."""
        item = Item(id="g1", name="Magic Sword", item_type=ItemType.WEAPON, symbol="?", glyph=")")
        assert item.symbol == ")"
