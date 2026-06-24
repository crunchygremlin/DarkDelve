"""Flee strategy service for handling entity flee behavior."""

from typing import Any, Dict, List, Optional
from src.domain.value_objects.position import Position


class FleeStrategy:
    """
    Strategy for calculating and executing flee behavior.
    
    This service encapsulates the flee logic, separating it from the ActionDispatcher
    to improve SRP and testability.
    """
    
    def __init__(self, flee_distance: int = 5):
        """Initialize the FleeStrategy.
        
        Args:
            flee_distance: Distance to move when fleeing (default 5 units)
        """
        self.flee_distance = flee_distance
    
    def calculate_flee_position(
        self,
        entity: Any,
        threat: Any
    ) -> Optional[Position]:
        """Calculate the position an entity should flee to.
        
        Args:
            entity: The entity fleeing
            threat: The threat being fled from
            
        Returns:
            Optional[Position]: The flee position, or None if calculation failed
        """
        if not hasattr(entity, 'position') or not hasattr(threat, 'position'):
            return None
        
        if entity.position is None or threat.position is None:
            return None
        
        # Calculate direction away from threat
        dx = entity.position.x - threat.position.x
        dy = entity.position.y - threat.position.y
        
        # Normalize to unit vector
        distance = (dx**2 + dy**2)**0.5
        if distance == 0:
            # Entities at same position, pick random direction
            dx, dy = 1, 0
            distance = 1
        
        dx = (dx / distance) * self.flee_distance
        dy = (dy / distance) * self.flee_distance
        
        return Position(int(entity.position.x + dx), int(entity.position.y + dy))
    
    def find_threat(
        self,
        entity: Any,
        all_entities: List[Any]
    ) -> Optional[Any]:
        """Find the nearest threat to an entity.
        
        Args:
            entity: The entity to find a threat for
            all_entities: List of all entities in the game
            
        Returns:
            Optional[Any]: The nearest threat, or None if no threat found
        """
        threat = None
        threat_distance = float('inf')
        
        for e in all_entities:
            if e.id == entity.id:
                continue
            if not hasattr(e, 'is_alive') or not e.is_alive():
                continue
            if not hasattr(e, 'position') or not hasattr(entity, 'position'):
                continue
            
            distance = entity.position.distance_to(e.position)
            if distance < threat_distance:
                threat_distance = distance
                threat = e
        
        return threat
    
    def execute_flee(
        self,
        entity: Any,
        threat: Any,
        movement_service: Any,
        event_bus: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Execute the flee action.
        
        Args:
            entity: The entity fleeing
            threat: The threat being fled from
            movement_service: Service for movement operations
            event_bus: Optional event bus for publishing events
            
        Returns:
            Dict[str, Any]: Result of the flee action
        """
        flee_pos = self.calculate_flee_position(entity, threat)
        
        if not flee_pos:
            return {"success": False, "message": "Cannot calculate flee position"}
        
        if movement_service.can_move_to(entity, flee_pos):
            success = movement_service.move_entity(entity, flee_pos)
            if success:
                if event_bus:
                    from src.shared.events.event import EventType
                    event_bus.publish_event_by_type(EventType.ENTITY_FLED.value)
                return {
                    "success": True,
                    "message": f"Fled from {threat.name} to {flee_pos.x},{flee_pos.y}",
                    "from_position": {"x": entity.position.x, "y": entity.position.y},
                    "to_position": {"x": flee_pos.x, "y": flee_pos.y}
                }
            else:
                return {"success": False, "message": "Could not move to flee position"}
        else:
            return {"success": False, "message": "Flee position is blocked or out of bounds"}