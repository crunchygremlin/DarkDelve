#!/usr/bin/env python3
"""
Test script to verify the actual game rendering works correctly
"""

import sys
import numpy as np
from pathlib import Path

# Add the current directory to the path to import darkdelve
sys.path.insert(0, str(Path(__file__).parent))

import tcod
from darkdelve import Game, COLORS, Entity

def test_game_rendering():
    """Test the actual game rendering process"""
    
    # Create a minimal game instance
    game = Game()
    
    # Initialize with minimal config
    game.config = {
        'llm': {'model': 'qwen2.5-coder:7b-instruct'},
        'display': {'tileset': 'new_tileset.png'},
        'dungeon': {'width': 20, 'height': 15},
        'classes': {
            'warrior': {
                'hp_per_level': 10,
                'stats': {'str': 16, 'dex': 12, 'con': 14, 'int': 10, 'wis': 10, 'cha': 10},
                'start_gear': ['sword', 'shield']
            }
        },
        'gameplay': {'max_nutrition': 100}
    }
    
    # Initialize game components
    game.initialize()
    
    # Create a player
    game.state = type('GameState', (), {'run_id': 'test123', 'player_class': 'warrior', 'player_name': 'Test Player'})()
    game.create_player()
    
    # Generate a test level
    game.generate_level(1, "main")
    
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
    print(f"Console dimensions: {game.console.width}x{game.console.height}")
    
    # Test rendering
    try:
        game.render()
        print("✓ Rendering completed successfully")
        
        # Check if player character is visible in the console
        player_char_found = False
        player_char_positions = []
        for y in range(game.console.height):
            for x in range(game.console.width):
                try:
                    # FIX: console.ch has shape (height, width), so access as [y, x]
                    char = game.console.ch[y, x]
                    if char == ord(game.player.char):
                        player_char_found = True
                        player_char_positions.append((x, y))
                        print(f"✓ Player character found at ({x}, {y})")
                        break
                except:
                    pass
            if player_char_found:
                break
        
        if not player_char_found:
            print("✗ Player character not found in console")
            # Check if player is within the map bounds
            print(f"Player position: ({game.player.x}, {game.player.y})")
            print(f"Map dimensions: {game.dungeon_map.shape}")
            print(f"FOV shape: {game.fov.shape}")
            print(f"Explored shape: {game.explored.shape}")
            
            # Check if player position is within FOV
            if (0 <= game.player.x < game.fov.shape[1] and
                0 <= game.player.y < game.fov.shape[0]):
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
                    char = game.console.ch[x, y]
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
                    char = game.console.ch[x, y]
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

if __name__ == "__main__":
    test_game_rendering()