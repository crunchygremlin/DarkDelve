"""Item factory component for creating items dynamically."""
from typing import Any, Optional, List, Dict
from .component import Component
from ..value_objects.item_creation import (
    Item, ItemStats, ItemType, ItemPower, ItemModifier, ItemCurse
)


class ItemFactory(Component):
    """Factory component for creating items dynamically."""

    def __init__(self, component_id: Optional[str] = None):
        super().__init__(component_id)
        self._item_counter: int = 0
        self._rarity_weights: Dict[str, float] = {
            "common": 0.6,
            "uncommon": 0.25,
            "rare": 0.1,
            "epic": 0.04,
            "legendary": 0.01,
        }

    def _next_id(self) -> str:
        """Generate next item ID."""
        self._item_counter += 1
        return f"item_{self._item_counter:06d}"

    def create_item(
        self,
        name: str,
        item_type: str,
        rarity: str = "common",
        powers: Optional[List[str]] = None,
        defenses: Optional[List[str]] = None,
        modifiers: Optional[List[str]] = None,
        curses: Optional[List[str]] = None,
        stats: Optional[ItemStats] = None,
        boss_bonus: Optional[str] = None,
        puzzle_role: Optional[str] = None,
        level_origin: int = 0,
        description: str = "",
    ) -> Item:
        """Create a single item with full customization."""
        return Item(
            item_id=self._next_id(),
            name=name,
            description=description or f"A {item_type} of {rarity} quality.",
            item_type=item_type,
            rarity=rarity,
            powers=powers or [],
            defenses=defenses or [],
            modifiers=modifiers or [],
            curses=curses or [],
            stats=stats or ItemStats(),
            boss_bonus=boss_bonus,
            puzzle_role=puzzle_role,
            level_origin=level_origin,
        )

    def create_boss_slayer(
        self,
        boss_type: str,
        boss_weakness: str,
        level: int,
    ) -> Item:
        """Create an item specifically designed to help kill a boss."""
        item_type = "weapon"
        name = f"{boss_weakness.title()}-bane {boss_type}"
        stats = ItemStats(
            damage=15.0 + level * 2,
            damage_type=boss_weakness,
            durability_max=150,
            durability_current=150,
        )
        return self.create_item(
            name=name,
            item_type=item_type,
            rarity="rare",
            powers=[boss_weakness],
            modifiers=["sharp"],
            stats=stats,
            boss_bonus=boss_weakness,
            level_origin=level,
            description=f"A weapon honed to strike down {boss_type}.",
        )

    def create_puzzle_item(
        self,
        puzzle_id: str,
        found_level: int,
        used_level: int,
    ) -> Item:
        """Create a seemingly useless item needed for a future puzzle."""
        name = f"Mysterious Artifact"
        description = "An item that seems mundane, but will prove useful later."
        return self.create_item(
            name=name,
            item_type="misc",
            rarity="uncommon",
            stats=ItemStats(durability_max=999, durability_current=999),
            puzzle_role=puzzle_id,
            level_origin=found_level,
            description=description,
        )

    def create_trash_item(self, level: int) -> Item:
        """Create a non-ordinary trash item with hidden potential."""
        name = "Oddly Shaped Stone"
        description = "Looks like a rock, but has strange markings."
        return self.create_item(
            name=name,
            item_type="misc",
            rarity="common",
            stats=ItemStats(durability_max=50, durability_current=50),
            level_origin=level,
            description=description,
        )

    def generate_item_name(
        self,
        item_type: str,
        powers: Optional[List[str]] = None,
        modifiers: Optional[List[str]] = None,
        curses: Optional[List[str]] = None,
    ) -> str:
        """Generate a thematic name for an item."""
        power_prefix = powers[0].title() if powers else ""
        modifier_prefix = modifiers[0].title() if modifiers else ""
        curse_suffix = f" of {curses[0]}" if curses else ""

        if power_prefix and modifier_prefix:
            return f"{modifier_prefix} {power_prefix} {item_type.title()}{curse_suffix}"
        elif power_prefix:
            return f"{power_prefix} {item_type.title()}{curse_suffix}"
        else:
            return f"{item_type.title()}{curse_suffix}"

    def update(self, delta_time: float, entity: Any) -> None:
        """Update factory state."""
        pass

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            "item_counter": self._item_counter,
        })
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ItemFactory":
        """Create from dictionary."""
        component = cls()
        component.enabled = data.get("enabled", True)
        component._item_counter = data.get("item_counter", 0)
        return component