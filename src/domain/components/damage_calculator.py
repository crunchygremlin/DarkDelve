"""Damage calculator component for Fuzion RPG damage model."""
from typing import Any, Optional
from .component import Component
from ..value_objects.damage_model import DamageCalculator, DamageResult
from ..value_objects.fuzion_damage import FuzionDamageCalculator, FuzionDamageResult


__all__ = [
    "DamageComponent",
]


class DamageComponent(Component):
    """Wrapper around DamageCalculator to integrate with combat component."""

    def __init__(self, component_id: Optional[str] = None):
        super().__init__(component_id)
        self._calculator = DamageCalculator()
        self._fuzion_calculator = FuzionDamageCalculator()

    def calculate_damage(
        self,
        attacker_power: float,
        damage_type: str,
        defender_resistance: float,
        defender_armor: float,
        is_critical: bool = False,
        critical_multiplier: float = 1.5,
    ) -> DamageResult:
        """Calculate damage using Hero-System style."""
        return self._calculator.calculate_damage(
            attacker_power=attacker_power,
            damage_type=damage_type,
            defender_resistance=defender_resistance,
            defender_armor=defender_armor,
            is_critical=is_critical,
            critical_multiplier=critical_multiplier,
        )

    def calculate_fuzion_damage(
        self,
        attacker: Any,
        target: Any,
        weapon_dc: int,
        damage_type: str = "physical",
        is_critical: bool = False,
        aimed_location: str = "body",
    ) -> FuzionDamageResult:
        """Calculate damage using Fuzion model."""
        return self._fuzion_calculator.calculate(
            attacker=attacker,
            target=target,
            weapon_dc=weapon_dc,
            damage_type=damage_type,
            is_critical=is_critical,
            aimed_location=aimed_location,
        )

    def apply_block(
        self,
        damage: DamageResult,
        block_chance: float,
        block_value: float,
    ) -> DamageResult:
        """Apply block reduction to damage."""
        return self._calculator.calculate_with_block(damage, block_chance, block_value)

    def apply_dodge(
        self,
        damage: DamageResult,
        dodge_chance: float,
    ) -> DamageResult:
        """Apply dodge chance to damage."""
        return self._calculator.calculate_with_dodge(damage, dodge_chance)

    def update(self, delta_time: float, entity: Any) -> None:
        """Update damage component state."""
        pass

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return super().to_dict()

    @classmethod
    def from_dict(cls, data: dict) -> "DamageComponent":
        """Create from dictionary."""
        component = cls()
        component.enabled = data.get("enabled", True)
        return component