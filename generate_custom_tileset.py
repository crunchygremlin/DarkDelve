#!/usr/bin/env python3
"""
Generate a custom ASCII tileset for DarkDelve to fix character rendering issues.
This creates a simple tileset with proper glyphs for all game characters.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_custom_tileset():
    """Create a custom ASCII tileset with proper character rendering"""
    
    print("=== Creating Custom ASCII Tileset ===")
    
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
        font = ImageFont.truetype("assets/tilesets/dejavu10x10_gs_tc.png", FONT_SIZE)
        print("Using DejaVu font")
    except:
        try:
            font = ImageFont.load_default()
            print("Using default font")
        except:
            print("No font available, using basic rendering")
    
    # Define the characters we want to include in our tileset
    # ASCII characters 33-126 (printable ASCII)
    start_char = 33
    end_char = 126
    
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
    
    # Draw each character
    char_index = 0
    for row in range(TILESET_HEIGHT):
        for col in range(TILESET_WIDTH):
            if char_index >= end_char - start_char + 1:
                break
                
            # Calculate character and position
            char_code = start_char + char_index
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
                # Use the actual character, not the code
                draw.text((x + 1, y + 1), char, fill=color, font=font)
            except:
                # Fallback: draw a simple rectangle with the actual character
                draw.rectangle([x, y, x + TILE_WIDTH, y + TILE_HEIGHT],
                              fill=color, outline=(255, 255, 255))
                draw.text((x + 2, y + 2), char, fill=(0, 0, 0))
            
            char_index += 1
    
    # Save the tileset
    output_path = "assets/tilesets/custom_ascii_tileset.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    image.save(output_path)
    print(f"Custom tileset saved to: {output_path}")
    
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

def test_tileset():
    """Test the tileset by rendering a sample game scene"""
    
    print("\n=== Testing Custom Tileset ===")
    
    # Create a simple test scene
    test_scene = [
        "############",
        "#..........#",
        "#.g.......D.#",
        "#..........#",
        "#....@.....#",
        "#..........#",
        "#...!......#",
        "#..........#",
        "############"
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
        font = ImageFont.truetype("assets/tilesets/custom_ascii_tileset.png", 8)
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
    test_path = "assets/tilesets/test_scene.png"
    test_image.save(test_path)
    print(f"Test scene saved to: {test_path}")
    
    print("Test scene created successfully!")

def main():
    """Main function to create the custom tileset"""
    
    print("DarkDelve Custom Tileset Generator")
    print("===================================")
    
    # Create the tileset
    tileset_path = create_custom_tileset()
    
    # Test the tileset
    test_tileset()
    
    print(f"\n=== Tileset Creation Complete ===")
    print(f"Main tileset: {tileset_path}")
    print(f"Test scene: assets/tilesets/test_scene.png")
    print(f"Character mapping: assets/tilesets/character_mapping.json")
    
    print("\nNext steps:")
    print("1. Update the game configuration to use the new tileset")
    print("2. Test the game with the new tileset")
    print("3. Verify that the '@' character renders correctly")

if __name__ == "__main__":
    main()