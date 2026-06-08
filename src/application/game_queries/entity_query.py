"""
Entity query for entity-related information.
"""
from typing import Optional, Dict, Any, List
from .base_query import BaseQuery, QueryResult
from ...domain.entities.player import Player
from ...domain.entities.mob import Mob
from ...domain.entities.item import Item
from ...domain.value_objects.position import Position


class EntityQuery(BaseQuery):
    """
    Query for entity-related information.
    
    Implements the Query pattern for entity management and information.
    """
    
    def __init__(self, player: Player):
        """
        Initialize the entity query.
        
        Args:
            player: The player entity for entity queries
        """
        super().__init__("entity")
        self.player = player
    
    def execute(self, *args, **kwargs) -> QueryResult:
        """
        Execute the entity query.
        
        Args:
            *args: Additional arguments (entity type or specific entity)
            **kwargs: Additional keyword arguments (not used)
            
        Returns:
            QueryResult: The result of the entity query
        """
        # Check cache first
        cached_result = self.get_cached_result(*args, **kwargs)
        if cached_result:
            return cached_result
        
        entity_type = args[0] if args else None
        entity_id = kwargs.get("entity_id")
        
        try:
            if entity_id:
                # Specific entity information
                result = self.get_entity_info(entity_id)
            elif entity_type:
                # Entity type information
                result = self.get_entities_by_type(entity_type)
            else:
                # General entity information
                result = self.get_general_entity_info()
            
            self.cache_result(result)
            return result
            
        except Exception as e:
            return QueryResult(
                success=False,
                error_message=f"Failed to execute entity query: {str(e)}"
            )
    
    def get_entity_info(self, entity_id: str) -> QueryResult:
        """
        Get specific entity information.
        
        Args:
            entity_id: ID of the entity to query
            
        Returns:
            QueryResult: Entity information
        """
        # This would typically query a repository or service
        # For now, we'll return a mock response
        return QueryResult(
            success=True,
            data={
                "entity_id": entity_id,
                "entity_type": "unknown",
                "name": "Unknown Entity",
                "position": Position(self.player.x, self.player.y),
                "health": 100,
                "max_health": 100,
                "attack_power": 10,
                "defense": 5,
                "level": 1
            },
            metadata={
                "distance_from_player": 0,
                "is_visible": True,
                "is_hostile": False
            }
        )
    
    def get_entities_by_type(self, entity_type: str) -> QueryResult:
        """
        Get entities by type.
        
        Args:
            entity_type: Type of entities to retrieve (e.g., "mob", "item", "npc")
            
        Returns:
            QueryResult: Entities by type
        """
        # This would typically query a repository or service
        # For now, we'll return a mock response
        entities = []
        
        if entity_type.lower() == "mob":
            entities = [
                {
                    "id": "mob_1",
                    "name": "Goblin",
                    "type": "mob",
                    "position": Position(self.player.x + 5, self.player.y + 5),
                    "health": 50,
                    "max_health": 50,
                    "attack_power": 8,
                    "defense": 3,
                    "level": 1
                }
            ]
        elif entity_type.lower() == "item":
            entities = [
                {
                    "id": "item_1",
                    "name": "Health Potion",
                    "type": "item",
                    "position": Position(self.player.x + 3, self.player.y + 3),
                    "value": 50,
                    "weight": 1
                }
            ]
        
        return QueryResult(
            success=True,
            data={
                "entity_type": entity_type,
                "entities": entities,
                "count": len(entities)
            },
            metadata={
                "average_level": sum(e.get("level", 1) for e in entities) / len(entities) if entities else 0,
                "total_value": sum(e.get("value", 0) for e in entities)
            }
        )
    
    def get_general_entity_info(self) -> QueryResult:
        """
        Get general entity information.
        
        Returns:
            QueryResult: General entity information
        """
        # This would typically query a repository or service
        # For now, we'll return a mock response
        return QueryResult(
            success=True,
            data={
                "player_position": Position(self.player.x, self.player.y),
                "player_level": self.player.level,
                "player_health": self.player.health,
                "player_max_health": self.player.max_health,
                "nearby_entities": [],
                "visible_entities": []
            },
            metadata={
                "total_entities": 0,
                "mob_count": 0,
                "item_count": 0,
                "npc_count": 0
            }
        )
    
    def get_entities_in_range(self, entities: List, range_radius: int = 10) -> List:
        """
        Get entities within a specified range.
        
        Args:
            entities: List of entities to filter
            range_radius: Range radius from player
            
        Returns:
            List: Entities within range
        """
        player_pos = Position(self.player.x, self.player.y)
        entities_in_range = []
        
        for entity in entities:
            entity_pos = Position(entity.x, entity.y)
            distance = player_pos.distance_to(entity_pos)
            
            if distance <= range_radius:
                entities_in_range.append(entity)
        
        return entities_in_range
    
    def get_entities_by_position(self, x: int, y: int, radius: int = 1) -> List:
        """
        Get entities at a specific position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            radius: Search radius
            
        Returns:
            List: Entities at the position
        """
        # This would typically query a repository or service
        # For now, we'll return an empty list
        return []
    
    def get_entity_stats(self, entity_id: str) -> QueryResult:
        """
        Get detailed entity statistics.
        
        Args:
            entity_id: ID of the entity
            
        Returns:
            QueryResult: Entity statistics
        """
        # This would typically query a repository or service
        # For now, we'll return a mock response
        return QueryResult(
            success=True,
            data={
                "entity_id": entity_id,
                "name": "Unknown Entity",
                "level": 1,
                "health": 100,
                "max_health": 100,
                "attack_power": 10,
                "defense": 5,
                "speed": 5,
                "experience": 0,
                "gold": 0
            },
            metadata={
                "damage_per_second": 10,
                "survivability": 20,
                "effectiveness": 15,
                "total_power": 30
            }
        )
    
    def get_hostile_entities(self, entities: List) -> List:
        """
        Get all hostile entities.
        
        Args:
            entities: List of entities to check
            
        Returns:
            List: List of hostile entities
        """
        hostile_entities = []
        
        for entity in entities:
            if hasattr(entity, 'is_hostile') and entity.is_hostile:
                hostile_entities.append(entity)
        
        return hostile_entities
    
    def get_neutral_entities(self, entities: List) -> List:
        """
        Get all neutral entities.
        
        Args:
            entities: List of entities to check
            
        Returns:
            List: List of neutral entities
        """
        neutral_entities = []
        
        for entity in entities:
            if hasattr(entity, 'is_hostile') and not entity.is_hostile:
                neutral_entities.append(entity)
        
        return neutral_entities