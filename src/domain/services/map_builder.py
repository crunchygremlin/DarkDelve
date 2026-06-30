"""
MapBuilder - Procedural dungeon map building blocks.

Provides a fluent API for constructing dungeon maps room-by-room,
with built-in validation and game integration.
"""

import numpy as np
from typing import List, Tuple, Dict, Any, Optional, Set
from dataclasses import dataclass, field


@dataclass
class Room:
    """Represents a carved room."""
    x: int
    y: int
    width: int
    height: int
    room_id: str = ""

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def tiles(self) -> List[Tuple[int, int]]:
        """Return all floor tiles in this room."""
        tiles = []
        for x in range(self.x, self.x + self.width):
            for y in range(self.y, self.y + self.height):
                tiles.append((x, y))
        return tiles


@dataclass
class Corridor:
    """Represents a carved corridor."""
    start: Tuple[int, int]
    end: Tuple[int, int]
    width: int = 1
    tiles: List[Tuple[int, int]] = field(default_factory=list)


@dataclass
class Stair:
    """Represents a stair tile."""
    x: int
    y: int
    direction: str  # "down" or "up"


@dataclass
class EntityPlacement:
    """Represents an entity to be placed."""
    x: int
    y: int
    entity_type: str
    name: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)


class MapBuilder:
    """
    Procedural dungeon map builder with building blocks.

    Usage:
        builder = MapBuilder(width=60, height=40)
        builder.create_room(5, 5, 10, 8)
        builder.create_corridor((10, 9), (20, 9))
        builder.create_room(20, 5, 12, 10)
        builder.create_stair_down(25, 14)
        builder.place_entity(7, 7, "giant_spider")
        validation = builder.validate_map()
        builder.apply_to_game(game)
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        # dungeon_map[x, y]: True = wall, False = floor
        self.dungeon_map: np.ndarray = np.ones((width, height), dtype=bool)
        self.rooms: List[Room] = []
        self.corridors: List[Corridor] = []
        self.stairs: List[Stair] = []
        self.entity_placements: List[EntityPlacement] = []
        self._room_counter = 0

    def create_room(self, x: int, y: int, width: int, height: int, room_id: Optional[str] = None) -> Room:
        """
        Carve a rectangular room into the map.

        Args:
            x: Top-left x coordinate
            y: Top-left y coordinate
            width: Room width
            height: Room height
            room_id: Optional identifier (auto-generated if not provided)

        Returns:
            The created Room object
        """
        # Clamp to map bounds
        x = max(0, min(x, self.width - 1))
        y = max(0, min(y, self.height - 1))
        width = max(1, min(width, self.width - x))
        height = max(1, min(height, self.height - y))

        # Carve room (set to False = floor)
        self.dungeon_map[x:x+width, y:y+height] = False

        # Create room object
        if room_id is None:
            self._room_counter += 1
            room_id = f"room_{self._room_counter}"

        room = Room(x=x, y=y, width=width, height=height, room_id=room_id)
        self.rooms.append(room)
        return room

    def create_corridor(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        width: int = 1
    ) -> Corridor:
        """
        Carve a corridor between two points using L-shaped path.

        Args:
            start: (x, y) start position
            end: (x, y) end position
            width: Corridor width (default 1)

        Returns:
            The created Corridor object
        """
        x1, y1 = start
        x2, y2 = end
        tiles = []

        # Randomly choose horizontal-first or vertical-first
        if np.random.random() < 0.5:
            # Horizontal then vertical
            for x in range(min(x1, x2), max(x1, x2) + 1):
                for w in range(width):
                    if 0 <= x < self.width and 0 <= y1 + w < self.height:
                        self.dungeon_map[x, y1 + w] = False
                        tiles.append((x, y1 + w))
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for w in range(width):
                    if 0 <= x2 + w < self.width and 0 <= y < self.height:
                        self.dungeon_map[x2 + w, y] = False
                        tiles.append((x2 + w, y))
        else:
            # Vertical then horizontal
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for w in range(width):
                    if 0 <= x1 + w < self.width and 0 <= y < self.height:
                        self.dungeon_map[x1 + w, y] = False
                        tiles.append((x1 + w, y))
            for x in range(min(x1, x2), max(x1, x2) + 1):
                for w in range(width):
                    if 0 <= x < self.width and 0 <= y2 + w < self.height:
                        self.dungeon_map[x, y2 + w] = False
                        tiles.append((x, y2 + w))

        corridor = Corridor(start=start, end=end, width=width, tiles=tiles)
        self.corridors.append(corridor)
        return corridor

    def create_stair_down(self, x: int, y: int) -> Stair:
        """Place a downward stair tile."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.dungeon_map[x, y] = False
            stair = Stair(x=x, y=y, direction="down")
            self.stairs.append(stair)
            return stair
        raise ValueError(f"Stair position ({x}, {y}) is out of bounds or wall")

    def create_stair_up(self, x: int, y: int) -> Stair:
        """Place an upward stair tile."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.dungeon_map[x, y] = False
            stair = Stair(x=x, y=y, direction="up")
            self.stairs.append(stair)
            return stair
        raise ValueError(f"Stair position ({x}, {y}) is out of bounds or wall")

    def place_entity(
        self,
        x: int,
        y: int,
        entity_type: str,
        name: Optional[str] = None,
        **properties
    ) -> EntityPlacement:
        """
        Queue an entity for placement at (x, y).

        Args:
            x: X coordinate
            y: Y coordinate
            entity_type: Type of entity (e.g., "goblin", "spider")
            name: Optional display name
            **properties: Additional entity properties

        Returns:
            The EntityPlacement object
        """
        placement = EntityPlacement(
            x=x, y=y, entity_type=entity_type,
            name=name or entity_type,
            properties=properties
        )
        self.entity_placements.append(placement)
        return placement

    def validate_map(self) -> Dict[str, Any]:
        """
        Validate the map for connectivity and reachability.

        Checks:
        1. All rooms are connected (reachable from first room)
        2. All stairs are on floor tiles
        3. All entity placements are on floor tiles
        4. At least one stair_down exists

        Returns:
            Dict with 'valid' (bool), 'errors' (list), 'warnings' (list)
        """
        errors = []
        warnings = []

        # Check: map has rooms
        if not self.rooms:
            errors.append("Map has no rooms")

        # Check: stairs on floor tiles
        for stair in self.stairs:
            if self.dungeon_map[stair.x, stair.y]:
                errors.append(f"Stair at ({stair.x}, {stair.y}) is on a wall tile")

        # Check: entity placements on floor tiles
        for placement in self.entity_placements:
            if (placement.x >= self.width or placement.y >= self.height
                    or self.dungeon_map[placement.x, placement.y]):
                errors.append(
                    f"Entity '{placement.entity_type}' at ({placement.x}, {placement.y}) "
                    f"is on a wall or out of bounds"
                )

        # Check: connectivity via flood fill from first room
        if self.rooms:
            connected = self._check_connectivity(self.rooms[0].center)
            unreachable_rooms = [
                r for r in self.rooms
                if (r.center[0], r.center[1]) not in connected
            ]
            if unreachable_rooms:
                errors.append(
                    f"{len(unreachable_rooms)} room(s) are unreachable from entrance"
                )

        # Check: at least one stair_down
        if not any(s.direction == "down" for s in self.stairs):
            warnings.append("No downward stairs placed")

        # Check: at least one stair_up
        if not any(s.direction == "up" for s in self.stairs):
            warnings.append("No upward stairs placed")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "room_count": len(self.rooms),
            "corridor_count": len(self.corridors),
            "stair_count": len(self.stairs),
            "entity_count": len(self.entity_placements),
        }

    def _check_connectivity(self, start: Tuple[int, int]) -> Set[Tuple[int, int]]:
        """
        Flood fill from start position to find all reachable floor tiles.

        Returns:
            Set of (x, y) tuples that are reachable
        """
        visited = set()
        queue = [start]

        while queue:
            x, y = queue.pop(0)
            if (x, y) in visited:
                continue
            visited.add((x, y))

            # Check 4 neighbors
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.width and 0 <= ny < self.height
                        and not self.dungeon_map[nx, ny]
                        and (nx, ny) not in visited):
                    queue.append((nx, ny))

        return visited

    def apply_to_game(self, game: Any) -> bool:
        """
        Write the built map into a Game instance.

        Args:
            game: The Game instance to modify

        Returns:
            True if applied successfully, False if validation failed
        """
        validation = self.validate_map()
        if not validation["valid"]:
            return False

        # Apply dungeon map
        game.dungeon_map = self.dungeon_map.copy()

        # Set stair positions
        for stair in self.stairs:
            if stair.direction == "down":
                game.stair_down_pos = (stair.x, stair.y)
            elif stair.direction == "up":
                game.stair_up_pos = (stair.x, stair.y)

        # Place entities
        from darkdelve import Entity, COLORS
        for placement in self.entity_placements:
            # Only place on floor tiles
            if self.dungeon_map[placement.x, placement.y]:
                continue  # Skip wall positions

            entity = Entity(
                x=placement.x,
                y=placement.y,
                char=placement.properties.get('symbol', '?'),
                color=placement.properties.get('color', COLORS.get('enemy_normal', (100, 150, 200))),
                name=placement.name,
                blocks=True,
                hp=placement.properties.get('hp', 5),
                max_hp=placement.properties.get('hp', 5),
                power=placement.properties.get('power', 2),
                defense=placement.properties.get('defense', 0),
                speed=placement.properties.get('speed', 80),
                intel_tier=placement.properties.get('intel_tier', 1),
            )
            game.entities.append(entity)
            game.energy_system.add_entity(entity)

        return True

    def get_map_data(self) -> Dict[str, Any]:
        """
        Export map data as a serializable dictionary.

        Returns:
            Dict with rooms, corridors, stairs, entities, and map array
        """
        return {
            "width": self.width,
            "height": self.height,
            "dungeon_map": self.dungeon_map.tolist(),
            "rooms": [
                {
                    "x": r.x, "y": r.y,
                    "width": r.width, "height": r.height,
                    "room_id": r.room_id,
                    "center": r.center,
                }
                for r in self.rooms
            ],
            "corridors": [
                {
                    "start": c.start,
                    "end": c.end,
                    "width": c.width,
                    "tiles": c.tiles,
                }
                for c in self.corridors
            ],
            "stairs": [
                {"x": s.x, "y": s.y, "direction": s.direction}
                for s in self.stairs
            ],
            "entities": [
                {
                    "x": e.x, "y": e.y,
                    "type": e.entity_type,
                    "name": e.name,
                }
                for e in self.entity_placements
            ],
        }

    @classmethod
    def from_map_data(cls, data: Dict[str, Any]) -> 'MapBuilder':
        """
        Create a MapBuilder from serialized map data.

        Args:
            data: Dictionary from get_map_data()

        Returns:
            New MapBuilder instance with loaded map
        """
        builder = cls(width=data["width"], height=data["height"])

        # Reconstruct dungeon_map from components if not provided directly
        if "dungeon_map" in data:
            builder.dungeon_map = np.array(data["dungeon_map"], dtype=bool)
        # else: dungeon_map stays as all walls; rooms/corridors/stairs will carve it

        for room_data in data.get("rooms", []):
            builder.create_room(
                x=room_data["x"],
                y=room_data["y"],
                width=room_data["width"],
                height=room_data["height"],
                room_id=room_data.get("room_id"),
            )

        for corridor_data in data.get("corridors", []):
            builder.create_corridor(
                start=tuple(corridor_data["start"]),
                end=tuple(corridor_data["end"]),
                width=corridor_data.get("width", 1),
            )

        for stair_data in data.get("stairs", []):
            if stair_data["direction"] == "down":
                builder.create_stair_down(stair_data["x"], stair_data["y"])
            else:
                builder.create_stair_up(stair_data["x"], stair_data["y"])

        for entity_data in data.get("entities", []):
            builder.place_entity(
                x=entity_data["x"],
                y=entity_data["y"],
                entity_type=entity_data["type"],
                name=entity_data.get("name"),
            )

        return builder

    def generate_procedural(
        self,
        room_count: int = 6,
        min_room_size: int = 4,
        max_room_size: int = 10,
        seed: Optional[int] = None,
    ) -> None:
        """
        Generate a complete procedural dungeon using room-and-corridor approach.

        Args:
            room_count: Number of rooms to generate
            min_room_size: Minimum room dimension
            max_room_size: Maximum room dimension
            seed: Random seed for reproducibility
        """
        if seed is not None:
            np.random.seed(seed)

        self.rooms = []
        self.corridors = []
        self.stairs = []
        self.entity_placements = []

        # Generate non-overlapping rooms
        for _ in range(room_count * 3):  # Extra attempts for placement
            if len(self.rooms) >= room_count:
                break

            w = np.random.randint(min_room_size, max_room_size + 1)
            h = np.random.randint(min_room_size, max_room_size + 1)
            x = np.random.randint(1, self.width - w - 1)
            y = np.random.randint(1, self.height - h - 1)

            # Check overlap with existing rooms
            overlap = False
            for room in self.rooms:
                if (x < room.x + room.width + 2 and x + w + 2 > room.x
                        and y < room.y + room.height + 2 and y + h + 2 > room.y):
                    overlap = True
                    break

            if not overlap:
                self.create_room(x, y, w, h)

        # Connect rooms with corridors
        for i in range(1, len(self.rooms)):
            prev_center = self.rooms[i - 1].center
            curr_center = self.rooms[i].center
            self.create_corridor(prev_center, curr_center)

        # Place stairs
        if self.rooms:
            first_room = self.rooms[0]
            self.create_stair_up(first_room.center[0], first_room.center[1])

            last_room = self.rooms[-1]
            self.create_stair_down(last_room.center[0], last_room.center[1])
