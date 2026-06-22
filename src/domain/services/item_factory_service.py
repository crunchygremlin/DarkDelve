"""Item factory service for creating items dynamically."""
from typing import List, Optional
from ..value_objects.item_creation import (
    Item, ItemStats, ItemType, ItemPower, ItemModifier, ItemCurse
)
from ..components.item_factory import ItemFactory


class ItemFactoryService:
    """Provides a clean API for the DM to request items."""

    def __init__(self, factory: Optional[ItemFactory] = None):
        self.factory = factory or ItemFactory()

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
        return self.factory.create_item(
            name=name,
            item_type=item_type,
            rarity=rarity,
            powers=powers,
            defenses=defenses,
            modifiers=modifiers,
            curses=curses,
            stats=stats,
            boss_bonus=boss_bonus,
            puzzle_role=puzzle_role,
            level_origin=level_origin,
            description=description,
        )

    def create_boss_slayer(
        self,
        boss_type: str,
        boss_weakness: str,
        level: int,
    ) -> Item:
        """Create an item specifically designed to help kill a boss."""
        return self.factory.create_boss_slayer(boss_type, boss_weakness, level)

    def create_puzzle_item(
        self,
        puzzle_id: str,
        found_level: int,
        used_level: int,
    ) -> Item:
        """Create a seemingly useless item needed for a future puzzle."""
        return self.factory.create_puzzle_item(puzzle_id, found_level, used_level)

    def create_trash_item(self, level: int) -> Item:
        """Create a non-ordinary trash item with hidden potential."""
        return self.factory.create_trash_item(level)

    def generate_item_name(
        self,
        item_type: str,
        powers: Optional[List[str]] = None,
        modifiers: Optional[List[str]] = None,
        curses: Optional[List[str]] = None,
    ) -> str:
        """Generate a thematic name for an item."""
        return self.factory.generate_item_name(item_type, powers, modifiers, curses)