from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class Position:
    """Position value object representing coordinates in 2D space"""
    x: int
    y: int
    
    def __post_init__(self) -> None:
        """Validate position values"""
        if not isinstance(self.x, int):
            raise TypeError("Position x must be an integer")
        if not isinstance(self.y, int):
            raise TypeError("Position y must be an integer")
            
    def distance_to(self, other: 'Position') -> float:
        """Calculate distance to another position"""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
        
    def manhattan_distance_to(self, other: 'Position') -> int:
        """Calculate Manhattan distance to another position"""
        return abs(self.x - other.x) + abs(self.y - other.y)
        
    def is_adjacent_to(self, other: 'Position') -> bool:
        """Check if position is adjacent to another position"""
        return self.manhattan_distance_to(other) == 1
        
    def is_within_distance(self, other: 'Position', distance: int) -> bool:
        """Check if position is within a certain distance of another position"""
        return self.distance_to(other) <= distance
        
    def get_direction_to(self, other: 'Position') -> Tuple[int, int]:
        """Get direction vector to another position"""
        dx = other.x - self.x
        dy = other.y - self.y
        
        # Normalize to unit direction
        if dx != 0:
            dx = 1 if dx > 0 else -1
        if dy != 0:
            dy = 1 if dy > 0 else -1
            
        return (dx, dy)
        
    def move(self, dx: int, dy: int) -> 'Position':
        """Create new position by moving by given deltas"""
        return Position(self.x + dx, self.y + dy)
        
    def translate(self, dx: int, dy: int) -> None:
        """Move position by given deltas"""
        self.x += dx
        self.y += dy
        
    def __eq__(self, other: object) -> bool:
        """Check if positions are equal"""
        if not isinstance(other, Position):
            return False
        return self.x == other.x and self.y == other.y
        
    def __hash__(self) -> int:
        """Hash position for use in sets/dictionaries"""
        return hash((self.x, self.y))
        
    def __str__(self) -> str:
        """String representation"""
        return f"({self.x}, {self.y})"
        
    def __repr__(self) -> str:
        """Detailed string representation"""
        return f"Position(x={self.x}, y={self.y})"
        
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {"x": self.x, "y": self.y}
        
    @classmethod
    def from_dict(cls, data: dict) -> 'Position':
        """Create position from dictionary"""
        return cls(x=data["x"], y=data["y"])
        
    @classmethod
    def from_tuple(cls, coords: Tuple[int, int]) -> 'Position':
        """Create position from tuple"""
        return cls(x=coords[0], y=coords[1])