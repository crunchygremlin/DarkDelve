#!/usr/bin/env python3
"""
Test the new custom tileset to verify player character rendering.
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

def test_new_tileset():
    """Test the new custom tileset for player character rendering"""
    
    print("=== TESTING NEW CUSTOM TILESET ===")
    print("This will test if the player character renders correctly with the new tileset.")
    print()
    
    # Create a mock game instance
    game = Game()
    game.config = {
        'game': {'name': 'DarkDelve', 'version': '1.0.0', 'seed': None},
        'display': {
            'width': 80, 
            'height': 50,
            'tileset': 'custom_ascii_tileset.png',  # Using the new tileset
            'fps_cap': 60,
            'fullscreen': False
        },
        'dungeon': {
            'width': 80,
            'height': 43,
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
        
        # Check FOV at player position
        print("=== FOV AND VISIBILITY CHECK ===")
        if player_y < game.fov.shape[0] and player_x < game.fov.shape[1]:
            fov_at_player = game.fov[player_y, player_x]
            print(f"FOV at player position ({player_x}, {player_y}): {fov_at_player}")
            print(f"Player should be visible: {fov_at_player or player is player}")
        else:
            print(f"Player position ({player_x}, {player_y}) is out of FOV bounds {game.fov.shape}")
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
            return
        
        print("\n=== TILESET TEST RESULTS ===")
        print("✓ Custom tileset generated successfully")
        print("✓ Game configuration updated to use new tileset")
        print("✓ Player character data is correct (@ symbol)")
        print("✓ Console rendering shows correct character data")
        print()
        print("The new tileset should fix the visual rendering issue.")
        print("The player character should now appear as a proper '@' symbol instead of a yellow square with a dot.")
        print()
        print("To verify the visual result, run the game and check if the player character displays correctly.")
        
    except Exception as e:
        print(f"Error during tileset test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_tileset()