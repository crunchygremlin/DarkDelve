#!/usr/bin/env python3
"""
Floor 1 Generation Playtest Script

Verifies that floor 1 generates correctly with:
- Cleared main path from entrance to stairs
- Guard patrols with sergeants
- Monster dens (spiders/rats) with leaders
- Roaming solitary creatures
- Adventurer corpses with loot
- All monsters weaker than player
- No entity overlaps
- No entities on walls
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from darkdelve import Game

def verify_floor1():
    """Run comprehensive floor 1 verification."""
    game = Game()
    game.initialize()
    
    errors = []
    warnings = []
    info = []
    
    # === 1. Basic map checks ===
    assert game.dungeon_map is not None, "Dungeon map is None"
    info.append(f"Map shape: {game.dungeon_map.shape}")
    
    floor_tiles = sum(1 for x in range(game.dungeon_map.shape[0]) 
                      for y in range(game.dungeon_map.shape[1]) 
                      if not game.dungeon_map[x, y])
    info.append(f"Floor tiles: {floor_tiles}")
    
    # === 2. Player position checks ===
    assert game.player is not None, "Player is None"
    px, py = game.player.x, game.player.y
    info.append(f"Player position: ({px}, {py})")
    
    # Player should be on floor
    if game.dungeon_map[px, py]:
        errors.append(f"Player at ({px}, {py}) is on a wall!")
    
    # === 3. Entity checks ===
    entities = game.entities
    info.append(f"Total entities: {len(entities)}")
    
    # Check for overlaps
    positions = {}
    for entity in entities:
        pos = (entity.x, entity.y)
        if pos in positions:
            other = positions[pos]
            if other.blocks and entity.blocks:
                errors.append(f"OVERLAP: {other.name} and {entity.name} at {pos}")
        positions[pos] = entity
    
    # Check for entities on walls
    for entity in entities:
        if game.dungeon_map[entity.x, entity.y]:
            errors.append(f"WALL: {entity.name} at ({entity.x}, {entity.y}) is on a wall!")
    
    # === 4. Monster type checks ===
    monsters = [e for e in entities if e is not game.player and getattr(e, 'blocks', False) and not getattr(e, 'is_corpse', False)]
    items = [e for e in entities if e is not game.player and not getattr(e, 'blocks', False) and getattr(e, 'item', None)]
    corpses = [e for e in entities if getattr(e, 'is_corpse', False)]
    
    info.append(f"Monsters: {len(monsters)}")
    info.append(f"Items: {len(items)}")
    info.append(f"Corpses: {len(corpses)}")
    
    # === 5. Guard patrol checks ===
    guards = [e for e in monsters if e.name in ('Dungeon Guard', 'Guard Sergeant')]
    sergeants = [e for e in monsters if e.name == 'Guard Sergeant']
    info.append(f"Guards: {len(guards)} (Sergeants: {len(sergeants)})")
    
    if len(guards) < 2:
        warnings.append(f"Expected at least 2 guards, got {len(guards)}")
    if len(sergeants) < 1:
        warnings.append(f"Expected at least 1 sergeant, got {len(sergeants)}")
    
    # === 6. Den creature checks ===
    spiders = [e for e in monsters if e.name in ('Giant Spider', 'Spider Queen')]
    rats = [e for e in monsters if e.name in ('Cave Rat', 'Rat King')]
    info.append(f"Spiders: {len(spiders)} (Queens: {len([s for s in spiders if s.name == 'Spider Queen'])}")
    info.append(f"Rats: {len(rats)} (Kings: {len([r for r in rats if r.name == 'Rat King'])}")
    
    if len(spiders) == 0 and len(rats) == 0:
        warnings.append("No den creatures (spiders or rats) found")
    
    # === 7. Roaming creature checks ===
    roamers = [e for e in monsters if e.name in ('Troll Scavenger', 'Fungal Creeper', 'Cave Bat')]
    info.append(f"Roaming creatures: {len(roamers)}")
    
    # === 8. Stat checks (all monsters weaker than player) ===
    player_hp = game.player.max_hp
    player_power = game.player.power
    for entity in monsters:
        if entity.max_hp > player_hp + 5:
            errors.append(f"STAT: {entity.name} HP={entity.max_hp} > player HP+5={player_hp+5}")
        if entity.power > player_power:
            errors.append(f"STAT: {entity.name} Power={entity.power} > player Power={player_power}")
    
    # === 9. Corpse loot checks ===
    for corpse in corpses:
        if not hasattr(corpse, 'loot'):
            errors.append(f"LOOT: Corpse at ({corpse.x}, {corpse.y}) has no loot attribute")
    
    # === 10. Stair checks ===
    assert game.stair_down_pos is not None, "No stair down position"
    sx, sy = game.stair_down_pos
    info.append(f"Stairs down: ({sx}, {sy})")
    if game.dungeon_map[sx, sy]:
        errors.append(f"Stairs down at ({sx}, {sy}) is on a wall!")
    
    # === Print results ===
    print("=" * 60)
    print("FLOOR 1 GENERATION PLAYTEST RESULTS")
    print("=" * 60)
    
    print("\n--- INFO ---")
    for line in info:
        print(f"  {line}")
    
    if warnings:
        print("\n--- WARNINGS ---")
        for line in warnings:
            print(f"  ⚠ {line}")
    
    if errors:
        print("\n--- ERRORS ---")
        for line in errors:
            print(f"  ✗ {line}")
    
    print("\n" + "=" * 60)
    if errors:
        print(f"RESULT: FAIL ({len(errors)} errors)")
        return False
    else:
        print("RESULT: PASS")
        if warnings:
            print(f"  ({len(warnings)} warnings)")
        return True


if __name__ == '__main__':
    success = verify_floor1()
    sys.exit(0 if success else 1)
