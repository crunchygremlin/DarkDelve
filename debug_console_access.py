#!/usr/bin/env python3

import tcod
import numpy as np
import sys
import os

def debug_console_access():
    """Debug console access patterns to understand coordinate system"""
    
    # Initialize console
    console = tcod.console.Console(40, 20)
    
    print("=== CONSOLE ACCESS DEBUG ===")
    print(f"Console dimensions: {console.width}x{console.height}")
    
    # Clear console
    console.clear()
    
    # Test 1: Render text at specific position
    print("\n=== TEST 1: Render at (5, 10) ===")
    console.print(5, 10, "HELLO", (255, 255, 0))
    print(f"Rendered 'HELLO' at (5, 10)")
    
    # Check different access patterns
    print("\nChecking different access patterns:")
    
    # Pattern 1: console.ch[x, y]
    try:
        char_at_5_10 = console.ch[5, 10]
        print(f"console.ch[5, 10] = {char_at_5_10} = {chr(char_at_5_10) if char_at_5_10 >= 32 else 'N/A'}")
    except Exception as e:
        print(f"console.ch[5, 10] failed: {e}")
    
    # Pattern 2: console.ch[y, x]
    try:
        char_at_10_5 = console.ch[10, 5]
        print(f"console.ch[10, 5] = {char_at_10_5} = {chr(char_at_10_5) if char_at_10_5 >= 32 else 'N/A'}")
    except Exception as e:
        print(f"console.ch[10, 5] failed: {e}")
    
    # Pattern 3: Check entire area around (5, 10)
    print("\nChecking area around (5, 10):")
    for y in range(8, 13):
        for x in range(3, 8):
            try:
                char_code = console.ch[x, y]
                char = chr(char_code) if char_code >= 32 and char_code <= 126 else '.'
                print(f"({x},{y}): {char}", end=" ")
            except:
                print(f"({x},{y}): ?", end=" ")
        print()
    
    # Test 2: Render at (0, 0) and (0, 19)
    print("\n=== TEST 2: Render at corners ===")
    console2 = tcod.console.Console(40, 20)
    console2.clear()
    
    # Render at top-left
    console2.print(0, 0, "TOP", (255, 255, 0))
    print(f"Rendered 'TOP' at (0, 0)")
    
    # Render at bottom-left
    console2.print(0, 19, "BOTTOM", (255, 255, 0))
    print(f"Rendered 'BOTTOM' at (0, 19)")
    
    # Check where characters are found
    print("\nFinding 'T' character:")
    for y in range(console2.height):
        for x in range(console2.width):
            try:
                char_code = console2.ch[x, y]
                if char_code == ord('T'):
                    print(f"Found 'T' at ({x}, {y})")
            except:
                pass
    
    print("\nFinding 'B' character:")
    for y in range(console2.height):
        for x in range(console2.width):
            try:
                char_code = console2.ch[x, y]
                if char_code == ord('B'):
                    print(f"Found 'B' at ({x}, {y})")
            except:
                pass
    
    # Test 3: Check console shape
    print(f"\n=== TEST 3: Console shape ===")
    print(f"console.ch.shape = {console.ch.shape}")
    print(f"console.width = {console.width}")
    print(f"console.height = {console.height}")
    
    # Test 4: Try different access methods
    print(f"\n=== TEST 4: Different access methods ===")
    console3 = tcod.console.Console(40, 20)
    console3.clear()
    console3.print(10, 5, "TEST", (255, 255, 0))
    
    # Method 1: Direct indexing
    try:
        char1 = console3.ch[10, 5]
        print(f"console3.ch[10, 5] = {char1} = {chr(char1)}")
    except:
        print("console3.ch[10, 5] failed")
    
    # Method 2: Flattened indexing
    try:
        flat_index = 5 * console3.width + 10
        char2 = console3.ch.flat[flat_index]
        print(f"console3.ch.flat[{flat_index}] = {char2} = {chr(char2)}")
    except:
        print(f"console3.ch.flat[{flat_index}] failed")
    
    # Method 3: Using numpy array
    try:
        char3 = np.array(console3.ch)[5, 10]
        print(f"np.array(console3.ch)[5, 10] = {char3} = {chr(char3)}")
    except:
        print("np.array(console3.ch)[5, 10] failed")

if __name__ == "__main__":
    debug_console_access()