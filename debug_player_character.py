#!/usr/bin/env python3

import tcod
import numpy as np
import sys
import os

# Add the current directory to the path so we can import darkdelve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import darkdelve

def debug_player_character():
    """Debug player character symbol through rendering process"""
    
    print("=== INTERACTIVE PLAYER CHARACTER DEBUG ===")
    print("This will show you the player character symbol before and after rendering")
    print("You can tell me what it looks like!\n")
    
    # Create a game instance
    game = darkdelve.Game()
    game.initialize()
    game.new_game()
    
    print("--- BEFORE RENDERING ---")
    print(f"Player character data:")
    print(f"  Symbol: '{game.player.char}'")
    print(f"  Code (ord): {ord(game.player.char)}")
    print(f"  Color: {game.player.color}")
    print(f"  Position: ({game.player.x}, {game.player.y})")
    print(f"  Is walkable: {not game.dungeon_map[game.player.x, game.player.y]}")
    
    # Check what's in the console at player position before rendering
    try:
        if hasattr(game.renderer, '_console'):
            console = game.renderer._console
            char_before = console.ch[game.player.y, game.player.x]  # [y, x] not [x, y]
            print(f"  Console at player position: {char_before} = '{chr(char_before) if char_before >= 32 else 'N/A'}'")
        else:
            print("  Console not available in current renderer")
    except Exception as e:
        print(f"  Console access error: {e}")
    
    print("\n--- RENDERING ---")
    game.render()
    print("✓ Rendering completed")
    
    print("\n--- AFTER RENDERING ---")
    print(f"Player character data (should be same):")
    print(f"  Symbol: '{game.player.char}'")
    print(f"  Code (ord): {ord(game.player.char)}")
    print(f"  Color: {game.player.color}")
    print(f"  Position: ({game.player.x}, {game.player.y})")
    
    # Check what's in the console at player position after rendering
    try:
        if hasattr(game.renderer, '_console'):
            console = game.renderer._console
            char_after = console.ch[game.player.y, game.player.x]  # [y, x] not [x, y]
            print(f"  Console at player position: {char_after} = '{chr(char_after) if char_after >= 32 else 'N/A'}'")
            
            # Check if it matches
            if char_after == ord(game.player.char):
                print("  ✓ Console character matches player character")
            else:
                print("  ✗ Console character does NOT match player character")
        else:
            print("  Console not available in current renderer")
            
    except Exception as e:
        print(f"  Console access error: {e}")
    
    # Show area around player
    print(f"\n--- AREA AROUND PLAYER POSITION ({game.player.x}, {game.player.y}) ---")
    if hasattr(game.renderer, '_console'):
        console = game.renderer._console
        for y in range(max(0, game.player.y - 2), min(console.height, game.player.y + 3)):
            line = ""
            for x in range(max(0, game.player.x - 10), min(console.width, game.player.x + 11)):
                try:
                    char_code = console.ch[y, x]
                    char = chr(char_code) if char_code >= 32 and char_code <= 126 else '.'
                    if x == game.player.x and y == game.player.y:
                        line += f"[{char}]"  # Highlight player position
                    else:
                        line += f" {char} "
                except:
                    line += " ? "
        print(f"{y:2d}: {line}")
    
    # Show the actual console presentation
    print(f"\n--- CONSOLE PRESENTATION ---")
    print("The game window should now be visible.")
    print("Look at the player character and tell me what you see!")
    print("Press any key in the game window to continue...")
    
    # Present the console
    if hasattr(game.renderer, '_context') and hasattr(game.renderer, '_console'):
        game.renderer._context.present(game.renderer._console)
    elif hasattr(game.renderer, 'present'):
        game.renderer.present()
    
    print("\n--- FINAL QUESTIONS ---")
    print("1. What does the player character look like?")
    print("2. Is it the symbol '@' that we expect?")
    print("3. Is it visible and clear?")
    print("4. Does it look different from the surrounding tiles?")
    print("5. What color is it?")
    print("6. The game window should be visible - look at the player character!")

if __name__ == "__main__":
    debug_player_character()