#!/usr/bin/env python3
"""
Test player character visibility with proper positioning.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tcod
import numpy as np
from unittest.mock import patch, MagicMock
import time

# Import the game modules
from darkdelve import Game, Entity, COLORS

def test_player_visibility():
    """Test player character visibility with proper positioning"""
    
    print("=== TESTING PLAYER CHARACTER VISIBILITY ===")
    print("This test ensures the player character is always visible.")
    print()
    
    # Create a mock game instance
    game = Game()
    game.config = {
        'game': {'name': 'DarkDelve', 'version': '1.0.0', 'seed': None},
        'display': {
            'width': 80, 
            'height': 50,
            'tileset': 'proper_ascii_tileset.png',  # Using the new tileset
            'fps_cap': 60,
            'fullscreen': False
        },
        'dungeon': {
            'width': 40,  # Smaller dungeon to ensure player is visible
            'height': 25,  # Smaller dungeon to ensure player is visible
            'max_rooms': 12,
            'room_min_size': 6,
            'room_max_size': 14,
            'max_depth': 26
        },
        'llm': {'model': 'cohere/north-mini-code:free'},
        'gameplay': {
            'permadeath': True,
            'hunger_enabled': True,
            'identification_enabled': True,
            'score_on_quit': True,
            'base_nutrition_per_turn': 1,
            'max_nutrition': 2000,
            'starving_threshold': 200
        },
        'classes': {
            'warrior': {
                'name': 'Warrior',
                'stats': {'str': 14, 'dex': 10, 'con': 13, 'int': 8, 'wis': 10, 'cha': 8},
                'hp_per_level': 10,
                'skills': ['power_attack', 'cleave', 'battle_shout', 'shield_block'],
                'start_gear': ['iron_longsword', 'chain_mail', 'wooden_shield', 'ration_3']
            }
        }
    }
    
    try:
        # Initialize game components
        game.initialize()
        game.new_game()
        
        # Get player character data
        player = game.player
        player_char = player.char
        player_char_code = ord(player_char)
        player_x, player_y = player.x, player.y
        
        print("=== PLAYER CHARACTER DATA ===")
        print(f"Player entity: {player}")
        print(f"Player char: '{player_char}' (ASCII: {player_char_code})")
        print(f"Player position: ({player_x}, {player_y})")
        print(f"Player color: {player.color}")
        print(f"Player in entities list: {player in game.entities}")
        print()
        
        # Check FOV bounds
        print("=== FOV BOUNDS CHECK ===")
        print(f"FOV shape: {game.fov.shape}")
        print(f"Player position in FOV bounds: {0 <= player_x < game.fov.shape[1] and 0 <= player_y < game.fov.shape[0]}")
        
        if player_y < game.fov.shape[0] and player_x < game.fov.shape[1]:
            fov_at_player = game.fov[player_y, player_x]
            print(f"FOV at player position ({player_x}, {player_y}): {fov_at_player}")
            print(f"Player should be visible: {fov_at_player or player is player}")
        else:
            print(f"Player position ({player_x}, {player_y}) is out of FOV bounds {game.fov.shape}")
            print("This is the issue! Player is outside the visible area.")
            return
        print()
        
        # Show console state before rendering
        print("=== CONSOLE STATE BEFORE RENDERING ===")
        try:
            if player_y < game.console.ch.shape[0] and player_x < game.console.ch.shape[1]:
                char_before = game.console.ch[player_y, player_x]
                color_before = game.console.fg[player_y, player_x]
                print(f"Console at player position ({player_x}, {player_y}): {char_before} = '{chr(char_before)}'")
                print(f"Color: {color_before}")
            else:
                print(f"Player position ({player_x}, {player_y}) is out of console bounds {game.console.ch.shape}")
        except Exception as e:
            print(f"Error reading console before rendering: {e}")
        print()
        
        print("=== RENDERING GAME WITH NEW TILESET ===")
        
        # Render the game
        try:
            game.render()
            
            # Show console state after rendering
            print("\n=== CONSOLE STATE AFTER RENDERING ===")
            try:
                if player_y < game.console.ch.shape[0] and player_x < game.console.ch.shape[1]:
                    char_after = game.console.ch[player_y, player_x]
                    color_after = game.console.fg[player_y, player_x]
                    print(f"Console at player position ({player_x}, {player_y}): {char_after} = '{chr(char_after)}'")
                    print(f"Color: {color_after}")
                    
                    # Check if the character matches
                    if char_after == player_char_code:
                        print("✓ Console character matches player character")
                        print("✓ Player character data is correct")
                        print("✓ Player character is being rendered correctly")
                    else:
                        print(f"✗ Console character ({char_after} = '{chr(char_after)}') does NOT match player character ({player_char_code} = '{player_char}')")
                        print(f"Expected: {player_char_code} ('{player_char}')")
                        print(f"Actual: {char_after} ('{chr(char_after)}')")
                        
                else:
                    print(f"Player position ({player_x}, {player_y}) is out of console bounds {game.console.ch.shape}")
                    
            except Exception as e:
                print(f"Error reading console after rendering: {e}")
                
        except Exception as e:
            print(f"Error during rendering: {e}")
            import traceback
            traceback.print_exc()
            return
        
        print("\n=== VISIBILITY TEST RESULTS ===")
        if player_y < game.fov.shape[0] and player_x < game.fov.shape[1]:
            if game.fov[player_y, player_x]:
                print("✓ Player is in FOV and should be visible")
                if player_y < game.console.ch.shape[0] and player_x < game.console.ch.shape[1]:
                    char_after = game.console.ch[player_y, player_x]
                    if char_after == player_char_code:
                        print("✓ Player character is correctly rendered in console")
                        print("✓ The tileset fix is working!")
                    else:
                        print("✗ Player character is not correctly rendered in console")
                        print("✗ There may still be a tileset issue")
            else:
                print("✗ Player is not in FOV but should be rendered anyway")
        else:
            print("✗ Player is outside FOV bounds")
            print("✗ The dungeon generation or player positioning needs adjustment")
        
    except Exception as e:
        print(f"Error during visibility test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_player_visibility()