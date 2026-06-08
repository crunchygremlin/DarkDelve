from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import uuid4


class Entity(ABC):
    """Base class for all game entities"""
    
    def __init__(self, entity_id: Optional[str] = None, name: str = "Unknown"):
        self.id = entity_id or str(uuid4())
        self.name = name
        self.components: Dict[str, Any] = {}
        
    def add_component(self, component_name: str, component: Any) -> None:
        """Add a component to the entity"""
        self.components[component_name] = component
        
    def get_component(self, component_name: str) -> Optional[Any]:
        """Get a component from the entity"""
        return self.components.get(component_name)
        
    def has_component(self, component_name: str) -> bool:
        """Check if entity has a specific component"""
        return component_name in self.components
        
    def remove_component(self, component_name: str) -> bool:
        """Remove a component from the entity"""
        if component_name in self.components:
            del self.components[component_name]
            return True
        return False
        
    @abstractmethod
    def update(self, delta_time: float) -> None:
        """Update the entity state"""
        pass
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "components": {k: str(v) for k, v in self.components.items()}
        }