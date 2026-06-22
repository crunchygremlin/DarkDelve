"""Loot planner component for generating loot plans."""
from typing import Any, Optional, List, Dict
from .component import Component
from ..value_objects.loot_plan import LootPlan
from ..value_objects.item_creation import Item


__all__ = [
    "LootPlanner",
]


class LootPlanner(Component):
    """Generates LootPlan per level based on player profile and difficulty."""

    def __init__(self, component_id: Optional[str] = None):
        super().__init__(component_id)
        self.current_plan: Optional[LootPlan] = None
        self.player_build_profile: Dict[str, Any] = {}

    def set_player_profile(self, stats: Dict[str, float], power_levels: Dict[str, float]) -> None:
        """Set the player's build profile for loot catering."""
        self.player_build_profile = {
            "stats": stats,
            "power_levels": power_levels,
        }

    def create_plan(
        self,
        level_number: int,
        target_power_type: str,
        target_challenge: str,
        items: List[Item],
    ) -> LootPlan:
        """Create a loot plan for a level."""
        self.current_plan = LootPlan(
            level_number=level_number,
            items=items,
            target_power_type=target_power_type,
            target_challenge=target_challenge,
        )
        return self.current_plan

    def add_catering_item(self, item_id: str) -> None:
        """Add an item that helps the player's build."""
        if self.current_plan:
            self.current_plan.catering_items.append(item_id)

    def add_challenge_item(self, item_id: str) -> None:
        """Add an item that tests player weaknesses."""
        if self.current_plan:
            self.current_plan.challenge_items.append(item_id)

    def get_plan(self) -> Optional[LootPlan]:
        """Get the current loot plan."""
        return self.current_plan

    def update(self, delta_time: float, entity: Any) -> None:
        """Update loot planner state."""
        pass

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            "player_build_profile": self.player_build_profile,
        })
        if self.current_plan:
            data["current_plan"] = {
                "level_number": self.current_plan.level_number,
                "target_power_type": self.current_plan.target_power_type,
                "target_challenge": self.current_plan.target_challenge,
                "catering_items": self.current_plan.catering_items,
                "challenge_items": self.current_plan.challenge_items,
            }
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "LootPlanner":
        """Create from dictionary."""
        component = cls()
        component.enabled = data.get("enabled", True)
        component.player_build_profile = data.get("player_build_profile", {})
        return component