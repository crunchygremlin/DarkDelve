"""Power levels value objects for the Entity AI system."""

from dataclasses import dataclass, field
from typing import Dict, List

__all__ = [
    "OffensivePower",
    "DefensivePower",
    "SkillSet",
    "PlayerProfile",
]


@dataclass
class OffensivePower:
    """Offensive power categories for an entity."""
    melee_strength: float = 0.0
    melee_precision: float = 0.0
    piercing: float = 0.0
    slashing: float = 0.0
    bludgeoning: float = 0.0
    fire_magic: float = 0.0
    ice_magic: float = 0.0
    lightning_magic: float = 0.0
    poison_magic: float = 0.0
    arcane_magic: float = 0.0
    divine_magic: float = 0.0
    shadow_magic: float = 0.0

    def as_dict(self) -> Dict[str, float]:
        """Convert to dictionary representation."""
        return {f: getattr(self, f) for f in self.__dataclass_fields__}

    def dominant_type(self) -> str:
        """Return the type with the highest power value."""
        return max(self.as_dict(), key=self.as_dict().get)


@dataclass
class DefensivePower:
    """Defensive power categories for an entity."""
    physical_armor: float = 0.0
    piercing_resist: float = 0.0
    slashing_resist: float = 0.0
    bludgeoning_resist: float = 0.0
    fire_resist: float = 0.0
    ice_resist: float = 0.0
    lightning_resist: float = 0.0
    poison_resist: float = 0.0
    arcane_resist: float = 0.0
    divine_resist: float = 0.0
    shadow_resist: float = 0.0
    evasion: float = 0.0

    def as_dict(self) -> Dict[str, float]:
        """Convert to dictionary representation."""
        return {f: getattr(self, f) for f in self.__dataclass_fields__}

    def weakest_defense(self) -> str:
        """Return the defense type with the lowest value."""
        return min(self.as_dict(), key=self.as_dict().get)


@dataclass
class SkillSet:
    """9 Fuzion skill categories (level = OP spent)."""
    # New Fuzion fields
    fighting: float = 0.0
    ranged_weapon: float = 0.0
    awareness: float = 0.0
    control: float = 0.0
    body: float = 0.0
    social: float = 0.0
    technique: float = 0.0
    performance: float = 0.0
    education: float = 0.0
    # Legacy fields for backward compatibility
    weapon_mastery: float = 0.0
    armor_mastery: float = 0.0
    tactical_awareness: float = 0.0
    perception: float = 0.0
    stealth: float = 0.0
    sneakiness: float = 0.0
    acrobatics: float = 0.0
    persuasion: float = 0.0
    deception: float = 0.0
    intimidation: float = 0.0
    investigation: float = 0.0
    language: float = 0.0
    arcane_knowledge: float = 0.0
    survival: float = 0.0
    medicine: float = 0.0

    def __init__(self, **kwargs):
        """Accept both new Fuzion fields and legacy field names for backward compatibility."""
        # Set fields using object.__setattr__ for dataclass compatibility
        for field_name in self.__dataclass_fields__:
            if field_name in kwargs:
                object.__setattr__(self, field_name, kwargs[field_name])
            else:
                object.__setattr__(self, field_name, self.__dataclass_fields__[field_name].default)

    def as_dict(self) -> Dict[str, float]:
        """Convert to dictionary representation."""
        return {f: getattr(self, f) for f in self.__dataclass_fields__}


@dataclass
class PlayerProfile:
    """Summary of player capabilities for LLM consumption."""
    offensive_power: OffensivePower = field(default_factory=OffensivePower)
    defensive_power: DefensivePower = field(default_factory=DefensivePower)
    skills: SkillSet = field(default_factory=SkillSet)
    inventory_summary: List[str] = field(default_factory=list)
    playstyle_indicators: Dict[str, float] = field(default_factory=dict)
    # e.g., {"aggressive": 0.8, "cautious": 0.2, "explorer": 0.6}

    def summary_for_llm(self) -> str:
        """Generate a text summary for the LLM."""
        lines = ["=== PLAYER PROFILE ==="]
        off = self.offensive_power
        lines.append(f"Offensive: STR={off.melee_strength:.1f}, "
                     f"best_magic={off.dominant_type()}({max(off.as_dict().values()):.1f})")
        dfn = self.defensive_power
        lines.append(f"Defensive: ARMOR={dfn.physical_armor:.1f}, "
                     f"weakest={dfn.weakest_defense()}({min(dfn.as_dict().values()):.1f})")
        sk = self.skills
        lines.append(f"Skills: fighting={sk.fighting:.1f}, "
                     f"ranged_weapon={sk.ranged_weapon:.1f}, awareness={sk.awareness:.1f}")
        lines.append(f"Playstyle: {self.playstyle_indicators}")
        lines.append(f"Items: {', '.join(self.inventory_summary[:10])}")
        return "\n".join(lines)