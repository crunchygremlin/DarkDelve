#!/usr/bin/env python3
"""
Interactive debugging tool for player character rendering.
Shows you the character data and rendered output, then asks for confirmation.
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

def debug_player_character_interactive():
    """Interactive debugging of player character rendering with user confirmation"""
    
    print("=== INTERACTIVE PLAYER CHARACTER DEBUGGING ===")
    print("This will show you the player character rendering process.")
    print("Please look at the game window and tell me if the player character looks correct.")
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
        'llm': {'model': 'qwen2.5-coder:7b-instruct'},
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
            },
            'rogue': {
                'name': 'Rogue',
                'stats': {'str': 10, 'dex': 16, 'con': 10, 'int': 12, 'wis': 10, 'cha': 10},
                'hp_per_level': 7,
                'skills': ['backstab', 'evasion', 'trap_disarm', 'poison_blade'],
                'start_gear': ['steel_dagger', 'leather_armor', 'lockpicks_5', 'ration_3']
            },
            'mage': {
                'name': 'Mage',
                'stats': {'str': 8, 'dex': 10, 'con': 10, 'int': 16, 'wis': 12, 'cha': 10},
                'hp_per_level': 5,
                'skills': ['fireball', 'magic_missile', 'shield', 'blink'],
                'start_gear': ['apprentice_staff', 'robe', 'spellbook_fire', 'ration_3']
            },
            'cleric': {
                'name': 'Cleric',
                'stats': {'str': 10, 'dex': 8, 'con': 12, 'int': 10, 'wis': 16, 'cha': 12},
                'hp_per_level': 8,
                'skills': ['heal', 'turn_undead', 'bless', 'divine_strike'],
                'start_gear': ['iron_mace', 'scale_mail', 'holy_symbol', 'ration_3']
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
    
    print(f"Player character data:")
    print(f"  Symbol: '{player_char}'")
    print(f"  Code (ord): {player_char_code}")
    print(f"  Position: ({player_x}, {player_y})")
    print()
    
    # Show console state before rendering
    print("--- BEFORE RENDERING ---")
    try:
        # Check what's in the console at player position before rendering
        char_before = game.console.ch[player_y, player_x]  # Note: tcod uses [y, x] indexing
        color_before = game.console.fg[player_y, player_x]
        print(f"Console at player position ({player_x}, {player_y}): {char_before} = '{chr(char_before)}'")
        print(f"Color: {color_before}")
    except Exception as e:
        print(f"Error reading console before rendering: {e}")
    
    print()
    print("Now rendering the game...")
    
    # Render the game
    try:
        game.render()
        
        # Show console state after rendering
        print("--- AFTER RENDERING ---")
        try:
            char_after = game.console.ch[player_y, player_x]
            color_after = game.console.fg[player_y, player_x]
            print(f"Console at player position ({player_x}, {player_y}): {char_after} = '{chr(char_after)}'")
            print(f"Color: {color_after}")
            
            # Check if the character matches
            if char_after == player_char_code:
                print("✓ Console character matches player character")
            else:
                print(f"✗ Console character ({char_after} = '{chr(char_after)}') does NOT match player character ({player_char_code} = '{player_char}')")
                
        except Exception as e:
            print(f"Error reading console after rendering: {e}")
    except Exception as e:
        print(f"Error during rendering: {e}")
        return
    
    print()
    print("=== PLEASE LOOK AT THE GAME WINDOW ===")
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
    
    print()
    print("=== DEBUGGING COMPLETE ===")
    print("Thank you for your feedback!")

if __name__ == "__main__":
    debug_player_character_interactive()