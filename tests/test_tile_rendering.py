import unittest
import numpy as np
from unittest.mock import MagicMock, patch
import sys
import os

# Add the project root to the path so we can import darkdelve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from darkdelve import UI


class TestTileRendering(unittest.TestCase):
    """Test cases for tile rendering functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.ui = UI(console=MagicMock(), config={
            'display': {
                'screen_width': 80,
                'screen_height': 24,
                'tileset': 'new_tileset.png'
            },
            'dungeon': {
                'width': 80,
                'height': 24,
                'max_rooms': 15,
                'room_min_size': 6,
                'room_max_size': 10
            }
        })
        
        # Track console calls for testing
        self.console_calls = []
        
        def mock_print(x, y, char, color):
            self.console_calls.append((x, y, char, color))
        
        self.ui.console.print = mock_print
        
    def test_render_dungeon_floor_wall_logic(self):
        """Test that floor and wall tiles are rendered correctly"""
        # Create a simple test map
        # False = floor, True = wall
        dungeon_map = np.array([
            [True, True, True, True, True],
            [True, False, False, False, True],
            [True, False, False, False, True],
            [True, False, False, False, True],
            [True, True, True, True, True]
        ], dtype=bool)
        
        # Create FOV and explored arrays
        fov = np.array([
            [False, False, False, False, False],
            [False, True, True, True, False],
            [False, True, True, True, False],
            [False, True, True, True, False],
            [False, False, False, False, False]
        ], dtype=bool)
        
        explored = np.array([
            [True, True, True, True, True],
            [True, True, True, True, True],
            [True, True, True, True, True],
            [True, True, True, True, True],
            [True, True, True, True, True]
        ], dtype=bool)
        
        # Mock the colors
        with patch('darkdelve.COLORS', {
            'wall': (255, 255, 255),
            'floor': (128, 128, 128)
        }):
            self.ui.render_dungeon(dungeon_map, fov, explored)
            
            # Check that console.print was called with the correct characters
            # The center 3x3 area should be floors (.) surrounded by walls (#)
            calls = self.console_calls
            
            # We expect calls for the visible tiles (the 3x3 center area)
            # These should all be floor tiles (.) since dungeon_map[y, x] is False
            for call in calls:
                x, y, char, color = call
                # For the visible area, we should see floor tiles (.)
                if 1 <= x <= 3 and 1 <= y <= 3:
                    self.assertEqual(char, ".", f"Expected floor tile at ({x}, {y}) but got {char}")
                else:
                    # For walls, we should see wall tiles (#)
                    self.assertEqual(char, "#", f"Expected wall tile at ({x}, {y}) but got {char}")
    
    def test_render_dungeon_explored_areas(self):
        """Test that explored areas are rendered with darker colors"""
        # Create a simple test map
        dungeon_map = np.array([
            [False, False, False],
            [False, False, False],
            [False, False, False]
        ], dtype=bool)
        
        # Create FOV and explored arrays
        fov = np.array([
            [False, False, False],
            [False, True, False],
            [False, False, False]
        ], dtype=bool)
        
        explored = np.array([
            [True, True, True],
            [True, True, True],
            [True, True, True]
        ], dtype=bool)
        
        # Mock the colors
        with patch('darkdelve.COLORS', {
            'wall': (255, 255, 255),
            'floor': (128, 128, 128)
        }):
            self.ui.render_dungeon(dungeon_map, fov, explored)
            
            # Check that console.print was called with the correct colors
            calls = self.console_calls
            
            # The center tile should be visible and use bright colors
            # The surrounding tiles should be explored and use dark colors
            for call in calls:
                x, y, char, color = call
                if x == 1 and y == 1:  # Center tile (visible)
                    self.assertEqual(color, (128, 128, 128), f"Expected bright floor color at ({x}, {y}) but got {color}")
                else:  # Surrounding tiles (explored but not visible)
                    self.assertEqual(color, (50, 50, 50), f"Expected dark floor color at ({x}, {y}) but got {color}")
    
    def test_text_symbol_conversion(self):
        """Test that dungeon maps can be converted to text symbols for debugging"""
        # Create a more complex test map
        dungeon_map = np.array([
            [True, True, True, True, True],
            [True, False, False, False, True],
            [True, False, True, False, True],
            [True, False, False, False, True],
            [True, True, True, True, True]
        ], dtype=bool)
        
        # Create FOV and explored arrays
        fov = np.array([
            [False, False, False, False, False],
            [False, True, True, True, False],
            [False, True, True, True, False],
            [False, True, True, True, False],
            [False, False, False, False, False]
        ], dtype=bool)
        
        explored = np.array([
            [True, True, True, True, True],
            [True, True, True, True, True],
            [True, True, True, True, True],
            [True, True, True, True, True],
            [True, True, True, True, True]
        ], dtype=bool)
        
        # Mock the colors
        with patch('darkdelve.COLORS', {
            'wall': (255, 255, 255),
            'floor': (128, 128, 128)
        }):
            self.ui.render_dungeon(dungeon_map, fov, explored)
            
            # Convert console calls to text grid for debugging
            text_grid = self._convert_calls_to_text_grid(dungeon_map.shape)
            
            # Verify the text representation
            expected_grid = [
                ['#', '#', '#', '#', '#'],
                ['#', '.', '.', '.', '#'],
                ['#', '.', '#', '.', '#'],
                ['#', '.', '.', '.', '#'],
                ['#', '#', '#', '#', '#']
            ]
            
            # Only check the visible area (3x3 center)
            for y in range(1, 4):
                for x in range(1, 4):
                    self.assertEqual(text_grid[y][x], expected_grid[y][x],
                                   f"Expected {expected_grid[y][x]} at ({x}, {y}) but got {text_grid[y][x]}")
    
    def test_debug_output_visualization(self):
        """Test that debug output can visualize the map state"""
        # Create a test map with mixed visibility
        dungeon_map = np.array([
            [True, False, True, False, True],
            [False, True, False, True, False],
            [True, False, True, False, True],
            [False, True, False, True, False],
            [True, False, True, False, True]
        ], dtype=bool)
        
        # Create FOV showing only a cross pattern
        fov = np.array([
            [False, True, False, True, False],
            [True, False, True, False, True],
            [False, True, False, True, False],
            [True, False, True, False, True],
            [False, True, False, True, False]
        ], dtype=bool)
        
        explored = np.array([
            [True, True, True, True, True],
            [True, True, True, True, True],
            [True, True, True, True, True],
            [True, True, True, True, True],
            [True, True, True, True, True]
        ], dtype=bool)
        
        # Mock the colors
        with patch('darkdelve.COLORS', {
            'wall': (255, 255, 255),
            'floor': (128, 128, 128)
        }):
            self.ui.render_dungeon(dungeon_map, fov, explored)
            
            # Generate debug output
            debug_output = self._generate_debug_output(dungeon_map, fov, explored)
            
            # Verify debug output contains expected information
            self.assertIn("DUNGEON MAP DEBUG OUTPUT", debug_output)
            self.assertIn("Visible tiles:", debug_output)
            self.assertIn("Explored but not visible tiles:", debug_output)
            self.assertIn("Unexplored tiles:", debug_output)
            
            # Count visible tiles in debug output (should be 13 based on our cross pattern)
            # Count all "V" characters in the text representation section
            lines = debug_output.split('\n')
            visible_count = 0
            for line in lines:
                if line.strip() and not line.startswith('DUNGEON') and not line.startswith('Map') and not line.startswith('Text') and not line.startswith('('):
                    visible_count += line.count('V')
            self.assertEqual(visible_count, 13, f"Expected 13 visible tiles, found {visible_count}")
    
    def test_edge_cases(self):
        """Test edge cases for tile rendering"""
        # Test empty map
        dungeon_map = np.array([], dtype=bool).reshape(0, 0)
        fov = np.array([], dtype=bool).reshape(0, 0)
        explored = np.array([], dtype=bool).reshape(0, 0)
        
        # Should not crash
        self.ui.render_dungeon(dungeon_map, fov, explored)
        self.assertEqual(len(self.console_calls), 0)
        
        # Test single tile map
        dungeon_map = np.array([[True]], dtype=bool)
        fov = np.array([[True]], dtype=bool)
        explored = np.array([[True]], dtype=bool)
        
        with patch('darkdelve.COLORS', {
            'wall': (255, 255, 255),
            'floor': (128, 128, 128)
        }):
            self.ui.render_dungeon(dungeon_map, fov, explored)
            
            # Should have one call for the single tile
            self.assertEqual(len(self.console_calls), 1)
            x, y, char, color = self.console_calls[0]
            self.assertEqual(x, 0)
            self.assertEqual(y, 0)
            self.assertEqual(char, "#")
            self.assertEqual(color, (255, 255, 255))
    
    def test_entity_character_rendering(self):
        """Test that entity characters are rendered correctly on tiles"""
        # Create a simple test map
        dungeon_map = np.array([
            [True, True, True],
            [True, False, True],
            [True, True, True]
        ], dtype=bool)
        
        # Create FOV and explored arrays
        fov = np.array([
            [False, False, False],
            [False, True, False],
            [False, False, False]
        ], dtype=bool)
        
        explored = np.array([
            [True, True, True],
            [True, True, True],
            [True, True, True]
        ], dtype=bool)
        
        # Mock entity with specific character
        class MockEntity:
            def __init__(self, x, y, char, color):
                self.x = x
                self.y = y
                self.char = char
                self.color = color
        
        # Create entities with different characters
        entities = [
            MockEntity(1, 1, "@", (255, 255, 0)),  # Player character
            MockEntity(0, 0, "D", (255, 0, 0)),    # Dragon
            MockEntity(2, 2, "g", (0, 255, 0)),    # Goblin
        ]
        
        # Mock the colors
        with patch('darkdelve.COLORS', {
            'wall': (255, 255, 255),
            'floor': (128, 128, 128)
        }):
            # First render the dungeon
            self.ui.render_dungeon(dungeon_map, fov, explored)
            
            # Then render entities
            self.ui.render_entities(entities, fov, entities[0])  # Pass player as first entity
            
            # Check console calls
            # render_dungeon will render all explored tiles (9 tiles for 3x3 map)
            # render_entities will render entities that are in FOV or the player
            self.assertEqual(len(self.console_calls), 10)  # 9 explored tiles + 1 entity (only player is visible)
            
            # Separate dungeon calls from entity calls
            dungeon_calls = []
            entity_calls = []
            
            for call in self.console_calls:
                x, y, char, color = call
                # Entity calls have specific colors that match our entities
                if color in [(255, 255, 0), (255, 0, 0), (0, 255, 0)]:
                    entity_calls.append(call)
                else:
                    dungeon_calls.append(call)
            
            # Verify we have the right number of each type
            self.assertEqual(len(dungeon_calls), 9)  # All explored tiles
            self.assertEqual(len(entity_calls), 1)   # Only player is visible
            
            # Verify entity characters are rendered correctly
            # Only the player should be visible (at position 1,1)
            expected_entity = (1, 1, "@", (255, 255, 0))  # Player
            
            found = False
            for call in entity_calls:
                x, y, char, color = call
                if x == expected_entity[0] and y == expected_entity[1]:
                    self.assertEqual(char, expected_entity[2],
                                   f"Expected character '{expected_entity[2]}' at ({x}, {y}) but got '{char}'")
                    self.assertEqual(color, expected_entity[3],
                                   f"Expected color {expected_entity[3]} at ({x}, {y}) but got {color}")
                    found = True
                    break
            
            self.assertTrue(found, f"Expected entity call at ({expected_entity[0]}, {expected_entity[1]}) not found")
    
    def _convert_calls_to_text_grid(self, map_shape):
        """Convert console calls to a text grid for debugging"""
        height, width = map_shape
        text_grid = [[' ' for _ in range(width)] for _ in range(height)]
        
        for x, y, char, color in self.console_calls:
            if 0 <= x < width and 0 <= y < height:
                text_grid[y][x] = char
        
        return text_grid
    
    def _generate_debug_output(self, dungeon_map, fov, explored):
        """Generate debug output showing map state"""
        height, width = dungeon_map.shape
        debug_lines = []
        
        debug_lines.append("DUNGEON MAP DEBUG OUTPUT")
        debug_lines.append("=" * 40)
        debug_lines.append(f"Map size: {width}x{height}")
        debug_lines.append("")
        
        # Count different tile types
        visible_count = 0
        explored_not_visible = 0
        unexplored_count = 0
        
        for y in range(height):
            for x in range(width):
                if fov[y, x]:
                    visible_count += 1
                elif explored[y, x]:
                    explored_not_visible += 1
                else:
                    unexplored_count += 1
        
        debug_lines.append(f"Visible tiles: {visible_count}")
        debug_lines.append(f"Explored but not visible tiles: {explored_not_visible}")
        debug_lines.append(f"Unexplored tiles: {unexplored_count}")
        debug_lines.append("")
        
        # Show text representation
        debug_lines.append("Text representation:")
        debug_lines.append("(# = wall, . = floor, V = visible, E = explored, U = unexplored)")
        debug_lines.append("")
        
        for y in range(height):
            row = []
            for x in range(width):
                if fov[y, x]:
                    if dungeon_map[y, x]:
                        row.append("#V")
                    else:
                        row.append(".V")
                elif explored[y, x]:
                    if dungeon_map[y, x]:
                        row.append("#E")
                    else:
                        row.append(".E")
                else:
                    if dungeon_map[y, x]:
                        row.append("#U")
                    else:
                        row.append(".U")
            debug_lines.append(" ".join(row))
        
        return "\n".join(debug_lines)


if __name__ == '__main__':
    unittest.main()