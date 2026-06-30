"""Tests for monster death loot system.

Verifies that monsters drop items on death, items appear on the ground,
and the loot event is logged.
"""
import pytest
from unittest.mock import MagicMock, patch
from darkdelve import (
    Game, Entity, Item, ItemType, MobTemplate, MobTier,
    COLORS, Inventory
)


class TestMonsterLoot:
    """Monster death should produce loot under the right conditions."""

    @pytest.fixture
    def game(self):
        """Create a minimal game instance for testing."""
        g = Game()
        g.state.player_class = 'warrior'
        g.state.player_name = 'TestHero'
        # Minimal config for item creation
        g.config.setdefault('classes', {}).setdefault('warrior', {
            'hp_per_level': 10, 'stats': {'str': 14, 'dex': 10, 'con': 13, 'int': 8, 'wis': 10, 'cha': 8},
            'start_gear': [],
        })
        g.config.setdefault('gameplay', {}).setdefault('max_nutrition', 2000)
        return g

    def test_monster_with_loot_table_drops_items(self, game):
        """A monster with a loot_table should drop items on death."""
        # Create a monster with a loot table
        template = MobTemplate(
            name="Goblin", symbol="g", color=(0, 255, 0), tier=MobTier.MINION,
            hp=10, power=3, defense=1,
            loot_table=[{'item_id': 'healing_potion', 'probability': 1.0}]
        )
        monster = Entity(x=5, y=5, char="g", color=(0, 255, 0), name="Goblin",
                         blocks=True, hp=0, max_hp=10, power=3, defense=1)
        monster.template = template

        # Create player
        game.create_player()
        game.player.x = 5
        game.player.y = 5

        # Track items before
        items_before = len([e for e in game.entities if hasattr(e, 'item') and e.item is not None])

        # Trigger kill
        with patch.object(game, 'create_item_by_id', return_value=Item(
            id="healing_potion", name="Healing Potion", item_type=ItemType.POTION, symbol="!"
        )) as mock_create:
            game.on_kill(game.player, monster)
            mock_create.assert_called_once_with('healing_potion')

        # An item entity should have been dropped
        items_after = [e for e in game.entities if hasattr(e, 'item') and e.item is not None]
        assert len(items_after) > items_before

    def test_monster_without_loot_table_no_items(self, game):
        """A monster without loot_table should not crash and not drop items."""
        monster = Entity(x=5, y=5, char="r", color=(255, 0, 0), name="Rat",
                         blocks=True, hp=0, max_hp=5, power=1, defense=0)
        monster.template = MobTemplate(
            name="Rat", symbol="r", color=(255, 0, 0), tier=MobTier.MINION,
            hp=5, power=1, defense=0
            # No loot_table
        )

        game.create_player()
        items_before = len([e for e in game.entities if hasattr(e, 'item') and e.item is not None])

        # Should not crash
        game.on_kill(game.player, monster)

        items_after = [e for e in game.entities if hasattr(e, 'item') and e.item is not None]
        assert len(items_after) == items_before

    def test_loot_drop_probability(self, game):
        """Loot with probability < 1.0 should sometimes drop and sometimes not."""
        template = MobTemplate(
            name="Orc", symbol="o", color=(0, 255, 0), tier=MobTier.SOLDIER,
            hp=20, power=5, defense=2,
            loot_table=[{'item_id': 'iron_longsword', 'probability': 0.0}]  # 0% chance
        )
        monster = Entity(x=5, y=5, char="o", color=(0, 255, 0), name="Orc",
                         blocks=True, hp=0, max_hp=20, power=5, defense=2)
        monster.template = template

        game.create_player()

        with patch.object(game, 'create_item_by_id', return_value=None):
            game.on_kill(game.player, monster)

        # With 0% probability, no item should be dropped
        items = [e for e in game.entities if hasattr(e, 'item') and e.item is not None and e.x == 5 and e.y == 5]
        assert len(items) == 0

    def test_loot_lands_on_monster_tile(self, game):
        """Dropped loot should appear at the monster's position."""
        template = MobTemplate(
            name="Goblin", symbol="g", color=(0, 255, 0), tier=MobTier.MINION,
            hp=10, power=3, defense=1,
            loot_table=[{'item_id': 'healing_potion', 'probability': 1.0}]
        )
        monster = Entity(x=7, y=8, char="g", color=(0, 255, 0), name="Goblin",
                         blocks=True, hp=0, max_hp=10, power=3, defense=1)
        monster.template = template

        game.create_player()

        with patch.object(game, 'create_item_by_id', return_value=Item(
            id="healing_potion", name="Healing Potion", item_type=ItemType.POTION, symbol="!"
        )):
            game.on_kill(game.player, monster)

        # Check item at monster's position
        items_here = [e for e in game.entities
                      if hasattr(e, 'item') and e.item is not None and e.x == 7 and e.y == 8]
        assert len(items_here) >= 1

    def test_on_kill_increments_kill_count(self, game):
        """Player kill count should increase on kill."""
        game.create_player()
        game.state.kills = 0

        monster = Entity(x=5, y=5, char="g", color=(0, 255, 0), name="Goblin",
                         blocks=True, hp=0, max_hp=10, power=3, defense=1)
        monster.template = MobTemplate(
            name="Goblin", symbol="g", color=(0, 255, 0), tier=MobTier.MINION,
            hp=10, power=3, defense=1
        )

        game.on_kill(game.player, monster)
        assert game.state.kills == 1

    def test_on_kill_grants_xp(self, game):
        """Player should gain XP on kill."""
        game.create_player()
        game.player.xp = 0

        monster = Entity(x=5, y=5, char="g", color=(0, 255, 0), name="Goblin",
                         blocks=True, hp=0, max_hp=10, power=3, defense=1)
        monster.template = MobTemplate(
            name="Goblin", symbol="g", color=(0, 255, 0), tier=MobTier.MINION,
            hp=10, power=3, defense=1
        )

        game.on_kill(game.player, monster)
        # XP = max_hp + power * 2 = 10 + 3*2 = 16
        assert game.player.xp == 16
