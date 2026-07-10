import random
from typing import Tuple, List, Any
from src.domain.value_objects.combat_config import COMBAT_CONFIG, FUZION_CONFIG
from src.shared.utils.dice import parse_dice
from src.domain.services.fuzion_skill_service import (
    get_skill_bonuses as fuzion_get_skill_bonuses,
    governing_char,
    MOB_SKILL_MAP
)

SKILL_BONUS_DIVISOR: int = 5      # SkillSet float value -> integer bonus
LEVEL_BONUS_PER_LEVEL: int = 1    # each level adds this to attack & defense values

# Re-export for backward compatibility with test_fuzion_entities.py
MOB_SKILL_BONUS_MAP = MOB_SKILL_MAP


def _reflex_mod(entity: Any) -> int:
    stats = getattr(entity, 'stats', None)
    if stats is None:
        return 0
    if hasattr(stats, 'get_modifier'):
        return stats.get_modifier('dexterity')
    if isinstance(stats, dict):
        return (stats.get('dex', 10) - 10) // 2
    return 0


def get_power(entity: Any) -> int:
    return getattr(entity, 'attack_power', getattr(entity, 'power', 0))


def get_defense_stat(entity: Any) -> int:
    return getattr(entity, 'defense', 0)


def get_level(entity: Any) -> int:
    lvl = getattr(entity, 'level', None)
    if isinstance(lvl, int) and lvl > 0:
        return lvl
    return _tier_to_level(getattr(entity, 'tier', None))


def _tier_to_level(tier: Any) -> int:
    if tier is None:
        return 1
    if isinstance(tier, int):
        return max(1, tier)
    val = getattr(tier, 'value', None)        # MobTier enum has .value
    if isinstance(val, int):
        return max(1, val)
    name = str(tier).lower()
    return {"minion": 1, "soldier": 2, "elite": 3, "boss": 4}.get(name, 1)


def get_skill_bonuses(entity: Any) -> Tuple[int, int, int]:
    """Returns (attack_bonus, dv_bonus, av_bonus) using Fuzion skill categories."""
    return fuzion_get_skill_bonuses(entity)


def get_to_hit_bonus(entity: Any) -> int:
    if hasattr(entity, 'to_hit_bonus') and not callable(getattr(entity, 'to_hit_bonus', None)):
        return entity.to_hit_bonus
    eq = getattr(entity, 'equipment', None)
    if eq is not None and hasattr(eq, 'get_bonus'):
        return eq.get_bonus("attack")
    comp = entity.get_component("combat") if hasattr(entity, 'get_component') else None
    if comp is not None and hasattr(comp, 'get_bonus_attack'):
        return comp.get_bonus_attack()
    return 0


def get_damage_bonus(entity: Any) -> int:
    if hasattr(entity, 'damage_bonus') and not callable(getattr(entity, 'damage_bonus', None)):
        return entity.damage_bonus
    eq = getattr(entity, 'equipment', None)
    if eq is not None and hasattr(eq, 'get_bonus'):
        return eq.get_bonus("damage")
    comp = entity.get_component("combat") if hasattr(entity, 'get_component') else None
    if comp is not None and hasattr(comp, 'get_bonus_damage'):
        return comp.get_bonus_damage()
    return 0


def get_armor_value(entity: Any) -> int:
    base = 0
    if hasattr(entity, 'armor_value') and not callable(getattr(entity, 'armor_value', None)):
        base += entity.armor_value          # inventory/equipment AV (darkdelve.Entity, Item)
    else:
        # B2 FIX: Player (src/domain/entities/player.Player) has NO armor_value
        # property, so equipped armor contributed 0 AV through combat_factors.
        # Mirror get_to_hit_bonus/get_damage_bonus: read equipment defense bonus.
        # Guard with getattr so darkdelve.Entity.armor_value path is NOT double-counted.
        eq = getattr(entity, 'equipment', None)
        if eq is not None and hasattr(eq, 'get_bonus'):
            base += eq.get_bonus("defense")
    base += getattr(entity, 'armor_value_override', 0)   # MobTemplate.armor_value for monsters
    _, am, _ = get_skill_bonuses(entity)     # armor_mastery -> AV
    base += am
    mod = getattr(entity, 'combat_av_modifier', 1.0)      # difficulty scaling
    return int(base * mod)


def calculate_attack_value(attacker: Any, weapon_dice: str = "1d6") -> Tuple[int, int]:
    # Returns (d10_roll, attack_total). Same formula for BOTH combat systems.
    d10 = random.randint(1, COMBAT_CONFIG.DIE_SIDES)
    wm, _, _ = get_skill_bonuses(attacker)
    level_bonus = get_level(attacker) * LEVEL_BONUS_PER_LEVEL
    atk = (d10 + _reflex_mod(attacker) + get_power(attacker) // 2
           + get_to_hit_bonus(attacker) + wm + level_bonus)
    mod = getattr(attacker, 'combat_attack_modifier', 1.0)
    return d10, int(atk * mod)


def calculate_defense_value(target: Any) -> int:
    # Same formula for BOTH combat systems. NOTE: this is the COMBAT DV
    # (includes skill + level factors). The Entity.defense_value property
    # remains the BASE DV (no skill/level) for test parity — see gotchas.md.
    wm, am, ta = get_skill_bonuses(target)
    level_bonus = get_level(target) * LEVEL_BONUS_PER_LEVEL
    dv = (COMBAT_CONFIG.BASE_DV + _reflex_mod(target)
          + int(get_defense_stat(target) * COMBAT_CONFIG.DEFENSE_COMPRESSION)
          + getattr(target, 'dodge_bonus', 0) + am + ta + level_bonus)
    mod = getattr(target, 'combat_dv_modifier', 1.0)
    return int(dv * mod)


def get_base_damage(attacker: Any, weapon_dice: str) -> int:
    # Pre-AV damage (used by Mob.get_attack_damage and inside calculate_damage).
    num, size, mod = parse_dice(weapon_dice)
    dmg = sum(random.randint(1, size) for _ in range(num)) + mod
    dmg += get_power(attacker) // 2
    dmg += get_damage_bonus(attacker)
    # S1 FIX: weapon_mastery is to-hit (ATTACK VALUE) ONLY per §1; do NOT add to damage.
    return max(COMBAT_CONFIG.MIN_DMG, dmg)


def calculate_damage(attacker: Any, target: Any, weapon_dice: str, is_critical: bool) -> int:
    dmg = get_base_damage(attacker, weapon_dice)
    if is_critical:
        dmg *= 2
    av = get_armor_value(target)
    if is_critical and COMBAT_CONFIG.CRIT_IGNORES_AV:
        av = 0
    dmg = max(COMBAT_CONFIG.MIN_DMG, dmg - av)
    return dmg


def apply_difficulty(entity: Any, adjustment: Any) -> None:
    # Sets the three modifier fields from a DifficultyAdjustment so spawned
    # monsters scale in the Fuzion model. Caller: spawn logic / dungeon master.
    entity.combat_dv_modifier = getattr(adjustment, 'monster_dv_modifier', 1.0)
    entity.combat_av_modifier = getattr(adjustment, 'monster_av_modifier', 1.0)
    entity.combat_attack_modifier = getattr(adjustment, 'monster_attack_modifier', 1.0)