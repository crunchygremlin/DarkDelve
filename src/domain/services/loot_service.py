"""Loot service for applying loot plans to dungeon levels."""
from typing import List, Optional, Dict, Any
from ..value_objects.loot_plan import LootPlan
from ..value_objects.item_creation import Item
from ..components.loot_planner import LootPlanner


__all__ = [
    "LootService",
]


class LootService:
    """Applies LootPlan to a DungeonLevel, updates inventory, and emits loot events."""

    def __init__(self, planner: Optional[LootPlanner] = None):
        self.planner = planner or LootPlanner()
        self.current_plan: Optional[LootPlan] = None

    def create_plan(
        self,
        level_number: int,
        target_power_type: str,
        target_challenge: str,
    ) -> LootPlan:
        """Create a new loot plan for a level."""
        self.current_plan = LootPlan(
            level_number=level_number,
            items=[],
            target_power_type=target_power_type,
            target_challenge=target_challenge,
        )
        return self.current_plan

    def add_item(self, item: Item) -> None:
        """Add an item to the current plan."""
        if self.current_plan:
            self.current_plan.items.append(item)

    def add_catering_item(self, item_id: str) -> None:
        """Add an item that helps the player's build."""
        if self.current_plan:
            self.current_plan.catering_items.append(item_id)

    def add_challenge_item(self, item_id: str) -> None:
        """Add an item that tests player weaknesses."""
        if self.current_plan:
            self.current_plan.challenge_items.append(item_id)

    def add_trash_item(self, item: Item) -> None:
        """Add a trash item with hidden potential."""
        if self.current_plan:
            self.current_plan.trash_items.append(item)

    def distribute_loot(self, player_inventory: List[Item]) -> List[Item]:
        """Distribute loot to the player's inventory."""
        if not self.current_plan:
            return player_inventory

        # Add all items from the plan to inventory
        new_inventory = player_inventory.copy()
        new_inventory.extend(self.current_plan.items)
        new_inventory.extend(self.current_plan.trash_items)

        return new_inventory

    def get_plan(self) -> Optional[LootPlan]:
        """Get the current loot plan."""
        return self.current_plan

    def set_player_profile(self, stats: Dict[str, Any], power_levels: Dict[str, Any]) -> None:
        """Set the player profile for loot catering."""
        self.planner.set_player_profile(stats, power_levels)