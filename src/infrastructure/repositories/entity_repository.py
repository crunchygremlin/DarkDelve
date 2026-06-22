"""Entity repository for data access."""

from typing import Optional

from src.domain.entities.entity import Entity
from src.shared.interfaces.repository import Repository


class EntityRepository(Repository[Entity]):
    """Repository for entity data access."""
    
    def __init__(self):
        self._entities: dict[str, Entity] = {}
    
    def get_by_id(self, entity_id: str) -> Entity | None:
        """Retrieve an entity by its ID."""
        return self._entities.get(entity_id)
    
    def get_all(self) -> list[Entity]:
        """Retrieve all entities."""
        return list(self._entities.values())
    
    def add(self, entity: Entity) -> None:
        """Add a new entity."""
        self._entities[entity.id] = entity
    
    def update(self, entity: Entity) -> None:
        """Update an existing entity."""
        if entity.id in self._entities:
            self._entities[entity.id] = entity
    
    def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID."""
        if entity_id in self._entities:
            del self._entities[entity_id]
            return True
        return False
    
    def find_by_name(self, name: str) -> Optional[Entity]:
        """Find an entity by name."""
        for entity in self._entities.values():
            if entity.name == name:
                return entity
        return None