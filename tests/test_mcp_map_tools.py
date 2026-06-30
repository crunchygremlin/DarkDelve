"""Tests for MCP Map Tools."""

import pytest
from unittest.mock import MagicMock
from src.infrastructure.services.mcp_map_tools import MCPMapTools
from src.domain.services.map_builder import MapBuilder


class TestMCPMapTools:
    """Test suite for MCPMapTools."""

    def test_build_map_procedural(self):
        """Test procedural map building."""
        mock_game = MagicMock()
        mock_game.config = {'dungeon': {'width': 50, 'height': 40}}
        mock_game.stair_down_pos = None
        mock_game.stair_up_pos = None
        mock_game.entities = []
        mock_game.fov_system = MagicMock()

        tools = MCPMapTools(game=mock_game)
        result = tools.build_map_procedural(width=50, height=40, room_count=5, seed=42)

        assert result.success
        assert mock_game.dungeon_map is not None

    def test_build_map_no_game_fails(self):
        """Test that building without game fails."""
        tools = MCPMapTools(game=None)
        result = tools.build_map_procedural()

        assert not result.success
        assert "not available" in result.error

    def test_modify_map(self):
        """Test map modification."""
        import numpy as np
        mock_game = MagicMock()
        mock_game.config = {'dungeon': {'width': 50, 'height': 40}}
        mock_game.dungeon_map = np.ones((50, 40), dtype=bool)
        mock_game.stair_down_pos = None
        mock_game.stair_up_pos = None
        mock_game.entities = []
        mock_game.fov_system = MagicMock()

        tools = MCPMapTools(game=mock_game)

        commands = [
            {"action": "create_room", "x": 5, "y": 5, "width": 10, "height": 8},
            {"action": "create_stair_down", "x": 7, "y": 7},
        ]

        result = tools.modify_map(commands)
        assert result.success

    def test_validate_current_map(self):
        """Test map validation."""
        import numpy as np
        mock_game = MagicMock()
        mock_game.dungeon_map = np.ones((30, 30), dtype=bool)
        # Carve a small room
        mock_game.dungeon_map[5:10, 5:10] = False

        tools = MCPMapTools(game=mock_game)
        result = tools.validate_current_map()

        assert result.value is not None
        assert "valid" in result.value

    def test_get_map_state(self):
        """Test getting map state."""
        import numpy as np
        mock_game = MagicMock()
        mock_game.dungeon_map = np.ones((30, 30), dtype=bool)
        mock_game.dungeon_map[5:10, 5:10] = False
        mock_game.stair_down_pos = (7, 7)
        mock_game.stair_up_pos = None
        mock_game.entities = []

        tools = MCPMapTools(game=mock_game)
        result = tools.get_map_state()

        assert result.success
        assert result.value["width"] == 30
        assert result.value["floor_tiles"] == 25  # 5x5 room
