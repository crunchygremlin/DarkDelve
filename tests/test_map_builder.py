"""Tests for MapBuilder class."""

import pytest
import numpy as np
from src.domain.services.map_builder import MapBuilder, Room, Corridor, Stair, EntityPlacement


class TestMapBuilder:
    """Test suite for MapBuilder."""

    def test_create_room_carves_floor(self):
        """Test that create_room sets tiles to False (floor)."""
        builder = MapBuilder(width=30, height=30)
        room = builder.create_room(5, 5, 10, 8)

        # Check room tiles are floor
        for x in range(5, 15):
            for y in range(5, 13):
                assert not builder.dungeon_map[x, y], f"Tile ({x}, {y}) should be floor"

    def test_create_room_clamps_to_bounds(self):
        """Test that room creation clamps to map bounds."""
        builder = MapBuilder(width=20, height=20)
        room = builder.create_room(15, 15, 10, 10)

        # Room should be clamped
        assert room.x + room.width <= 20
        assert room.y + room.height <= 20

    def test_create_corridor_connects_points(self):
        """Test that corridor creates a path between two points."""
        builder = MapBuilder(width=30, height=30)
        corridor = builder.create_corridor((5, 5), (15, 5))

        # Start and end should be floor
        assert not builder.dungeon_map[5, 5]
        assert not builder.dungeon_map[15, 5]

        # Corridor tiles should be floor
        for tile in corridor.tiles:
            assert not builder.dungeon_map[tile[0], tile[1]]

    def test_create_stair_down(self):
        """Test stair down placement."""
        builder = MapBuilder(width=30, height=30)
        builder.create_room(5, 5, 10, 8)
        stair = builder.create_stair_up(7, 7)

        assert stair.direction == "up"
        assert not builder.dungeon_map[7, 7]

    def test_validate_map_empty_fails(self):
        """Test that empty map fails validation."""
        builder = MapBuilder(width=30, height=30)
        result = builder.validate_map()

        assert not result["valid"]
        assert "no rooms" in result["errors"][0].lower()

    def test_validate_map_connected_passes(self):
        """Test that a connected map passes validation."""
        builder = MapBuilder(width=40, height=40)
        builder.create_room(5, 5, 10, 8)
        builder.create_corridor((10, 9), (20, 9))
        builder.create_room(20, 5, 10, 8)
        builder.create_stair_up(7, 7)
        builder.create_stair_down(25, 9)

        result = builder.validate_map()

        assert result["valid"], f"Expected valid but got errors: {result['errors']}"
        assert result["room_count"] == 2
        assert result["stair_count"] == 2

    def test_validate_map_disconnected_fails(self):
        """Test that disconnected rooms fail validation."""
        builder = MapBuilder(width=50, height=50)
        builder.create_room(5, 5, 8, 6)
        builder.create_room(35, 35, 8, 6)  # No corridor connecting
        builder.create_stair_up(7, 7)
        builder.create_stair_down(37, 37)

        result = builder.validate_map()

        assert not result["valid"]
        assert any("unreachable" in e.lower() for e in result["errors"])

    def test_place_entity_on_floor(self):
        """Test entity placement on floor tile."""
        builder = MapBuilder(width=30, height=30)
        builder.create_room(5, 5, 10, 8)
        placement = builder.place_entity(7, 7, "goblin")

        assert placement.x == 7
        assert placement.y == 7
        assert placement.entity_type == "goblin"

    def test_get_map_data_serialization(self):
        """Test map data serialization."""
        builder = MapBuilder(width=30, height=30)
        builder.create_room(5, 5, 10, 8)
        builder.create_stair_down(7, 7)

        data = builder.get_map_data()

        assert data["width"] == 30
        assert data["height"] == 30
        assert len(data["rooms"]) == 1
        assert len(data["stairs"]) == 1

    def test_from_map_data_deserialization(self):
        """Test map data deserialization."""
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

    def test_generate_procedural(self):
        """Test procedural generation."""
        builder = MapBuilder(width=50, height=40)
        builder.generate_procedural(room_count=5, seed=42)

        result = builder.validate_map()
        assert result["valid"], f"Procedural map should be valid: {result['errors']}"
        assert result["room_count"] >= 3  # At least some rooms placed

    def test_apply_to_game(self):
        """Test applying map to a mock game object."""
        class MockGame:
            def __init__(self):
                self.dungeon_map = None
                self.stair_down_pos = None
                self.stair_up_pos = None
                self.entities = []

        builder = MapBuilder(width=30, height=30)
        builder.create_room(5, 5, 10, 8)
        builder.create_stair_up(7, 7)
        builder.create_stair_down(10, 9)

        game = MockGame()
        success = builder.apply_to_game(game)

        assert success
        assert game.dungeon_map is not None
        assert game.stair_down_pos == (10, 9)
        assert game.stair_up_pos == (7, 7)


class TestMapBuilderConnectivity:
    """Test connectivity checking."""

    def test_flood_fill_finds_all_connected(self):
        """Test that flood fill finds all connected floor tiles."""
        builder = MapBuilder(width=20, height=20)
        builder.create_room(5, 5, 10, 10)

        connected = builder._check_connectivity((7, 7))

        # All room tiles should be connected
        for x in range(5, 15):
            for y in range(5, 15):
                assert (x, y) in connected

    def test_flood_fill_stops_at_walls(self):
        """Test that flood fill doesn't cross walls."""
        builder = MapBuilder(width=30, height=30)
        builder.create_room(5, 5, 5, 5)
        # Leave gap, then another room
        builder.create_room(15, 15, 5, 5)

        connected = builder._check_connectivity((7, 7))

        # Second room should NOT be connected
        assert (17, 17) not in connected
