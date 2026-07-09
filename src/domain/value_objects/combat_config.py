from dataclasses import dataclass

@dataclass(frozen=True)
class CombatConfig:
    DIE_SIDES: int = 10
    BASE_DV: int = 6
    MIN_DMG: int = 1
    CRIT_IGNORES_AV: bool = False
    DEFENSE_COMPRESSION: float = 0.4

COMBAT_CONFIG = CombatConfig()