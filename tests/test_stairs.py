"""Tests for floor 1 stairs functionality."""

import pytest
import numpy as np
import tcod
from unittest.mock import MagicMock, patch

from darkdelve import Game, Entity, Item, Inventory, GameState, CONFIG, COLORS, ItemType, EquipmentSlot, EnergySystem, FOVSystem
from src.application.services.floor1_generator import Floor1Generator

# Disable DM LLM for all stairs tests to avoid blocking on Ollama subprocess
import darkdelve
darkdelve.CONFIG['dungeon_master']['enabled'] = False


class TestStairs:
    """Test cases for stairs functionality."""

    def test_stair_down_pos_set_after_generate_floor1(self):
        """Test that stair_down_pos is set after _generate_floor1()."""
        game = Game()
        game.initialize()
        
        # Generate floor 1
        game.generate_level(1, "main")
        
        # Verify stair_down_pos is not None
        assert game.stair_down_pos is not None, "stair_down_pos should be set after floor 1 generation"
        
        # Verify it's a tuple of two integers
        assert isinstance(game.stair_down_pos, tuple), "stair_down_pos should be a tuple"
        assert len(game.stair_down_pos) == 2, "stair_down_pos should have 2 elements"
        assert all(isinstance(coord, int) for coord in game.stair_down_pos), "stair_down_pos coordinates should be integers"

    def test_stair_down_pos_is_floor_tile(self):
        """Test that stair_down_pos is on a floor tile (dungeon_map[x, y] == False)."""
        game = Game()
        game.initialize()
        
        # Generate floor 1
        game.generate_level(1, "main")
        
        # Verify stair_down_pos is not None
        assert game.stair_down_pos is not None, "stair_down_pos should be set"
        
        # Verify it's on a floor tile (False = floor, True = wall)
        x, y = game.stair_down_pos
        assert game.dungeon_map[x, y] == False, f"stair_down_pos {game.stair_down_pos} should be on a floor tile, but is on wall"

    def test_stair_down_pos_reachable_from_entrance(self):
        """Test that stair_down_pos is reachable from entrance via BFS on floor tiles."""
        game = Game()
        game.initialize()
        
        # Generate floor 1
        game.generate_level(1, "main")
        
        # Verify stair_down_pos is not None
        assert game.stair_down_pos is not None, "stair_down_pos should be set"
        
        # Find entrance (player start position)
        entrance = (game.player.x, game.player.y)
        
        # Import pathfinding function
        from darkdelve import find_path
        
        # Find path from entrance to stairs
        path = find_path(entrance, game.stair_down_pos, game.dungeon_map, [])
        
        # Verify path exists and has more than 1 step (entrance != stairs)
        assert len(path) > 1, f"No path found from entrance {entrance} to stairs {game.stair_down_pos}"

    def test_use_stairs_down_on_stairs_increments_depth(self):
        """Test that calling use_stairs_down() while on stair_down_pos increments depth."""
        game = Game()
        game.initialize()
        
        # Generate floor 1
        game.generate_level(1, "main")
        
        # Verify stair_down_pos is not None
        assert game.stair_down_pos is not None, "stair_down_pos should be set"
        
        # Move player to stairs
        game.player.x, game.player.y = game.stair_down_pos
        
        # Record initial depth
        initial_depth = game.state.depth
        
        # Use stairs down
        game.use_stairs_down()
        
        # Verify depth increased by 1
        assert game.state.depth == initial_depth + 1, f"Depth should increase by 1 when using stairs down, from {initial_depth} to {initial_depth + 1}"
        
        # Verify message was added
        assert any("descend deeper" in msg for msg in game.message_log), "Should have a descent message"

    def test_use_stairs_down_off_stairs_does_not_change_depth(self):
        """Test that calling use_stairs_down() while NOT on stairs does NOT change depth and adds a message."""
        game = Game()
        game.initialize()
        
        # Generate floor 1
        game.generate_level(1, "main")
        
        # Verify stair_down_pos is not None
        assert game.stair_down_pos is not None, "stair_down_pos should be set"
        
        # Ensure player is NOT on stairs (player starts at entrance)
        assert (game.player.x, game.player.y) != game.stair_down_pos, "Player should not start on stairs"
        
        # Record initial depth
        initial_depth = game.state.depth
        
        # Use stairs down
        game.use_stairs_down()
        
        # Verify depth did NOT change
        assert game.state.depth == initial_depth, f"Depth should not change when not on stairs, remains {initial_depth}"
        
        # Verify message was added (should be "There are no stairs here.")
        assert any("no stairs here" in msg for msg in game.message_log), "Should have a 'no stairs here' message when not on stairs"

    def test_use_stairs_up_on_stairs_increments_depth(self):
        """Test that calling use_stairs_up() while on stair_up_pos decrements depth."""
        game = Game()
        game.initialize()
        
        # Verify stair_up_pos is not None (should be set for floor 1)
        assert game.stair_up_pos is not None, "stair_up_pos should be set"
        
        # Move player to stairs up
        game.player.x, game.player.y = game.stair_up_pos
        
        # Record initial depth
        initial_depth = game.state.depth
        
        # Use stairs up
        game.use_stairs_up()
        
        # Verify depth decreased by 1 (unless at depth 1, which would be victory)
        if game.state.depth > 1:
            assert game.state.depth == initial_depth - 1, f"Depth should decrease by 1 when using stairs up, from {initial_depth} to {initial_depth - 1}"
        else:
            # At depth 1, should be victory
            assert game.state.depth == 1, "Should be at depth 1"
            assert any("escape the dungeon" in msg for msg in game.message_log), "Should have victory message"
        
        # Verify message was added
        assert any("climb back up" in msg for msg in game.message_log) or any("escape the dungeon" in msg for msg in game.message_log), "Should have a climb back up or victory message"

    def test_use_stairs_up_off_stairs_does_not_change_depth(self):
        """Test that calling use_stairs_up() while NOT on stairs does NOT change depth and adds a message."""
        game = Game()
        game.initialize()
        
        # Verify stair_up_pos is not None
        assert game.stair_up_pos is not None, "stair_up_pos should be set"
        
        # For floor 1, stair_up_pos is set to entrance (player start position)
        # So we need to move player away from stairs up to test the "not on stairs" case
        if (game.player.x, game.player.y) == game.stair_up_pos:
            # Move player one step away from stairs up
            game.player.x = (game.player.x + 1) % game.dungeon_map.shape[0]
        
        # Ensure player is NOT on stairs up
        assert (game.player.x, game.player.y) != game.stair_up_pos, "Player should not start on stairs up"
        
        # Record initial depth
        initial_depth = game.state.depth
        
        # Use stairs up
        game.use_stairs_up()
        
        # Verify depth did NOT change
        assert game.state.depth == initial_depth, f"Depth should not change when not on stairs up, remains {initial_depth}"
        
        # Verify message was added (should be "There are no stairs here.")
        assert any("no stairs here" in msg for msg in game.message_log), "Should have a 'no stairs here' message when not on stairs up"


class TestStairsRenderOrder:
    """Regression tests: stairs must render ON TOP of entities so they are never hidden."""

    def _make_console_renderer(self, console):
        """Wrap a tcod console in a minimal renderer interface."""
        class ConsoleLikeRenderer:
            def __init__(self, console):
                self.console = console
            def print(self, x, y, text, color=None):
                self.console.print(x, y, text, fg=color)
            def clear(self):
                self.console.clear()
        return ConsoleLikeRenderer(console)

    def _render_full(self, game):
        """Run the full render pipeline with proper stair position passing."""
        game.renderer.clear()
        game.ui.render_dungeon(game.dungeon_map, game.fov, game.explored, game.player)
        game.ui.render_entities(game.entities, game.fov, game.player)
        game.ui.render_stairs(game.dungeon_map, game.fov, game.explored, game.player,
                              stair_down_pos=game.stair_down_pos,
                              stair_up_pos=game.stair_up_pos)

    def test_stair_glyph_not_overwritten_by_entity(self):
        """When an entity stands on a stair tile, the stair glyph must be on top after full render."""
        console = tcod.console.Console(80, 50)
        renderer = self._make_console_renderer(console)

        game = Game()
        game.initialize()
        game.generate_level(1, "main")
        game.renderer = renderer
        game.ui = darkdelve.UI(renderer, game.config)

        # Place player directly on the down-stairs tile
        game.player.x, game.player.y = game.stair_down_pos

        # Run the full render pipeline (dungeon -> entities -> stairs)
        self._render_full(game)

        # Check the console at the stair position - the stair glyph '>' must be on top
        sx, sy = game.stair_down_pos
        cam_x = sx - game.ui.camera_x
        cam_y = sy - game.ui.camera_y
        actual_char = console.ch[cam_y, cam_x]
        assert actual_char == ord('>'), (
            f"Stair down glyph '>' should be on top at ({sx},{sy}), "
            f"but got '{chr(int(actual_char))}' (entity overwrote stairs)"
        )

    def test_stair_up_glyph_not_overwritten_by_entity(self):
        """When an entity stands on a stair-up tile, the '<' glyph must be on top after full render."""
        console = tcod.console.Console(80, 50)
        renderer = self._make_console_renderer(console)

        game = Game()
        game.initialize()
        game.generate_level(1, "main")
        game.renderer = renderer
        game.ui = darkdelve.UI(renderer, game.config)

        # Place player on the up-stairs tile
        game.player.x, game.player.y = game.stair_up_pos

        # Run the full render pipeline
        self._render_full(game)

        sx, sy = game.stair_up_pos
        cam_x = sx - game.ui.camera_x
        cam_y = sy - game.ui.camera_y
        actual_char = console.ch[cam_y, cam_x]
        assert actual_char == ord('<'), (
            f"Stair up glyph '<' should be on top at ({sx},{sy}), "
            f"but got '{chr(int(actual_char))}' (entity overwrote stairs)"
        )

    def test_monster_on_stairs_still_shows_stair_glyph(self):
        """A monster standing on stairs must not hide the stair glyph."""
        console = tcod.console.Console(80, 50)
        renderer = self._make_console_renderer(console)

        game = Game()
        game.initialize()
        game.generate_level(1, "main")
        game.renderer = renderer
        game.ui = darkdelve.UI(renderer, game.config)

        # Spawn a monster on the down-stairs tile
        monster = Entity(
            x=game.stair_down_pos[0], y=game.stair_down_pos[1],
            char='g', color=(0, 255, 0),
            name='goblin', blocks=True,
            hp=5, max_hp=5, power=2, defense=0,
            speed=50, intel_tier=1, is_commander=False,
        )
        game.entities.append(monster)

        # Run the full render pipeline
        self._render_full(game)

        sx, sy = game.stair_down_pos
        cam_x = sx - game.ui.camera_x
        cam_y = sy - game.ui.camera_y
        actual_char = console.ch[cam_y, cam_x]
        assert actual_char == ord('>'), (
            f"Stair down glyph '>' should be on top even with monster at ({sx},{sy}), "
            f"but got '{chr(int(actual_char))}'"
        )