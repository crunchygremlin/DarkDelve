"""Durability configuration and component value objects."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict


__all__ = [
    "DurabilityConfig",
    "ItemDurabilityComponent",
]


@dataclass
class DurabilityConfig:
    """Configuration for how durability works."""
    base_durability: Dict[str, int] = field(default_factory=lambda: {
        "sword": 100, "axe": 120, "mace": 150, "dagger": 60,
        "spear": 80, "bow": 70, "shield": 200, "potion": 1,
        "wand": 30, "ring": 999, "amulet": 999, "scroll": 1,
    })
    hit_durability_loss: int = 1       # durability lost per hit taken while equipped
    block_durability_loss: int = 3     # durability lost per block
    crit_durability_loss: int = 5      # durability lost on critical hit received
    degradation_threshold: float = 0.5  # below this, stats are halved
    repair_stations: List[str] = field(default_factory=lambda: ["shrine", "forge"])


@dataclass
class ItemDurabilityComponent:
    """Component for tracking item condition."""
    item_id: str
    condition: float = 1.0          # 1.0 = perfect, 0.0 = broken
    times_repaired: int = 0
    max_repairs: int = 3
    is_broken: bool = False

    def degrade(self, amount: float):
        """Apply degradation to the item."""
        self.condition = max(0.0, self.condition - amount)
        if self.condition <= 0:
            self.is_broken = True

    def can_repair(self) -> bool:
        """Check if the item can be repaired."""
        return not self.is_broken and self.times_repaired < self.max_repairs

    def repair(self, amount: float) -> bool:
        """Attempt to repair the item. Returns True if successful."""
        if not self.can_repair():
            return False
        self.condition = min(1.0, self.condition + amount)
        self.times_repaired += 1
        return True