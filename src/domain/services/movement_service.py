"""
Movement service for handling entity movement and navigation.
"""
from typing import List, Dict, Any, Optional, Tuple, Set
from ..entities.player import Player
from ..entities.mob import Mob
from ..entities.item import Item
from ..components.movement import Movement
from ..value_objects.position import Position
from typing import Any


def distance_between(pos1: Any, pos2: Any) -> float:
    """Calculate distance between two positions."""
    return ((pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2) ** 0.5


class MovementService:
    """
    Service for handling entity movement and navigation.
    
    Implements the Service pattern for movement management.
    """
    
    def __init__(self, map_width: int = 100, map_height: int = 100):
        """
        Initialize the movement service.
        
        Args:
            map_width: Width of the game map
            map_height: Height of the game map
        """
        self.map_width = map_width
        self.map_height = map_height
        self.movement_history: List[Dict[str, Any]] = []
        self.blocked_positions: Set[Tuple[int, int]] = set()
    
    def move_entity(self, entity: Any, target_position: Position) -> bool:
        """
        Move an entity to a target position.
        
        Args:
            entity: The entity to move
            target_position: The target position
            
        Returns:
            bool: True if movement was successful, False otherwise
        """
        if not self.can_move_to(entity, target_position):
            return False
        
        # Store old position
        old_position = Position(entity.position.x, entity.position.y)
        
        # Move entity
        entity.position = target_position
        
        # Record movement
        movement_record = {
            "entity_id": entity.id,
            "entity_name": entity.name,
            "old_position": old_position,
            "new_position": target_position,
            "distance": old_position.distance_to(target_position),
            "timestamp": self.get_current_timestamp()
        }
        self.movement_history.append(movement_record)
        
        return True
    
    def can_move_to(self, entity: Any, target_position: Position) -> bool:
        """
        Check if an entity can move to a target position.
        
        Args:
            entity: The entity attempting to move
            target_position: The target position
            
        Returns:
            bool: True if movement is possible, False otherwise
        """
        # Check if position is within map bounds
        if not self.is_within_bounds(target_position):
            return False
        
        # Check if position is blocked
        if self.is_position_blocked(target_position):
            return False
        
        # Check if entity has movement capability
        if not hasattr(entity, 'movement') or not entity.movement.can_move():
            return False
        
        # Check movement range
        current_position = entity.position
        distance = current_position.distance_to(target_position)
        
        if distance > entity.movement.max_move_distance:
            return False
        
        return True
    
    def is_within_bounds(self, position: Position) -> bool:
        """
        Check if a position is within map bounds.
        
        Args:
            position: The position to check
            
        Returns:
            bool: True if position is within bounds, False otherwise
        """
        return (0 <= position.x < self.map_width and 
                0 <= position.y < self.map_height)
    
    def is_position_blocked(self, position: Position) -> bool:
        """
        Check if a position is blocked.
        
        Args:
            position: The position to check
            
        Returns:
            bool: True if position is blocked, False otherwise
        """
        return (position.x, position.y) in self.blocked_positions
    
    def get_valid_moves(self, entity: Any) -> List[Position]:
        """
        Get all valid moves for an entity.
        
        Args:
            entity: The entity to get moves for
            
        Returns:
            List[Position]: List of valid positions
        """
        valid_moves = []
        current_position = entity.position
        max_distance = entity.movement.max_move_distance if hasattr(entity, 'movement') else 1
        
        # Check all positions within movement range
        for x in range(current_position.x - max_distance, current_position.x + max_distance + 1):
            for y in range(current_position.y - max_distance, current_position.y + max_distance + 1):
                target_position = Position(x, y)
                
                if (self.is_within_bounds(target_position) and 
                    not self.is_position_blocked(target_position) and
                    current_position.distance_to(target_position) <= max_distance):
                    valid_moves.append(target_position)
        
        return valid_moves
    
    def get_path_to(self, entity: Any, target_position: Position) -> List[Position]:
        """
        Get a path from entity's current position to target position.
        
        Args:
            entity: The entity to get path for
            target_position: The target position
            
        Returns:
            List[Position]: List of positions in the path
        """
        # Simple pathfinding (can be enhanced with A* or other algorithms)
        path = []
        current_position = Position(entity.position.x, entity.position.y)
        
        # Direct path (can be improved with proper pathfinding)
        while current_position.x != target_position.x or current_position.y != target_position.y:
            next_position = Position(current_position.x, current_position.y)
            
            # Move towards target
            if current_position.x < target_position.x:
                next_position.x += 1
            elif current_position.x > target_position.x:
                next_position.x -= 1
            
            if current_position.y < target_position.y:
                next_position.y += 1
            elif current_position.y > target_position.y:
                next_position.y -= 1
            
            # Check if next position is valid
            if self.can_move_to(entity, next_position):
                path.append(next_position)
                current_position = next_position
            else:
                # Path blocked, return what we have
                break
        
        return path
    
    def get_distance_to(self, entity: Any, target_position: Position) -> float:
        """
        Get distance from entity to target position.
        
        Args:
            entity: The entity to get distance from
            target_position: The target position
            
        Returns:
            float: Distance to target
        """
        return entity.position.distance_to(target_position)
    
    def get_manhattan_distance_to(self, entity: Any, target_position: Position) -> int:
        """
        Get Manhattan distance from entity to target position.
        
        Args:
            entity: The entity to get distance from
            target_position: The target position
            
        Returns:
            int: Manhattan distance to target
        """
        return entity.position.manhattan_distance_to(target_position)
    
    def get_entities_in_range(self, entity: Any, entities: List[Any], range_radius: int = 10) -> List[Any]:
        """
        Get entities within a certain range of the given entity.
        
        Args:
            entity: The entity to get range from
            entities: List of entities to check
            range_radius: Range radius to check
            
        Returns:
            List[Any]: List of entities within range
        """
        entities_in_range = []
        
        for other_entity in entities:
            if other_entity.id != entity.id:
                distance = self.get_distance_to(entity, other_entity.position)
                if distance <= range_radius:
                    entities_in_range.append(other_entity)
        
        return entities_in_range
    
    def get_visible_entities(self, entity: Any, entities: List[Any], vision_range: int = 10) -> List[Any]:
        """
        Get entities visible to the given entity.
        
        Args:
            entity: The entity to get visible entities from
            entities: List of entities to check
            vision_range: Vision range to check
            
        Returns:
            List[Any]: List of visible entities
        """
        visible_entities = []
        
        for other_entity in entities:
            if other_entity.id != entity.id:
                # Check if entity is within vision range
                distance = self.get_distance_to(entity, other_entity.position)
                if distance <= vision_range:
                    # Check if there's line of sight (simplified)
                    if self.has_line_of_sight(entity.position, other_entity.position):
                        visible_entities.append(other_entity)
        
        return visible_entities
    
    def has_line_of_sight(self, start_position: Position, end_position: Position) -> bool:
        """
        Check if there's a clear line of sight between two positions.
        
        Args:
            start_position: Starting position
            end_position: Ending position
            
        Returns:
            bool: True if line of sight exists, False otherwise
        """
        # Simple line of sight check (can be enhanced with proper raycasting)
        dx = abs(end_position.x - start_position.x)
        dy = abs(end_position.y - start_position.y)
        
        # Check if positions are the same
        if dx == 0 and dy == 0:
            return True
        
        # Check if either coordinate is the same
        if dx == 0:
            # Vertical line
            y1, y2 = min(start_position.y, end_position.y), max(start_position.y, end_position.y)
            for y in range(y1, y2 + 1):
                if self.is_position_blocked(Position(start_position.x, y)):
                    return False
            return True
        
        if dy == 0:
            # Horizontal line
            x1, x2 = min(start_position.x, end_position.x), max(start_position.x, end_position.x)
            for x in range(x1, x2 + 1):
                if self.is_position_blocked(Position(x, start_position.y)):
                    return False
            return True
        
        # Diagonal line (simplified)
        return True
    
    def add_blocked_position(self, position: Position) -> None:
        """
        Add a blocked position.
        
        Args:
            position: The position to block
        """
        self.blocked_positions.add((position.x, position.y))
    
    def remove_blocked_position(self, position: Position) -> None:
        """
        Remove a blocked position.
        
        Args:
            position: The position to unblock
        """
        self.blocked_positions.discard((position.x, position.y))
    
    def get_movement_history(self, entity_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get movement history.
        
        Args:
            entity_id: Optional entity ID to filter history
            limit: Maximum number of records to return
            
        Returns:
            List[Dict[str, Any]]: Movement history
        """
        if entity_id:
            filtered_history = [record for record in self.movement_history if record["entity_id"] == entity_id]
            return filtered_history[-limit:]
        
        return self.movement_history[-limit:]
    
    def get_movement_statistics(self) -> Dict[str, Any]:
        """
        Get movement statistics.
        
        Returns:
            Dict[str, Any]: Movement statistics
        """
        total_movements = len(self.movement_history)
        unique_entities = len(set(record["entity_id"] for record in self.movement_history))
        
        # Calculate average distance moved
        if total_movements > 0:
            avg_distance = sum(record["distance"] for record in self.movement_history) / total_movements
        else:
            avg_distance = 0
        
        return {
            "total_movements": total_movements,
            "unique_entities": unique_entities,
            "average_distance": avg_distance,
            "blocked_positions": len(self.blocked_positions),
            "map_size": f"{self.map_width}x{self.map_height}"
        }
    
    def get_current_timestamp(self) -> str:
        """
        Get current timestamp.
        
        Returns:
            str: Current timestamp
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def clear_movement_history(self) -> None:
        """Clear all movement history."""
        self.movement_history.clear()
    
    def clear_blocked_positions(self) -> None:
        """Clear all blocked positions."""
        self.blocked_positions.clear()
    
    def set_map_size(self, width: int, height: int) -> None:
        """
        Set the map size.
        
        Args:
            width: New map width
            height: New map height
        """
        self.map_width = width
        self.map_height = height
        
        # Clear blocked positions that are now out of bounds
        self.blocked_positions = {
            (x, y) for x, y in self.blocked_positions
            if 0 <= x < width and 0 <= y < height
        }