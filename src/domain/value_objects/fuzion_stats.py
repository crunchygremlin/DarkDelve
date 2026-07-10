"""Fuzion RPG characteristics and skills value objects."""

from dataclasses import dataclass, field
from typing import Dict, Any

__all__ = [
    "PrimaryCharacteristics",
    "DerivedCharacteristics",
    "SkillSet",
    "EVERYMAN_DEFAULT",
]

# Everyman skills start at level 2 free (per PDF)
EVERYMAN_DEFAULT: Dict[str, float] = {
    "fighting": 2.0,
    "ranged_weapon": 2.0,
    "awareness": 2.0,
    "control": 2.0,
    "body": 2.0,
    "social": 2.0,
    "technique": 2.0,
    "performance": 2.0,
    "education": 2.0,
}


@dataclass(frozen=True)
class PrimaryCharacteristics:
    """10 Fuzion primary characteristics."""
    int: int = 10
    will: int = 10
    pre: int = 10
    tech: int = 10
    ref: int = 10
    dex: int = 10
    con: int = 10
    str: int = 10
    body: int = 10
    move: int = 10

    def __post_init__(self) -> None:
        for name, val in self.__dict__.items():
            if not isinstance(val, int) or val < 0:
                raise ValueError(f"{name} must be a non-negative int")

    def modifier(self, char: str) -> int:
        """Backward-compat D&D-style modifier; new code uses raw values."""
        return (getattr(self, char, 10) - 10) // 2

    def to_dict(self) -> Dict[str, int]:
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, d: Dict[str, int]) -> "PrimaryCharacteristics":
        return cls(**{k: d.get(k, 10) for k in cls.__dataclass_fields__})


@dataclass(frozen=True)
class DerivedCharacteristics:
    """Derived stats computed from PrimaryCharacteristics."""
    stun: int = 50
    hits: int = 50
    sd: int = 20          # Stun Defense
    rec: int = 20         # Recovery
    run: int = 20
    sprint: int = 30
    leap: int = 10
    ed: int = 20          # Energy Defense (optional)
    end: int = 100        # Endurance (optional)
    spd: int = 5          # Speed (optional)
    res: int = 30         # Presence/Res (optional)
    hum: int = 100        # Humanity (optional)

    @classmethod
    def from_primary(cls, pc: PrimaryCharacteristics) -> "DerivedCharacteristics":
        return cls(
            stun=pc.body * 5,
            hits=pc.body * 5,
            sd=pc.con * 2,
            rec=pc.str + pc.con,
            run=pc.move * 2,
            sprint=pc.move * 3,
            leap=pc.move * 1,
            ed=pc.con * 2,
            end=pc.con * 10,
            spd=pc.ref // 2,
            res=pc.will * 3,
            hum=pc.will * 10,
        )


@dataclass
class SkillSet:
    """9 Fuzion skill categories (level = OP spent)."""
    fighting: float = 0.0
    ranged_weapon: float = 0.0
    awareness: float = 0.0
    control: float = 0.0
    body: float = 0.0
    social: float = 0.0
    technique: float = 0.0
    performance: float = 0.0
    education: float = 0.0

    def level(self, category: str) -> float:
        return getattr(self, category, 0.0)

    def as_dict(self) -> Dict[str, float]:
        return {f: getattr(self, f) for f in self.__dataclass_fields__}

    @classmethod
    def everyman(cls) -> "SkillSet":
        """Everyman skills start at level 2 free (per PDF)."""
        return cls(**EVERYMAN_DEFAULT)