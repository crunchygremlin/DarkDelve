from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from uuid import uuid4


class Component(ABC):
    """Base class for all entity components"""
    
    def __init__(self, component_id: Optional[str] = None):
        self.id = component_id or str(uuid4())
        self.enabled = True
        
    def enable(self) -> None:
        """Enable the component"""
        self.enabled = True
        
    def disable(self) -> None:
        """Disable the component"""
        self.enabled = False
        
    def is_enabled(self) -> bool:
        """Check if component is enabled"""
        return self.enabled
        
    @abstractmethod
    def update(self, delta_time: float, entity: Any) -> None:
        """Update component state"""
        pass
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary for serialization"""
        return {
            "id": self.id,
            "enabled": self.enabled,
            "type": self.__class__.__name__
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Component':
        """Create component from dictionary"""
        # This should be overridden by subclasses
        component = cls()
        component.enabled = data.get("enabled", True)
        return component