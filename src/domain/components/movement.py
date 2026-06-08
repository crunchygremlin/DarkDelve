from typing import Dict, Any, Optional, List, Tuple
from .component import Component
from ..value_objects.position import Position


class Movement(Component):
    """Movement component for handling entity movement"""
    
    def __init__(self, component_id: Optional[str] = None):
        super().__init__(component_id)
        self.speed = 5.0  # tiles per second
        self.position = Position(0, 0)
        self.target_position: Optional[Position] = None
        self.path: List[Position] = []
        self.is_moving = False
        self.move_progress = 0.0
        self.current_position = Position(0, 0)
        self.previous_position = Position(0, 0)
        self.move_cooldown = 0.0
        self.can_move_diagonally = True
        self.move_cost_modifier = 1.0
        self.teleport_cooldown = 0.0
        
    def set_position(self, position: Position) -> None:
        """Set current position"""
        self.previous_position = Position(self.current_position.x, self.current_position.y)
        self.current_position = Position(position.x, position.y)
        self.position = Position(position.x, position.y)
        
    def get_position(self) -> Position:
        """Get current position"""
        return Position(self.current_position.x, self.current_position.y)
        
    def set_target_position(self, target: Position) -> bool:
        """Set target position for movement"""
        if self.move_cooldown > 0:
            return False
            
        self.target_position = Position(target.x, target.y)
        self.is_moving = True
        self.move_progress = 0.0
        return True
        
    def move_to(self, target: Position) -> bool:
        """Move to target position"""
        return self.set_target_position(target)
        
    def move_by(self, dx: int, dy: int) -> bool:
        """Move by offset from current position"""
        new_position = Position(self.current_position.x + dx, self.current_position.y + dy)
        return self.set_target_position(new_position)
        
    def stop_movement(self) -> None:
        """Stop current movement"""
        self.is_moving = False
        self.target_position = None
        self.path = []
        self.move_progress = 0.0
        
    def update(self, delta_time: float, entity: Any) -> None:
        """Update movement"""
        # Update cooldowns
        if self.move_cooldown > 0:
            self.move_cooldown = max(0, self.move_cooldown - delta_time)
            
        if self.teleport_cooldown > 0:
            self.teleport_cooldown = max(0, self.teleport_cooldown - delta_time)
            
        # Handle movement
        if self.is_moving and self.target_position:
            self._update_movement(delta_time)
            
    def _update_movement(self, delta_time: float) -> None:
        """Update movement logic"""
        if not self.target_position:
            self.stop_movement()
            return
            
        # Calculate distance to target
        distance = self.current_position.distance_to(self.target_position)
        
        if distance < 0.1:  # Close enough to target
            self.set_position(self.target_position)
            self.stop_movement()
            return
            
        # Calculate movement
        move_distance = self.speed * self.move_cost_modifier * delta_time
        
        # Normalize direction
        dx = self.target_position.x - self.current_position.x
        dy = self.target_position.y - self.current_position.y
        
        # Normalize to unit vector
        if distance > 0:
            dx /= distance
            dy /= distance
            
        # Apply movement
        new_x = self.current_position.x + dx * move_distance
        new_y = self.current_position.y + dy * move_distance
        
        # Update position
        self.previous_position = Position(self.current_position.x, self.current_position.y)
        self.current_position = Position(new_x, new_y)
        self.position = Position(new_x, new_y)
        
        # Check if reached target
        if self.current_position.distance_to(self.target_position) < 0.1:
            self.set_position(self.target_position)
            self.stop_movement()
            
    def get_move_cost(self, target: Position) -> float:
        """Get movement cost to target position"""
        distance = self.current_position.distance_to(target)
        return distance * self.move_cost_modifier
        
    def can_reach_position(self, target: Position, max_distance: Optional[float] = None) -> bool:
        """Check if position can be reached"""
        if max_distance is None:
            max_distance = self.speed
            
        distance = self.current_position.distance_to(target)
        return distance <= max_distance and self.move_cooldown <= 0
        
    def teleport_to(self, position: Position, cooldown: float = 1.0) -> bool:
        """Teleport to position"""
        if self.teleport_cooldown > 0:
            return False
            
        self.previous_position = Position(self.current_position.x, self.current_position.y)
        self.current_position = Position(position.x, position.y)
        self.position = Position(position.x, position.y)
        self.teleport_cooldown = cooldown
        return True
        
    def get_direction_to(self, target: Position) -> Tuple[int, int]:
        """Get direction vector to target"""
        return self.current_position.get_direction_to(target)
        
    def is_adjacent_to(self, position: Position) -> bool:
        """Check if adjacent to position"""
        return self.current_position.is_adjacent_to(position)
        
    def get_movement_info(self) -> Dict[str, Any]:
        """Get movement information"""
        return {
            "position": self.position.to_dict(),
            "target_position": self.target_position.to_dict() if self.target_position else None,
            "is_moving": self.is_moving,
            "speed": self.speed,
            "move_cooldown": self.move_cooldown,
            "teleport_cooldown": self.teleport_cooldown,
            "can_move_diagonally": self.can_move_diagonally,
            "move_cost_modifier": self.move_cost_modifier
        }
        
    def set_speed(self, speed: float) -> None:
        """Set movement speed"""
        self.speed = max(0, speed)
        
    def set_move_cooldown(self, cooldown: float) -> None:
        """Set movement cooldown"""
        self.move_cooldown = max(0, cooldown)
        
    def set_teleport_cooldown(self, cooldown: float) -> None:
        """Set teleport cooldown"""
        self.teleport_cooldown = max(0, cooldown)
        
    def set_can_move_diagonally(self, can_move: bool) -> None:
        """Set whether entity can move diagonally"""
        self.can_move_diagonally = can_move
        
    def set_move_cost_modifier(self, modifier: float) -> None:
        """Set movement cost modifier"""
        self.move_cost_modifier = max(0.1, modifier)
        
    def clear_path(self) -> None:
        """Clear current path"""
        self.path = []
        
    def set_path(self, path: List[Position]) -> None:
        """Set movement path"""
        self.path = path.copy()
        
    def get_next_waypoint(self) -> Optional[Position]:
        """Get next waypoint in path"""
        if self.path:
            return self.path[0]
        return None
        
    def remove_waypoint(self) -> None:
        """Remove current waypoint"""
        if self.path:
            self.path.pop(0)
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "speed": self.speed,
            "position": self.position.to_dict(),
            "target_position": self.target_position.to_dict() if self.target_position else None,
            "path": [pos.to_dict() for pos in self.path],
            "is_moving": self.is_moving,
            "move_progress": self.move_progress,
            "current_position": self.current_position.to_dict(),
            "previous_position": self.previous_position.to_dict(),
            "move_cooldown": self.move_cooldown,
            "can_move_diagonally": self.can_move_diagonally,
            "move_cost_modifier": self.move_cost_modifier,
            "teleport_cooldown": self.teleport_cooldown
        })
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Movement':
        """Create movement component from dictionary"""
        movement = cls()
        movement.enabled = data.get("enabled", True)
        movement.speed = data.get("speed", 5.0)
        movement.position = Position.from_dict(data.get("position", {"x": 0, "y": 0}))
        movement.target_position = Position.from_dict(data["target_position"]) if data.get("target_position") else None
        movement.path = [Position.from_dict(pos) for pos in data.get("path", [])]
        movement.is_moving = data.get("is_moving", False)
        movement.move_progress = data.get("move_progress", 0.0)
        movement.current_position = Position.from_dict(data.get("current_position", {"x": 0, "y": 0}))
        movement.previous_position = Position.from_dict(data.get("previous_position", {"x": 0, "y": 0}))
        movement.move_cooldown = data.get("move_cooldown", 0.0)
        movement.can_move_diagonally = data.get("can_move_diagonally", True)
        movement.move_cost_modifier = data.get("move_cost_modifier", 1.0)
        movement.teleport_cooldown = data.get("teleport_cooldown", 0.0)
        return movement