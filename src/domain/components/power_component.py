"""Power component for managing entity power levels and skills."""

from dataclasses import dataclass, field
from typing import Any
from src.domain.components.component import Component
from src.domain.value_objects.power_levels import OffensivePower, DefensivePower, SkillSet

__all__ = ["PowerComponent"]


@dataclass
class PowerComponent(Component):
    """Component that manages an entity's power levels and skills."""
    entity_id: str = ""
    offensive: OffensivePower = field(default_factory=OffensivePower)
    defensive: DefensivePower = field(default_factory=DefensivePower)
    skills: SkillSet = field(default_factory=SkillSet)

    @property
    def component_type(self) -> str:
        return "power"

    def get_attack_power(self, damage_type: str) -> float:
        """Get attack power for a specific damage type."""
        return getattr(self.offensive, damage_type, 0.0)

    def get_defense_power(self, damage_type: str) -> float:
        """Get defense power for a specific damage type."""
        return getattr(self.defensive, damage_type.replace("_magic", "_resist").replace("_strength", "_resist"), 0.0)

    def get_skill(self, skill_name: str) -> float:
        """Get skill level for a specific skill."""
        return getattr(self.skills, skill_name, 0.0)

    def update(self, delta_time: float, entity: Any) -> None:
        """Update component state (called each frame)."""
        pass  # Power levels are typically static or updated via events