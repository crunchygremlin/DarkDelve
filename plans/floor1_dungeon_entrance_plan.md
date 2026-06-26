# Floor 1: Dungeon Entrance - Implementation Plan

## Overview

Floor 1 is the dungeon entrance. It has:
- A **main path** (cleared) from entrance to stairs
- **Guard patrols** (groups of 2-3) walking the main path
- **Monster dens** in side rooms (spiders, rats) with loot from victims
- **Roaming scavengers** (solitary, not grouped)
- **Failed adventurer corpses** with items

All monsters are weaker than the starting player (HP <= 15, Power <= 3).

---

## Step 1: Create Monster Templates File

**New File**: `config/floor1_monsters.yaml`

Define all floor 1 monster types with stats. Keep stats LOW - weaker than player (player starts with HP 12-15, Power 5).

```yaml
# Floor 1 Monster Templates
# All monsters are weaker than starting player (HP <= 15, Power <= 3)

floor1_monsters:
  # === GUARD SQUAD (from lower levels, patrol in groups) ===
  dungeon_guard:
    name: "Dungeon Guard"
    symbol: "g"
    color: [100, 150, 200]
    hp: 8
    power: 2
    defense: 1
    speed: 60
    ai_type: "patrol"
    role: "guard"
    loyalty: 0.35
    group_size: [2, 3]
    
  guard_sergeant:
    name: "Guard Sergeant"
    symbol: "s"
    color: [120, 170, 220]
    hp: 12
    power: 3
    defense: 2
    speed: 55
    ai_type: "tactical"
    role: "leader"
    loyalty: 0.4
    commands: ["dungeon_guard"]
    
  # === DEN CREATURES (territorial, fear guards, collect loot) ===
  giant_spider:
    name: "Giant Spider"
    symbol: "x"
    color: [80, 80, 80]
    hp: 6
    power: 2
    defense: 0
    speed: 70
    ai_type: "ambush"
    role: "worker"
    loyalty: 1.0
    fears_guards: true
    loot_behavior: "collect"
    
  spider_queen:
    name: "Spider Queen"
    symbol: "X"
    color: [100, 50, 50]
    hp: 15
    power: 3
    defense: 1
    speed: 50
    ai_type: "hive_leader"
    role: "leader"
    loyalty: 1.0
    commands: ["giant_spider"]
    fears_guards: true
    
  cave_rat:
    name: "Cave Rat"
    symbol: "r"
    color: [139, 90, 43]
    hp: 3
    power: 1
    defense: 0
    speed: 90
    ai_type: "swarm"
    role: "minion"
    loyalty: 0.8
    fears_guards: true
    group_size: [3, 5]
    
  rat_king:
    name: "Rat King"
    symbol: "R"
    color: [160, 100, 50]
    hp: 8
    power: 2
    defense: 0
    speed: 80
    ai_type: "pack_leader"
    role: "leader"
    loyalty: 0.85
    commands: ["cave_rat"]
    fears_guards: true
    
  # === SCAVENGER & FORAGERS (solitary, not grouped) ===
  troll_scavenger:
    name: "Troll Scavenger"
    symbol: "T"
    color: [100, 150, 100]
    hp: 10
    power: 3
    defense: 1
    speed: 45
    ai_type: "scavenger"
    role: "solitary"
    loyalty: 0.0
    collects_items: true
    
  fungal_creeper:
    name: "Fungal Creeper"
    symbol: "f"
    color: [50, 100, 50]
    hp: 4
    power: 1
    defense: 0
    speed: 30
    ai_type: "stationary"
    role: "solitary"
    loyalty: 0.0
    
  cave_bat:
    name: "Cave Bat"
    symbol: "b"
    color: [60, 60, 80]
    hp: 4
    power: 1
    defense: 0
    speed: 120
    ai_type: "erratic"
    role: "solitary"
    loyalty: 0.0
```

---

## Step 2: Create Floor 1 Generator

**New File**: `src/application/services/floor1_generator.py`

This generates the dungeon map with:
1. Main path (clear) from top to stairs at bottom
2. Side rooms branching off main path
3. Guard patrol routes along main path
4. Monster dens in side rooms
5. Roaming creatures scattered

```python
"""
Floor 1 Generator - Dungeon Entrance Level

Generates floor 1 with:
- Cleared main path from entrance to stairs
- Guard patrols along main path
- Monster dens in side rooms
- Roaming solitary scavengers
"""

import random
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Den:
    """A monster den in a side room."""
    center: Tuple[int, int]
    radius: int
    creature_type: str
    count: int
    loot_items: List[Any] = field(default_factory=list)
    guard_kills: int = 0


@dataclass
class PatrolRoute:
    """A guard patrol route along the main path."""
    waypoints: List[Tuple[int, int]]
    guard_types: List[str]
    current_waypoint: int = 0


@dataclass
class Floor1Data:
    """All data needed for floor 1."""
    dungeon_map: np.ndarray
    entrance: Tuple[int, int]
    stair_down: Tuple[int, int]
    main_path: List[Tuple[int, int]]
    dens: List[Den]
    patrol_routes: List[PatrolRoute]
    roaming_spawns: List[Tuple[int, int, str]]  # x, y, creature_type
    corpses: List[Tuple[int, int]]  # positions for adventurer corpses


class Floor1Generator:
    """Generates the dungeon entrance level."""
    
    def __init__(self, config: dict):
        self.config = config
        self.width = config['dungeon']['width']
        self.height = config['dungeon']['height']
        self.floor1_config = config.get('floor1', {})
        
    def generate(self) -> Floor1Data:
        """Generate complete floor 1 data."""
        # Create base map (all walls)
        dungeon_map = np.ones((self.width, self.height), dtype=bool)
        
        # Generate main path (vertical corridor, 3 wide)
        entrance, stair_down, main_path = self._generate_main_path(dungeon_map)
        
        # Generate side rooms branching from main path
        side_rooms = self._generate_side_rooms(dungeon_map, main_path)
        
        # Place dens in side rooms
        dens = self._place_dens(side_rooms)
        
        # Create patrol routes along main path
        patrol_routes = self._create_patrol_routes(main_path)
        
        # Place roaming creature spawns (away from main path)
        roaming_spawns = self._place_roaming_spawns(dungeon_map, main_path)
        
        # Place adventurer corpse positions
        corpses = self._place_corpses(dungeon_map, dens)
        
        return Floor1Data(
            dungeon_map=dungeon_map,
            entrance=entrance,
            stair_down=stair_down,
            main_path=main_path,
            dens=dens,
            patrol_routes=patrol_routes,
            roaming_spawns=roaming_spawns,
            corpses=corpses,
        )
    
    def _generate_main_path(self, dungeon_map: np.ndarray) -> Tuple[Tuple[int, int], Tuple[int, int], List[Tuple[int, int]]]:
        """Generate the cleared main path from entrance to stairs."""
        path_width = self.floor1_config.get('main_path_width', 3)
        
        # Entrance at top center
        entrance_x = self.width // 2
        entrance_y = 2
        
        # Stairs at bottom center
        stair_x = self.width // 2
        stair_y = self.height - 3
        
        # Carve main path
        main_path = []
        for y in range(entrance_y, stair_y + 1):
            for dx in range(-path_width // 2, path_width // 2 + 1):
                x = entrance_x + dx
                if 0 <= x < self.width and 0 <= y < self.height:
                    dungeon_map[x, y] = False  # False = floor
                    main_path.append((x, y))
        
        return (entrance_x, entrance_y), (stair_x, stair_y), main_path
    
    def _generate_side_rooms(self, dungeon_map: np.ndarray, main_path: List[Tuple[int, int]]) -> List[Dict]:
        """Generate side rooms branching from main path."""
        room_count = self.floor1_config.get('den_count', 4)
        side_rooms = []
        
        for _ in range(room_count):
            # Pick a random point on main path (not at ends)
            if len(main_path) < 10:
                break
            path_idx = random.randint(len(main_path) // 4, 3 * len(main_path) // 4)
            branch_x, branch_y = main_path[path_idx]
            
            # Random side (left or right)
            direction = random.choice([-1, 1])
            
            # Room dimensions
            room_w = random.randint(4, 7)
            room_h = random.randint(4, 6)
            
            # Room position (offset from main path)
            room_x = branch_x + direction * (room_w // 2 + 1)
            room_y = branch_y - room_h // 2
            
            # Clamp to map bounds
            room_x = max(1, min(room_x, self.width - room_w - 1))
            room_y = max(1, min(room_y, self.height - room_h - 1))
            
            # Carve room
            for x in range(room_x, room_x + room_w):
                for y in range(room_y, room_y + room_h):
                    if 0 <= x < self.width and 0 <= y < self.height:
                        dungeon_map[x, y] = False
            
            # Carve corridor from main path to room
            corridor_x = branch_x
            while corridor_x != room_x + room_w // 2:
                dungeon_map[corridor_x, branch_y] = False
                corridor_x += 1 if room_x > branch_x else -1
            
            side_rooms.append({
                'x': room_x, 'y': room_y,
                'w': room_w, 'h': room_h,
                'center': (room_x + room_w // 2, room_y + room_h // 2),
            })
        
        return side_rooms
    
    def _place_dens(self, side_rooms: List[Dict]) -> List[Den]:
        """Place monster dens in side rooms."""
        dens = []
        den_types = ['spider', 'rat']
        
        for i, room in enumerate(side_rooms):
            den_type = den_types[i % len(den_types)]
            
            if den_type == 'spider':
                count = random.randint(2, 4)
                creature_type = 'giant_spider'
            else:  # rat
                count = random.randint(3, 5)
                creature_type = 'cave_rat'
            
            dens.append(Den(
                center=room['center'],
                radius=max(room['w'], room['h']) // 2,
                creature_type=creature_type,
                count=count,
            ))
        
        return dens
    
    def _create_patrol_routes(self, main_path: List[Tuple[int, int]]) -> List[PatrolRoute]:
        """Create guard patrol routes along main path."""
        patrol_count = self.floor1_config.get('guard_patrol_count', 3)
        routes = []
        
        # Divide main path into segments
        segment_size = len(main_path) // patrol_count
        
        for i in range(patrol_count):
            start_idx = i * segment_size
            end_idx = min((i + 1) * segment_size, len(main_path) - 1)
            
            # Get waypoints along this segment
            waypoints = [
                main_path[idx] 
                for idx in range(start_idx, end_idx, max(1, (end_idx - start_idx) // 3))
            ]
            
            if len(waypoints) >= 2:
                routes.append(PatrolRoute(
                    waypoints=waypoints,
                    guard_types=['dungeon_guard'],
                ))
        
        return routes
    
    def _place_roaming_spawns(self, dungeon_map: np.ndarray, main_path: List[Tuple[int, int]]) -> List[Tuple[int, int, str]]:
        """Place roaming creature spawn points away from main path."""
        roaming_count = self.floor1_config.get('roaming_creature_count', 5)
        main_path_set = set(main_path)
        spawns = []
        
        creature_types = ['troll_scavenger', 'cave_bat', 'fungal_creeper']
        
        attempts = 0
        while len(spawns) < roaming_count and attempts < 100:
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            
            # Must be floor and not on main path
            if not dungeon_map[x, y] and (x, y) not in main_path_set:
                # Check distance from main path
                min_dist = min(abs(x - px) + abs(y - py) for px, py in main_path)
                if min_dist > 5:  # At least 5 tiles from main path
                    creature_type = random.choice(creature_types)
                    spawns.append((x, y, creature_type))
            
            attempts += 1
        
        return spawns
    
    def _place_corpses(self, dungeon_map: np.ndarray, dens: List[Den]) -> List[Tuple[int, int]]:
        """Place adventurer corpse positions in/near dens."""
        corpse_chance = self.floor1_config.get('corpse_chance', 0.5)
        corpses = []
        
        for den in dens:
            if random.random() < corpse_chance:
                # Place corpse near den center
                cx, cy = den.center
                offset_x = random.randint(-den.radius, den.radius)
                offset_y = random.randint(-den.radius, den.radius)
                corpse_x = cx + offset_x
                corpse_y = cy + offset_y
                
                if (0 <= corpse_x < self.width and 0 <= corpse_y < self.height
                        and not dungeon_map[corpse_x, corpse_y]):
                    corpses.append((corpse_x, corpse_y))
        
        return corpses
```

---

## Step 3: Create Floor 1 Entity Spawner

**New File**: `src/application/services/floor1_spawner.py`

Spawns entities based on Floor1Data from the generator.

```python
"""
Floor 1 Entity Spawner

Spawns all entities for floor 1 based on Floor1Data.
"""

import random
from typing import List, Tuple, Optional
import numpy as np

from darkdelve import Entity, COLORS, MobTier, Item, ItemType


# Monster stats from floor1_monsters.yaml (hardcoded for simplicity)
MONSTER_TEMPLATES = {
    'dungeon_guard': {
        'name': 'Dungeon Guard', 'symbol': 'g', 'color': (100, 150, 200),
        'hp': 8, 'power': 2, 'defense': 1, 'speed': 60,
    },
    'guard_sergeant': {
        'name': 'Guard Sergeant', 'symbol': 's', 'color': (120, 170, 220),
        'hp': 12, 'power': 3, 'defense': 2, 'speed': 55,
    },
    'giant_spider': {
        'name': 'Giant Spider', 'symbol': 'x', 'color': (80, 80, 80),
        'hp': 6, 'power': 2, 'defense': 0, 'speed': 70,
    },
    'spider_queen': {
        'name': 'Spider Queen', 'symbol': 'X', 'color': (100, 50, 50),
        'hp': 15, 'power': 3, 'defense': 1, 'speed': 50,
    },
    'cave_rat': {
        'name': 'Cave Rat', 'symbol': 'r', 'color': (139, 90, 43),
        'hp': 3, 'power': 1, 'defense': 0, 'speed': 90,
    },
    'rat_king': {
        'name': 'Rat King', 'symbol': 'R', 'color': (160, 100, 50),
        'hp': 8, 'power': 2, 'defense': 0, 'speed': 80,
    },
    'troll_scavenger': {
        'name': 'Troll Scavenger', 'symbol': 'T', 'color': (100, 150, 100),
        'hp': 10, 'power': 3, 'defense': 1, 'speed': 45,
    },
    'fungal_creeper': {
        'name': 'Fungal Creeper', 'symbol': 'f', 'color': (50, 100, 50),
        'hp': 4, 'power': 1, 'defense': 0, 'speed': 30,
    },
    'cave_bat': {
        'name': 'Cave Bat', 'symbol': 'b', 'color': (60, 60, 80),
        'hp': 4, 'power': 1, 'defense': 0, 'speed': 120,
    },
}


class Floor1Spawner:
    """Spawns entities for floor 1."""
    
    def __init__(self, player: Entity, config: dict):
        self.player = player
        self.config = config
    
    def spawn_all(self, floor1_data, roster) -> List[Entity]:
        """Spawn all entities for floor 1."""
        entities = []
        
        # Spawn guard patrols
        entities.extend(self._spawn_guard_patrols(floor1_data))
        
        # Spawn den creatures
        entities.extend(self._spawn_den_creatures(floor1_data))
        
        # Spawn roaming creatures
        entities.extend(self._spawn_roaming(floor1_data))
        
        # Spawn corpses with loot
        entities.extend(self._spawn_corpses(floor1_data))
        
        return entities
    
    def _spawn_guard_patrols(self, floor1_data) -> List[Entity]:
        """Spawn guard patrol groups."""
        entities = []
        
        for route in floor1_data.patrol_routes:
            if not route.waypoints:
                continue
            
            # Spawn 2-3 guards at first waypoint
            count = random.randint(2, 3)
            start_x, start_y = route.waypoints[0]
            
            for i in range(count):
                offset_x = random.randint(-1, 1)
                offset_y = random.randint(-1, 1)
                x = start_x + offset_x
                y = start_y + offset_y
                
                # First guard is sergeant, rest are regular
                template_key = 'guard_sergeant' if i == 0 else 'dungeon_guard'
                template = MONSTER_TEMPLATES[template_key]
                
                entity = self._create_monster_entity(template, x, y)
                entity.is_commander = (i == 0)  # Sergeant commands
                entities.append(entity)
        
        return entities
    
    def _spawn_den_creatures(self, floor1_data) -> List[Entity]:
        """Spawn creatures in dens."""
        entities = []
        
        for den in floor1_data.dens:
            cx, cy = den.center
            
            for i in range(den.count):
                # Random position within den radius
                angle = random.uniform(0, 2 * 3.14159)
                dist = random.randint(0, max(1, den.radius - 1))
                x = int(cx + dist * np.cos(angle))
                y = int(cy + dist * np.sin(angle))
                
                # Clamp to map bounds
                x = max(1, min(x, self.config['dungeon']['width'] - 2))
                y = max(1, min(y, self.config['dungeon']['height'] - 2))
                
                # First creature is leader (queen/king), rest are minions
                if i == 0 and den.creature_type == 'giant_spider':
                    template_key = 'spider_queen'
                elif i == 0 and den.creature_type == 'cave_rat':
                    template_key = 'rat_king'
                else:
                    template_key = den.creature_type
                
                template = MONSTER_TEMPLATES[template_key]
                entity = self._create_monster_entity(template, x, y)
                entity.home_position = (x, y)  # Stay near den
                entities.append(entity)
        
        return entities
    
    def _spawn_roaming(self, floor1_data) -> List[Entity]:
        """Spawn roaming solitary creatures."""
        entities = []
        
        for x, y, creature_type in floor1_data.roaming_spawns:
            template = MONSTER_TEMPLATES[creature_type]
            entity = self._create_monster_entity(template, x, y)
            entities.append(entity)
        
        return entities
    
    def _spawn_corpses(self, floor1_data) -> List[Entity]:
        """Spawn adventurer corpses with loot."""
        entities = []
        
        for x, y in floor1_data.corpses:
            corpse = Entity(
                x=x, y=y,
                char='%', color=(150, 100, 100),
                name="Adventurer's Remains",
                blocks=False,
                hp=1, max_hp=1, power=0, defense=0,
                speed=0, intel_tier=0,
            )
            corpse.is_corpse = True
            corpse.loot = self._generate_corpse_loot()
            entities.append(corpse)
        
        return entities
    
    def _create_monster_entity(self, template: dict, x: int, y: int) -> Entity:
        """Create a monster entity from template."""
        # Scale speed relative to player (player speed = 100)
        player_speed = self.player.speed if self.player else 100
        monster_speed = max(1, int(player_speed * template.get('speed', 60) / 100))
        
        entity = Entity(
            x=x, y=y,
            char=template['symbol'],
            color=template['color'],
            name=template['name'],
            blocks=True,
            hp=template['hp'],
            max_hp=template['hp'],
            power=template['power'],
            defense=template['defense'],
            speed=monster_speed,
            intel_tier=1,
        )
        return entity
    
    def _generate_corpse_loot(self) -> List[Item]:
        """Generate random loot for a corpse."""
        loot = []
        
        # 50% chance of gold
        if random.random() < 0.5:
            gold_item = Item(
                id=f"gold_{random.randint(1000, 9999)}",
                name="Gold Coins",
                item_type=ItemType.MISC,
                symbol='$',
                value=random.randint(5, 20),
            )
            loot.append(gold_item)
        
        # 30% chance of potion
        if random.random() < 0.3:
            potion = Item(
                id=f"potion_{random.randint(1000, 9999)}",
                name="Healing Potion",
                item_type=ItemType.POTION,
                symbol='!',
                special_effect="heal",
                effect_strength=10,
                value=25,
            )
            loot.append(potion)
        
        # 20% chance of weapon
        if random.random() < 0.2:
            weapons = [
                Item("Rusty Sword", "rusty_sword", ItemType.WEAPON, "/", 
                     damage_bonus=1, value=10),
                Item("Wooden Club", "wooden_club", ItemType.WEAPON, '/', 
                     damage_bonus=1, value=8),
            ]
            loot.append(random.choice(weapons))
        
        return loot
```

---

## Step 4: Modify Game.generate_level()

**File**: `darkdelve.py` (around line 1984)

Add conditional logic at the start of `generate_level()`:

```python
def generate_level(self, depth: int, branch: str):
    self.state.depth = depth
    self.state.branch = branch
    
    # Use specialized floor 1 generator for entrance level
    if depth == 1:
        self._generate_floor1()
    else:
        self._generate_standard_level(depth, branch)
```

Then add the `_generate_floor1()` method to the Game class:

```python
def _generate_floor1(self):
    """Generate floor 1 (dungeon entrance) with specialized layout."""
    from src.application.services.floor1_generator import Floor1Generator
    from src.application.services.floor1_spawner import Floor1Spawner
    
    # Generate floor data
    floor1_gen = Floor1Generator(self.config)
    floor1_data = floor1_gen.generate()
    
    # Apply map
    self.dungeon_map = floor1_data.dungeon_map
    self.stair_down_pos = floor1_data.stair_down
    self.stair_up_pos = floor1_data.entrance  # Go back up = entrance
    
    # Place player at entrance
    self.player.x, self.player.y = floor1_data.entrance
    self.player.home_position = floor1_data.entrance
    
    # Spawn entities
    spawner = Floor1Spawner(self.player, self.config)
    self.entities = [self.player]
    self.entities.extend(spawner.spawn_all(floor1_data, None))
    
    # Generate minimal items (most loot is in dens)
    items = self.content_generator.generate_items("martial", 5)
    for item in items:
        for _ in range(20):
            x = random.randint(1, self.dungeon_map.shape[0] - 2)
            y = random.randint(1, self.dungeon_map.shape[1] - 2)
            # Only place on floor, not on entities, and not on main path
            main_path_set = set(floor1_data.main_path)
            if (not self.dungeon_map[x, y] 
                    and not any(e.x == x and e.y == y for e in self.entities)
                    and (x, y) not in main_path_set):
                entity = Entity(
                    x=x, y=y,
                    char=item.symbol, color=COLORS['item'],
                    name=item.name, blocks=False,
                    hp=1, max_hp=1, power=0, defense=0,
                    speed=0, intel_tier=0,
                )
                entity.item = item
                self.entities.append(entity)
                break
    
    # Initialize energy system
    self.energy_system = EnergySystem()
    for entity in self.entities:
        initial_energy = 100 if entity is self.player else 0
        self.energy_system.add_entity(entity, initial_energy=initial_energy)
    
    # Initialize FOV
    self.fov = self.fov_system.compute(self.dungeon_map, self.player.x, self.player.y)
    self.explored = self.fov_system.explored.copy()
    
    self.add_message("You enter the dungeon entrance. The air smells of damp stone and something rotten.")
```

And refactor the existing generation into `_generate_standard_level()`:

```python
def _generate_standard_level(self, depth: int, branch: str):
    """Generate standard dungeon level (depth > 1)."""
    # Generate theme
    self.current_theme = self.content_generator.generate_level_theme(depth, branch)
    self.add_message(f"Entering {self.current_theme.name}: {self.current_theme.description}")
    
    # Generate dungeon
    self.dungeon_map, _, player_start, stair_down, stair_up = self.dungeon_generator.generate_level(depth, branch, self.current_theme)
    self.stair_down_pos = stair_down
    self.stair_up_pos = stair_up
    
    # ... (rest of existing generate_level code from lines 2000-2116)
```

---

## Step 5: Add Floor 1 Config

**File**: `config/game.yaml`

Add floor1 section:

```yaml
floor1:
  corpse_chance: 0.5
  guard_patrol_count: 3
  den_count: 4
  roaming_creature_count: 5
  main_path_width: 3
  guard_group_size: [2, 3]
  den_group_size: [2, 4]
```

---

## Step 6: Add Tests

**New File**: `tests/test_floor1_generator.py`

```python
"""Tests for floor 1 generation."""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from src.application.services.floor1_generator import Floor1Generator, Floor1Data
from src.application.services.floor1_spawner import Floor1Spawner, MONSTER_TEMPLATES


@pytest.fixture
def config():
    return {
        'dungeon': {'width': 60, 'height': 40},
        'floor1': {
            'corpse_chance': 0.5,
            'guard_patrol_count': 3,
            'den_count': 4,
            'roaming_creature_count': 5,
            'main_path_width': 3,
        }
    }


class TestFloor1Generator:
    
    def test_generate_returns_floor1_data(self, config):
        gen = Floor1Generator(config)
        data = gen.generate()
        assert isinstance(data, Floor1Data)
    
    def test_main_path_is_clear(self, config):
        gen = Floor1Generator(config)
        data = gen.generate()
        
        # All positions in main path should be floor (False)
        for x, y in data.main_path:
            assert data.dungeon_map[x, y] == False
    
    def test_entrance_and_stairs_exist(self, config):
        gen = Floor1Generator(config)
        data = gen.generate()
        
        assert data.entrance is not None
        assert data.stair_down is not None
        assert data.entrance != data.stair_down
    
    def test_dens_placed(self, config):
        gen = Floor1Generator(config)
        data = gen.generate()
        
        assert len(data.dens) > 0
        assert len(data.dens) <= config['floor1']['den_count']
    
    def test_patrol_routes_created(self, config):
        gen = Floor1Generator(config)
        data = gen.generate()
        
        assert len(data.patrol_routes) > 0
    
    def test_stairs_reachable(self, config):
        """Verify path exists from entrance to stairs."""
        gen = Floor1Generator(config)
        data = gen.generate()
        
        # Import pathfinding
        from darkdelve import find_path
        
        path = find_path(data.entrance, data.stair_down, data.dungeon_map, [])
        assert len(path) > 1  # Should have actual path


class TestFloor1Spawner:
    
    @pytest.fixture
    def mock_player(self):
        player = MagicMock()
        player.speed = 100
        player.x = 30
        player.y = 2
        return player
    
    def test_spawn_all_returns_entities(self, mock_player, config):
        from src.application.services.floor1_generator import Floor1Generator
        
        gen = Floor1Generator(config)
        floor1_data = gen.generate()
        
        spawner = Floor1Spawner(mock_player, config)
        entities = spawner.spawn_all(floor1_data, None)
        
        assert len(entities) > 0
    
    def test_guard_patrols_spawned(self, mock_player, config):
        from src.application.services.floor1_generator import Floor1Generator
        
        gen = Floor1Generator(config)
        floor1_data = gen.generate()
        
        spawner = Floor1Spawner(mock_player, config)
        entities = spawner._spawn_guard_patrols(floor1_data)
        
        guards = [e for e in entities if e.name in ('Dungeon Guard', 'Guard Sergeant')]
        assert len(guards) >= 2  # At least one patrol of 2
    
    def test_den_creatures_spawned(self, mock_player, config):
        from src.application.services.floor1_generator import Floor1Generator
        
        gen = Floor1Generator(config)
        floor1_data = gen.generate()
        
        spawner = Floor1Spawner(mock_player, config)
        entities = spawner._spawn_den_creatures(floor1_data)
        
        creatures = [e for e in entities if e.name in ('Giant Spider', 'Spider Queen', 'Cave Rat', 'Rat King')]
        assert len(creatures) >= 2
    
    def test_monsters_weaker_than_player(self, mock_player, config):
        """All monsters should be weaker than starting player."""
        from src.application.services.floor1_generator import Floor1Generator
        
        mock_player.hp = 15
        mock_player.power = 5
        
        gen = Floor1Generator(config)
        floor1_data = gen.generate()
        
        spawner = Floor1Spawner(mock_player, config)
        entities = spawner.spawn_all(floor1_data, None)
        
        for entity in entities:
            assert entity.max_hp <= mock_player.hp + 5
            assert entity.power <= mock_player.power
    
    def test_corpses_have_loot(self, mock_player, config):
        from src.application.services.floor1_generator import Floor1Generator
        
        gen = Floor1Generator(config)
        floor1_data = gen.generate()
        
        spawner = Floor1Spawner(mock_player, config)
        entities = spawner._spawn_corpses(floor1_data)
        
        for entity in entities:
            if hasattr(entity, 'is_corpse') and entity.is_corpse:
                assert hasattr(entity, 'loot')
                # Some corpses may have empty loot list, that's ok


class TestMonsterTemplates:
    
    def test_all_templates_exist(self):
        required = [
            'dungeon_guard', 'guard_sergeant',
            'giant_spider', 'spider_queen',
            'cave_rat', 'rat_king',
            'troll_scavenger', 'fungal_creeper', 'cave_bat',
        ]
        for key in required:
            assert key in MONSTER_TEMPLATES
    
    def test_stats_are_low(self):
        """All floor 1 monsters should have low stats."""
        for key, template in MONSTER_TEMPLATES.items():
            assert template['hp'] <= 15, f"{key} has too much HP"
            assert template['power'] <= 3, f"{key} has too much power"
```

---

## Step 7: Run Tests

```bash
cd /home/danny/Code/DarkDelve
python -m pytest tests/test_floor1_generator.py -v
```

---

## Step 8: Playtest

Run the playtester to validate:

```bash
cd /home/danny/Code/DarkDelve
python darkdelve.py --playtest --turns 100
```

Or with the enhanced config:

```bash
python ollama_playtester.py --persona "Default" --max-turns 100
```

---

## Step 9: Debug Issues

If playtester finds issues:
1. Check test output for failures
2. Fix generation/spawning code
3. Re-run tests
4. Re-run playtester

---

## Key Design Decisions

1. **All monsters weaker than player**: HP <= 15, Power <= 3 (player starts with HP 12-15, Power 5)
2. **Main path cleared**: No dens within 5 tiles, max 2 roaming creatures
3. **Guard groups**: 2-3 guards patrol together, sergeant leads
4. **Den creatures**: Stay in rooms, don't chase far
5. **Loot in dens**: Corpses and collected items from victims
6. **Fear mechanic**: Dens track guard kills, trigger cleanup if too many

## Files to Create/Modify

| File | Action | Step |
|------|--------|------|
| `config/floor1_monsters.yaml` | Create | 1 |
| `src/application/services/floor1_generator.py` | Create | 2 |
| `src/application/services/floor1_spawner.py` | Create | 3 |
| `darkdelve.py` | Modify | 4 |
| `config/game.yaml` | Modify | 5 |
| `tests/test_floor1_generator.py` | Create | 6 |
