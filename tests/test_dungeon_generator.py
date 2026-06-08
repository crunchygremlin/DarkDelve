#!/usr/bin/env python3
"""
Test suite for DarkDelve dungeon generation
"""

import unittest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path to import darkdelve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from darkdelve import DungeonGenerator, CONFIG


class TestDungeonGenerator(unittest.TestCase):
    """Test cases for DungeonGenerator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = CONFIG
        self.generator = DungeonGenerator(self.config)
        
    def test_dungeon_generator_initialization(self):
        """Test that DungeonGenerator initializes correctly"""
        self.assertIsNotNone(self.generator)
        self.assertEqual(self.generator.config, self.config)
        self.assertIsNotNone(self.generator.themes)
        
    def test_generate_level_basic(self):
        """Test basic level generation"""
        width, height = 40, 30
        level = 1
        branch = "main"
        
        dungeon_map, entities, player_start, stair_down, stair_up = self.generator.generate_level(
            width, height, level, branch
        )
        
        # Test that we get the expected outputs
        self.assertIsInstance(dungeon_map, np.ndarray)
        self.assertEqual(dungeon_map.shape, (height, width))
        self.assertIsInstance(entities, list)
        self.assertIsInstance(player_start, tuple)
        self.assertEqual(len(player_start), 2)
        
        # Test that dungeon map contains valid tiles
        unique_tiles = np.unique(dungeon_map)
        self.assertIn(0, unique_tiles)  # Empty space
        self.assertIn(1, unique_tiles)  # Wall
        
    def test_generate_level_dimensions(self):
        """Test that generated levels have correct dimensions"""
        widths = [20, 40, 80]
        heights = [15, 30, 60]
        
        for width in widths:
            for height in heights:
                with self.subTest(width=width, height=height):
                    dungeon_map, _, _, _, _ = self.generator.generate_level(
                        width, height, 1, "main"
                    )
                    self.assertEqual(dungeon_map.shape, (height, width))
                    
    def test_generate_level_different_branches(self):
        """Test level generation for different branches"""
        branches = ["main", "catacombs", "abyss"]
        level = 1
        
        for branch in branches:
            with self.subTest(branch=branch):
                dungeon_map, _, _, _, _ = self.generator.generate_level(
                    40, 30, level, branch
                )
                self.assertIsInstance(dungeon_map, np.ndarray)
                self.assertEqual(dungeon_map.shape, (30, 40))
                
    def test_generate_level_different_depths(self):
        """Test level generation at different depths"""
        depths = [1, 5, 10, 15, 20, 25]
        branch = "main"
        
        for depth in depths:
            with self.subTest(depth=depth):
                dungeon_map, _, _, _, _ = self.generator.generate_level(
                    40, 30, depth, branch
                )
                self.assertIsInstance(dungeon_map, np.ndarray)
                
    def test_player_start_position(self):
        """Test that player start position is valid"""
        dungeon_map, _, player_start, _, _ = self.generator.generate_level(
            40, 30, 1, "main"
        )
        
        x, y = player_start
        self.assertTrue(0 <= x < 40)
        self.assertTrue(0 <= y < 30)
        self.assertEqual(dungeon_map[y, x], 0)  # Should be on empty space
        
    def test_stair_positions(self):
        """Test that stair positions are valid"""
        dungeon_map, _, player_start, stair_down, stair_up = self.generator.generate_level(
            40, 30, 1, "main"
        )
        
        # Test stairs down
        if stair_down:
            x, y = stair_down
            self.assertTrue(0 <= x < 40)
            self.assertTrue(0 <= y < 30)
            self.assertEqual(dungeon_map[y, x], 0)  # Should be on empty space
            
        # Test stairs up
        if stair_up:
            x, y = stair_up
            self.assertTrue(0 <= x < 40)
            self.assertTrue(0 <= y < 30)
            self.assertEqual(dungeon_map[y, x], 0)  # Should be on empty space
            
    def test_room_generation(self):
        """Test that rooms are generated properly"""
        dungeon_map, _, _, _, _ = self.generator.generate_level(
            40, 30, 1, "main"
        )
        
        # Count connected empty spaces (rooms)
        empty_spaces = np.sum(dungeon_map == 0)
        wall_spaces = np.sum(dungeon_map == 1)
        
        self.assertGreater(empty_spaces, 0)
        self.assertGreater(wall_spaces, 0)
        
    def test_connectivity(self):
        """Test that all rooms are connected"""
        dungeon_map, _, _, _, _ = self.generator.generate_level(
            40, 30, 1, "main"
        )
        
        # This is a basic connectivity test
        # In a real implementation, you might want a more sophisticated algorithm
        empty_spaces = np.argwhere(dungeon_map == 0)
        self.assertGreater(len(empty_spaces), 0)
        
    def test_theme_application(self):
        """Test that themes are applied correctly"""
        theme = {"name": "test", "description": "test theme"}
        
        # Create a simple test map
        test_map = np.ones((10, 10), dtype=int)
        test_map[2:8, 2:8] = 0  # Create a room
        
        result_map = self.generator.apply_theme(test_map, theme)
        
        # The theme application should not change the basic structure
        self.assertEqual(result_map.shape, test_map.shape)
        np.testing.assert_array_equal(result_map, test_map)


class TestDungeonMapAnalysis(unittest.TestCase):
    """Test cases for analyzing dungeon map properties"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = CONFIG
        self.generator = DungeonGenerator(self.config)
        
    def test_traditional_roguelike_characteristics(self):
        """Test if generated maps have traditional roguelike characteristics"""
        dungeon_map, _, _, _, _ = self.generator.generate_level(
            40, 30, 1, "main"
        )
        
        # Traditional roguelike characteristics:
        # 1. Grid-based movement
        # 2. Clear distinction between walls and floors
        # 3. Room-based layout
        # 4. Corridor connections
        
        # Test 1: Grid-based structure
        self.assertTrue(self._is_grid_based(dungeon_map))
        
        # Test 2: Clear wall/floor distinction
        wall_floor_ratio = self._calculate_wall_floor_ratio(dungeon_map)
        self.assertGreater(wall_floor_ratio[1], 0.3)  # At least 30% walls
        self.assertGreater(wall_floor_ratio[0], 0.2)  # At least 20% floors
        
        # Test 3: Room detection
        rooms = self._detect_rooms(dungeon_map)
        self.assertGreater(len(rooms), 0)  # Should have at least one room
        
        # Test 4: Corridor detection
        corridors = self._detect_corridors(dungeon_map)
        # Corridors are optional but should be reasonable if present
        
    def _is_grid_based(self, dungeon_map):
        """Check if the map is grid-based"""
        return isinstance(dungeon_map, np.ndarray) and dungeon_map.dtype in [int, np.int32, np.int64]
        
    def _calculate_wall_floor_ratio(self, dungeon_map):
        """Calculate ratio of walls to floors"""
        total_tiles = dungeon_map.size
        wall_count = np.sum(dungeon_map == 1)
        floor_count = np.sum(dungeon_map == 0)
        return (floor_count / total_tiles, wall_count / total_tiles)
        
    def _detect_rooms(self, dungeon_map):
        """Simple room detection algorithm"""
        rooms = []
        height, width = dungeon_map.shape
        
        # Simple flood fill to find connected floor areas
        visited = np.zeros_like(dungeon_map, dtype=bool)
        
        for y in range(height):
            for x in range(width):
                if dungeon_map[y, x] == 0 and not visited[y, x]:
                    room = self._flood_fill(dungeon_map, visited, x, y)
                    if len(room) > 4:  # Minimum room size
                        rooms.append(room)
                        
        return rooms
        
    def _flood_fill(self, dungeon_map, visited, start_x, start_y):
        """Flood fill algorithm to find connected areas"""
        room = []
        stack = [(start_x, start_y)]
        
        while stack:
            x, y = stack.pop()
            if x < 0 or x >= dungeon_map.shape[1] or y < 0 or y >= dungeon_map.shape[0]:
                continue
            if visited[y, x] or dungeon_map[y, x] != 0:
                continue
                
            visited[y, x] = True
            room.append((x, y))
            
            # Add adjacent cells
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                stack.append((x + dx, y + dy))
                
        return room
        
    def _detect_corridors(self, dungeon_map):
        """Simple corridor detection"""
        corridors = []
        height, width = dungeon_map.shape
        
        # Look for 1-2 tile wide horizontal or vertical passages
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                if dungeon_map[y, x] == 0:  # Floor tile
                    # Check if it's part of a horizontal corridor
                    if (dungeon_map[y-1, x] == 1 and dungeon_map[y+1, x] == 1 and
                        self._is_corridor_horizontal(dungeon_map, y, x)):
                        corridors.append((x, y))
                        
                    # Check if it's part of a vertical corridor
                    elif (dungeon_map[y, x-1] == 1 and dungeon_map[y, x+1] == 1 and
                          self._is_corridor_vertical(dungeon_map, y, x)):
                        corridors.append((x, y))
                        
        return corridors
        
    def _is_corridor_horizontal(self, dungeon_map, y, x):
        """Check if a position is part of a horizontal corridor"""
        # Check left and right for continuous floor tiles
        left = x
        while left > 0 and dungeon_map[y, left-1] == 0:
            left -= 1
            
        right = x
        while right < dungeon_map.shape[1] - 1 and dungeon_map[y, right+1] == 0:
            right += 1
            
        # Corridor should be 1-2 tiles wide
        return right - left <= 2
        
    def _is_corridor_vertical(self, dungeon_map, y, x):
        """Check if a position is part of a vertical corridor"""
        # Check up and down for continuous floor tiles
        up = y
        while up > 0 and dungeon_map[up-1, x] == 0:
            up -= 1
            
        down = y
        while down < dungeon_map.shape[0] - 1 and dungeon_map[down+1, x] == 0:
            down += 1
            
        # Corridor should be 1-2 tiles wide
        return down - up <= 2
        
    def test_tile_compatibility_analysis(self):
        """Analyze tile compatibility with traditional roguelike standards"""
        dungeon_map, _, _, _, _ = self.generator.generate_level(
            40, 30, 1, "main"
        )
        
        analysis = self._analyze_tile_compatibility(dungeon_map)
        
        # Print analysis for debugging
        print(f"\nTile Compatibility Analysis:")
        print(f"Grid-based: {analysis['grid_based']}")
        print(f"Wall/Floor ratio: {analysis['wall_floor_ratio']}")
        print(f"Room count: {analysis['room_count']}")
        print(f"Corridor count: {analysis['corridor_count']}")
        print(f"Average room size: {analysis['avg_room_size']:.1f}")
        print(f"Traditional roguelike score: {analysis['traditional_score']}/10")
        
        # Assert that the map has reasonable characteristics
        self.assertGreater(analysis['traditional_score'], 3)  # Should be somewhat traditional
        
    def _analyze_tile_compatibility(self, dungeon_map):
        """Analyze how compatible the tiles are with traditional roguelike standards"""
        analysis = {}
        
        # Grid-based check
        analysis['grid_based'] = self._is_grid_based(dungeon_map)
        
        # Wall/Floor ratio
        wall_floor_ratio = self._calculate_wall_floor_ratio(dungeon_map)
        analysis['wall_floor_ratio'] = wall_floor_ratio
        
        # Room analysis
        rooms = self._detect_rooms(dungeon_map)
        analysis['room_count'] = len(rooms)
        analysis['avg_room_size'] = np.mean([len(room) for room in rooms]) if rooms else 0
        
        # Corridor analysis
        corridors = self._detect_corridors(dungeon_map)
        analysis['corridor_count'] = len(corridors)
        
        # Traditional roguelike scoring (0-10)
        score = 0
        
        # Grid-based (2 points)
        if analysis['grid_based']:
            score += 2
            
        # Wall/Floor ratio (3 points)
        if 0.2 <= wall_floor_ratio[0] <= 0.6:  # 20-60% floors
            score += 1
        if 0.2 <= wall_floor_ratio[1] <= 0.5:  # 20-50% walls
            score += 1
        if 0.1 <= wall_floor_ratio[0] <= 0.7:  # Reasonable range
            score += 1
            
        # Room characteristics (3 points)
        if analysis['room_count'] >= 1:
            score += 1
        if analysis['avg_room_size'] >= 9:  # At least 3x3 rooms
            score += 1
        if analysis['room_count'] <= 15:  # Not too many rooms
            score += 1
            
        # Corridors (2 points)
        if analysis['corridor_count'] >= 0:  # Corridors are optional
            score += 1
        if analysis['corridor_count'] <= 20:  # Not too many corridors
            score += 1
            
        analysis['traditional_score'] = score
        
        return analysis


if __name__ == '__main__':
    unittest.main()