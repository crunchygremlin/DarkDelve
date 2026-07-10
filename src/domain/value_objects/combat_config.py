from dataclasses import dataclass

@dataclass(frozen=True)
class CombatConfig:
    DIE_SIDES: int = 10
    BASE_DV: int = 6
    MIN_DMG: int = 1
    CRIT_IGNORES_AV: bool = False
    DEFENSE_COMPRESSION: float = 0.4

COMBAT_CONFIG = CombatConfig()


@dataclass(frozen=True)
class FuzionCombatConfig:
    DIE_SIDES: int = 10
    BASE_DV: int = 6
    DEFENSE_COMPRESSION: float = 0.4
    CRIT_DIE_MAX: int = 10            # natural max => open-end / +1 DC
    SKILL_BONUS_DIVISOR: int = 5      # float skill level -> int bonus
    LEVEL_BONUS_PER_LEVEL: int = 1
    EVERYMAN_SKILL_LEVEL: int = 2
    MIN_DMG: int = 1
    DICE_MODE: str = "interlock"      # or "hero" (3d6 + flat 10 DV)
    HERO_DV_FLAT: int = 10
    KNOCKBACK_DIVISOR: int = 5
    AIMED_HEAD_MULT: float = 2.0
    AIMED_VITALS_MULT: float = 1.5
    RULE_OF_X_ATTACK: int = 20        # campaign cap (config-overridable)
    RULE_OF_X_DEFENSE: int = 20

FUZION_CONFIG = FuzionCombatConfig()