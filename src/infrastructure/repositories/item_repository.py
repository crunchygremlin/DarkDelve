"""Item repository for data access."""

from typing import Optional

from src.domain.entities.item import Item
from src.shared.interfaces.repository import Repository


class ItemRepository(Repository[Item]):
    """Repository for item data access."""
    
    def __init__(self):
        self._items: dict[str, Item] = {}
    
    def get_by_id(self, item_id: str) -> Item | None:
        """Retrieve an item by its ID."""
        return self._items.get(item_id)
    
    def get_all(self) -> list[Item]:
        """Retrieve all items."""
        return list(self._items.values())
    
    def add(self, item: Item) -> None:
        """Add a new item."""
        self._items[item.id] = item
    
    def update(self, item: Item) -> None:
        """Update an existing item."""
        if item.id in self._items:
            self._items[item.id] = item
    
    def delete(self, item_id: str) -> bool:
        """Delete an item by ID."""
        if item_id in self._items:
            del self._items[item_id]
            return True
        return False
    
    def find_by_name(self, name: str) -> Optional[Item]:
        """Find an item by name."""
        for item in self._items.values():
            if item.name == name:
                return item
        return None