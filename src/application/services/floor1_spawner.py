"""
Floor 1 Entity Spawner

Spawns all entities for floor 1 based on Floor1Data.
"""

import random
from typing import List, Tuple, Optional, Set
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
    
    def __init__(self, player: Entity, config: dict, dungeon_map: np.ndarray = None):
        self.player = player
        self.config = config
        self.dungeon_map = dungeon_map
        self.occupied_positions: Set[Tuple[int, int]] = set()
    
    def spawn_all(self, floor1_data, roster) -> List[Entity]:
        """Spawn all entities for floor 1."""
        entities = []
        
        # Track player position
        self.occupied_positions.add((self.player.x, self.player.y))
        
        # Spawn guard patrols
        entities.extend(self._spawn_guard_patrols(floor1_data))
        
        # Spawn den creatures
        entities.extend(self._spawn_den_creatures(floor1_data))
        
        # Spawn roaming creatures
        entities.extend(self._spawn_roaming(floor1_data))
        
        # Spawn corpses with loot
        entities.extend(self._spawn_corpses(floor1_data))
        
        return entities
    
    def _is_valid_position(self, x: int, y: int) -> bool:
        """Check if position is valid (on floor, not wall)."""
        if self.dungeon_map is None:
            return True  # No map to check against
        if x < 0 or y < 0:
            return False
        if x >= self.dungeon_map.shape[0] or y >= self.dungeon_map.shape[1]:
            return False
        return not self.dungeon_map[x, y]  # False = floor, True = wall
    
    def _find_valid_position(self, x: int, y: int, max_attempts: int = 50) -> Tuple[int, int]:
        """Find a valid position near the given coordinates that's not occupied."""
        # Try the exact position first
        if self._is_valid_position(x, y) and (x, y) not in self.occupied_positions:
            self.occupied_positions.add((x, y))
            return (x, y)
        
        # Try nearby positions
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                nx, ny = x + dx, y + dy
                if self._is_valid_position(nx, ny) and (nx, ny) not in self.occupied_positions:
                    self.occupied_positions.add((nx, ny))
                    return (nx, ny)
        
        # Search the map for an unoccupied floor tile
        for _ in range(max_attempts):
            nx = random.randint(1, self.config['dungeon']['width'] - 2)
            ny = random.randint(1, self.config['dungeon']['height'] - 2)
            if self._is_valid_position(nx, ny) and (nx, ny) not in self.occupied_positions:
                self.occupied_positions.add((nx, ny))
                return (nx, ny)
        
        # Fallback: return original position even if invalid
        return (x, y)
    
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
                
                # Find valid position
                x, y = self._find_valid_position(x, y)
                
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
                # First creature is leader (queen/king), rest are minions
                if i == 0 and den.creature_type == 'giant_spider':
                    template_key = 'spider_queen'
                elif i == 0 and den.creature_type == 'cave_rat':
                    template_key = 'rat_king'
                else:
                    template_key = den.creature_type
                
                # Find a position that's not occupied
                attempts = 0
                while attempts < 50:
                    angle = random.uniform(0, 2 * 3.14159)
                    dist = random.randint(0, max(1, den.radius - 1))
                    x = int(cx + dist * np.cos(angle))
                    y = int(cy + dist * np.sin(angle))
                    
                    # Check if position is valid and not occupied
                    if self._is_valid_position(x, y) and (x, y) not in self.occupied_positions:
                        break
                    attempts += 1
                
                # Mark position as occupied
                self.occupied_positions.add((x, y))
                
                template = MONSTER_TEMPLATES[template_key]
                entity = self._create_monster_entity(template, x, y)
                entity.home_position = (x, y)  # Stay near den
                entities.append(entity)
        
        return entities
    
    def _spawn_roaming(self, floor1_data) -> List[Entity]:
        """Spawn roaming solitary creatures."""
        entities = []
        
        for x, y, creature_type in floor1_data.roaming_spawns:
            # Find valid position
            x, y = self._find_valid_position(x, y)
            
            template = MONSTER_TEMPLATES[creature_type]
            entity = self._create_monster_entity(template, x, y)
            entities.append(entity)
        
        return entities
    
    def _spawn_corpses(self, floor1_data) -> List[Entity]:
        """Spawn adventurer corpses with loot."""
        entities = []
        
        for x, y in floor1_data.corpses:
            # Find valid position
            x, y = self._find_valid_position(x, y)
            
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