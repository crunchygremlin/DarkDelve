"""
Tests for inventory use/drop input path.

Verifies:
- UseCommand applies item effects and removes consumables
- DropCommand removes item and records drop position
- Player.drop_item / Player.use_item domain methods
- Integration between UseCommand and DropCommand
- Runtime Entity (darkdelve.py) drop/use behaviour
"""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.domain.entities.player import Player
from src.domain.entities.item import Item
from src.domain.value_objects.position import Position
from src.application.game_commands.use_command import UseCommand
from src.application.game_commands.drop_command import DropCommand


# ---------------------------------------------------------------------------
# TestUseCommand – 3 tests, domain Player
# ---------------------------------------------------------------------------
class TestUseCommand(unittest.TestCase):
    """Test UseCommand directly with domain Player."""

    def test_use_potion_heals_player(self):
        """Using a heal potion via UseCommand should restore HP."""
        player = Player(position=Position(0, 0), name="Tester")
        potion = Item(
            item_id="potion_heal",
            name="Health Potion",
            item_type="potion",
            description="Restores 20 HP.",
            value=10,
            weight=0.5,
        )
        potion.consumable = True
        potion.effect = "heal+20"
        player.add_item_to_inventory("potion_heal")
        player.health = 50

        cmd = UseCommand(player=player, item=potion)
        result = cmd.execute()

        self.assertTrue(result.success)
        self.assertEqual(player.health, 70)

    def test_use_consumable_decrements_stack(self):
        """Using a consumable should remove it from inventory."""
        player = Player(position=Position(0, 0), name="Tester")
        potion = Item(
            item_id="potion_heal2",
            name="Health Potion",
            item_type="potion",
            description="Restores 20 HP.",
            value=10,
            weight=0.5,
        )
        potion.consumable = True
        potion.effect = "heal+20"
        player.add_item_to_inventory("potion_heal2")

        self.assertEqual(player.get_item_count("potion_heal2"), 1)

        cmd = UseCommand(player=player, item=potion)
        result = cmd.execute()

        self.assertTrue(result.success)
        self.assertEqual(player.get_item_count("potion_heal2"), 0)

    def test_use_non_usable_item_fails(self):
        """Using a non-usable item (e.g. weapon with no effect) should fail."""
        player = Player(position=Position(0, 0), name="Tester")
        sword = Item(
            item_id="sword_1",
            name="Iron Sword",
            item_type="weapon",
            description="A basic sword.",
            value=25,
            weight=3.0,
        )
        sword.consumable = False
        # weapon has no effect string → can_execute returns False
        player.add_item_to_inventory("sword_1")

        cmd = UseCommand(player=player, item=sword)
        result = cmd.execute()

        self.assertFalse(result.success)


# ---------------------------------------------------------------------------
# TestDropCommand – 2 tests, domain Player
# ---------------------------------------------------------------------------
class TestDropCommand(unittest.TestCase):
    """Test DropCommand directly with domain Player."""

    def test_drop_removes_item_from_inventory(self):
        """Dropping an item should remove it from the player's inventory."""
        player = Player(position=Position(5, 3), name="Tester")
        potion = Item(
            item_id="potion_drop",
            name="Health Potion",
            item_type="potion",
            description="Restores 20 HP.",
            value=10,
            weight=0.5,
        )
        player.add_item_to_inventory("potion_drop")
        self.assertEqual(player.get_item_count("potion_drop"), 1)

        cmd = DropCommand(player=player, item=potion)
        result = cmd.execute()

        self.assertTrue(result.success)
        self.assertEqual(player.get_item_count("potion_drop"), 0)

    def test_drop_records_player_position(self):
        """DropCommand result data should contain the player's position."""
        player = Player(position=Position(7, 11), name="Tester")
        sword = Item(
            item_id="sword_drop",
            name="Iron Sword",
            item_type="weapon",
            description="A basic sword.",
            value=25,
            weight=3.0,
        )
        player.add_item_to_inventory("sword_drop")

        cmd = DropCommand(player=player, item=sword)
        result = cmd.execute()

        self.assertTrue(result.success)
        drop_pos = result.data["drop_position"]
        self.assertIsInstance(drop_pos, Position)
        self.assertEqual(drop_pos.x, 7)
        self.assertEqual(drop_pos.y, 11)


# ---------------------------------------------------------------------------
# TestPlayerDropItem – 2 tests, domain Player
# ---------------------------------------------------------------------------
class TestPlayerDropItem(unittest.TestCase):
    """Test Player.drop_item domain method directly."""

    def test_drop_item_removes_from_inventory(self):
        """Player.drop_item should remove the item and return True."""
        player = Player(position=Position(0, 0), name="Tester")
        potion = Item(
            item_id="p_drop_1",
            name="Mana Potion",
            item_type="potion",
            description="Restores mana.",
            value=15,
            weight=0.5,
        )
        player.add_item_to_inventory("p_drop_1")
        self.assertTrue(player.get_item_count("p_drop_1") > 0)

        result = player.drop_item(potion)
        self.assertTrue(result)
        self.assertEqual(player.get_item_count("p_drop_1"), 0)

    def test_drop_item_not_in_inventory_fails(self):
        """Dropping an item the player doesn't have should return False."""
        player = Player(position=Position(0, 0), name="Tester")
        potion = Item(
            item_id="p_drop_missing",
            name="Ghost Potion",
            item_type="potion",
            description="Doesn't exist in inventory.",
            value=0,
            weight=0.5,
        )
        # Never added to inventory
        result = player.drop_item(potion)
        self.assertFalse(result)


# ---------------------------------------------------------------------------
# TestInventoryUseDropIntegration – 2 tests, domain Player
# ---------------------------------------------------------------------------
class TestInventoryUseDropIntegration(unittest.TestCase):
    """Integration tests combining use and drop workflows."""

    def test_use_then_drop_different_items(self):
        """Use one item and drop another; both should work independently."""
        player = Player(position=Position(2, 4), name="Tester")
        # Item A – consumable potion for use
        potion = Item(
            item_id="int_potion",
            name="Health Potion",
            item_type="potion",
            description="Heal 10.",
            value=5,
            weight=0.5,
        )
        potion.consumable = True
        potion.effect = "heal+10"
        # Item B – weapon for drop
        sword = Item(
            item_id="int_sword",
            name="Short Sword",
            item_type="weapon",
            description="A sword.",
            value=20,
            weight=2.0,
        )
        player.add_item_to_inventory("int_potion")
        player.add_item_to_inventory("int_sword")
        player.health = 40

        use_cmd = UseCommand(player=player, item=potion)
        use_result = use_cmd.execute()
        self.assertTrue(use_result.success)
        self.assertEqual(player.health, 50)
        self.assertEqual(player.get_item_count("int_potion"), 0)

        drop_cmd = DropCommand(player=player, item=sword)
        drop_result = drop_cmd.execute()
        self.assertTrue(drop_result.success)
        self.assertEqual(player.get_item_count("int_sword"), 0)

    def test_drop_then_use_remaining_item(self):
        """Drop an item, then use a remaining consumable."""
        player = Player(position=Position(1, 1), name="Tester")
        potion = Item(
            item_id="int_potion2",
            name="Health Potion",
            item_type="potion",
            description="Heal 15.",
            value=5,
            weight=0.5,
        )
        potion.consumable = True
        potion.effect = "heal+15"
        sword = Item(
            item_id="int_sword2",
            name="Long Sword",
            item_type="weapon",
            description="A sword.",
            value=30,
            weight=3.0,
        )
        player.add_item_to_inventory("int_potion2")
        player.add_item_to_inventory("int_sword2")
        player.health = 30

        # Drop the sword first
        drop_cmd = DropCommand(player=player, item=sword)
        drop_result = drop_cmd.execute()
        self.assertTrue(drop_result.success)

        # Then use the potion
        use_cmd = UseCommand(player=player, item=potion)
        use_result = use_cmd.execute()
        self.assertTrue(use_result.success)
        self.assertEqual(player.health, 45)


# ---------------------------------------------------------------------------
# TestRuntimeEntityDropUse – 8 tests, runtime Entity from darkdelve.py
# ---------------------------------------------------------------------------
class TestRuntimeEntityDropUse(unittest.TestCase):
    """Test drop/use on the runtime Entity dataclass from darkdelve.py."""

    def _import_runtime(self):
        """Import darkdelve.py at runtime to access Entity, Item, Inventory, ItemType."""
        import importlib.util as _ilu
        _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _DARKDELVE_PATH = os.path.join(_REPO_ROOT, "darkdelve.py")
        _spec = _ilu.spec_from_file_location("darkdelve_runtime", _DARKDELVE_PATH)
        _mod = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        return _mod

    def setUp(self):
        """Import runtime module and create a fresh player-like Entity."""
        mod = self._import_runtime()
        self.mod = mod
        self.ItemType = mod.ItemType
        self.Item = mod.Item
        self.Inventory = mod.Inventory
        self.Entity = mod.Entity

        # Create a player-like entity with an inventory
        self.entity = mod.Entity(
            name="RuntimePlayer",
            x=3,
            y=7,
            char="@",
            hp=50,
            max_hp=100,
        )
        self.entity.inventory = mod.Inventory()

    def _make_potion(self, item_id="rt_potion", name="Health Potion", effect="heal+20"):
        """Helper to create a runtime potion Item."""
        return self.Item(
            id=item_id,
            name=name,
            item_type=self.ItemType.POTION,
            special_effect=effect,
        )

    def _make_weapon(self, item_id="rt_sword", name="Iron Sword"):
        """Helper to create a runtime weapon Item."""
        return self.Item(
            id=item_id,
            name=name,
            item_type=self.ItemType.WEAPON,
        )

    # --- 8 tests ---

    def test_runtime_add_item_to_inventory(self):
        """Adding an item to runtime Entity inventory should succeed."""
        potion = self._make_potion()
        result = self.entity.add_item(potion)
        self.assertTrue(result)
        self.assertEqual(len(self.entity.inventory.items), 1)
        self.assertEqual(self.entity.inventory.items[0].id, "rt_potion")

    def test_runtime_get_item_count(self):
        """get_item_count should reflect items in runtime inventory."""
        potion = self._make_potion()
        self.entity.add_item(potion)
        self.assertEqual(self.entity.get_item_count(potion), 1)

        sword = self._make_weapon()
        self.entity.add_item(sword)
        self.assertEqual(self.entity.get_item_count(sword), 1)
        self.assertEqual(self.entity.get_item_count("nonexistent"), 0)

    def test_runtime_drop_item_removes_from_inventory(self):
        """drop_item should remove the item from runtime Entity inventory."""
        potion = self._make_potion()
        self.entity.add_item(potion)
        self.assertEqual(self.entity.get_item_count(potion), 1)

        result = self.entity.drop_item(potion)
        self.assertTrue(result)
        self.assertEqual(self.entity.get_item_count(potion), 0)

    def test_runtime_drop_item_not_in_inventory_fails(self):
        """Dropping an item not in inventory should return False."""
        potion = self._make_potion(item_id="ghost_potion")
        result = self.entity.drop_item(potion)
        self.assertFalse(result)

    def test_runtime_use_item_heals(self):
        """Using a heal potion should increase HP on runtime Entity."""
        potion = self._make_potion(effect="heal+25")
        self.entity.add_item(potion)
        self.entity.hp = 30

        result = self.entity.use_item(potion)
        self.assertTrue(result)
        self.assertEqual(self.entity.hp, 55)

    def test_runtime_use_consumable_removes_item(self):
        """Using a consumable potion should remove it from inventory."""
        potion = self._make_potion()
        self.entity.add_item(potion)
        self.assertEqual(self.entity.get_item_count(potion), 1)

        result = self.entity.use_item(potion)
        self.assertTrue(result)
        self.assertEqual(self.entity.get_item_count(potion), 0)

    def test_runtime_use_item_not_in_inventory_fails(self):
        """Using an item not in inventory should return False."""
        potion = self._make_potion(item_id="missing_potion")
        result = self.entity.use_item(potion)
        self.assertFalse(result)

    def test_runtime_drop_then_use_separate_items(self):
        """Drop one item and use another; both should work correctly."""
        potion = self._make_potion(item_id="rt_p2", effect="heal+10")
        sword = self._make_weapon(item_id="rt_sw2")
        self.entity.add_item(potion)
        self.entity.add_item(sword)
        self.entity.hp = 40

        # Drop the sword
        drop_result = self.entity.drop_item(sword)
        self.assertTrue(drop_result)
        self.assertEqual(self.entity.get_item_count(sword), 0)
        self.assertEqual(self.entity.get_item_count(potion), 1)

        # Use the potion
        use_result = self.entity.use_item(potion)
        self.assertTrue(use_result)
        self.assertEqual(self.entity.hp, 50)
        self.assertEqual(self.entity.get_item_count(potion), 0)


if __name__ == "__main__":
    unittest.main()
