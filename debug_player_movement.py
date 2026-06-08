#!/usr/bin/env python3

import tcod
import numpy as np
import sys
import os

# Add the current directory to the path so we can import darkdelve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import darkdelve

def debug_player_movement():
    """Debug player movement to understand why player can't move"""
    
    # Create a game instance
    game = darkdelve.Game()
    game.initialize()
    game.new_game()
    
    print("=== DEBUG PLAYER MOVEMENT ===")
    print(f"Initial player position: ({game.player.x}, {game.player.y})")
    print(f"Player character: '{game.player.char}'")
    print(f"Dungeon map shape: {game.dungeon_map.shape}")
    print(f"Dungeon map[game.player.x, game.player.y]: {game.dungeon_map[game.player.x, game.player.y]}")
    
    # Check if player is in a wall
    if game.dungeon_map[game.player.x, game.player.y]:
        print("ERROR: Player is in a wall!")
        # Find the nearest walkable position
        for radius in range(1, 10):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    new_x, new_y = game.player.x + dx, game.player.y + dy
                    if (0 <= new_x < game.dungeon_map.shape[0] and
                        0 <= new_y < game.dungeon_map.shape[1] and
                        not game.dungeon_map[new_x, new_y]):
                        print(f"Found walkable position at ({new_x}, {new_y})")
                        # Move player to walkable position
                        game.player.x, game.player.y = new_x, new_y
                        print(f"Moved player to ({game.player.x}, {game.player.y})")
                        break
                else:
                    continue
                break
            else:
                continue
            break
    
    # Check what's around the player
    print(f"\nChecking area around player:")
    for y in range(max(0, game.player.y - 2), min(game.dungeon_map.shape[1], game.player.y + 3)):
        for x in range(max(0, game.player.x - 2), min(game.dungeon_map.shape[0], game.player.x + 3)):
            if x == game.player.x and y == game.player.y:
                print(f"({x},{y}): [{game.dungeon_map[x, y]}]", end=" ")
            else:
                print(f"({x},{y}): {game.dungeon_map[x, y]}", end=" ")
        print()
    
    # Test movement in different directions
    print(f"\n=== Testing movement ===")
    
    # Test moving to a nearby position
    test_positions = [
        (game.player.x + 1, game.player.y),  # Right
        (game.player.x - 1, game.player.y),  # Left
        (game.player.x, game.player.y + 1),  # Down
        (game.player.x, game.player.y - 1),  # Up
    ]
    
    for new_x, new_y in test_positions:
        if (0 <= new_x < game.dungeon_map.shape[0] and 
            0 <= new_y < game.dungeon_map.shape[1]):
            is_walkable = not game.dungeon_map[new_x, new_y]
            can_move = game.player.move_to(new_x, new_y, game.dungeon_map, game.entities)
            print(f"Move to ({new_x}, {new_y}): walkable={is_walkable}, can_move={can_move}")
        else:
            print(f"Move to ({new_x}, {new_y}): out of bounds")
    
    # Test the move_to method directly
    print(f"\n=== Testing move_to method directly ===")
    
    # Find a walkable position
    walkable_positions = []
    for x in range(game.dungeon_map.shape[0]):
        for y in range(game.dungeon_map.shape[1]):
            if not game.dungeon_map[x, y]:  # False means walkable (floor)
                walkable_positions.append((x, y))
    
    print(f"Found {len(walkable_positions)} walkable positions")
    
    # Try to move to the first walkable position
    if walkable_positions:
        target_x, target_y = walkable_positions[0]
        print(f"Trying to move to walkable position ({target_x}, {target_y})")
        print(f"Dungeon map[{target_x}, {target_y}]: {game.dungeon_map[target_x, target_y]}")
        
        # Check if position is occupied by entities
        position_occupied = any(e.x == target_x and e.y == target_y for e in game.entities)
        print(f"Position occupied by entities: {position_occupied}")
        
        # Try to move
        can_move = game.player.move_to(target_x, target_y, game.dungeon_map, game.entities)
        print(f"Can move to ({target_x}, {target_y}): {can_move}")
        
        if can_move:
            print(f"Player moved to: ({game.player.x}, {game.player.y})")
        else:
            print(f"Player could not move to ({target_x}, {target_y})")
    
    # Test with a simple case
    print(f"\n=== Testing simple case ===")
    
    # Create a simple 5x5 map
    simple_map = np.array([
        [False, False, False, False, False],  # Floor
        [False, False, False, False, False],  # Floor
        [False, False, False, False, False],  # Floor
        [False, False, False, False, False],  # Floor
        [False, False, False, False, False],  # Floor
    ], dtype=bool)
    
    # Create a simple player
    simple_player = darkdelve.Entity(x=2, y=2, char='@', color=(255, 255, 0), name="Test Player")
    
    print(f"Simple player position: ({simple_player.x}, {simple_player.y})")
    print(f"Simple map[2, 2]: {simple_map[2, 2]}")
    
    # Try to move
    can_move_simple = simple_player.move_to(3, 3, simple_map, [])
    print(f"Can move to (3, 3): {can_move_simple}")
    
    if can_move_simple:
        print(f"Simple player moved to: ({simple_player.x}, {simple_player.y})")
    else:
        print(f"Simple player could not move to (3, 3)")

if __name__ == "__main__":
    debug_player_movement()