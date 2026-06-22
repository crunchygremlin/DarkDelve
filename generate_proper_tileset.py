#!/usr/bin/env python3
"""
Generate a proper ASCII tileset for DarkDelve with correct character mappings.
This creates a tileset where each character is properly mapped to its ASCII code position.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_proper_ascii_tileset():
    """Create a proper ASCII tileset with correct character mappings"""
    
    print("=== Creating Proper ASCII Tileset ===")
    
    # Tileset configuration
    TILE_WIDTH = 10
    TILE_HEIGHT = 10
    FONT_SIZE = 8
    TILESET_WIDTH = 16  # 16 characters per row
    TILESET_HEIGHT = 16  # 16 rows of characters
    
    # Create a new image for the tileset
    tileset_width = TILE_WIDTH * TILESET_WIDTH
    tileset_height = TILE_HEIGHT * TILESET_HEIGHT
    image = Image.new('RGBA', (tileset_width, tileset_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, fall back to default if not available
    try:
        # Try to load the original DejaVu font
        font = ImageFont.truetype("assets/tilesets/dejavu10x10_gs_tc.png", FONT_SIZE)
        print("Using DejaVu font")
    except:
        try:
            # Try to load system font
            font = ImageFont.truetype("arial.ttf", FONT_SIZE)
            print("Using Arial font")
        except:
            try:
                # Try to load default font
                font = ImageFont.load_default()
                print("Using default font")
            except:
                print("No font available, using basic rendering")
    
    # Color palette for different character types
    colors = {
        'player': (255, 255, 0),      # Yellow
        'wall': (100, 100, 100),     # Gray
        'floor': (50, 50, 50),       # Dark gray
        'enemy': (255, 0, 0),        # Red
        'item': (0, 255, 0),         # Green
        'text': (255, 255, 255),     # White
        'ui': (200, 200, 200),       # Light gray
    }
    
    # Draw each character in its proper position
    char_index = 0
    for row in range(TILESET_HEIGHT):
        for col in range(TILESET_WIDTH):
            if char_index >= 256:  # 256 characters total (16x16)
                break
                
            # Calculate character and position
            char_code = char_index
            char = chr(char_code)
            
            x = col * TILE_WIDTH
            y = row * TILE_HEIGHT
            
            # Determine color based on character type
            if char == '@':
                color = colors['player']
            elif char in ['#', '█', '▓', '▒', '░']:
                color = colors['wall']
            elif char in ['.', ' ', '·']:
                color = colors['floor']
            elif char in ['g', 'D', '☠', '👑', '🔥', '🔮', '🧟', 'p']:
                color = colors['enemy']
            elif char in ['!', '?', '/', '[', ',', '=']:
                color = colors['item']
            else:
                color = colors['text']
            
            # Draw the character
            try:
                # Center the character in the tile
                draw.text((x + 1, y + 1), char, fill=color, font=font)
            except:
                # Fallback: draw a simple rectangle with the character
                draw.rectangle([x, y, x + TILE_WIDTH, y + TILE_HEIGHT], 
                              fill=color, outline=(255, 255, 255))
                draw.text((x + 2, y + 2), char, fill=(0, 0, 0))
            
            char_index += 1
    
    # Save the tileset
    output_path = "assets/tilesets/proper_ascii_tileset.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    image.save(output_path)
    print(f"Proper tileset saved to: {output_path}")
    
    # Create a character mapping file
    create_character_mapping()
    
    return output_path

def create_character_mapping():
    """Create a character mapping file for the tileset"""
    
    mapping = {
        'player': '@',
        'wall': ['#', '█', '▓', '▒', '░'],
        'floor': ['.', ' ', '·'],
        'enemy': ['g', 'D', '☠', '👑', '🔥', '🔮', '🧟', 'p'],
        'item': ['!', '?', '/', '[', ',', '='],
        'text': [chr(i) for i in range(33, 127)],  # All printable ASCII
        'ui': ['-', '_', '|', '═', '║', '╔', '╗', '╚', '╝', '╠', '╣', '╬', '╦', '╩']
    }
    
    mapping_path = "assets/tilesets/character_mapping.json"
    import json
    with open(mapping_path, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"Character mapping saved to: {mapping_path}")

def create_simple_test_scene():
    """Create a simple test scene to verify the tileset works"""
    
    print("\n=== Creating Simple Test Scene ===")
    
    # Create a simple test scene
    test_scene = [
        "##########",
        "#........#",
        "#.g......#",
        "#........#",
        "#....@...#",
        "#........#",
        "#...!....#",
        "#........#",
        "##########"
    ]
    
    # Create test image
    TILE_WIDTH = 10
    TILE_HEIGHT = 10
    scene_width = len(test_scene[0]) * TILE_WIDTH
    scene_height = len(test_scene) * TILE_HEIGHT
    
    test_image = Image.new('RGB', (scene_width, scene_height), (0, 0, 0))
    draw = ImageDraw.Draw(test_image)
    
    # Try to load the font
    try:
        font = ImageFont.truetype("assets/tilesets/proper_ascii_tileset.png", 8)
    except:
        try:
            font = ImageFont.truetype("arial.ttf", 8)
        except:
            try:
                font = ImageFont.load_default()
            except:
                print("No font available for testing")
                return
    
    # Draw the test scene
    for y, row in enumerate(test_scene):
        for x, char in enumerate(row):
            pixel_x = x * TILE_WIDTH
            pixel_y = y * TILE_HEIGHT
            
            # Choose color based on character
            if char == '#':
                color = (100, 100, 100)  # Wall - gray
            elif char == '.':
                color = (50, 50, 50)     # Floor - dark gray
            elif char == '@':
                color = (255, 255, 0)   # Player - yellow
            elif char in ['g', 'D']:
                color = (255, 0, 0)     # Enemy - red
            elif char == '!':
                color = (0, 255, 0)     # Item - green
            else:
                color = (255, 255, 255) # Text - white
            
            draw.text((pixel_x + 1, pixel_y + 1), char, fill=color, font=font)
    
    # Save test image
    test_path = "assets/tilesets/test_simple_scene.png"
    test_image.save(test_path)
    print(f"Simple test scene saved to: {test_path}")
    
    print("Simple test scene created successfully!")

def main():
    """Main function to create the proper tileset"""
    
    print("DarkDelve Proper ASCII Tileset Generator")
    print("=========================================")
    
    # Create the tileset
    tileset_path = create_proper_ascii_tileset()
    
    # Create a simple test scene
    create_simple_test_scene()
    
    print(f"\n=== Tileset Creation Complete ===")
    print(f"Main tileset: {tileset_path}")
    print(f"Test scene: assets/tilesets/test_simple_scene.png")
    print(f"Character mapping: assets/tilesets/character_mapping.json")
    
    print("\nNext steps:")
    print("1. Update the game configuration to use the new tileset")
    print("2. Test the game with the new tileset")
    print("3. Verify that the '@' character renders correctly")
    print("4. The tileset should now show actual characters, not character codes")

if __name__ == "__main__":
    main()