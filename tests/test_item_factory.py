"""Tests for item creation system."""
import pytest
from src.domain.value_objects.item_creation import (
    ItemType, ItemPower, ItemDefense, ItemModifier, ItemCurse,
    ItemStats, Item
)
from src.domain.components.item_factory import ItemFactory


class TestItemEnums:
    """Tests for item creation enums."""

    def test_item_type_values(self):
        """Test ItemType enum values."""
        assert ItemType.SWORD.value == "sword"
        assert ItemType.AXE.value == "axe"
        assert ItemType.SHIELD.value == "shield"
        assert ItemType.POTION.value == "potion"

    def test_item_power_values(self):
        """Test ItemPower enum values."""
        assert ItemPower.FIRE.value == "fire"
        assert ItemPower.LIGHTNING.value == "lightning"
        assert ItemPower.HOLY.value == "holy"

    def test_item_modifier_values(self):
        """Test ItemModifier enum values."""
        assert ItemModifier.SHARP.value == "sharp"
        assert ItemModifier.VAMPIRIC.value == "vampiric"


class TestItemStats:
    """Tests for ItemStats dataclass."""

    def test_default_stats(self):
        """Test default ItemStats values."""
        stats = ItemStats()
        assert stats.damage == 0.0
        assert stats.damage_type == "physical"
        assert stats.defense == 0.0
        assert stats.attack_speed == 1.0
        assert stats.critical_chance == 0.05
        assert stats.durability_max == 100
        assert stats.durability_current == 100
        assert stats.uses_remaining == -1

    def test_custom_stats(self):
        """Test creating custom ItemStats."""
        stats = ItemStats(
            damage=15.0,
            damage_type="fire",
            defense=5.0,
            durability_max=200
        )
        assert stats.damage == 15.0
        assert stats.damage_type == "fire"
        assert stats.defense == 5.0
        assert stats.durability_max == 200


class TestItem:
    """Tests for Item dataclass."""

    def test_item_creation(self):
        """Test creating an item."""
        stats = ItemStats(damage=10.0, durability_max=100)
        item = Item(
            item_id="test_sword",
            name="Test Sword",
            description="A test weapon",
            item_type="sword",
            rarity="rare",
            powers=["fire"],
            defenses=["fire_def"],
            modifiers=["sharp"],
            curses=[],
            stats=stats
        )
        assert item.item_id == "test_sword"
        assert item.name == "Test Sword"
        assert item.rarity == "rare"
        assert item.is_identified is True

    def test_item_degraded_check(self):
        """Test is_degraded property."""
        stats = ItemStats(damage=10.0, durability_max=100, durability_current=40)
        item = Item(
            item_id="test", name="Test", description="", item_type="sword",
            rarity="common", powers=[], defenses=[], modifiers=[], curses=[], stats=stats
        )
        assert item.is_degraded is True

    def test_item_destroyed_check(self):
        """Test is_destroyed property."""
        stats = ItemStats(damage=10.0, durability_max=100, durability_current=0)
        item = Item(
            item_id="test", name="Test", description="", item_type="sword",
            rarity="common", powers=[], defenses=[], modifiers=[], curses=[], stats=stats
        )
        assert item.is_destroyed is True

    def test_item_use(self):
        """Test using an item with limited uses."""
        stats = ItemStats(uses_remaining=3)
        item = Item(
            item_id="potion", name="Health Potion", description="", item_type="potion",
            rarity="common", powers=[], defenses=[], modifiers=[], curses=[], stats=stats
        )
        assert item.use() is False  # uses_remaining becomes 2
        assert item.use() is False  # uses_remaining becomes 1
        assert item.use() is True   # uses_remaining becomes 0, item consumed


class TestItemFactory:
    """Tests for ItemFactory component."""

    def test_factory_creates_item(self):
        """Test that factory creates items with unique IDs."""
        factory = ItemFactory()
        item = factory.create_item(name="Test Weapon", item_type="sword")
        assert item.item_id.startswith("item_")
        assert item.name == "Test Weapon"

    def test_factory_boss_slayer(self):
        """Test creating a boss slayer item."""
        factory = ItemFactory()
        item = factory.create_boss_slayer("dragon", "fire", 5)
        assert "dragon" in item.name.lower()
        assert item.boss_bonus == "fire"

    def test_factory_puzzle_item(self):
        """Test creating a puzzle item."""
        factory = ItemFactory()
        item = factory.create_puzzle_item("puzzle_001", 1, 3)
        assert item.puzzle_role == "puzzle_001"
        assert item.level_origin == 1

    def test_factory_trash_item(self):
        """Test creating a trash item."""
        factory = ItemFactory()
        item = factory.create_trash_item(2)
        assert item.level_origin == 2

    def test_generate_item_name(self):
        """Test item name generation."""
        factory = ItemFactory()
        name = factory.generate_item_name("sword", ["fire"], ["sharp"])
        assert "Sharp" in name
        assert "Fire" in name
        assert "Sword" in name