#!/usr/bin/env python3
"""
Debug script to understand the actual rendering output
"""

import numpy as np
import tcod
import sys
from pathlib import Path

# Add the current directory to the path to import darkdelve
sys.path.insert(0, str(Path(__file__).parent))

from darkdelve import COLORS, Entity, UI

def debug_rendering():
    """Debug the actual rendering output"""
    
    # Create a simple test console
    console = tcod.console.Console(80, 24)
    
    # Create UI
    ui = UI(console, {
        'display': {},
        'dungeon': {'width': 10, 'height': 10}
    })
    
    # Create test data
    dungeon_map = np.array([
        [True, False, True, False, True, False, True, False, True, False],
        [False, True, False, True, False, True, False, True, False, True],
        [True, False, True, False, True, False, True, False, True, False],
        [False, True, False, True, False, True, False, True, False, True],
        [True, False, True, False, True, False, True, False, True, False],
        [False, True, False, True, False, True, False, True, False, True],
        [True, False, True, False, True, False, True, False, True, False],
        [False, True, False, True, False, True, False, True, False, True],
        [True, False, True, False, True, False, True, False, True, False],
        [False, True, False, True, False, True, False, True, False, True],
    ], dtype=bool)
    
    fov = np.array([
        [False, True, False, True, False, True, False, True, False, True],
        [True, False, True, False, True, False, True, False, True, False],
        [False, True, False, True, False, True, False, True, False, True],
        [True, False, True, False, True, False, True, False, True, False],
        [False, True, False, True, False, True, False, True, False, True],
        [True, False, True, False, True, False, True, False, True, False],
        [False, True, False, True, False, True, False, True, False, True],
        [True, False, True, False, True, False, True, False, True, False],
        [False, True, False, True, False, True, False, True, False, True],
        [True, False, True, False, True, False, True, False, True, False],
    ], dtype=bool)
    
    explored = np.ones((10, 10), dtype=bool)
    
    # Create player entity
    player = Entity(
        x=5, y=5,
        char="@",
        color=COLORS['player'],
        name="Test Player",
        blocks=True,
        hp=10, max_hp=10,
        power=5, defense=2, speed=100,
        intel_tier=3, is_commander=False,
        stats={'str': 10, 'dex': 10, 'con': 10, 'int': 10, 'wis': 10, 'cha': 10},
        level=1, xp=0, xp_to_next=100,
        skill_points=0,
        nutrition=100, max_nutrition=100,
        inventory=None
    )
    
    # Create other entities
    entities = [
        player,
        Entity(x=2, y=2, char="D", color=COLORS['enemy_normal'], name="Dragon", blocks=True, hp=10, max_hp=10),
        Entity(x=7, y=7, char="g", color=COLORS['enemy_weak'], name="Goblin", blocks=True, hp=5, max_hp=5),
    ]
    
    # Mock combat log
    class MockCombatLog:
        def __init__(self):
            self.events = [
                "Player hits Dragon for 5 damage",
                "Dragon breathes fire at Player",
                "Player takes 3 damage"
            ]
        
        def get_recent(self, count):
            return self.events[-count:]
    
    combat_log = MockCombatLog()
    
    # Mock game state
    class MockGameState:
        def __init__(self):
            self.run_id = "test123"
    
    state = MockGameState()
    
    # Clear console and render
    console.clear()
    
    # Print UI positioning info
    print(f"UI Y position: {ui.ui_y}")
    print(f"Console height: {console.height}")
    print(f"Console width: {console.width}")
    print(f"Map height: {ui.map_height}")
    print(f"Expected UI start: {ui.map_height + 2}")
    
    # Render each component separately to see what's happening
    print("=== RENDERING DUNGEON ===")
    ui.render_dungeon(dungeon_map, fov, explored)
    
    print("=== RENDERING ENTITIES ===")
    ui.render_entities(entities, fov, player)
    
    print("=== RENDERING UI ===")
    # Add debug output to track UI coordinates
    original_render_text = ui._render_text
    def debug_render_text(x, y, text, color):
        print(f"DEBUG: Rendering text '{text}' at ({x}, {y}) with color {color}")
        original_render_text(x, y, text, color)
    ui._render_text = debug_render_text
    
    ui.render_ui(player, state, combat_log, 42)
    
    # Print the console content
    print("\n=== CONSOLE CONTENT ===")
    for y in range(min(console.height, 24)):  # Limit to 24 rows to avoid index error
        line = ""
        for x in range(console.width):
            try:
                char = console.ch[x, y]
                if char == 0:
                    line += " "
                else:
                    line += chr(char)
            except IndexError:
                line += "?"
        print(f"{y:2d}: {line}")
    
    # Also try to access the console differently
    print("\n=== CONSOLE CONTENT (alternative method) ===")
    try:
        for y in range(min(console.height, 24)):
            line = ""
            for x in range(console.width):
                # Try using console instead of console.ch
                try:
                    # Get the character at position (x, y)
                    char = console.get_char(x, y)
                    if char == (0, 0, 0):  # Default background color
                        line += " "
                    else:
                        line += chr(char[0])  # Get the character code
                except:
                    line += "?"
            print(f"{y:2d}: {line}")
    except Exception as e:
        print(f"Alternative method failed: {e}")
    
    # Print color information
    print("\n=== COLOR INFORMATION ===")
    print(f"Player color: {COLORS['player']}")
    print(f"Wall color: {COLORS['wall']}")
    print(f"Floor color: {COLORS['floor']}")
    print(f"Text color: {COLORS['text']}")
    print(f"Magic color: {COLORS['magic']}")
    
    # Print entity information
    print("\n=== ENTITY INFORMATION ===")
    for entity in entities:
        print(f"Entity {entity.name}: pos=({entity.x}, {entity.y}), char='{entity.char}', color={entity.color}")

if __name__ == "__main__":
    debug_rendering()