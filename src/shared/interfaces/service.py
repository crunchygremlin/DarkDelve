"""Service interfaces for domain services following Dependency Inversion Principle."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class ICombatService(ABC):
    """Interface for combat-related operations."""
    
    @abstractmethod
    def execute_attack(self, attacker: Any, target: Any) -> Dict[str, Any]:
        """Execute an attack from attacker to target."""
        pass
    
    @abstractmethod
    def can_attack(self, attacker: Any, target: Any) -> bool:
        """Check if attacker can attack target."""
        pass
    
    @abstractmethod
    def calculate_damage(self, attacker: Any, target: Any) -> int:
        """Calculate damage for an attack."""
        pass


class IMovementService(ABC):
    """Interface for movement-related operations."""
    
    @abstractmethod
    def move_entity(self, entity: Any, target_position: Any) -> bool:
        """Move an entity to a target position."""
        pass
    
    @abstractmethod
    def can_move_to(self, entity: Any, target_position: Any) -> bool:
        """Check if an entity can move to a target position."""
        pass


class ISocialService(ABC):
    """Interface for social-related operations."""
    
    @abstractmethod
    def is_ally(self, entity1: Any, entity2: Any) -> bool:
        """Check if two entities are allies."""
        pass
    
    @abstractmethod
    def get_loyalty_score(self, entity_id: str) -> float:
        """Get loyalty score for an entity."""
        pass


class Service(ABC):
    """Base service interface."""
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the service."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up service resources."""
        pass