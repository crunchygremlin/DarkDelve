#!/usr/bin/env python3

import tcod
import numpy as np
import sys
import os

# Add the current directory to the path so we can import darkdelve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import darkdelve

def debug_ui_positioning():
    """Debug UI positioning to understand why text appears at wrong coordinates"""
    
    # Initialize console
    console = tcod.console.Console(120, 50)
    
    # Create a simple UI instance
    config = {
        'display': {'width': 120, 'height': 50},
        'dungeon': {'width': 80, 'height': 43}
    }
    
    ui = darkdelve.UI(console, config)
    
    print("=== UI POSITIONING DEBUG ===")
    print(f"Map width: {ui.map_width}")
    print(f"Map height: {ui.map_height}")
    print(f"UI Y position: {ui.ui_y}")
    print(f"Console dimensions: {console.width}x{console.height}")
    
    # Clear console
    console.clear()
    
    # Test rendering text at different positions
    print("\n=== Testing text rendering at different positions ===")
    
    # Test at UI position
    ui._render_text(0, ui.ui_y, "UI TEXT AT CORRECT POSITION", (255, 255, 0))
    print(f"Rendered 'UI TEXT AT CORRECT POSITION' at y={ui.ui_y}")
    
    # Test at y=0 (where text is actually appearing)
    ui._render_text(0, 0, "UI TEXT AT Y=0", (255, 0, 0))
    print(f"Rendered 'UI TEXT AT Y=0' at y=0")
    
    # Test at y=18 (where test expected it)
    ui._render_text(0, 18, "UI TEXT AT Y=18", (0, 255, 0))
    print(f"Rendered 'UI TEXT AT Y=18' at y=18")
    
    # Check what's actually in the console
    print("\n=== CONSOLE CONTENT ANALYSIS ===")
    
    # Check for specific characters
    for char_to_find in ['U', 'T', 'X']:  # Characters from our test text
        positions = []
        for y in range(console.height):
            for x in range(console.width):
                try:
                    char_code = console.ch[x, y]
                    if char_code == ord(char_to_find):
                        positions.append((x, y))
                except:
                    pass
        
        if positions:
            print(f"Character '{char_to_find}' found at: {positions}")
        else:
            print(f"Character '{char_to_find}' not found in console")
    
    # Print console content around key areas
    print("\n=== CONSOLE CONTENT SAMPLE ===")
    for y in range(0, min(25, console.height)):
        line = ""
        for x in range(0, min(80, console.width)):
            try:
                char_code = console.ch[x, y]
                line += chr(char_code) if char_code >= 32 and char_code <= 126 else '.'
            except:
                line += '?'
        print(f"{y:2d}: {line}")
    
    # Present the console to see what actually gets displayed
    print("\n=== Presenting console (this will show in a separate window) ===")
    tcod.context.new(width=console.width, height=console.height).present(console)
    
    # Wait for key press
    print("Press any key in the game window to continue...")
    tcod.console.wait_for_keypress(True)

if __name__ == "__main__":
    debug_ui_positioning()