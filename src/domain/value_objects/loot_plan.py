"""Loot catering value objects."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .item_creation import Item


__all__ = [
    "LootPlan",
]


@dataclass
class LootPlan:
    """DM's plan for what items to place in a level."""
    level_number: int
    items: List["Item"]
    target_power_type: str      # what damage type to emphasize
    target_challenge: str       # what to challenge the player with
    catering_items: List[str] = field(default_factory=list)   # items that help the player's build
    challenge_items: List[str] = field(default_factory=list)  # items that test player weaknesses
    trash_items: List["Item"] = field(default_factory=list)     # seemingly useless items with puzzle potential