#!/usr/bin/env python3

import tcod
import numpy as np
import sys
import os

# Add the current directory to the path so we can import darkdelve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import darkdelve

def debug_console_content():
    # Create a simple game instance
    game = darkdelve.Game()
    game.initialize()
    game.new_game()
    
    # Render the game
    game.render()
    
    # Check renderer content
    if hasattr(game.renderer, '_console'):
        console = game.renderer._console
        print(f"Console dimensions: {console.width}x{console.height}")
        print(f"Player position: ({game.player.x}, {game.player.y})")
        print(f"Player character: '{game.player.char}'")
        
        # Check the console character array
        print("\nConsole character array (sample):")
        for y in range(min(10, console.height)):
            for x in range(min(20, console.width)):
                try:
                    char = console.ch[x, y]
                    print(f"[{x},{y}]: {char} ", end="")
                except Exception as e:
                    print(f"[{x},{y}]: ERROR ", end="")
            print()
        
        # Check if player character is at the expected position
        px, py = game.player.x, game.player.y
        if 0 <= px < console.width and 0 <= py < console.height:
            try:
                player_char_at_pos = console.ch[px, py]
                print(f"\nCharacter at player position ({px}, {py}): {player_char_at_pos}")
                print(f"Expected player character: {ord(game.player.char)}")
                print(f"Match: {player_char_at_pos == ord(game.player.char)}")
            except Exception as e:
                print(f"Error accessing player position: {e}")
        else:
            print(f"\nPlayer position ({px}, {py}) is out of console bounds")
    else:
        print("Console not available in current renderer")

if __name__ == "__main__":
    debug_console_content()