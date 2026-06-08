"""
Field of View (FOV) query for visibility calculations.
"""
from typing import Optional, Dict, Any, List, Set, Tuple
from .base_query import BaseQuery, QueryResult
from ...domain.entities.player import Player
from ...domain.entities.mob import Mob
from ...domain.value_objects.position import Position


class FOVQuery(BaseQuery):
    """
    Query for calculating field of view.
    
    Implements the Query pattern for visibility calculations.
    """
    
    def __init__(self, player: Player, radius: int = 10):
        """
        Initialize the FOV query.
        
        Args:
            player: The player entity for FOV calculation
            radius: The radius of the FOV
        """
        super().__init__("fov")
        self.player = player
        self.radius = radius
        self.fov_cache: Dict[Tuple[int, int, int], Set[Tuple[int, int]]] = {}
    
    def execute(self, *args, **kwargs) -> QueryResult:
        """
        Execute the FOV query.
        
        Args:
            *args: Additional arguments (radius override)
            **kwargs: Additional keyword arguments (not used)
            
        Returns:
            QueryResult: The result of the FOV calculation
        """
        # Check cache first
        cached_result = self.get_cached_result(*args, **kwargs)
        if cached_result:
            return cached_result
        
        # Get radius from args or use default
        radius = args[0] if args else self.radius
        
        try:
            # Calculate FOV using simple algorithm
            visible_positions = self.calculate_fov(radius)
            
            # Cache the result
            result = QueryResult(
                success=True,
                data=visible_positions,
                metadata={
                    "player_position": Position(self.player.x, self.player.y),
                    "radius": radius,
                    "visible_count": len(visible_positions)
                }
            )
            
            self.cache_result(result)
            return result
            
        except Exception as e:
            return QueryResult(
                success=False,
                error_message=f"Failed to calculate FOV: {str(e)}"
            )
    
    def calculate_fov(self, radius: int) -> Set[Tuple[int, int]]:
        """
        Calculate field of view using a simple algorithm.
        
        Args:
            radius: The radius of the FOV
            
        Returns:
            Set[Tuple[int, int]]: Set of visible positions
        """
        visible_positions = set()
        player_pos = (self.player.x, self.player.y)
        
        # Simple circular FOV calculation
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                distance = abs(dx) + abs(dy)  # Manhattan distance
                if distance <= radius:
                    x, y = player_pos[0] + dx, player_pos[1] + dy
                    visible_positions.add((x, y))
        
        return visible_positions
    
    def is_position_visible(self, x: int, y: int) -> bool:
        """
        Check if a position is within the player's FOV.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            bool: True if position is visible, False otherwise
        """
        result = self.execute()
        if not result.success:
            return False
        
        return (x, y) in result.data
    
    def get_visible_entities(self, entities: List) -> List:
        """
        Get all entities within the player's FOV.
        
        Args:
            entities: List of entities to check
            
        Returns:
            List: List of visible entities
        """
        visible_entities = []
        
        for entity in entities:
            if self.is_position_visible(entity.x, entity.y):
                visible_entities.append(entity)
        
        return visible_entities
    
    def clear_cache(self) -> None:
        """Clear the FOV cache."""
        super().clear_cache()
        self.fov_cache.clear()
    
    def update_player_position(self, x: int, y: int) -> None:
        """
        Update the player position and clear cache.
        
        Args:
            x: New X coordinate
            y: New Y coordinate
        """
        self.player.x = x
        self.player.y = y
        self.clear_cache()