"""Fuzion skill service for resolving skill bonuses."""

import yaml
from pathlib import Path
from typing import Any, Tuple, Optional

from src.domain.value_objects.fuzion_stats import PrimaryCharacteristics, SkillSet
from src.domain.value_objects.combat_config import FUZION_CONFIG as C

# Load config
_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "fuzion.yaml"
_CONFIG = None


def _load_config():
    global _CONFIG
    if _CONFIG is None:
        with open(_CONFIG_PATH) as f:
            _CONFIG = yaml.safe_load(f)
    return _CONFIG


# Config-driven mappings
GOVERNING_CHAR_MAP = {
    "fighting": "ref",
    "ranged_weapon": "dex",
    "awareness": "int",
    "control": "will",
    "body": "str",
    "social": "pre",
    "technique": "tech",
    "performance": "pre",
    "education": "int",
}

SKILL_TO_BONUS = {
    "fighting": "attack",
    "ranged_weapon": "attack",
    "awareness": "dv",
    "control": "dv",
    "body": "av",
    "technique": "av",
    "social": "dv",
    "performance": "dv",
    "education": "dv",
}

MOB_SKILL_MAP = {
    "bite": ("attack", 2), "claw": ("attack", 2), "slash": ("attack", 2),
    "sting": ("attack", 1), "feral": ("attack", 1), "power_attack": ("attack", 3),
    "rend": ("attack", 2), "whirlwind": ("attack", 2), "maul": ("attack", 3),
    "howl": ("dv", 1), "war_cry": ("dv", 1), "guard": ("dv", 2), "parry": ("dv", 2),
    "dodge": ("dv", 2), "keen": ("dv", 1), "command": ("dv", 1), "evade": ("dv", 2),
    "shield": ("av", 2), "armor": ("av", 2), "tough": ("av", 1),
    "scales": ("av", 2), "plating": ("av", 3), "dash": ("dv", 0),
}


def get_skill_bonuses(entity: Any) -> Tuple[int, int, int]:
    """Returns (attack_bonus, dv_bonus, av_bonus)."""
    sk = _resolve_skillset(entity)
    if sk is not None:
        return _bonuses_from_skillset(sk)
    # mob string-list path
    skills = getattr(entity, 'skills', []) or []
    atk = dv = av = 0
    for s in skills:
        cat, bonus = MOB_SKILL_MAP.get(s, (None, 0))
        if cat == "attack":
            atk += bonus
        elif cat == "dv":
            dv += bonus
        elif cat == "av":
            av += bonus
    return atk, dv, av


def _resolve_skillset(entity) -> Optional[SkillSet]:
    pc = entity.get_component("power") if hasattr(entity, 'get_component') else None
    if pc is not None and hasattr(pc, 'skills'):
        return pc.skills
    # Check skills list first (for Mob with string skills)
    skills_list = getattr(entity, 'skills', []) or []
    if skills_list:
        return None  # Will use string-list path in get_skill_bonuses
    if hasattr(entity, 'skill_set') and entity.skill_set:
        return entity.skill_set
    return None


def _bonuses_from_skillset(sk: SkillSet) -> Tuple[int, int, int]:
    # Only use Fuzion fields (not legacy fields)
    atk = int((sk.fighting + sk.ranged_weapon) // C.SKILL_BONUS_DIVISOR)
    dv = int((sk.awareness + sk.control) // C.SKILL_BONUS_DIVISOR)
    av = int((sk.technique + sk.body) // C.SKILL_BONUS_DIVISOR)
    return atk, dv, av


def governing_char(entity, category: str) -> int:
    pc = getattr(entity, 'characteristics', None)
    if pc is None:
        return _legacy_char(entity, category)
    return getattr(pc, GOVERNING_CHAR_MAP.get(category, 'dex'), 10)


def _legacy_char(entity, category: str) -> int:
    stats = getattr(entity, 'stats', None)
    if stats is None:
        return 10
    if hasattr(stats, 'get_modifier'):
        # Map Fuzion category to D&D stat
        stat_map = {
            'fighting': 'dexterity',
            'ranged_weapon': 'dexterity',
            'awareness': 'intelligence',
            'control': 'wisdom',
            'body': 'strength',
            'social': 'charisma',
            'technique': 'intelligence',
            'performance': 'charisma',
            'education': 'intelligence',
        }
        return stats.get_modifier(stat_map.get(category, 'dexterity'))
    if isinstance(stats, dict):
        return (stats.get('dex', 10) - 10) // 2
    return 10


def check_rule_of_x(entity: Any, weapon_dc: int = 0) -> Tuple[bool, bool]:
    """Check if entity violates Rule-of-X caps.
    
    Returns (attack_ok, defense_ok) - True if within caps.
    
    AttackPower = DamageDC + REF + Skill <= RULE_OF_X_ATTACK
    DefensePower = Hits/5 + Def/5 + DEX + Skill <= RULE_OF_X_DEFENSE
    """
    pc = getattr(entity, 'characteristics', None)
    if pc is None:
        return True, True  # Legacy entities pass
    
    sk = _resolve_skillset(entity)
    if sk is None:
        return True, True  # No skills, pass
    
    # Attack cap check
    ref = pc.ref
    skill_atk = (sk.fighting + sk.ranged_weapon) // C.SKILL_BONUS_DIVISOR
    attack_power = weapon_dc + ref + skill_atk
    attack_ok = attack_power <= C.RULE_OF_X_ATTACK
    
    # Defense cap check
    dex = pc.dex
    skill_dv = (sk.awareness + sk.control) // C.SKILL_BONUS_DIVISOR
    derived = getattr(entity, 'derived', None)
    hits = derived.hits if derived else pc.body * 5
    defense_power = hits // 5 + pc.con // 5 + dex + skill_dv
    defense_ok = defense_power <= C.RULE_OF_X_DEFENSE
    
    return attack_ok, defense_ok


def enforce_rule_of_x(entity: Any, weapon_dc: int = 0) -> Tuple[int, int]:
    """Enforce Rule-of-X caps, returning clamped (attack_bonus, dv_bonus).
    
    If caps would be exceeded, skill levels are reduced proportionally.
    """
    pc = getattr(entity, 'characteristics', None)
    if pc is None:
        return 0, 0
    
    sk = _resolve_skillset(entity)
    if sk is None:
        return 0, 0
    
    # Get current bonuses
    atk_bonus = int((sk.fighting + sk.ranged_weapon) // C.SKILL_BONUS_DIVISOR)
    dv_bonus = int((sk.awareness + sk.control) // C.SKILL_BONUS_DIVISOR)
    
    # Check and clamp attack
    ref = pc.ref
    attack_power = weapon_dc + ref + atk_bonus
    if attack_power > C.RULE_OF_X_ATTACK:
        excess = attack_power - C.RULE_OF_X_ATTACK
        atk_bonus = max(0, atk_bonus - excess)
    
    # Check and clamp defense
    dex = pc.dex
    derived = getattr(entity, 'derived', None)
    hits = derived.hits if derived else pc.body * 5
    defense_power = hits // 5 + pc.con // 5 + dex + dv_bonus
    if defense_power > C.RULE_OF_X_DEFENSE:
        excess = defense_power - C.RULE_OF_X_DEFENSE
        dv_bonus = max(0, dv_bonus - excess)
    
    return atk_bonus, dv_bonus