"""Repository interface for data access abstraction."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar('T')


class Repository(ABC, Generic[T]):
    """Base repository interface following the Repository pattern."""
    
    @abstractmethod
    def get_by_id(self, entity_id: str) -> T | None:
        """Retrieve an entity by its ID."""
        pass
    
    @abstractmethod
    def get_all(self) -> list[T]:
        """Retrieve all entities."""
        pass
    
    @abstractmethod
    def add(self, entity: T) -> None:
        """Add a new entity."""
        pass
    
    @abstractmethod
    def update(self, entity: T) -> None:
        """Update an existing entity."""
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID."""
        pass