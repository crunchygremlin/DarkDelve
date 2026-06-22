#!/usr/bin/env python3
"""
Enhanced debugging tool for player character rendering.
Shows detailed information about what character is being rendered and why.
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

def debug_player_character_detailed():
    """Detailed debugging of player character rendering with enhanced visibility"""
    
    print("=== DETAILED PLAYER CHARACTER DEBUGGING ===")
    print("This will show you exactly what's happening with player character rendering.")
    print()
    
    # Create a mock game instance
    game = Game()
    game.config = {
        'game': {'name': 'DarkDelve', 'version': '1.0.0', 'seed': None},
        'display': {
            'width': 80, 
            'height': 50,
            'tileset': 'dejavu10x10_gs_tc.png',
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
        if hasattr(game.renderer, '_console'):
            console = game.renderer._console
            if player_y < console.ch.shape[0] and player_x < console.ch.shape[1]:
                char_before = console.ch[player_y, player_x]
                color_before = console.fg[player_y, player_x]
                print(f"Console at player position ({player_x}, {player_y}): {char_before} = '{chr(char_before)}'")
                print(f"Color: {color_before}")
            else:
                print(f"Player position ({player_x}, {player_y}) is out of console bounds {console.ch.shape}")
        else:
            print("Console not available in current renderer")
    except Exception as e:
        print(f"Error reading console before rendering: {e}")
    print()
    
    # Add debugging to render_entities method
    print("=== DEBUGGING render_entities METHOD ===")
    
    # Mock the render_entities method to add debugging
    original_render_entities = game.ui.render_entities
    
    def debug_render_entities(entities, fov, player):
        print(f"render_entities called with {len(entities)} entities")
        print(f"Player passed to render_entities: {player}")
        print(f"Player char: '{player.char}' (ASCII: {ord(player.char)})")
        
        for entity in entities:
            print(f"Entity: {entity.name} at ({entity.x}, {entity.y}) with char '{entity.char}'")
            
            # Prevent crashes if entity position goes out of bounds
            height, width = fov.shape
            if 0 <= entity.x < width and 0 <= entity.y < height:
                # Only render entities in field of view or the player
                if fov[entity.y, entity.x] or entity is player:
                    print(f"Would render {entity.name} at ({entity.x}, {entity.y}) with '{entity.char}'")
                    if hasattr(game.renderer, '_console'):
                        game.renderer._console.print(entity.x, entity.y, entity.char, entity.color)
                    else:
                        print(f"Would render {entity.name} at ({entity.x}, {entity.y}) with '{entity.char}' (no console available)")
                else:
                    print(f"Entity {entity.name} not in FOV and not player, skipping")
            else:
                print(f"Entity {entity.name} at ({entity.x}, {entity.y}) out of bounds")
    
    # Replace the method with our debug version
    game.ui.render_entities = debug_render_entities
    
    print("Now rendering the game...")
    
    # Render the game
    try:
        game.render()
        
        # Show console state after rendering
        print("\n=== CONSOLE STATE AFTER RENDERING ===")
        try:
            if hasattr(game.renderer, '_console'):
                console = game.renderer._console
                if player_y < console.ch.shape[0] and player_x < console.ch.shape[1]:
                    char_after = console.ch[player_y, player_x]
                    color_after = console.fg[player_y, player_x]
                    print(f"Console at player position ({player_x}, {player_y}): {char_after} = '{chr(char_after)}'")
                    print(f"Color: {color_after}")
                    
                    # Check if the character matches
                    if char_after == player_char_code:
                        print("✓ Console character matches player character")
                    else:
                        print(f"✗ Console character ({char_after} = '{chr(char_after)}') does NOT match player character ({player_char_code} = '{player_char}')")
                        print(f"Expected: {player_char_code} ('{player_char}')")
                        print(f"Actual: {char_after} ('{chr(char_after)}')")
                else:
                    print(f"Player position ({player_x}, {player_y}) is out of console bounds {console.ch.shape}")
            else:
                print("Console not available in current renderer")
                
        except Exception as e:
            print(f"Error reading console after rendering: {e}")
            
    except Exception as e:
        print(f"Error during rendering: {e}")
        return
    
    print("\n=== PLEASE LOOK AT THE GAME WINDOW ===")
    print("The game window should now be visible.")
    print("Look at the player character at the position shown above.")
    print()
    
    # Ask for user confirmation
    while True:
        response = input("Does the player character look correct in the game window? (yes/no/correct/incorrect): ").strip().lower()
        
        if response in ['yes', 'correct']:
            print("✓ Great! The player character rendering is working correctly.")
            break
        elif response in ['no', 'incorrect']:
            print("✗ The player character rendering needs to be fixed.")
            print("Please describe what you see:")
            description = input("What does the player character look like? (e.g., blank, wrong symbol, color issue): ").strip()
            print(f"Thank you for the feedback: {description}")
            break
        else:
            print("Please answer with 'yes', 'no', 'correct', or 'incorrect'.")
    
    print("\n=== DEBUGGING COMPLETE ===")
    print("Thank you for your feedback!")

if __name__ == "__main__":
    debug_player_character_detailed()