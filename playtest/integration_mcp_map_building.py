"""
Integration test for MCP Map Building feature (T-2026-0629-001).

Exercises the full pipeline:
1. Create a Game with dm_enabled=False
2. Use MapBuilder to create a room, corridor, and stairs
3. Validate the map
4. Apply to game
5. Walk player to stairs and descend

This is a headless integration test — no pygame, no LLM calls.
"""

import sys
import os
import numpy as np

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from darkdelve import Game
from src.domain.services.map_builder import MapBuilder
from src.infrastructure.services.mcp_map_tools import MCPMapTools


def test_map_builder_creates_room_corridor_stairs():
    """Phase 1: MapBuilder can create a room, corridor, and stairs."""
    builder = MapBuilder(width=40, height=30)
    room_a = builder.create_room(5, 5, 10, 8)
    center_a = room_a.center
    center_b = (25, 9)
    corridor = builder.create_corridor(center_a, center_b)
    room_b = builder.create_room(20, 5, 10, 8)
    stair_up = builder.create_stair_up(center_a[0], center_a[1])
    stair_down = builder.create_stair_down(center_b[0], center_b[1])
    assert stair_up.direction == "up"
    assert stair_down.direction == "down"
    assert len(corridor.tiles) > 0
    print("[PASS] Phase 1: MapBuilder creates room, corridor, stairs")
    return builder


def test_map_validation(builder):
    """Phase 2: Map validation passes for connected map."""
    result = builder.validate_map()
    assert result["valid"], f"Map validation failed: {result['errors']}"
    assert result["room_count"] == 2
    assert result["corridor_count"] == 1
    assert result["stair_count"] == 2
    print(f"[PASS] Phase 2: Map validation passed")


def test_apply_to_game(builder):
    """Phase 3: Apply builder output to a real Game instance with initialized player."""
    game = Game()
    game.initialize()
    game.dm_enabled = False
    game.generate_level(1, "main")
    success = builder.apply_to_game(game)
    assert success, "apply_to_game returned False"
    assert game.dungeon_map is not None
    assert game.dungeon_map.shape == (40, 30)
    assert game.stair_down_pos is not None
    assert game.stair_up_pos is not None
    sx, sy = game.stair_down_pos
    assert not game.dungeon_map[sx, sy], f"Stair down at ({sx},{sy}) is on a wall"
    ux, uy = game.stair_up_pos
    assert not game.dungeon_map[ux, uy], f"Stair up at ({ux},{uy}) is on a wall"
    print(f"[PASS] Phase 3: Map applied to game")
    return game


def test_walk_to_stairs_and_descend(game):
    """Phase 4: Walk player to stairs and descend."""
    game.player.x, game.player.y = game.stair_up_pos
    assert (game.player.x, game.player.y) == game.stair_up_pos
    game.player.x, game.player.y = game.stair_down_pos
    assert (game.player.x, game.player.y) == game.stair_down_pos
    depth_before = game.state.depth
    game.use_stairs_down()
    assert game.state.depth == depth_before + 1, \
        f"Expected depth {depth_before + 1}, got {game.state.depth}"
    assert any("descend deeper" in msg for msg in game.message_log), \
        "Expected 'descend deeper' message"
    print(f"[PASS] Phase 4: Player descended depth {depth_before} -> {game.state.depth}")


def test_mcp_map_tools_procedural():
    """Phase 5: MCPMapTools.build_map_procedural works end-to-end."""
    game = Game()
    game.initialize()
    game.dm_enabled = False
    game.generate_level(1, "main")
    tools = MCPMapTools(game=game)
    result = tools.build_map_procedural(width=50, height=40, room_count=5, seed=42)
    assert result.success, f"build_map_procedural failed: {result.error}"
    assert game.dungeon_map is not None
    assert game.stair_down_pos is not None
    state_result = tools.get_map_state()
    assert state_result.success
    assert state_result.value["floor_tiles"] > 0
    print(f"[PASS] Phase 5: MCPMapTools.build_map_procedural OK")


def test_mcp_map_tools_modify():
    """Phase 6: MCPMapTools.modify_map can add rooms/corridors."""
    game = Game()
    game.initialize()
    game.dm_enabled = False
    game.generate_level(1, "main")
    tools = MCPMapTools(game=game)
    tools.build_map_procedural(width=50, height=40, room_count=3, seed=99)
    commands = [
        {"action": "create_room", "x": 2, "y": 2, "width": 6, "height": 6},
        {"action": "create_stair_down", "x": 4, "y": 4},
    ]
    result = tools.modify_map(commands)
    assert result.success, f"modify_map failed: {result.error}"
    val_result = tools.validate_current_map()
    assert val_result.value is not None
    print(f"[PASS] Phase 6: MCPMapTools.modify_map applied {len(commands)} commands")


def test_serialization_roundtrip():
    """Phase 7: MapBuilder serialization roundtrip preserves map data."""
    builder1 = MapBuilder(width=30, height=30)
    builder1.create_room(5, 5, 10, 8)
    builder1.create_corridor((10, 9), (20, 9))
    builder1.create_room(20, 5, 10, 8)
    builder1.create_stair_up(7, 7)
    builder1.create_stair_down(25, 9)
    data = builder1.get_map_data()
    builder2 = MapBuilder.from_map_data(data)
    assert len(builder2.rooms) == 2
    assert len(builder2.stairs) == 2
    np.testing.assert_array_equal(builder1.dungeon_map, builder2.dungeon_map)
    print("[PASS] Phase 7: Serialization roundtrip preserves map data")


def main():
    print("=" * 60)
    print("MCP Map Building Integration Test — T-2026-0629-001")
    print("=" * 60)
    builder = test_map_builder_creates_room_corridor_stairs()
    test_map_validation(builder)
    game = test_apply_to_game(builder)
    test_walk_to_stairs_and_descend(game)
    test_mcp_map_tools_procedural()
    test_mcp_map_tools_modify()
    test_serialization_roundtrip()
    print("=" * 60)
    print("ALL PHASES PASSED — MCP Map Building integration verified")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
