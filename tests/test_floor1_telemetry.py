"""Integration tests for floor 1 telemetry state."""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch


class TestFloor1Telemetry:
    """Verify floor 1 game state meets expectations."""

    @pytest.fixture
    def game(self):
        """Create a game instance and generate floor 1."""
        from darkdelve import Game
        g = Game()
        g.initialize()
        return g

    def test_entity_count_in_range(self, game):
        """Floor 1 should have between 15 and 35 entities (player + monsters + items + corpses)."""
        assert 15 <= len(game.entities) <= 35, f"Expected 15-35 entities, got {len(game.entities)}"

    def test_at_least_two_guard_sergeants(self, game):
        """Floor 1 should have at least 2 guard sergeants."""
        sergeants = [e for e in game.entities if e.name == 'Guard Sergeant']
        assert len(sergeants) >= 2, f"Expected >=2 sergeants, got {len(sergeants)}"

    def test_at_least_one_den_leader(self, game):
        """Floor 1 should have at least 1 den leader (Spider Queen or Rat King)."""
        leaders = [e for e in game.entities if e.name in ('Spider Queen', 'Rat King')]
        assert len(leaders) >= 1, f"Expected >=1 den leader, got {len(leaders)}"

    def test_no_blocking_entity_overlaps(self, game):
        """No two blocking entities should share the same position."""
        blocking = [e for e in game.entities if e.blocks]
        positions = [(e.x, e.y) for e in blocking]
        assert len(positions) == len(set(positions)), "Overlapping blocking entities detected"

    def test_all_entities_on_floor_tiles(self, game):
        """All entities should be on floor tiles (not walls)."""
        for e in game.entities:
            if 0 <= e.x < game.dungeon_map.shape[0] and 0 <= e.y < game.dungeon_map.shape[1]:
                assert not game.dungeon_map[e.x, e.y], f"Entity {e.name} at ({e.x},{e.y}) is on a wall"

    def test_stairs_down_exists(self, game):
        """Stairs down should exist and be on a floor tile."""
        assert game.stair_down_pos is not None, "No stairs down found"
        sx, sy = game.stair_down_pos
        assert not game.dungeon_map[sx, sy], f"Stairs down at ({sx},{sy}) is on a wall"