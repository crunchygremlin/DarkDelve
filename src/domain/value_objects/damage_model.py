"""Hero-System RPG damage model value objects."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class DamageInstance:
    """A single damage calculation."""
    raw_damage: float
    damage_type: str           # "physical", "fire", "ice", "lightning", etc.
    source_id: str             # who/what dealt the damage
    target_id: str
    is_critical: bool = False
    is_blocked: bool = False
    is_dodged: bool = False
    overkill: float = 0.0      # damage beyond 0 health


@dataclass
class DamageResult:
    """Result of damage calculation."""
    final_damage: float
    was_blocked: bool
    was_dodged: bool
    was_critical: bool
    overkill: float
    resistance_applied: float
    resistance_type: str
    target_died: bool = False


@dataclass
class ResistanceProfile:
    """Entity's resistance to different damage types."""
    resistances: Dict[str, float] = field(default_factory=dict)
    # damage_type -> resistance value (0.0 = no resist, 1.0 = immune)

    def get_resistance(self, damage_type: str) -> float:
        """Get resistance for a specific damage type."""
        return self.resistances.get(damage_type, 0.0)

    def set_resistance(self, damage_type: str, value: float):
        """Set resistance for a specific damage type (clamped 0.0-1.0)."""
        self.resistances[damage_type] = max(0.0, min(1.0, value))


class DamageCalculator:
    """Hero System style damage model."""

    def calculate_damage(
        self,
        attacker_power: float,
        damage_type: str,
        defender_resistance: float,
        defender_armor: float,
        is_critical: bool = False,
        critical_multiplier: float = 1.5,
    ) -> DamageResult:
        """
        Hero System style: damage is reduced by resistance first, then armor.
        Resistance is percentage reduction. Armor is flat reduction.
        """
        raw = attacker_power
        if is_critical:
            raw *= critical_multiplier

        # Apply resistance (percentage reduction)
        resisted = raw * defender_resistance
        after_resistance = raw - resisted

        # Apply armor (flat reduction, minimum 1 damage if hit lands)
        after_armor = max(1.0, after_resistance - defender_armor)

        final = after_armor
        return DamageResult(
            final_damage=final,
            was_blocked=False,
            was_dodged=False,
            was_critical=is_critical,
            overkill=0.0,
            resistance_applied=resisted,
            resistance_type=damage_type,
        )

    def calculate_with_block(
        self,
        damage: DamageResult,
        block_chance: float,
        block_value: float,
    ) -> DamageResult:
        """Apply block reduction."""
        import random
        if random.random() < block_chance:
            damage.final_damage = max(0, damage.final_damage - block_value)
            damage.was_blocked = True
        return damage

    def calculate_with_dodge(
        self,
        damage: DamageResult,
        dodge_chance: float,
    ) -> DamageResult:
        """Apply dodge chance."""
        import random
        if random.random() < dodge_chance:
            damage.final_damage = 0
            damage.was_dodged = True
        return damage