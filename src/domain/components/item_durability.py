"""Item durability component for tracking item condition."""
from typing import Any, Optional
from .component import Component
from ..value_objects.durability import ItemDurabilityComponent


class ItemDurability(Component):
    """Component that tracks durability state and applies degradation logic."""

    def __init__(self, component_id: Optional[str] = None):
        super().__init__(component_id)
        self.item_id: str = ""
        self.condition: float = 1.0          # 1.0 = perfect, 0.0 = broken
        self.times_repaired: int = 0
        self.max_repairs: int = 3
        self.is_broken: bool = False

    def set_item_id(self, item_id: str) -> None:
        """Set the item ID this component tracks."""
        self.item_id = item_id

    def degrade(self, amount: float) -> bool:
        """Apply degradation. Returns True if item breaks."""
        self.condition = max(0.0, self.condition - amount)
        if self.condition <= 0:
            self.is_broken = True
        return self.is_broken

    def can_repair(self) -> bool:
        """Check if the item can be repaired."""
        return not self.is_broken and self.times_repaired < self.max_repairs

    def repair(self, amount: float) -> bool:
        """Attempt to repair. Returns True if successful."""
        if not self.can_repair():
            return False
        self.condition = min(1.0, self.condition + amount)
        self.times_repaired += 1
        return True

    def get_condition_percent(self) -> float:
        """Get condition as percentage (0-100)."""
        return self.condition * 100

    def is_degraded(self) -> bool:
        """Check if item is below 50% condition."""
        return self.condition < 0.5

    def update(self, delta_time: float, entity: Any) -> None:
        """Update durability state."""
        pass

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            "item_id": self.item_id,
            "condition": self.condition,
            "times_repaired": self.times_repaired,
            "max_repairs": self.max_repairs,
            "is_broken": self.is_broken,
        })
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ItemDurability":
        """Create from dictionary."""
        component = cls()
        component.enabled = data.get("enabled", True)
        component.item_id = data.get("item_id", "")
        component.condition = data.get("condition", 1.0)
        component.times_repaired = data.get("times_repaired", 0)
        component.max_repairs = data.get("max_repairs", 3)
        component.is_broken = data.get("is_broken", False)
        return component

    @classmethod
    def from_value_object(cls, vo: ItemDurabilityComponent, item_id: str) -> "ItemDurability":
        """Create from ItemDurabilityComponent value object."""
        component = cls()
        component.item_id = item_id
        component.condition = vo.condition
        component.times_repaired = vo.times_repaired
        component.is_broken = vo.is_broken
        return component