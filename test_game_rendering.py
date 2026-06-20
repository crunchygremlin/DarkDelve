#!/usr/bin/env python3
"""
Test script to verify the actual game rendering works correctly
"""

import copy
import sys
import numpy as np
from pathlib import Path

# Add the current directory to the path to import darkdelve
sys.path.insert(0, str(Path(__file__).parent))

from darkdelve import CONFIG, Game, COLORS, Entity

def test_game_rendering():
    """Test the actual game rendering process"""
    
    # Create a minimal game instance
    game = Game()
    
    game.config = copy.deepcopy(CONFIG)
    game.config['display'].update({
        'tileset': 'proper_ascii_tileset.png',
        'renderer': 'console',
        'width': 80,
        'height': 30,
    })
    game.config['dungeon'].update({'width': 40, 'height': 20})
    
    game.state = type('GameState', (), {'run_id': 'test123', 'player_class': 'warrior', 'player_name': 'Test Player'})()
    
    # Initialize game components and start a new game.
    game.initialize()
    
    # Create some test entities
    game.entities = [
        game.player,
        Entity(x=5, y=5, char="D", color=COLORS['enemy_normal'], name="Dragon", blocks=True, hp=10, max_hp=10),
        Entity(x=10, y=10, char="g", color=COLORS['enemy_weak'], name="Goblin", blocks=True, hp=5, max_hp=5),
    ]
    
    # Create a simple combat log with get_recent method
    class MockCombatLog:
        def __init__(self):
            self.events = [
                "Player hits Dragon for 5 damage",
                "Dragon breathes fire at Player",
                "Player takes 3 damage"
            ]
        
        def get_recent(self, count):
            return self.events[-count:]
    
    game.combat_log = MockCombatLog()
    
    # Test the rendering process
    print("=== TESTING GAME RENDERING ===")
    print(f"Map dimensions: {game.dungeon_map.shape}")
    print(f"Player position: ({game.player.x}, {game.player.y})")
    print(f"Player character: '{game.player.char}'")
    print(f"Player color: {game.player.color}")
    print(f"UI Y position: {game.ui.ui_y}")
    
    # Check console dimensions if available
    if hasattr(game.renderer, '_console'):
        console = game.renderer._console
        print(f"Console dimensions: {console.width}x{console.height}")
    else:
        print("Console not available in current renderer")
    
    # Test rendering
    try:
        print("DEBUG: About to render game...")
        game.render()
        print("✓ Rendering completed successfully")
        
        # Check if player character is visible in the console
        player_char_found = False
        player_char_positions = []
        print(f"DEBUG: Searching for player character '{game.player.char}' (code: {ord(game.player.char)}) in console...")
        
        if hasattr(game.renderer, '_console'):
            console = game.renderer._console
            print(f"DEBUG: Console dimensions: {console.width}x{console.height}")
            print(f"DEBUG: Player expected position: ({game.player.x}, {game.player.y})")

            for y in range(console.height):
                for x in range(console.width):
                    try:
                        # FIX: console.ch has shape (height, width), so access as [y, x]
                        char = console.ch[y, x]
                        if char == ord(game.player.char):
                            player_char_found = True
                            player_char_positions.append((x, y))
                            print(f"✓ Player character found at ({x}, {y})")
                    except Exception as e:
                        print(f"DEBUG: Error accessing console.ch[{y}, {x}]: {e}")
                        pass
        
        if not player_char_found:
            print("✗ Player character not found in console")
            # Check if player is within the map bounds
            print(f"Player position: ({game.player.x}, {game.player.y})")
            print(f"Map dimensions: {game.dungeon_map.shape}")
            print(f"FOV shape: {game.fov.shape}")
            print(f"Explored shape: {game.explored.shape}")
            
            # Check if player position is within FOV
            if (0 <= game.player.x < game.fov.shape[0] and
                0 <= game.player.y < game.fov.shape[1]):
                if game.fov[game.player.y, game.player.x]:
                    print("✓ Player is in FOV")
                else:
                    print("✗ Player is not in FOV")
            else:
                print("✗ Player is out of FOV bounds")
        
        if not player_char_found:
            print("✗ Player character not found in console")
        
        # Check if UI text is present
        ui_text_found = False
        for y in range(game.console.height):
            for x in range(game.console.width):
                try:
                    # FIX: console.ch has shape (height, width), so access as [y, x]
                    char = game.console.ch[y, x]
                    if char == ord('L'):  # First character of "LLM:"
                        ui_text_found = True
                        print(f"✓ UI text found at ({x}, {y})")
                        break
                except:
                    pass
            if ui_text_found:
                break
        
        if not ui_text_found:
            print("✗ UI text not found in console")
        
        # Print a sample of the console content
        print("\n=== CONSOLE CONTENT SAMPLE ===")
        for y in range(min(game.console.height, 10)):
            line = ""
            for x in range(min(game.console.width, 40)):
                try:
                    char = game.console.ch[y, x]
                    if char == 0:
                        line += " "
                    else:
                        line += chr(char)
                except:
                    line += "?"
            print(f"{y:2d}: {line}")
        
        print("\n=== CONSOLE CONTENT (UI area) ===")
        for y in range(max(0, game.ui.ui_y - 2), game.console.height):
            line = ""
            for x in range(min(game.console.width, 40)):
                try:
                    char = game.console.ch[y, x]
                    if char == 0:
                        line += " "
                    else:
                        line += chr(char)
                except:
                    line += "?"
            print(f"{y:2d}: {line}")
        
    except Exception as e:
        print(f"✗ Rendering failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    assert player_char_found, "Player character was not rendered to the console"
    assert ui_text_found, "UI text was not rendered to the console"

if __name__ == "__main__":
    test_game_rendering()