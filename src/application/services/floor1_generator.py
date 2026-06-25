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