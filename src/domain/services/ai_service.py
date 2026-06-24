"""
AI service for handling entity AI and decision making.
"""
from typing import List, Dict, Any, Optional, Tuple, Set
from enum import Enum
from ..entities.player import Player
from ..entities.mob import Mob
from ..entities.item import Item
from ..components.ai import AI, AIState, AIBehavior
from ..components.movement import Movement
from ..components.combat import Combat
from ..value_objects.position import Position
from typing import Any
import time


def distance_between(pos1: Any, pos2: Any) -> float:
    """Calculate distance between two positions."""
    return ((pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2) ** 0.5


class AIStrategy(Enum):
    """AI strategy types."""
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    NEUTRAL = "neutral"
    COWARDLY = "cowardly"
    PATROL = "patrol"
    RANDOM = "random"


class AIService:
    """
    Service for handling entity AI and decision making.
    
    Implements the Service pattern for AI management.
    """
    
    def __init__(self):
        """Initialize the AI service."""
        self.ai_states: Dict[str, AIState] = {}
        self.ai_strategies: Dict[str, AIStrategy] = {}
        self.ai_events: List[Dict[str, Any]] = []
        self.patrol_routes: Dict[str, List[Position]] = {}
        self.target_memory: Dict[str, Optional[str]] = {}
        self.action_cooldowns: Dict[str, Dict[str, float]] = {}
    
    def update_ai(self, entity: Any, delta_time: float, game_state: Dict[str, Any]) -> None:
        """
        Update AI for an entity.
        
        Args:
            entity: The entity to update AI for
            delta_time: Time since last update
            game_state: Current game state
        """
        if not hasattr(entity, 'ai') or not entity.ai.enabled:
            return
        
        # Update action cooldowns
        self.update_action_cooldowns(entity, delta_time)
        
        # Get AI strategy
        strategy = self.get_ai_strategy(entity)
        
        # Execute AI behavior based on strategy
        if strategy == AIStrategy.AGGRESSIVE:
            self.execute_aggressive_ai(entity, game_state)
        elif strategy == AIStrategy.DEFENSIVE:
            self.execute_defensive_ai(entity, game_state)
        elif strategy == AIStrategy.NEUTRAL:
            self.execute_neutral_ai(entity, game_state)
        elif strategy == AIStrategy.COWARDLY:
            self.execute_cowardly_ai(entity, game_state)
        elif strategy == AIStrategy.PATROL:
            self.execute_patrol_ai(entity, game_state)
        elif strategy == AIStrategy.RANDOM:
            self.execute_random_ai(entity, game_state)
        
        # Update AI state
        self.ai_states[entity.id] = entity.ai.current_state
        
        # Record AI event
        event = {
            "event_type": "ai_update",
            "entity_id": entity.id,
            "entity_name": entity.name,
            "ai_state": entity.ai.current_state.value,
            "strategy": strategy.value,
            "timestamp": self.get_current_timestamp()
        }
        self.ai_events.append(event)
    
    def get_ai_strategy(self, entity: Any) -> AIStrategy:
        """
        Get AI strategy for an entity.
        
        Args:
            entity: The entity to get strategy for
            
        Returns:
            AIStrategy: AI strategy
        """
        if entity.id in self.ai_strategies:
            return self.ai_strategies[entity.id]
        
        # Default strategy based on entity type
        if hasattr(entity, 'mob_type'):
            if entity.mob_type == "goblin":
                return AIStrategy.AGGRESSIVE
            elif entity.mob_type == "skeleton":
                return AIStrategy.DEFENSIVE
            elif entity.mob_type == "slime":
                return AIStrategy.NEUTRAL
            elif entity.mob_type == "rat":
                return AIStrategy.COWARDLY
        
        return AIStrategy.NEUTRAL
    
    def set_ai_strategy(self, entity: Any, strategy: AIStrategy) -> None:
        """
        Set AI strategy for an entity.
        
        Args:
            entity: The entity to set strategy for
            strategy: AI strategy to set
        """
        self.ai_strategies[entity.id] = strategy
    
    def execute_aggressive_ai(self, entity: Any, game_state: Dict[str, Any]) -> None:
        """
        Execute aggressive AI behavior.
        
        Args:
            entity: The entity to execute AI for
            game_state: Current game state
        """
        # Find nearest enemy
        nearest_enemy = self.find_nearest_enemy(entity, game_state.get("entities", []))
        
        if nearest_enemy:
            # Move towards enemy
            if self.can_attack(entity, nearest_enemy):
                self.execute_attack(entity, nearest_enemy)
            else:
                self.move_towards_target(entity, nearest_enemy.position)
        else:
            # Patrol or random movement
            self.execute_patrol_ai(entity, game_state)
    
    def execute_defensive_ai(self, entity: Any, game_state: Dict[str, Any]) -> None:
        """
        Execute defensive AI behavior.
        
        Args:
            entity: The entity to execute AI for
            game_state: Current game state
        """
        # Find nearest enemy
        nearest_enemy = self.find_nearest_enemy(entity, game_state.get("entities", []))
        
        if nearest_enemy:
            # Check if enemy is too close
            distance = entity.position.distance_to(nearest_enemy.position)
            if distance < 3:
                # Move away from enemy
                self.move_away_from_target(entity, nearest_enemy.position)
            else:
                # Stay in place or patrol
                self.execute_patrol_ai(entity, game_state)
        else:
            # Patrol or random movement
            self.execute_patrol_ai(entity, game_state)
    
    def execute_neutral_ai(self, entity: Any, game_state: Dict[str, Any]) -> None:
        """
        Execute neutral AI behavior.
        
        Args:
            entity: The entity to execute AI for
            game_state: Current game state
        """
        # Find nearest enemy
        nearest_enemy = self.find_nearest_enemy(entity, game_state.get("entities", []))
        
        if nearest_enemy:
            distance = entity.position.distance_to(nearest_enemy.position)
            if distance < 2:
                # Attack if very close
                if self.can_attack(entity, nearest_enemy):
                    self.execute_attack(entity, nearest_enemy)
            else:
                # Ignore or move away slightly
                self.execute_patrol_ai(entity, game_state)
        else:
            # Patrol or random movement
            self.execute_patrol_ai(entity, game_state)
    
    def execute_cowardly_ai(self, entity: Any, game_state: Dict[str, Any]) -> None:
        """
        Execute cowardly AI behavior.
        
        Args:
            entity: The entity to execute AI for
            game_state: Current game state
        """
        # Find nearest enemy
        nearest_enemy = self.find_nearest_enemy(entity, game_state.get("entities", []))
        
        if nearest_enemy:
            # Always move away from enemies
            self.move_away_from_target(entity, nearest_enemy.position)
        else:
            # Patrol or random movement
            self.execute_patrol_ai(entity, game_state)
    
    def execute_patrol_ai(self, entity: Any, game_state: Dict[str, Any]) -> None:
        """
        Execute patrol AI behavior.
        
        Args:
            entity: The entity to execute AI for
            game_state: Current game state
        """
        if entity.id in self.patrol_routes:
            # Follow patrol route
            patrol_route = self.patrol_routes[entity.id]
            current_target = self.get_patrol_target(entity, patrol_route)
            
            if current_target:
                self.move_towards_target(entity, current_target)
        else:
            # Random movement
            self.execute_random_ai(entity, game_state)
    
    def execute_random_ai(self, entity: Any, game_state: Dict[str, Any]) -> None:
        """
        Execute random AI behavior.
        
        Args:
            entity: The entity to execute AI for
            game_state: Current game state
        """
        # Random movement
        if self.is_action_ready(entity, "move"):
            import random
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
            dx, dy = random.choice(directions)
            new_position = Position(entity.position.x + dx, entity.position.y + dy)
            
            if self.can_move_to(entity, new_position):
                # Use movement component if available, otherwise update position directly
                movement_comp = entity.get_component("movement") if hasattr(entity, 'get_component') else None
                if movement_comp:
                    movement_comp.set_position(new_position)
                else:
                    entity.position = new_position
                self.set_action_cooldown(entity, "move", 1.0)
    
    def find_nearest_enemy(self, entity: Any, entities: List[Any]) -> Optional[Any]:
        """
        Find the nearest enemy to an entity.
        
        Args:
            entity: The entity to find enemy for
            entities: List of entities to search
            
        Returns:
            Optional[Any]: Nearest enemy or None
        """
        nearest_enemy = None
        min_distance = float('inf')
        
        for other_entity in entities:
            if other_entity.id != entity.id:
                # Check if entities are enemies
                if self.are_enemies(entity, other_entity):
                    distance = entity.position.distance_to(other_entity.position)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_enemy = other_entity
        
        return nearest_enemy
    
    def are_enemies(self, entity1: Any, entity2: Any) -> bool:
        """
        Check if two entities are enemies.
        
        Args:
            entity1: First entity
            entity2: Second entity
            
        Returns:
            bool: True if entities are enemies, False otherwise
        """
        # Simple enemy detection - can be enhanced with faction system
        if hasattr(entity1, 'mob_type') and hasattr(entity2, 'mob_type'):
            return entity1.mob_type != entity2.mob_type
        elif hasattr(entity1, 'mob_type') and hasattr(entity2, 'player'):
            return True
        elif hasattr(entity1, 'player') and hasattr(entity2, 'mob_type'):
            return True
        
        return False
    
    def can_attack(self, entity: Any, target: Any) -> bool:
        """
        Check if an entity can attack a target.
        
        Args:
            entity: The entity attempting to attack
            target: The target to attack
            
        Returns:
            bool: True if attack is possible, False otherwise
        """
        if not hasattr(entity, 'combat'):
            return False
        
        # Check if combat component can attack (requires current_time)
        current_time = time.time()
        if not entity.combat.can_attack(current_time):
            return False
        
        # Check range
        distance = entity.position.distance_to(target.position)
        return distance <= entity.combat.attack_range
    
    def execute_attack(self, entity: Any, target: Any) -> None:
        """
        Execute an attack.
        
        Args:
            entity: The entity attacking
            target: The target being attacked
        """
        if self.is_action_ready(entity, "attack"):
            # Perform attack
            if hasattr(entity, 'combat') and hasattr(target, 'health'):
                target.health -= entity.combat.damage
                self.set_action_cooldown(entity, "attack", 2.0)
                
                # Record AI event
                event = {
                    "event_type": "ai_attack",
                    "entity_id": entity.id,
                    "target_id": target.id,
                    "timestamp": self.get_current_timestamp()
                }
                self.ai_events.append(event)
    
    def move_towards_target(self, entity: Any, target_position: Position) -> None:
        """
        Move entity towards a target position.
        
        Args:
            entity: The entity to move
            target_position: Target position
        """
        if self.is_action_ready(entity, "move"):
            # Simple movement towards target
            dx = target_position.x - entity.position.x
            dy = target_position.y - entity.position.y
            
            # Normalize movement
            if abs(dx) > abs(dy):
                move_x = 1 if dx > 0 else -1
                move_y = 0
            else:
                move_x = 0
                move_y = 1 if dy > 0 else -1
            
            new_position = Position(entity.position.x + move_x, entity.position.y + move_y)
            
            if self.can_move_to(entity, new_position):
                # Use movement component if available
                movement_comp = entity.get_component("movement") if hasattr(entity, 'get_component') else None
                if movement_comp:
                    movement_comp.set_position(new_position)
                else:
                    entity.position = new_position
                self.set_action_cooldown(entity, "move", 0.5)
    
    def move_away_from_target(self, entity: Any, target_position: Position) -> None:
        """
        Move entity away from a target position.
        
        Args:
            entity: The entity to move
            target_position: Target position to move away from
        """
        if self.is_action_ready(entity, "move"):
            # Calculate direction away from target
            dx = entity.position.x - target_position.x
            dy = entity.position.y - target_position.y
            
            # Normalize movement
            if abs(dx) > abs(dy):
                move_x = 1 if dx > 0 else -1
                move_y = 0
            else:
                move_x = 0
                move_y = 1 if dy > 0 else -1
            
            new_position = Position(entity.position.x + move_x, entity.position.y + move_y)
            
            if self.can_move_to(entity, new_position):
                # Use movement component if available
                movement_comp = entity.get_component("movement") if hasattr(entity, 'get_component') else None
                if movement_comp:
                    movement_comp.set_position(new_position)
                else:
                    entity.position = new_position
                self.set_action_cooldown(entity, "move", 0.5)
    
    def can_move_to(self, entity: Any, position: Position) -> bool:
        """
        Check if entity can move to a position.
        
        Args:
            entity: The entity to check
            position: Target position
            
        Returns:
            bool: True if movement is possible, False otherwise
        """
        # Check bounds
        if position.x < 0 or position.x >= 100 or position.y < 0 or position.y >= 100:
            return False
        
        # Check if entity has movement capability
        movement_comp = entity.get_component("movement") if hasattr(entity, 'get_component') else None
        if movement_comp:
            return movement_comp.can_move()
        else:
            # Fallback: check if entity has position attribute
            return hasattr(entity, 'position')
    
    def set_patrol_route(self, entity: Any, route: List[Position]) -> None:
        """
        Set patrol route for an entity.
        
        Args:
            entity: The entity to set patrol route for
            route: List of positions in patrol route
        """
        self.patrol_routes[entity.id] = route
    
    def get_patrol_target(self, entity: Any, route: List[Position]) -> Optional[Position]:
        """
        Get current patrol target for an entity.
        
        Args:
            entity: The entity to get patrol target for
            route: Patrol route
            
        Returns:
            Optional[Position]: Current patrol target or None
        """
        if not route:
            return None
        
        # Find closest point in route
        min_distance = float('inf')
        closest_point = None
        
        for point in route:
            distance = entity.position.distance_to(point)
            if distance < min_distance:
                min_distance = distance
                closest_point = point
        
        return closest_point
    
    def set_action_cooldown(self, entity: Any, action: str, duration: float) -> None:
        """
        Set action cooldown.
        
        Args:
            entity: The entity to set cooldown for
            action: Action name
            duration: Cooldown duration in seconds
        """
        if entity.id not in self.action_cooldowns:
            self.action_cooldowns[entity.id] = {}
        
        self.action_cooldowns[entity.id][action] = duration
    
    def is_action_ready(self, entity: Any, action: str) -> bool:
        """
        Check if an action is ready (off cooldown).
        
        Args:
            entity: The entity to check
            action: Action name
            
        Returns:
            bool: True if action is ready, False otherwise
        """
        if entity.id not in self.action_cooldowns:
            return True
        
        if action not in self.action_cooldowns[entity.id]:
            return True
        
        return self.action_cooldowns[entity.id][action] <= 0
    
    def update_action_cooldowns(self, entity: Any, delta_time: float) -> None:
        """
        Update action cooldowns.
        
        Args:
            entity: The entity to update cooldowns for
            delta_time: Time since last update
        """
        if entity.id not in self.action_cooldowns:
            return
        
        for action in list(self.action_cooldowns[entity.id].keys()):
            self.action_cooldowns[entity.id][action] -= delta_time
            
            # Remove expired cooldowns
            if self.action_cooldowns[entity.id][action] <= 0:
                del self.action_cooldowns[entity.id][action]
    
    def get_ai_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get AI events.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List[Dict[str, Any]]: AI events
        """
        return self.ai_events[-limit:]
    
    def get_current_timestamp(self) -> str:
        """
        Get current timestamp.
        
        Returns:
            str: Current timestamp
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def clear_ai_events(self) -> None:
        """Clear all AI events."""
        self.ai_events.clear()
    
    def reset_ai_state(self, entity: Any) -> None:
        """
        Reset AI state for an entity.
        
        Args:
            entity: The entity to reset AI state for
        """
        if entity.id in self.ai_states:
            del self.ai_states[entity.id]
        
        if entity.id in self.ai_strategies:
            del self.ai_strategies[entity.id]
        
        if entity.id in self.patrol_routes:
            del self.patrol_routes[entity.id]
        
        if entity.id in self.target_memory:
            del self.target_memory[entity.id]
        
        if entity.id in self.action_cooldowns:
            del self.action_cooldowns[entity.id]