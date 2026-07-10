"""Fuzion damage model for DC/Hits/Stun/KD/SD/ED."""

import random
from dataclasses import dataclass
from typing import Any, Tuple

from src.domain.value_objects.combat_config import FUZION_CONFIG as C


@dataclass
class FuzionDamageResult:
    """Result of Fuzion damage calculation."""
    hits: int = 0          # lethal body damage
    stun: int = 0          # non-lethal stun damage
    sdp: int = 0           # structural damage (inanimate)
    kills: int = 0         # massive/tough damage
    knockback: int = 0     # tiles pushed
    aimed_location: str = "body"


class FuzionDamageCalculator:
    """Calculate Fuzion damage based on Damage Class (DC) and defenses."""

    def calculate(self, attacker: Any, target: Any, weapon_dc: int,
                  damage_type: str = "physical",
                  is_critical: bool = False,
                  aimed_location: str = "body") -> FuzionDamageResult:
        """Calculate Fuzion damage.

        Args:
            attacker: Entity performing the attack
            target: Entity receiving the damage
            weapon_dc: Damage Class (number of d6 to roll)
            damage_type: "physical" or "energy"
            is_critical: Whether this is a critical hit
            aimed_location: "head", "vitals", or "body"

        Returns:
            FuzionDamageResult with hits, stun, knockback, etc.
        """
        dc = max(1, int(weapon_dc))
        if is_critical:
            dc += 1                      # open-end: one extra d6

        raw = sum(random.randint(1, 6) for _ in range(dc))

        # Get aimed shot multiplier
        mult = 1.0
        if aimed_location == "head":
            mult = C.AIMED_HEAD_MULT
        elif aimed_location == "vitals":
            mult = C.AIMED_VITALS_MULT

        raw = int(raw * mult)

        # Melee fists deal Stun only (STR in DC of Stun); others deal Hits.
        is_stun_only = getattr(attacker, 'unarmed_stun', False)
        hits = 0 if is_stun_only else raw
        stun = raw

        # Defenses
        kd = getattr(target, 'killing_defense', 0)   # from armor (KD)
        sd = getattr(target, 'stun_defense', 0)      # target DerivedCharacteristics.sd
        ed = getattr(target, 'energy_defense', 0)

        if damage_type == "energy":
            hits = max(0, hits - ed)
            stun = max(0, stun - ed)
        else:
            hits = max(0, hits - kd)
        stun = max(0, stun - sd)

        # Knockback
        pc = getattr(attacker, 'characteristics', None)
        if pc is None:
            # Legacy fallback
            str_val = 10
            if hasattr(attacker, 'stats'):
                str_val = getattr(attacker.stats, 'strength', 10) if hasattr(attacker.stats, 'strength') else 10
        else:
            str_val = pc.str

        knockback = (str_val + hits) // C.KNOCKBACK_DIVISOR

        return FuzionDamageResult(
            hits=max(C.MIN_DMG, hits) if (hits > 0 or not is_stun_only) else 0,
            stun=max(0, stun),
            sdp=0,
            kills=0,
            knockback=knockback,
            aimed_location=aimed_location
        )