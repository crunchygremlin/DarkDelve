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
        game.generate_level(1, "main")
        assert game.stair_down_pos is not None, "stair_down_pos should be set after floor 1 generation"
        assert isinstance(game.stair_down_pos, tuple), "stair_down_pos should be a tuple"
        assert len(game.stair_down_pos) == 2, "stair_down_pos should have 2 elements"
        assert all(isinstance(coord, int) for coord in game.stair_down_pos), "stair_down_pos coordinates should be integers"

    def test_stair_down_pos_is_floor_tile(self):
        """Test that stair_down_pos is on a floor tile (dungeon_map[x, y] == False)."""
        game = Game()
        game.initialize()
        game.generate_level(1, "main")
        assert game.stair_down_pos is not None, "stair_down_pos should be set"
        x, y = game.stair_down_pos
        assert game.dungeon_map[x, y] == False, f"stair_down_pos {game.stair_down_pos} should be on a floor tile, but is on wall"

    def test_stair_down_pos_reachable_from_entrance(self):
        """Test that stair_down_pos is reachable from entrance via BFS on floor tiles."""
        game = Game()
        game.initialize()
        game.generate_level(1, "main")
        assert game.stair_down_pos is not None, "stair_down_pos should be set"
        entrance = (game.player.x, game.player.y)
        from darkdelve import find_path
        path = find_path(entrance, game.stair_down_pos, game.dungeon_map, [])
        assert len(path) > 1, f"No path found from entrance {entrance} to stairs {game.stair_down_pos}"

    def test_use_stairs_down_on_stairs_increments_depth(self):
        """Test that calling use_stairs_down() while on stair_down_pos increments depth."""
        game = Game()
        game.initialize()
        game.generate_level(1, "main")
        assert game.stair_down_pos is not None, "stair_down_pos should be set"
        game.player.x, game.player.y = game.stair_down_pos
        initial_depth = game.state.depth
        game.use_stairs_down()
        assert game.state.depth == initial_depth + 1, f"Depth should increase by 1 when using stairs down, from {initial_depth} to {initial_depth + 1}"
        assert any("descend deeper" in msg for msg in game.message_log), "Should have a descent message"

    def test_use_stairs_down_off_stairs_does_not_change_depth(self):
        """Test that calling use_stairs_down() while NOT on stairs does NOT change depth."""
        game = Game()
        game.initialize()
        game.generate_level(1, "main")
        assert game.stair_down_pos is not None, "stair_down_pos should be set"
        assert (game.player.x, game.player.y) != game.stair_down_pos, "Player should not start on stairs"
        initial_depth = game.state.depth
        game.use_stairs_down()
        assert game.state.depth == initial_depth, f"Depth should not change when not on stairs, remains {initial_depth}"

    def test_use_stairs_up_on_stairs_increments_depth(self):
        """Test that calling use_stairs_up() while on stair_up_pos decrements depth."""
        game = Game()
        game.initialize()
        assert game.stair_up_pos is not None, "stair_up_pos should be set"
        game.player.x, game.player.y = game.stair_up_pos
        initial_depth = game.state.depth
        game.use_stairs_up()
        if game.state.depth > 1:
            assert game.state.depth == initial_depth - 1, f"Depth should decrease by 1 when using stairs up, from {initial_depth} to {initial_depth - 1}"
        else:
            assert game.state.depth == 1, "Should be at depth 1"
            assert any("escape the dungeon" in msg for msg in game.message_log), "Should have victory message"
        assert any("climb back up" in msg for msg in game.message_log) or any("escape the dungeon" in msg for msg in game.message_log), "Should have a climb back up or victory message"

    def test_use_stairs_up_off_stairs_does_not_change_depth(self):
        """Test that calling use_stairs_up() while NOT on stairs does NOT change depth."""
        game = Game()
        game.initialize()
        assert game.stair_up_pos is not None, "stair_up_pos should be set"
        if (game.player.x, game.player.y) == game.stair_up_pos:
            game.player.x = (game.player.x + 1) % game.dungeon_map.shape[0]
        assert (game.player.x, game.player.y) != game.stair_up_pos, "Player should not start on stairs up"
        initial_depth = game.state.depth
        game.use_stairs_up()
        assert game.state.depth == initial_depth, f"Depth should not change when not on stairs up, remains {initial_depth}"


class TestStairsRenderOrder:
    """Regression tests: stairs render order and FOV gating.

    Render order: dungeon -> stairs -> entities (entities always on top).
    Stairs only render when in FOV or explored.
    """

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
        """Run the full render pipeline: dungeon -> stairs -> entities."""
        game.renderer.clear()
        game.ui.render_dungeon(game.dungeon_map, game.fov, game.explored, game.player)
        game.ui.render_stairs(game.dungeon_map, game.fov, game.explored, game.player,
                              stair_down_pos=game.stair_down_pos,
                              stair_up_pos=game.stair_up_pos)
        game.ui.render_entities(game.entities, game.fov, game.player)

    def test_stair_glyph_not_overwritten_by_entity(self):
        """Player on stairs: player glyph '@' must be on top (entities render after stairs)."""
        console = tcod.console.Console(80, 50)
        renderer = self._make_console_renderer(console)

        game = Game()
        game.initialize()
        game.generate_level(1, "main")
        game.renderer = renderer
        game.ui = darkdelve.UI(renderer, game.config)

        game.player.x, game.player.y = game.stair_down_pos
        game.fov = game.fov_system.compute(game.dungeon_map, game.player.x, game.player.y)
        game.explored = game.fov_system.explored.copy()

        self._render_full(game)

        sx, sy = game.stair_down_pos
        cam_x = sx - game.ui.camera_x
        cam_y = sy - game.ui.camera_y
        actual_char = console.ch[cam_y, cam_x]
        assert actual_char == ord('@'), (
            f"Player glyph '@' should be on top of stairs at ({sx},{sy}), "
            f"but got '{chr(int(actual_char))}'"
        )

    def test_stair_up_glyph_not_overwritten_by_entity(self):
        """Player on up-stairs: player glyph '@' must be on top."""
        console = tcod.console.Console(80, 50)
        renderer = self._make_console_renderer(console)

        game = Game()
        game.initialize()
        game.generate_level(1, "main")
        game.renderer = renderer
        game.ui = darkdelve.UI(renderer, game.config)

        game.player.x, game.player.y = game.stair_up_pos
        game.fov = game.fov_system.compute(game.dungeon_map, game.player.x, game.player.y)
        game.explored = game.fov_system.explored.copy()

        self._render_full(game)

        sx, sy = game.stair_up_pos
        cam_x = sx - game.ui.camera_x
        cam_y = sy - game.ui.camera_y
        actual_char = console.ch[cam_y, cam_x]
        assert actual_char == ord('@'), (
            f"Player glyph '@' should be on top of stairs at ({sx},{sy}), "
            f"but got '{chr(int(actual_char))}'"
        )

    def test_monster_on_stairs_still_shows_monster_glyph(self):
        """A monster standing on stairs must be visible on top of the stair glyph."""
        console = tcod.console.Console(80, 50)
        renderer = self._make_console_renderer(console)

        game = Game()
        game.initialize()
        game.generate_level(1, "main")
        game.renderer = renderer
        game.ui = darkdelve.UI(renderer, game.config)

        sx, sy = game.stair_down_pos
        game.player.x = sx
        game.player.y = max(0, sy - 2)
        game.fov = game.fov_system.compute(game.dungeon_map, game.player.x, game.player.y)
        game.explored = game.fov_system.explored.copy()

        monster = Entity(
            x=sx, y=sy,
            char='g', color=(0, 255, 0),
            name='goblin', blocks=True,
            hp=5, max_hp=5, power=2, defense=0,
            speed=50, intel_tier=1, is_commander=False,
        )
        game.entities.append(monster)

        self._render_full(game)

        cam_x = sx - game.ui.camera_x
        cam_y = sy - game.ui.camera_y
        actual_char = console.ch[cam_y, cam_x]
        assert actual_char == ord('g'), (
            f"Monster glyph 'g' should be on top of stairs at ({sx},{sy}), "
            f"but got '{chr(int(actual_char))}'"
        )

    def test_stairs_visible_only_in_fov_or_explored(self):
        """Stairs should only be visible when in FOV or explored memory.
        When the player is on the stairs, the stairs are in FOV, so the stair
        glyph should be rendered (but the player '@' will be on top).
        """
        console = tcod.console.Console(80, 50)
        renderer = self._make_console_renderer(console)

        game = Game()
        game.initialize()
        game.generate_level(1, "main")
        game.renderer = renderer
        game.ui = darkdelve.UI(renderer, game.config)

        game.player.x, game.player.y = game.stair_down_pos
        game.fov = game.fov_system.compute(game.dungeon_map, game.player.x, game.player.y)
        game.explored = game.fov_system.explored.copy()

        self._render_full(game)

        sx, sy = game.stair_down_pos
        cam_x = sx - game.ui.camera_x
        cam_y = sy - game.ui.camera_y
        actual_char = console.ch[cam_y, cam_x]
        assert actual_char == ord('@'), (
            f"Player '@' should be on top of stairs at ({sx},{sy}), "
            f"but got '{chr(int(actual_char))}'"
        )

    def test_stairs_not_visible_when_outside_fov_and_not_explored(self):
        """Stairs should NOT be visible when outside FOV and NOT explored."""
        console = tcod.console.Console(80, 50)
        renderer = self._make_console_renderer(console)

        game = Game()
        game.initialize()
        game.generate_level(1, "main")
        game.renderer = renderer
        game.ui = darkdelve.UI(renderer, game.config)

        sx, sy = game.stair_down_pos
        map_width, map_height = game.dungeon_map.shape
        player_x = (sx + map_width // 2) % map_width
        player_y = (sy + map_height // 2) % map_height
        game.player.x, game.player.y = player_x, player_y
        game.fov = game.fov_system.compute(game.dungeon_map, game.player.x, game.player.y)
        game.explored = game.fov_system.explored.copy()

        console.clear()
        self._render_full(game)

        cam_x = sx - game.ui.camera_x
        cam_y = sy - game.ui.camera_y
        if 0 <= cam_x < 80 and 0 <= cam_y < 50:
            actual_char = console.ch[cam_y, cam_x]
            assert actual_char != ord('>'), (
                f"Stair down glyph '>' should NOT be visible when outside FOV and not explored, "
                f"but got '{chr(int(actual_char))}'"
            )
