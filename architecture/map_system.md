# DarkDelve Map System Architecture

## Overview

The DarkDelve Map System is a comprehensive roguelike dungeon generation and rendering system. This document outlines the architecture, components, and design patterns used.

## System Components

### 1. Dungeon Generation (`darkdelve.py:DungeonGenerator`)

**Purpose:** Generates procedurally-created dungeon levels using room-and-corridor algorithm.

**Key Methods:**
- `generate_level(depth, branch, theme)` - Main entry point for level creation
- `tunnel_between(start, end)` - Creates connecting passages between rooms

**Data Structures:**
- `dungeon_map: np.ndarray` - Boolean array where `True` = wall, `False` = floor
- `entities: List[Entity]` - List of entities spawned in the level
- `rooms: List[Tuple]` - Room coordinates and centers

**Coordinate System:**
- Dungeon maps are indexed as `dungeon_map[x, y]`
- `True` = wall (blocked)
- `False` = floor (walkable)

**IMPORTANT:** Map starts as all walls (ones), rooms/corridors are carved as floors (zeros)

### 2. Field of View System (`darkdelve.py:FOVSystem`)

**Purpose:** Computes visible tiles from a given position using raycasting.

**Key Methods:**
- `compute(dungeon_map, player_x, player_y)` - Returns FOV as boolean numpy array
- Tracks `explored` state for fog-of-war

**Algorithm:** Uses `tcod.map.compute_fov()` with `FOV_BASIC` algorithm

### 3. UI Rendering (`darkdelve.py:UI`)

**Purpose:** Renders the dungeon map, entities, and UI elements to the console.

**Key Methods:**
- `render_dungeon(dungeon_map, fov, explored, player)` - Renders map tiles
- `render_entities(entities, fov, player)` - Renders entities on map
- `render_ui(player, state, combat_log, turn, game)` - Renders status panel

**Camera System:**
- Centers on player position
- Clamps to map bounds
- Applies offset for screen coordinates

### 4. Entity Movement (`darkdelve.py:Entity`)

**Purpose:** Handles entity movement and collision detection.

**Key Methods:**
- `move_to(x, y, dungeon_map, entities)` - Move to absolute position
- `move(dx, dy, dungeon_map, entities)` - Move by delta
- `move_towards(target_x, target_y, dungeon_map, entities)` - Path towards target

**Collision Logic:**
- Checks dungeon_map for walls (`True` = blocked)
- Checks entity positions for blocking entities
- Returns `True` if movement successful, `False` otherwise

### 5. Pathfinding (`darkdelve.py:find_path`)

**Purpose:** A* pathfinding for AI movement.

**Algorithm:** Uses heapq-based A* with 8-directional movement

## Data Flow

```
1. Game Initialization
   └── DungeonGenerator.generate_level()
       └── Creates dungeon_map (numpy array)
       └── Spawns entities (monsters, items)
       └── Returns player_start position

2. Game Loop
   └── FOVSystem.compute() → fov array
   └── UI.render_dungeon() → console output
   └── UI.render_entities() → entity glyphs
   └── UI.render_ui() → status panel

3. Player Input
   └── InputHandler.handle_event()
       └── Entity.move_to() with collision check
       └── Update FOV
       └── Render frame
```

## Key Design Patterns

### 1. Boolean Map Convention
```python
# dungeon_map[x, y]
True  = wall (blocked)
False = floor (walkable)
```

### 2. Camera-Based Rendering
```python
screen_x = x - camera_x
screen_y = y - camera_y
```

### 3. Entity-Component Architecture
Entities have:
- Position (x, y)
- Visual properties (char, color)
- Game properties (hp, power, defense)
- Optional components (inventory, effects)

## Integration Points

### With AI System
- `PerceptionStatus` uses FOV to determine visibility
- `FOVSystem` provides visibility data to perception service

### With Combat System
- `CombatResolver` handles attack resolution
- `CombatLog` tracks combat events

### With Inventory System
- `Inventory` manages player items
- Items are entities with `item` attribute

## Testing Strategy

### Unit Tests
- `tests/test_map_rendering.py` - FOV and rendering tests
- `tests/test_tile_rendering.py` - Tile rendering tests
- `tests/test_dungeon_generator.py` - Dungeon generation tests

### Integration Tests
- `tests/test_game_logic.py` - Game flow tests
- `tests/test_entity_system.py` - Entity movement tests

## Known Issues & Solutions

### 1. Player Spawning in Walls
**Problem:** Player could spawn on wall tiles
**Solution:** Validate spawn position and find walkable alternative

### 2. FOV Coordinate System
**Problem:** tcod expects (row, col) but dungeon uses [x, y]
**Solution:** Pass FOV as (safe_x, safe_y) to maintain consistency

### 3. Entity Rendering Order
**Problem:** Items could overwrite player glyph
**Solution:** Render player after other entities

### 4. Dungeon Generation Inverted Logic (FIXED)
**Problem:** Rooms and corridors were being created as walls instead of floors
**Solution:** Start with all walls (ones), carve rooms/corridors as floors (zeros)

## Performance Considerations

1. **FOV Caching:** Explored state is cached and OR'd with new FOV
2. **Camera Clamping:** Prevents rendering outside map bounds
3. **Entity Filtering:** Only render entities in FOV or at player position

## Future Improvements

1. **Viewport Optimization:** Only render visible portion of map
2. **LOD Rendering:** Different detail levels for explored vs visible
3. **Dynamic Lighting:** Light sources affecting visibility
4. **Map Streaming:** Load/unload map sections for large dungeons