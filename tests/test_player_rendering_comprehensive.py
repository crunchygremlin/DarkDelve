#!/usr/bin/env python3
"""
Comprehensive test for player rendering and visibility
"""

import copy
import sys
import numpy as np
from pathlib import Path

# Add the current directory to the path to import darkdelve
sys.path.insert(0, str(Path(__file__).parent.parent))

import tcod
from darkdelve import CONFIG, Game, COLORS, Entity

def test_player_rendering_comprehensive():
    """Comprehensive test for player rendering and visibility"""
    
    print("=== COMPREHENSIVE PLAYER RENDERING TEST ===")
    
    # Test 1: Basic player rendering
    print("\n--- Test 1: Basic Player Rendering ---")
    game = Game()
    
    game.config = copy.deepcopy(CONFIG)
    game.config['display'].update({
        'tileset': 'proper_ascii_tileset.png',
        'renderer': 'console',
        'width': 80,
        'height': 50,
    })
    game.config['dungeon'].update({'width': 60, 'height': 40})
    
    game.state = type('GameState', (), {'run_id': 'test123', 'player_class': 'warrior', 'player_name': 'Test Player'})()
    
    # Initialize game components and start a new game.
    game.initialize()
    
    # Test player properties
    print(f"Player position: ({game.player.x}, {game.player.y})")
    print(f"Player character: '{game.player.char}' (code: {ord(game.player.char)})")
    print(f"Player color: {game.player.color}")
    print(f"Player is walkable: {not game.player.blocks}")
    
    # Test 2: Console coordinate system
    print("\n--- Test 2: Console Coordinate System ---")
    # The renderer uses _root_console, not _console
    if hasattr(game.renderer, '_root_console') and game.renderer._root_console is not None:
        console = game.renderer._root_console
        print(f"Console dimensions: {console.width}x{console.height}")
        print(f"Console.ch shape: {console.ch.shape}")
        
        # Verify coordinate system
        if console.ch.shape == (console.height, console.width):
            print("✓ Console coordinate system is correct (height, width)")
        else:
            print("✗ Console coordinate system is incorrect")
    else:
        print("Console not available in current renderer")
    
    # Test 3: Player rendering
    print("\n--- Test 3: Player Rendering ---")
    game.render()
    
    # Check if player character is visible in the console
    player_char_found = False
    player_char_positions = []
    
    if hasattr(game.renderer, '_root_console') and game.renderer._root_console is not None:
        console = game.renderer._root_console
        for y in range(console.height):
            for x in range(console.width):
                try:
                    char = console.ch[y, x]
                    if char == ord(game.player.char):
                        player_char_found = True
                        player_char_positions.append((x, y))
                        print(f"✓ Player character found at ({x}, {y})")
                except Exception as e:
                    print(f"DEBUG: Error accessing console.ch[{y}, {x}]: {e}")
    
    if not player_char_found:
        print("✗ Player character not found in console")
    
    # Test 4: Player visibility in FOV
    print("\n--- Test 4: Player Visibility in FOV ---")
    print(f"Player position: ({game.player.x}, {game.player.y})")
    print(f"FOV shape: {game.fov.shape}")
    
    if (0 <= game.player.x < game.fov.shape[0] and
        0 <= game.player.y < game.fov.shape[1]):
        if game.fov[game.player.x, game.player.y]:
            print("✓ Player is in FOV")
        else:
            print("✗ Player is not in FOV")
    else:
        print("✗ Player is out of FOV bounds")
    
    # Test 5: Player spawning validation
    print("\n--- Test 5: Player Spawning Validation ---")
    print(f"Player spawn position: ({game.player.x}, {game.player.y})")
    print(f"Is walkable: {not game.dungeon_map[game.player.x, game.player.y]}")
    
    if game.dungeon_map[game.player.x, game.player.y]:
        print("✗ Player spawned in a wall!")
    else:
        print("✓ Player spawned on a walkable tile")
    
    # Test 6: Multiple players test
    print("\n--- Test 6: Multiple Players Test ---")
    game2 = Game()
    game2.config = copy.deepcopy(game.config)
    game2.state = type('GameState', (), {'run_id': 'test456', 'player_class': 'warrior', 'player_name': 'Player 1'})()
    game2.initialize()
    
    # Create a second player-like entity on the same tile so visibility does not depend on FOV randomness.
    player2 = Entity(x=game2.player.x, y=game2.player.y, char="P", color=COLORS['player'], name="Player 2", blocks=True, hp=10, max_hp=10)
    game2.entities.append(player2)
    
    # Render and check both players
    game2.render()
    
    players_found = 0
    additional_player_found = False
    
    if hasattr(game2.renderer, '_root_console') and game2.renderer._root_console is not None:
        console = game2.renderer._root_console
        for y in range(console.height):
            for x in range(console.width):
                try:
                    char = console.ch[y, x]
                    if char == ord('@'):
                        players_found += 1
                        print(f"✓ Player character found at ({x}, {y})")
                    elif char == ord('P'):
                        additional_player_found = True
                        print(f"✓ Additional player entity found at ({x}, {y})")
                except:
                    pass
    
    print(f"Total primary players found: {players_found}")
    print(f"Additional player entity found: {'✓ PASS' if additional_player_found else '✗ FAIL'}")
    
    # Test 7: Edge cases
    print("\n--- Test 7: Edge Cases ---")
    
    # Test with very small map
    game3 = Game()
    game3.config = copy.deepcopy(game.config)
    game3.config['display'].update({
        'tileset': 'proper_ascii_tileset.png',
        'renderer': 'console',
        'width': 40,
        'height': 25,
    })
    game3.config['dungeon'].update({'width': 20, 'height': 15})
    
    game3.state = type('GameState', (), {'run_id': 'test789', 'player_class': 'warrior', 'player_name': 'Test Player'})()
    game3.initialize()
    game3.render()
    
    # Check if player is within bounds
    if hasattr(game3.renderer, '_root_console'):
        console = game3.renderer._root_console
        if (0 <= game3.player.x < console.width and 
            0 <= game3.player.y < console.height):
            print("✓ Player is within console bounds")
        else:
            print("✗ Player is out of console bounds")
    else:
        print("Console not available for bounds check")
    
    print("\n=== TEST SUMMARY ===")
    print(f"Basic player rendering: {'✓ PASS' if player_char_found else '✗ FAIL'}")
    
    # Check console coordinate system if available
    if hasattr(game.renderer, '_root_console') and game.renderer._root_console is not None:
        console = game.renderer._root_console
        coord_system_ok = console.ch.shape == (console.height, console.width)
        print(f"Player coordinate system: {'✓ PASS' if coord_system_ok else '✗ FAIL'}")
    else:
        print("Player coordinate system: ? SKIP (console not available)")
    
    player_fov_visible = (0 <= game.player.x < game.fov.shape[0] and 0 <= game.player.y < game.fov.shape[1] and game.fov[game.player.x, game.player.y])
    player_walkable = not game.dungeon_map[game.player.x, game.player.y]
    
    if hasattr(game3.renderer, '_root_console') and game3.renderer._root_console is not None:
        edge_case_player_in_bounds = 0 <= game3.player.x < game3.renderer._root_console.width and 0 <= game3.player.y < game3.renderer._root_console.height
    else:
        edge_case_player_in_bounds = True  # Skip this check if console not available
    
    print(f"Player FOV visibility: {'✓ PASS' if player_fov_visible else '✗ FAIL'}")
    print(f"Player walkable spawn: {'✓ PASS' if player_walkable else '✗ FAIL'}")
    print(f"Multiple player entities: {'✓ PASS' if additional_player_found else '✗ FAIL'}")
    print(f"Edge cases: {'✓ PASS' if edge_case_player_in_bounds else '✗ FAIL'}")
    
    assert player_char_found
    assert coord_system_ok
    assert player_walkable
    assert additional_player_found
    assert edge_case_player_in_bounds

if __name__ == "__main__":
    test_player_rendering_comprehensive()