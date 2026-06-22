#!/usr/bin/env python3
"""
Test the tileset directly to see what characters are actually being rendered.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image
import numpy as np

def test_tileset_content():
    """Test what the tileset actually contains"""
    
    print("=== TESTING TILESET CONTENT DIRECTLY ===")
    
    # Check if the tileset file exists
    tileset_path = "assets/tilesets/proper_ascii_tileset.png"
    if not os.path.exists(tileset_path):
        print(f"Tileset file not found: {tileset_path}")
        return
    
    # Load the tileset image
    try:
        tileset_image = Image.open(tileset_path)
        print(f"Tileset image loaded: {tileset_image.size}")
        print(f"Tileset mode: {tileset_image.mode}")
    except Exception as e:
        print(f"Error loading tileset: {e}")
        return
    
    # Convert to numpy array for analysis
    tileset_array = np.array(tileset_image)
    print(f"Tileset array shape: {tileset_array.shape}")
    
    # Tile configuration
    TILE_WIDTH = 10
    TILE_HEIGHT = 10
    TILESET_WIDTH = 16
    TILESET_HEIGHT = 16
    
    # Check specific characters
    test_chars = ['@', '#', '.', 'g', 'D', '!', '?']
    
    for char in test_chars:
        char_code = ord(char)
        row = char_code // TILESET_WIDTH
        col = char_code % TILESET_WIDTH
        
        x = col * TILE_WIDTH
        y = row * TILE_HEIGHT
        
        print(f"\n=== Character '{char}' (ASCII {char_code}) ===")
        print(f"Position in tileset: row={row}, col={col}")
        print(f"Pixel coordinates: x={x}, y={y}")
        
        # Extract the tile
        tile = tileset_array[y:y+TILE_HEIGHT, x:x+TILE_WIDTH]
        print(f"Tile shape: {tile.shape}")
        
        # Check if the tile has any non-zero pixels
        non_zero_pixels = np.any(tile != [0, 0, 0, 0])  # Check for non-transparent pixels
        print(f"Non-transparent pixels: {non_zero_pixels}")
        
        # Check the center pixel
        center_y = TILE_HEIGHT // 2
        center_x = TILE_WIDTH // 2
        center_pixel = tile[center_y, center_x]
        print(f"Center pixel (x={center_x}, y={center_y}): {center_pixel}")
        
        # Check all pixels in the tile
        colored_pixels = np.sum(tile, axis=2) > 0  # Sum RGB channels
        colored_count = np.sum(colored_pixels)
        print(f"Colored pixels in tile: {colored_count}/{TILE_WIDTH*TILE_HEIGHT}")
        
        if colored_count > 0:
            print("✓ Tile has content")
        else:
            print("✗ Tile is empty/transparent")

def test_simple_rendering():
    """Test simple rendering with the tileset"""
    
    print("\n=== TESTING SIMPLE RENDERING ===")
    
    # Create a simple test
    from PIL import Image, ImageDraw, ImageFont
    
    # Create a small test image
    test_image = Image.new('RGB', (50, 50), (0, 0, 0))
    draw = ImageDraw.Draw(test_image)
    
    # Try to draw the '@' character
    try:
        # Try different fonts
        fonts_to_try = [
            "assets/tilesets/proper_ascii_tileset.png",
            "arial.ttf",
            "dejavu10x10_gs_tc.png"
        ]
        
        font_found = False
        for font_path in fonts_to_try:
            try:
                font = ImageFont.truetype(font_path, 16)
                draw.text((10, 10), "@", fill=(255, 255, 0), font=font)
                print(f"✓ Successfully drew '@' with {font_path}")
                font_found = True
                break
            except:
                continue
        
        if not font_found:
            # Try default font
            try:
                font = ImageFont.load_default()
                draw.text((10, 10), "@", fill=(255, 255, 0), font=font)
                print("✓ Successfully drew '@' with default font")
                font_found = True
            except:
                print("✗ Could not draw '@' with any font")
        
        # Save the test image
        test_image.save("assets/tilesets/test_direct_render.png")
        print("Test image saved to: assets/tilesets/test_direct_render.png")
        
    except Exception as e:
        print(f"Error in simple rendering test: {e}")

def main():
    """Main function"""
    
    print("DarkDelve Tileset Direct Test")
    print("==============================")
    
    # Test tileset content
    test_tileset_content()
    
    # Test simple rendering
    test_simple_rendering()
    
    print("\n=== ANALYSIS ===")
    print("This test will help us understand:")
    print("1. What the tileset actually contains")
    print("2. Whether the '@' character is properly stored in the tileset")
    print("3. Whether we can render the character directly")
    print()
    print("If the tileset contains the correct characters, the issue might be in:")
    print("- How the game loads and uses the tileset")
    print("- Character-to-tile mapping in the game engine")
    print("- Font rendering configuration")

if __name__ == "__main__":
    main()