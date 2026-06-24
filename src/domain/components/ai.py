from typing import Dict, Any, Optional, List, Tuple
from .component import Component
from ..value_objects.position import Position
import random
import math
from enum import Enum


class AIState(Enum):
    """AI state enumeration"""
    IDLE = "idle"
    PATROLLING = "patrolling"
    CHASING = "chasing"
    FLEEING = "fleeing"
    ATTACKING = "attacking"
    DEFENDING = "defending"
    DEAD = "dead"


class AIBehavior(Enum):
    """AI behavior enumeration"""
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    NEUTRAL = "neutral"
    COWARDLY = "cowardly"
    PATROL = "patrol"
    RANDOM = "random"


class AI(Component):
    """AI component for handling entity behavior"""
    
    def __init__(self, component_id: Optional[str] = None):
        super().__init__(component_id)
        self.ai_type = "basic"  # basic, aggressive, defensive, passive, smart
        self.current_state = AIState.IDLE
        self.target_id: Optional[str] = None
        self.patrol_points: List[Position] = []
        self.current_patrol_index = 0
        self.vision_range = 10
        self.attack_range = 1
        self.flee_health_threshold = 0.3  # 30% health
        self.wander_chance = 0.1  # 10% chance to wander
        self.alertness = 1.0  # 1.0 = normal, higher = more alert
        self.memory: Dict[str, Any] = {}  # AI memory
        self.behavior_state = "idle"  # idle, patrolling, chasing, fleeing, attacking
        self.state_timer = 0.0
        self.last_seen_target: Optional[Position] = None
        
    def update(self, delta_time: float, entity: Any) -> None:
        """Update AI behavior"""
        self.state_timer += delta_time
        
        # Get entity position
        entity_pos = getattr(entity, 'position', Position(0, 0))
        
        # Update behavior based on AI type and state
        if self.ai_type == "basic":
            self._update_basic_ai(delta_time, entity, entity_pos)
        elif self.ai_type == "aggressive":
            self._update_aggressive_ai(delta_time, entity, entity_pos)
        elif self.ai_type == "defensive":
            self._update_defensive_ai(delta_time, entity, entity_pos)
        elif self.ai_type == "passive":
            self._update_passive_ai(delta_time, entity, entity_pos)
        elif self.ai_type == "smart":
            self._update_smart_ai(delta_time, entity, entity_pos)
            
    def _update_basic_ai(self, delta_time: float, entity: Any, entity_pos: Position) -> None:
        """Update basic AI behavior"""
        if self.behavior_state == "idle":
            self._handle_idle_state(delta_time, entity_pos)
        elif self.behavior_state == "patrolling":
            self._handle_patrolling_state(delta_time, entity_pos)
        elif self.behavior_state == "chasing":
            self._handle_chasing_state(delta_time, entity, entity_pos)
        elif self.behavior_state == "fleeing":
            self._handle_fleeing_state(delta_time, entity, entity_pos)
            
    def _update_aggressive_ai(self, delta_time: float, entity: Any, entity_pos: Position) -> None:
        """Update aggressive AI behavior"""
        # Aggressive AI is always looking for targets
        if self.target_id is None:
            self._find_target(entity, entity_pos)
            
        if self.target_id:
            # Check if target is visible before chasing
            if self._can_see_target(entity, entity_pos):
                self._handle_chasing_state(delta_time, entity, entity_pos)
            else:
                # Target not visible - clear target and go idle
                self.target_id = None
                self.behavior_state = "idle"
            
    def _update_defensive_ai(self, delta_time: float, entity: Any, entity_pos: Position) -> None:
        """Update defensive AI behavior"""
        # Defensive AI flees when health is low
        health_ratio = self._get_entity_health_ratio(entity)
        if health_ratio < self.flee_health_threshold:
            self.behavior_state = "fleeing"
            self._find_flee_target(entity, entity_pos)
        else:
            self._update_basic_ai(delta_time, entity, entity_pos)
            
    def _update_passive_ai(self, delta_time: float, entity: Any, entity_pos: Position) -> None:
        """Update passive AI behavior"""
        # Passive AI never attacks, only flees when attacked
        if self.target_id and self._was_attacked_by(entity, self.target_id):
            self.behavior_state = "fleeing"
            self._find_flee_target(entity, entity_pos)
        else:
            self.behavior_state = "idle"
            self._handle_idle_state(delta_time, entity_pos)
            
    def _update_smart_ai(self, delta_time: float, entity: Any, entity_pos: Position) -> None:
        """Update smart AI behavior"""
        # Smart AI combines multiple behaviors
        health_ratio = self._get_entity_health_ratio(entity)
        
        if health_ratio < self.flee_health_threshold:
            self.behavior_state = "fleeing"
            self._find_flee_target(entity, entity_pos)
        elif self.target_id and self._can_see_target(entity, entity_pos):
            self.behavior_state = "chasing"
            self._handle_chasing_state(delta_time, entity, entity_pos)
        elif self.target_id and not self._can_see_target(entity, entity_pos):
            self.behavior_state = "searching"
            self._handle_searching_state(delta_time, entity_pos)
        else:
            self.behavior_state = "patrolling"
            self._handle_patrolling_state(delta_time, entity_pos)
            
    def _handle_idle_state(self, delta_time: float, entity_pos: Position) -> None:
        """Handle idle state"""
        if random.random() < self.wander_chance:
            self._wander(entity_pos)
            
    def _handle_patrolling_state(self, delta_time: float, entity_pos: Position) -> None:
        """Handle patrolling state"""
        if self.patrol_points:
            target = self.patrol_points[self.current_patrol_index]
            if entity_pos.distance_to(target) < 1.0:
                self.current_patrol_index = (self.current_patrol_index + 1) % len(self.patrol_points)
            else:
                self._move_towards(target, entity_pos)
                
    def _handle_chasing_state(self, delta_time: float, entity: Any, entity_pos: Position) -> None:
        """Handle chasing state"""
        if self.target_id:
            # Check if target is visible before attacking
            if not self._can_see_target(entity, entity_pos):
                # Target not visible - switch to searching state
                self.behavior_state = "searching"
                self._handle_searching_state(delta_time, entity_pos)
                return
                
            target_pos = self._get_entity_position(entity, self.target_id)
            if target_pos:
                distance = entity_pos.distance_to(target_pos)
                if distance <= self.attack_range:
                    self._attack_target(entity, self.target_id)
                else:
                    self._move_towards(target_pos, entity_pos)
            else:
                self.target_id = None
                self.behavior_state = "idle"
                
    def _handle_fleeing_state(self, delta_time: float, entity: Any, entity_pos: Position) -> None:
        """Handle fleeing state"""
        if self.target_id:
            target_pos = self._get_entity_position(entity, self.target_id)
            if target_pos:
                # Move away from target
                dx = entity_pos.x - target_pos.x
                dy = entity_pos.y - target_pos.y
                
                # Normalize and scale
                distance = (dx**2 + dy**2)**0.5
                if distance > 0:
                    dx = (dx / distance) * 5
                    dy = (dy / distance) * 5
                    
                flee_pos = Position(entity_pos.x + dx, entity_pos.y + dy)
                self._move_towards(flee_pos, entity_pos)
                
    def _handle_searching_state(self, delta_time: float, entity_pos: Position) -> None:
        """Handle searching state"""
        if self.last_seen_target:
            self._move_towards(self.last_seen_target, entity_pos)
        else:
            self._wander(entity_pos)
            
    def _find_target(self, entity: Any, entity_pos: Position) -> None:
        """Find a target to chase"""
        # This would normally scan for visible entities
        # For now, just set a random target
        if random.random() < 0.1:  # 10% chance to find target
            self.target_id = f"target_{random.randint(1, 100)}"
            
    def _find_flee_target(self, entity: Any, entity_pos: Position) -> None:
        """Find a safe location to flee to"""
        # This would normally find the farthest safe point
        # For now, just move in a random direction
        self._wander(entity_pos)
        
    def _wander(self, entity_pos: Position) -> None:
        """Make entity wander randomly"""
        angle = random.uniform(0, 2 * 3.14159)
        distance = random.uniform(1, 3)
        
        new_x = entity_pos.x + distance * math.cos(angle)
        new_y = entity_pos.y + distance * math.sin(angle)
        
        target_pos = Position(int(new_x), int(new_y))
        self._move_towards(target_pos, entity_pos)
        
    def _move_towards(self, target: Position, entity_pos: Position) -> None:
        """Move entity towards target"""
        # This method should be called by behavior engine
        # The actual movement should be handled by the movement component
        # through the behavior script execution
        # For now, we'll keep the old logic but mark it as deprecated
        # TODO: Remove this method when behavior engine is implemented
        # NOTE: This method directly modifies entity position, which is not the intended behavior.
        # The LLM should only update behavior scripts, not directly move monsters.
        # The proper implementation should use the movement component through the behavior engine.
        # We'll log a warning to indicate this is deprecated behavior
        import warnings
        warnings.warn(
            "AI._move_towards is deprecated. Movement should be handled by the movement component through the behavior engine.",
            DeprecationWarning,
            stacklevel=2
        )
        # Keep the old logic for backward compatibility
        dx = target.x - entity_pos.x
        dy = target.y - entity_pos.y
        
        # Normalize to unit movement
        distance = (dx**2 + dy**2)**0.5
        if distance > 0:
            dx = dx / distance
            dy = dy / distance
            
        # Update position
        entity_pos.x += dx
        entity_pos.y += dy
                
        
    def _attack_target(self, entity: Any, target_id: str) -> None:
        """Attack the target"""
        # This would normally call combat component
        pass
        
    def _can_see_target(self, entity: Any, entity_pos: Position) -> bool:
        """Check if target is visible via perception component"""
        if not self.target_id:
            return False
            
        # First check perception component if available
        perception_comp = entity.get_component("perception") if hasattr(entity, 'get_component') else None
        if perception_comp and perception_comp.current_status:
            # Use the perception status to determine if player is visible
            if perception_comp.current_status.can_see_player:
                return True
            
        # Fallback to distance-based check
        target_pos = self._get_entity_position(entity, self.target_id)
        if not target_pos:
            return False
            
        distance = entity_pos.distance_to(target_pos)
        return distance <= self.vision_range
        
    def _get_entity_position(self, entity: Any, entity_id: str) -> Optional[Position]:
        """Get position of entity by ID"""
        # This would normally look up entity in game world
        # For now, return None
        return None
        
    def _get_entity_health_ratio(self, entity: Any) -> float:
        """Get entity health as ratio (0.0 to 1.0)"""
        # This would normally get entity health
        return 1.0
        
    def _was_attacked_by(self, entity: Any, attacker_id: str) -> bool:
        """Check if entity was recently attacked by someone"""
        # This would normally check combat events
        return False
        
    def set_ai_type(self, ai_type: str) -> None:
        """Set AI type"""
        self.ai_type = ai_type
        
    def set_target(self, target_id: str) -> None:
        """Set target ID"""
        self.target_id = target_id
        
    def clear_target(self) -> None:
        """Clear target"""
        self.target_id = None
        
    def add_patrol_point(self, position: Position) -> None:
        """Add patrol point"""
        self.patrol_points.append(position)
        
    def clear_patrol_points(self) -> None:
        """Clear all patrol points"""
        self.patrol_points.clear()
        self.current_patrol_index = 0
        
    def set_vision_range(self, range: int) -> None:
        """Set vision range"""
        self.vision_range = max(0, range)
        
    def set_attack_range(self, range: int) -> None:
        """Set attack range"""
        self.attack_range = max(0, range)
        
    def set_flee_health_threshold(self, threshold: float) -> None:
        """Set flee health threshold"""
        self.flee_health_threshold = max(0.0, min(1.0, threshold))
        
    def set_wander_chance(self, chance: float) -> None:
        """Set wander chance"""
        self.wander_chance = max(0.0, min(1.0, chance))
        
    def set_alertness(self, alertness: float) -> None:
        """Set alertness level"""
        self.alertness = max(0.0, alertness)
        
    def get_behavior_state(self) -> str:
        """Get current behavior state"""
        return self.behavior_state
        
    def get_target_id(self) -> Optional[str]:
        """Get target ID"""
        return self.target_id
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "ai_type": self.ai_type,
            "target_id": self.target_id,
            "patrol_points": [pos.to_dict() for pos in self.patrol_points],
            "current_patrol_index": self.current_patrol_index,
            "vision_range": self.vision_range,
            "attack_range": self.attack_range,
            "flee_health_threshold": self.flee_health_threshold,
            "wander_chance": self.wander_chance,
            "alertness": self.alertness,
            "memory": self.memory,
            "behavior_state": self.behavior_state,
            "state_timer": self.state_timer,
            "last_seen_target": self.last_seen_target.to_dict() if self.last_seen_target else None
        })
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AI':
        """Create AI component from dictionary"""
        ai = cls()
        ai.enabled = data.get("enabled", True)
        ai.ai_type = data.get("ai_type", "basic")
        ai.target_id = data.get("target_id")
        ai.patrol_points = [Position.from_dict(pos) for pos in data.get("patrol_points", [])]
        ai.current_patrol_index = data.get("current_patrol_index", 0)
        ai.vision_range = data.get("vision_range", 10)
        ai.attack_range = data.get("attack_range", 1)
        ai.flee_health_threshold = data.get("flee_health_threshold", 0.3)
        ai.wander_chance = data.get("wander_chance", 0.1)
        ai.alertness = data.get("alertness", 1.0)
        ai.memory = data.get("memory", {})
        ai.behavior_state = data.get("behavior_state", "idle")
        ai.state_timer = data.get("state_timer", 0.0)
        ai.last_seen_target = Position.from_dict(data["last_seen_target"]) if data.get("last_seen_target") else None
        return ai