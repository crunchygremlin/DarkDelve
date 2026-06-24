"""Test that entities spawn inside the map boundaries."""

import numpy as np
from darkdelve import Game


def test_player_spawns_inside_map():
    """Test that player spawns on a walkable tile inside the map."""
    game = Game()
    game.initialize()
    
    # Player should be inside map bounds
    assert 0 <= game.player.x < game.dungeon_map.shape[0]
    assert 0 <= game.player.y < game.dungeon_map.shape[1]
    
    # Player should be on a floor tile (False = floor)
    assert not game.dungeon_map[game.player.x, game.player.y], \
        f"Player at ({game.player.x}, {game.player.y}) is on a wall!"
    
    print(f"Player spawned at ({game.player.x}, {game.player.y})")


def test_monsters_spawn_inside_map():
    """Test that monsters spawn on walkable tiles inside the map."""
    game = Game()
    game.initialize()
    
    for entity in game.entities:
        if entity is game.player:
            continue
        
        # Entity should be inside map bounds
        assert 0 <= entity.x < game.dungeon_map.shape[0], \
            f"Entity {entity.name} x={entity.x} out of bounds (width={game.dungeon_map.shape[0]})"
        assert 0 <= entity.y < game.dungeon_map.shape[1], \
            f"Entity {entity.name} y={entity.y} out of bounds (height={game.dungeon_map.shape[1]})"
        
        # Entity should be on a floor tile
        assert not game.dungeon_map[entity.x, entity.y], \
            f"Entity {entity.name} at ({entity.x}, {entity.y}) is on a wall!"
    
    print(f"All {len(game.entities) - 1} monsters spawn inside the map")


def test_items_spawn_inside_map():
    """Test that items spawn on walkable tiles inside the map."""
    game = Game()
    game.initialize()
    
    for entity in game.entities:
        if entity is game.player:
            continue
        if entity.blocks:  # Monsters block, items don't
            continue
        
        # Entity should be inside map bounds
        assert 0 <= entity.x < game.dungeon_map.shape[0]
        assert 0 <= entity.y < game.dungeon_map.shape[1]
        
        # Entity should be on a floor tile
        assert not game.dungeon_map[entity.x, entity.y], \
            f"Item {entity.name} at ({entity.x}, {entity.y}) is on a wall!"
    
    print(f"All items spawn inside the map")


def test_no_entities_on_walls():
    """Test that no entities are spawned on wall tiles."""
    game = Game()
    game.initialize()
    
    for entity in game.entities:
        if entity is game.player:
            continue
        
        # Check if entity is on a wall
        is_wall = game.dungeon_map[entity.x, entity.y]
        assert not is_wall, \
            f"Entity {entity.name} at ({entity.x}, {entity.y}) is on a wall!"
    
    print("No entities spawned on walls")


def test_entities_not_on_top_of_each_other():
    """Test that entities don't overlap."""
    game = Game()
    game.initialize()
    
    positions = {}
    for entity in game.entities:
        pos = (entity.x, entity.y)
        if pos in positions:
            # Only player and items can share positions
            other = positions[pos]
            assert not other.blocks or not entity.blocks, \
                f"Two blocking entities at {pos}: {other.name} and {entity.name}"
        positions[pos] = entity
    
    print(f"All {len(game.entities)} entities have valid positions")


if __name__ == "__main__":
    test_player_spawns_inside_map()
    test_monsters_spawn_inside_map()
    test_items_spawn_inside_map()
    test_no_entities_on_walls()
    test_entities_not_on_top_of_each_other()
    print("\nAll entity spawning tests passed!")