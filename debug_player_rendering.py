#!/usr/bin/env python3

import tcod
import numpy as np
import sys
import os

# Add the current directory to the path so we can import darkdelve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import darkdelve

def debug_player_rendering():
    """Debug player character rendering to understand why it's not visible"""
    
    # Create a game instance
    game = darkdelve.Game()
    game.initialize()
    game.new_game()
    
    print("=== DEBUG PLAYER RENDERING ===")
    print(f"Player position: ({game.player.x}, {game.player.y})")
    print(f"Player character: '{game.player.char}'")
    print(f"Player color: {game.player.color}")
    print(f"FOV shape: {game.fov.shape}")
    print(f"Player in FOV: {game.fov[game.player.y, game.player.x]}")
    
    # Test rendering
    game.render()
    
    # Check what's at the player position
    player_x, player_y = game.player.x, game.player.y
    print(f"\nChecking console at player position ({player_x}, {player_y}):")
    
    # Check the character at player position
    try:
        char_at_player = game.console.ch[player_y, player_x]  # FIX: [y, x] not [x, y]
        print(f"console.ch[{player_y}, {player_x}] = {char_at_player} = {chr(char_at_player) if char_at_player >= 32 else 'N/A'}")
    except Exception as e:
        print(f"Error accessing console.ch[{player_y}, {player_x}]: {e}")
    
    # Check a small area around the player
    print(f"\nChecking area around player ({player_x}, {player_y}):")
    for y in range(max(0, player_y - 2), min(game.console.height, player_y + 3)):
        for x in range(max(0, player_x - 2), min(game.console.width, player_x + 3)):
            try:
                char_code = game.console.ch[y, x]
                char = chr(char_code) if char_code >= 32 and char_code <= 126 else '.'
                if x == player_x and y == player_y:
                    print(f"({x},{y}): [{char}]", end=" ")
                else:
                    print(f"({x},{y}): {char}", end=" ")
            except:
                print(f"({x},{y}): ?", end=" ")
        print()
    
    # Check for player character in entire console
    print(f"\nSearching for player character '{game.player.char}' in entire console:")
    player_found = False
    for y in range(game.console.height):
        for x in range(game.console.width):
            try:
                char_code = game.console.ch[y, x]
                if char_code == ord(game.player.char):
                    print(f"Found player character at ({x}, {y})")
                    player_found = True
            except:
                pass
    
    if not player_found:
        print("Player character not found in console")
    
    # Check what characters are actually in the console
    print(f"\nConsole content sample:")
    for y in range(game.console.height):
        line = ""
        for x in range(game.console.width):
            try:
                char_code = game.console.ch[y, x]
                line += chr(char_code) if char_code >= 32 and char_code <= 126 else '.'
            except:
                line += '?'
        print(f"{y:2d}: {line[:80]}")  # Limit to 80 chars for readability
    
    # Test rendering just the player
    print(f"\n=== Testing player rendering in isolation ===")
    console2 = tcod.console.Console(120, 50)
    console2.clear()
    
    # Render player at specific position
    test_x, test_y = 10, 10
    console2.print(test_x, test_y, "@", (255, 255, 0))
    print(f"Rendered '@' at ({test_x}, {test_y})")
    
    # Check if it's there
    try:
        char_at_test = console2.ch[test_y, test_x]
        print(f"console2.ch[{test_y}, {test_x}] = {char_at_test} = {chr(char_at_test)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Check area around test position
    print(f"Area around ({test_x}, {test_y}):")
    for y in range(max(0, test_y - 2), min(console2.height, test_y + 3)):
        for x in range(max(0, test_x - 2), min(console2.width, test_x + 3)):
            try:
                char_code = console2.ch[y, x]
                char = chr(char_code) if char_code >= 32 and char_code <= 126 else '.'
                if x == test_x and y == test_y:
                    print(f"({x},{y}): [{char}]", end=" ")
                else:
                    print(f"({x},{y}): {char}", end=" ")
            except:
                print(f"({x},{y}): ?", end=" ")
        print()

if __name__ == "__main__":
    debug_player_rendering()