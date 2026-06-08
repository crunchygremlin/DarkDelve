#!/usr/bin/env python3

import tcod
import numpy as np
import sys
import os

# Add the current directory to the path so we can import darkdelve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import darkdelve

def debug_console_coordinates():
    """Debug console coordinate system to understand rendering vs reading mismatch"""
    
    # Initialize console
    console = tcod.console.Console(120, 50)
    
    print("=== CONSOLE COORDINATE DEBUG ===")
    print(f"Console dimensions: {console.width}x{console.height}")
    
    # Clear console
    console.clear()
    
    # Test rendering text at specific positions
    test_positions = [(0, 0), (10, 5), (20, 10), (30, 15), (40, 20), (50, 25)]
    test_texts = ["ORIG", "TEST", "COORD", "SYSTEM", "DEBUG", "END"]
    
    for i, (x, y) in enumerate(test_positions):
        console.print(x, y, test_texts[i], (255, 255, 0))
        print(f"Rendered '{test_texts[i]}' at ({x}, {y})")
    
    # Check what's actually in the console
    print("\n=== CONSOLE CONTENT ANALYSIS ===")
    
    # Look for our test characters
    for char_to_find in ['O', 'T', 'C', 'S', 'D', 'E']:
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
    
    # Print console content
    print("\n=== CONSOLE CONTENT ===")
    for y in range(console.height):
        line = ""
        for x in range(console.width):
            try:
                char_code = console.ch[x, y]
                line += chr(char_code) if char_code >= 32 and char_code <= 126 else '.'
            except:
                line += '?'
        print(f"{y:2d}: {line[:80]}")  # Limit to 80 chars for readability
    
    # Test without presenting (just reading)
    print("\n=== TESTING WITHOUT PRESENTING ===")
    
    # Create a new console and test
    console2 = tcod.console.Console(120, 50)
    console2.clear()
    
    # Render text at y=46 (where UI should be)
    console2.print(0, 46, "UI TEXT AT Y=46", (255, 255, 0))
    print(f"Rendered 'UI TEXT AT Y=46' at y=46")
    
    # Check console content
    ui_text_found = False
    for y in range(console2.height):
        for x in range(console2.width):
            try:
                char_code = console2.ch[x, y]
                if char_code == ord('U'):
                    ui_text_found = True
                    print(f"Found 'U' at ({x}, {y})")
            except:
                pass
    
    if ui_text_found:
        print("✓ UI text found in console")
    else:
        print("✗ UI text not found in console")
    
    # Test with a smaller console
    print("\n=== TESTING WITH SMALLER CONSOLE ===")
    console3 = tcod.console.Console(40, 20)
    console3.clear()
    
    # Render text at bottom of console
    console3.print(0, 18, "BOTTOM TEXT", (255, 255, 0))
    print(f"Rendered 'BOTTOM TEXT' at y=18 (bottom of 20-height console)")
    
    # Check console content
    for y in range(console3.height):
        line = ""
        for x in range(console3.width):
            try:
                char_code = console3.ch[x, y]
                line += chr(char_code) if char_code >= 32 and char_code <= 126 else '.'
            except:
                line += '?'
        print(f"{y:2d}: {line}")

if __name__ == "__main__":
    debug_console_coordinates()