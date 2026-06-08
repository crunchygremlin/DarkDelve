#!/usr/bin/env python3
"""
Debug script to visualize map tiles as text symbols.
This script demonstrates how to use the tile rendering test functionality
to convert map output back to text for debugging purposes.
"""

import sys
import os
import numpy as np
from unittest.mock import patch

# Add the project root to the path so we can import darkdelve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from darkdelve import UI


def create_debug_ui():
    """Create a UI instance with debug capabilities"""
    console = type('MockConsole', (), {'print': lambda *args, **kwargs: None})()
    ui = UI(console=console, config={
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
    
    # Track console calls for debugging
    console_calls = []
    
    def mock_print(x, y, char, color):
        console_calls.append((x, y, char, color))
    
    ui.console.print = mock_print
    return ui, console_calls


def convert_to_text_grid(dungeon_map, fov, explored, console_calls):
    """Convert console calls to a text grid for visualization"""
    height, width = dungeon_map.shape
    text_grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    for x, y, char, color in console_calls:
        if 0 <= x < width and 0 <= y < height:
            if fov[y, x]:
                text_grid[y][x] = char.upper()  # Visible tiles are uppercase
            elif explored[y, x]:
                text_grid[y][x] = char.lower()  # Explored tiles are lowercase
            else:
                text_grid[y][x] = '?'  # Unexplored tiles
    
    return text_grid


def generate_debug_output(dungeon_map, fov, explored):
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
    debug_lines.append("(# = wall, . = floor, V/E/U = visible/explored/unexplored)")
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


def main():
    """Main function to demonstrate tile debugging"""
    print("DarkDelve Tile Debugging Demo")
    print("=" * 40)
    
    # Create UI instance
    ui, console_calls = create_debug_ui()
    
    # Create a test map
    dungeon_map = np.array([
        [True, True, True, True, True, True, True],
        [True, False, False, False, False, False, True],
        [True, False, True, False, True, False, True],
        [True, False, False, False, False, False, True],
        [True, False, True, False, True, False, True],
        [True, False, False, False, False, False, True],
        [True, True, True, True, True, True, True]
    ], dtype=bool)
    
    # Create FOV (player can see a cross pattern)
    fov = np.array([
        [False, False, False, False, False, False, False],
        [False, True, False, True, False, True, False],
        [False, False, True, False, True, False, False],
        [False, True, False, True, False, True, False],
        [False, False, True, False, True, False, False],
        [False, True, False, True, False, True, False],
        [False, False, False, False, False, False, False]
    ], dtype=bool)
    
    # Create explored areas
    explored = np.array([
        [True, True, True, True, True, True, True],
        [True, True, True, True, True, True, True],
        [True, True, True, True, True, True, True],
        [True, True, True, True, True, True, True],
        [True, True, True, True, True, True, True],
        [True, True, True, True, True, True, True],
        [True, True, True, True, True, True, True]
    ], dtype=bool)
    
    # Mock the colors
    with patch('darkdelve.COLORS', {
        'wall': (255, 255, 255),
        'floor': (128, 128, 128)
    }):
        # Render the dungeon
        ui.render_dungeon(dungeon_map, fov, explored)
        
        # Generate debug output
        debug_output = generate_debug_output(dungeon_map, fov, explored)
        print(debug_output)
        
        # Convert to text grid
        text_grid = convert_to_text_grid(dungeon_map, fov, explored, console_calls)
        
        print("\nText Grid Visualization:")
        print("(Uppercase = Visible, Lowercase = Explored, ? = Unexplored)")
        print("-" * 20)
        for row in text_grid:
            print(" ".join(row))
        
        print("\nLegend:")
        print("# = Wall, . = Floor")
        print("V = Visible, E = Explored, U = Unexplored")


if __name__ == "__main__":
    main()