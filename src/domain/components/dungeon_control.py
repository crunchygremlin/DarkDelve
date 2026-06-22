"""Dungeon control component for managing dungeon state."""
from typing import Any, Optional, List
from .component import Component
from ..value_objects.difficulty import DungeonLevel, DifficultyMode


class DungeonControl(Component):
    """Component that holds the current dungeon level and exposes generation hooks."""

    def __init__(self, component_id: Optional[str] = None):
        super().__init__(component_id)
        self.current_level: Optional[DungeonLevel] = None
        self.difficulty: DifficultyMode = DifficultyMode.NORMAL
        self.level_number: int = 0
        self.rooms_explored: List[int] = []
        self.items_collected: List[str] = []
        self.mobs_defeated: List[str] = []

    def set_level(self, level: DungeonLevel) -> None:
        """Set the current dungeon level."""
        self.current_level = level
        self.level_number = level.level_number

    def explore_room(self, room_index: int) -> None:
        """Mark a room as explored."""
        if room_index not in self.rooms_explored:
            self.rooms_explored.append(room_index)

    def collect_item(self, item_id: str) -> None:
        """Record item collection."""
        if item_id not in self.items_collected:
            self.items_collected.append(item_id)

    def defeat_mob(self, mob_id: str) -> None:
        """Record mob defeat."""
        if mob_id not in self.mobs_defeated:
            self.mobs_defeated.append(mob_id)

    def update(self, delta_time: float, entity: Any) -> None:
        """Update dungeon control state."""
        pass  # State is updated via method calls

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            "level_number": self.level_number,
            "difficulty": self.difficulty.value,
            "rooms_explored": self.rooms_explored,
            "items_collected": self.items_collected,
            "mobs_defeated": self.mobs_defeated,
        })
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "DungeonControl":
        """Create from dictionary."""
        component = cls()
        component.enabled = data.get("enabled", True)
        component.level_number = data.get("level_number", 0)
        component.difficulty = DifficultyMode(data.get("difficulty", "normal"))
        component.rooms_explored = data.get("rooms_explored", [])
        component.items_collected = data.get("items_collected", [])
        component.mobs_defeated = data.get("mobs_defeated", [])
        return component