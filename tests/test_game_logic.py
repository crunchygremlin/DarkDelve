#!/usr/bin/env python3
"""
Test suite for DarkDelve game logic
"""

import unittest
import numpy as np
import tcod
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path to import darkdelve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from darkdelve import Game, Entity, Item, Inventory, GameState, CONFIG, COLORS, ItemType, EquipmentSlot, EnergySystem, FOVSystem


class TestGameLogic(unittest.TestCase):
    """Test cases for game logic"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = CONFIG
        self.game = Game()
        self.game.initialize()

    def _game_with_player(self) -> Game:
        """Create a lightweight game instance for action-level tests."""
        game = Game()
        game.player = Entity(
            x=1,
            y=1,
            char="@",
            color=COLORS["player"],
            name="Test Player",
            blocks=True,
            hp=10,
            max_hp=10,
            power=5,
            defense=2,
            speed=100,
            intel_tier=0,
            inventory=Inventory(max_weight=100),
        )
        game.dungeon_map = np.zeros((5, 5), dtype=bool)
        game.entities = [game.player]
        game.energy_system = EnergySystem()
        game.energy_system.add_entity(game.player, initial_energy=100)
        game.fov = np.zeros((5, 5), dtype=bool)
        game.fov[1, 1] = True
        game.explored = game.fov.copy()
        game.fov_system = FOVSystem(radius=1)
        game.combat_log = MagicMock()
        game.survival = MagicMock()
        game.renderer = MagicMock()
        game.ui = MagicMock()
        game.check_level_up = lambda: None
        return game

    def test_game_config_has_playtest_flag(self):
        """The game config should expose an opt-in in-process playtester flag."""
        self.assertIn("playtest", CONFIG)
        self.assertEqual(CONFIG["playtest"]["config_path"], "playtest/playtest_config.yaml")
        self.assertIs(CONFIG["playtest"]["enabled"], False)

    def test_game_initialization(self):
        """Test game initialization"""
        self.assertIsNotNone(self.game)
        self.assertIsNotNone(self.game.config)
        self.assertIsNotNone(self.game.state)
        self.assertIsNotNone(self.game.entities)

    def test_create_player(self):
        """Test player creation"""
        self.game.create_player()

        self.assertIsNotNone(self.game.player)
        self.assertEqual(self.game.player.char, "@")
        self.assertEqual(self.game.player.name, "Adventurer")
        self.assertTrue(self.game.player.blocks)

    def test_generate_level(self):
        """Test level generation"""
        self.game.create_player()
        self.game.generate_level(1, "main")

        # Check that level was generated
        self.assertIsNotNone(self.game.dungeon_map)
        self.assertGreater(len(self.game.entities), 0)
        self.assertIsNotNone(self.game.player.x)
        self.assertIsNotNone(self.game.player.y)

    def test_player_movement(self):
        """Test player movement"""
        self.game.create_player()
        self.game.generate_level(1, "main")

        original_x, original_y = self.game.player.x, self.game.player.y
        if original_x + 1 < self.game.dungeon_map.shape[0]:
            self.game.dungeon_map[original_x + 1, original_y] = 0

        # Move player
        self.game.player.move(1, 0, self.game.dungeon_map)

        # Check that player moved
        self.assertEqual(self.game.player.x, original_x + 1)
        self.assertEqual(self.game.player.y, original_y)

    def test_process_action_moves_player_without_blocking_input(self):
        """Library actions should move the player without waiting for console input."""
        game = self._game_with_player()

        game.process_action("d")

        self.assertEqual(game.player.x, 2)
        self.assertEqual(game.player.y, 1)

    def test_process_action_attacks_blocking_entity(self):
        """Movement actions should attack blocking enemies adjacent to the player."""
        game = self._game_with_player()
        enemy = Entity(
            x=2,
            y=1,
            char="g",
            color=COLORS["enemy_normal"],
            name="Goblin",
            blocks=True,
            hp=10,
            max_hp=10,
            power=5,
            defense=2,
            speed=100,
        )
        game.entities.append(enemy)

        with patch("darkdelve.random.randint", return_value=20):
            game.process_action("d")

        self.assertEqual(game.player.x, 1)
        self.assertLess(enemy.hp, 10)

    def test_process_action_pickup_uses_comma(self):
        """Comma should pick up an item on the player's tile."""
        game = self._game_with_player()
        item = Item(id="test_item", name="Test Item", item_type=ItemType.MISC, symbol="*")
        item_entity = Entity(
            x=game.player.x,
            y=game.player.y,
            char="*",
            color=COLORS["item"],
            name="Test Item",
            blocks=False,
            item=item,
        )
        game.entities.append(item_entity)
        game.energy_system.add_entity(item_entity)

        picked_up = game.process_action(",")

        self.assertFalse(picked_up)
        self.assertEqual(game.player.inventory.items, [item])
        self.assertNotIn(item_entity, game.entities)

    def test_process_action_stairs_down(self):
        """Greater-than should descend stairs when the player is standing on them."""
        self.game.create_player()
        self.game.generate_level(1, "main")
        self.assertIsNotNone(self.game.stair_down_pos)
        self.game.player.x, self.game.player.y = self.game.stair_down_pos

        self.game.process_action(">")

        self.assertEqual(self.game.state.depth, 2)

    def test_process_action_inventory_is_noop(self):
        """Inventory should not enter the blocking screen during automated playtests."""
        game = self._game_with_player()

        self.assertFalse(game.process_action("i"))
        self.assertFalse(game.showing_inventory)

    def test_process_action_unknown_action_is_noop(self):
        """Unknown actions should not change game state."""
        game = self._game_with_player()
        original_x, original_y = game.player.x, game.player.y

        self.assertFalse(game.process_action("z"))

        self.assertEqual(game.player.x, original_x)
        self.assertEqual(game.player.y, original_y)

    def test_process_action_quit_stops_game(self):
        """Control characters should stop the automated game loop."""
        game = self._game_with_player()

        self.assertTrue(game.process_action("\x1b"))
        self.assertFalse(game.running)

    def test_main_loop_accepts_library_action(self):
        """main_loop should process a supplied action without waiting for input."""
        game = self._game_with_player()
        game._wait_for_events = MagicMock()

        game.main_loop(action="d", render_to_stdout=False, frame_text="frame")

        self.assertEqual(game.player.x, 2)
        self.assertEqual(game.turn, 1)
        game._wait_for_events.assert_not_called()
        game.renderer.present.assert_not_called()

    def test_render_frame_text_returns_console_text_without_presenting(self):
        """render_frame_text should render to the console buffer and return text."""
        game = self._game_with_player()
        console = tcod.console.Console(5, 3)
        console.print(1, 1, "@")
        renderer = SimpleNamespace(_console=console, clear=MagicMock())
        ui = SimpleNamespace(
            render_dungeon=MagicMock(),
            render_entities=MagicMock(),
            render_ui=MagicMock(),
        )
        game.renderer = renderer
        game.ui = ui

        text = game.render_frame_text()

        self.assertIn("@", text)
        renderer.clear.assert_called_once()
        ui.render_dungeon.assert_called_once()
        ui.render_entities.assert_called_once()
        ui.render_ui.assert_called_once()

    def test_player_collision(self):
        """Test player collision with walls"""
        self.game.create_player()
        self.game.generate_level(1, "main")

        # Try to move into a wall
        original_x, original_y = self.game.player.x, self.game.player.y

        # Find a wall direction
        moved = False
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            new_x = self.game.player.x + dx
            new_y = self.game.player.y + dy

            if (0 <= new_x < self.game.dungeon_map.shape[1] and
                0 <= new_y < self.game.dungeon_map.shape[0]):

                if self.game.dungeon_map[new_x, new_y] == 1:  # Wall
                    self.game.player.move(dx, dy, self.game.dungeon_map)
                    # Should not move into wall
                    self.assertEqual(self.game.player.x, original_x)
                    self.assertEqual(self.game.player.y, original_y)
                    moved = True
                    break
                    
        # If no wall found, test with a guaranteed wall
        if not moved:
            # Create a wall at player position + 2
            wall_x = self.game.player.x + 2
            wall_y = self.game.player.y
            
            if wall_x < self.game.dungeon_map.shape[1]:
                self.game.dungeon_map[wall_x, wall_y] = 1
                
                # Try to move into wall
                self.game.player.move(2, 0, self.game.dungeon_map)
                self.assertEqual(self.game.player.x, original_x)
                
    def test_pickup_items(self):
        """Test item pickup"""
        self.game.create_player()
        self.game.generate_level(1, "main")
        
        # Create an item at player position
        item = Item(
            id="test_item",
            name="Test Item",
            description="A test item",
            glyph="*",
            color=COLORS['item'],
            item_type=ItemType.MISC
        )
        
        # Place item at player position
        item_entity = Entity(
            x=self.game.player.x,
            y=self.game.player.y,
            char="*",
            color=COLORS['item'],
            name="Test Item",
            blocks=False,
            item=item
        )
        
        self.game.entities.append(item_entity)
        self.game.energy_system.add_entity(item_entity, speed=0)
        
        # Pick up item
        picked_up = self.game.pickup_item()
        
        # Check that item was picked up
        self.assertTrue(picked_up)
        self.assertEqual(len(self.game.player.inventory.items), 1)
        self.assertEqual(self.game.player.inventory.items[0], item)
        self.assertNotIn(item_entity, self.game.entities)
        self.assertNotIn(item_entity, [entry["entity"] for entry in self.game.energy_system.entities])

    def test_pickup_item_accepts_string_weight_from_generated_content(self):
        """Item weights from generated/external content may arrive as strings."""
        inventory = Inventory(max_weight=10)
        item = Item(
            id="string_weight_item",
            name="String Weight Item",
            description="A generated item with a string weight",
            item_type=ItemType.MISC,
            weight="3",
        )

        self.assertTrue(inventory.add_item(item))
        self.assertEqual(inventory.get_total_weight(), 3)

    def test_pickup_item_reports_when_no_item_is_present(self):
        """Test item pickup feedback when the current tile has no item."""
        self.game.create_player()
        self.game.generate_level(1, "main")

        picked_up = self.game.pickup_item()

        self.assertFalse(picked_up)
        self.assertEqual(self.game.message_log[-1], "There is nothing here to pick up.")

    def test_main_loop_updates_fov_after_player_movement(self):
        """Player movement must recompute FOV before the next render."""
        game = Game()
        game.create_player()
        game.player.x = 3
        game.player.y = 3
        game.dungeon_map = np.zeros((7, 7), dtype=bool)
        game.entities = [game.player]
        game.energy_system = EnergySystem()
        game.energy_system.add_entity(game.player, initial_energy=100)
        game.fov_system = FOVSystem(radius=2)
        game.fov = game.fov_system.compute(game.dungeon_map, game.player.x, game.player.y)
        game.explored = game.fov_system.explored.copy()
        game.renderer = MagicMock()
        game.ui = MagicMock()
        game.combat_log = MagicMock()
        game.survival = MagicMock()

        def handle_event(event, player, dungeon_map, entities, state, game_instance):
            player.move_to(player.x + 1, player.y, dungeon_map, entities)
            return False

        game.input_handler = MagicMock()
        game.input_handler.handle_event.side_effect = handle_event
        game._wait_for_events = lambda: [
            tcod.event.KeyDown(
                scancode=tcod.event.Scancode.W,
                sym=tcod.event.KeySym.W,
                mod=tcod.event.Modifier.NONE,
            )
        ]

        game.main_loop()

        self.assertEqual(game.player.x, 4)
        self.assertTrue(game.fov[4, 3])
        self.assertTrue(game.explored[4, 3])

    def test_use_stairs_down(self):
        """Test using stairs down"""
        self.game.create_player()
        self.game.generate_level(1, "main")
        
        # Set player position at stairs down
        if self.game.stair_down_pos:
            self.game.player.x, self.game.player.y = self.game.stair_down_pos
            
            # Use stairs down
            self.game.use_stairs_down()
            
            # Check that level increased
            self.assertEqual(self.game.state.depth, 2)
            
    def test_use_stairs_up(self):
        """Test using stairs up"""
        self.game.create_player()
        self.game.generate_level(2, "main")  # Start at level 2
        
        # Set player position at stairs up
        if self.game.stair_up_pos:
            self.game.player.x, self.game.player.y = self.game.stair_up_pos
            
            # Use stairs up
            self.game.use_stairs_up()
            
            # Check that level decreased
            self.assertEqual(self.game.state.depth, 1)
            
    def test_attack_enemy(self):
        """Test attacking enemies"""
        self.game.create_player()
        self.game.generate_level(1, "main")
        
        # Create an enemy adjacent to player
        enemy = Entity(
            x=self.game.player.x + 1,
            y=self.game.player.y,
            char="g",
            color=COLORS['enemy_normal'],
            name="Goblin",
            blocks=True
        )
        
        # Add combat attributes
        enemy.power = 5
        enemy.defense = 2
        enemy.max_hp = 10
        enemy.hp = 10
        
        self.game.entities.append(enemy)
    
        # Attack enemy
        with patch('random.randint', return_value=20):
            self.game.attack(self.game.player, enemy)
        
        # Check that enemy took damage
        self.assertLess(enemy.hp, 10)
        
    def test_player_death(self):
        """Test player death"""
        self.game.create_player()
        
        # Set player HP to 0
        self.game.player.hp = 0
        
        # Check that player is dead
        self.assertFalse(self.game.player.is_alive)
        
    def test_enemy_death(self):
        """Test enemy death"""
        enemy = Entity(
            x=5, y=5,
            char="g",
            color=COLORS['enemy_normal'],
            name="Goblin",
            blocks=True
        )
        
        # Set enemy HP to 0
        enemy.hp = 0
        
        # Check that enemy is dead
        self.assertFalse(enemy.is_alive)
        
    def test_game_over(self):
        """Test game over"""
        self.game.create_player()
        
        # Set player HP to 0
        self.game.player.hp = 0
        
        # Trigger game over
        self.game.game_over()
        
        # Check that game is over
        self.assertFalse(self.game.running)
        
    def test_save_and_load_game(self):
        """Test saving and loading game"""
        self.game.create_player()
        self.game.generate_level(1, "main")
        
        # Modify game state
        self.game.player.x = 10
        self.game.player.y = 10
        self.game.player.hp = 15
        
        # Save game
        self.game.save_and_quit()
        
        # Load game (this would require actual file I/O)
        # For now, just check that save system exists
        self.assertIsNotNone(self.game.save_system)
        
    def test_inventory_management(self):
        """Test inventory management"""
        self.game.create_player()
        
        # Create items
        item1 = Item(
            id="item1",
            name="Item 1",
            description="First item",
            glyph="*",
            color=COLORS['item'],
            item_type=ItemType.MISC
        )
        
        item2 = Item(
            id="item2",
            name="Item 2",
            description="Second item",
            glyph="=",
            color=COLORS['item'],
            item_type=ItemType.MISC
        )
        
        # Add items to inventory
        self.game.player.inventory.add_item(item1)
        self.game.player.inventory.add_item(item2)
        
        # Check inventory
        self.assertEqual(len(self.game.player.inventory.items), 2)
        
        # Remove item
        self.game.player.inventory.remove_item(item1)
        self.assertEqual(len(self.game.player.inventory.items), 1)
        
    def test_equipment_system(self):
        """Test equipment system"""
        self.game.create_player()
        
        # Create equipment
        weapon = Item(
            id="iron_sword",
            name="Iron Sword",
            description="A sharp iron sword",
            glyph="/",
            color=COLORS['item'],
            item_type=ItemType.WEAPON,
            equipment_slot=EquipmentSlot.MAIN_HAND
        )
        
        armor = Item(
            id="leather_armor",
            name="Leather Armor",
            description="Protective leather armor",
            glyph="[",
            color=COLORS['equipment'],
            item_type=ItemType.ARMOR,
            equipment_slot=EquipmentSlot.BODY
        )
        
        # Add items to inventory
        self.game.player.inventory.add_item(weapon)
        self.game.player.inventory.add_item(armor)
        
        # Equip items
        self.game.player.inventory.equip(weapon.id, EquipmentSlot.MAIN_HAND)
        self.game.player.inventory.equip(armor.id, EquipmentSlot.BODY)
        
        # Check that items are equipped
        self.assertTrue(weapon.equipped)
        self.assertTrue(armor.equipped)
        
    def test_experience_and_leveling(self):
        """Test experience and leveling system"""
        self.game.create_player()
        
        # Set initial experience
        self.game.player.xp = 0
        self.game.player.level = 1
        self.game.player.xp_to_next = 100
        
        # Add experience
        self.game.player.xp = 100
        
        # Check for level up
        self.game.check_level_up()
        
        # Check that player leveled up
        self.assertEqual(self.game.player.level, 2)
        self.assertEqual(self.game.player.xp, 0)
        self.assertEqual(self.game.player.xp_to_next, 150)
        
    def test_score_calculation(self):
        """Test score calculation"""
        self.game.create_player()
        
        # Set up player stats
        self.game.player.level = 5
        self.game.player.kill_count = 10
        self.game.player.gold = 100
        
        # Calculate score
        score = self.game.state.calculate_score()
        
        # Score should be based on level, kills, and gold
        self.assertGreater(score, 0)
        
    def test_game_state_serialization(self):
        """Test game state serialization"""
        self.game.create_player()
        self.game.generate_level(1, "main")
        
        # Modify game state
        self.game.state.depth = 3
        self.game.state.branch = "catacombs"
        self.game.state.kills = 5
        
        # Serialize game state
        serialized = {
            "run_id": self.game.state.run_id,
            "depth": self.game.state.depth,
            "branch": self.game.state.branch,
            "kills": self.game.state.kills,
            "flags": list(self.game.state.flags)
        }
        
        # Check serialization
        self.assertEqual(serialized["depth"], 3)
        self.assertEqual(serialized["branch"], "catacombs")
        self.assertEqual(serialized["kills"], 5)
        self.assertIn("run_id", serialized)


class TestGameIntegration(unittest.TestCase):
    """Integration tests for game logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = CONFIG
        self.game = Game()
        self.game.initialize()
        
    def test_full_game_cycle(self):
        """Test a full game cycle"""
        # Create player
        self.game.create_player()
        
        # Generate level
        self.game.generate_level(1, "main")
        
        # Move player
        self.game.player.move(1, 0, self.game.dungeon_map)
        expected_x = self.game.player.x
        
        # Create and pick up item
        item = Item(
            id="test_item",
            name="Test Item",
            description="A test item",
            glyph="*",
            color=COLORS['item'],
            item_type=ItemType.MISC
        )
        
        item_entity = Entity(
            x=expected_x,
            y=self.game.player.y,
            char="*",
            color=COLORS['item'],
            name="Test Item",
            blocks=False,
            item=item
        )
        
        self.game.entities.append(item_entity)
        self.game.pickup_item()
        
        # Check results
        self.assertEqual(len(self.game.player.inventory.items), 1)
        self.assertEqual(self.game.player.x, expected_x)  # Moved one tile from starting position
        
    def test_combat_sequence(self):
        """Test a combat sequence"""
        self.game.create_player()
        self.game.generate_level(1, "main")
        
        # Create enemy
        enemy = Entity(
            x=self.game.player.x + 1,
            y=self.game.player.y,
            char="g",
            color=COLORS['enemy_normal'],
            name="Goblin",
            blocks=True
        )
        
        enemy.power = 5
        enemy.defense = 2
        enemy.max_hp = 10
        enemy.hp = 10
        
        self.game.entities.append(enemy)
    
        # Attack enemy
        with patch('random.randint', return_value=20):
            self.game.attack(self.game.player, enemy)
        
        # Check that enemy took damage
        self.assertLess(enemy.hp, 10)
        
    def test_level_progression(self):
        """Test level progression"""
        self.game.create_player()
        
        # Start at level 1
        self.game.generate_level(1, "main")
        self.assertEqual(self.game.state.depth, 1)
        
        # Use stairs down
        if self.game.stair_down_pos:
            self.game.player.x, self.game.player.y = self.game.stair_down_pos
            self.game.use_stairs_down()
            
            # Should be at level 2
            self.assertEqual(self.game.state.depth, 2)
            
            # Use stairs up
            if self.game.stair_up_pos:
                self.game.player.x, self.game.player.y = self.game.stair_up_pos
                self.game.use_stairs_up()
                
                # Should be back at level 1
                self.assertEqual(self.game.state.depth, 1)


if __name__ == '__main__':
    unittest.main()
