"""Damage cap and floor formulas for balance clamping."""
from __future__ import annotations

__all__ = [
    "compute_monster_damage_cap",
    "compute_player_damage_floor",
    "clamp_monster_damage",
    "clamp_player_damage",
]


def compute_monster_damage_cap(player_max_hp: int) -> int:
    """Monster damage to player is capped at 1/5 of player max HP (min 1)."""
    return max(1, player_max_hp // 5)


def compute_player_damage_floor(monster_max_hp: int) -> int:
    """Player damage to monster is floored so any monster dies in ≤4 hits (min 1)."""
    return max(1, (monster_max_hp + 3) // 4)


def clamp_monster_damage(raw_damage: int, player_max_hp: int) -> int:
    """Clamp monster→player damage to the cap."""
    cap = compute_monster_damage_cap(player_max_hp)
    return min(raw_damage, cap)


def clamp_player_damage(raw_damage: int, monster_max_hp: int) -> int:
    """Clamp player→monster damage to the floor (ensures ≤4 hits to kill)."""
    floor = compute_player_damage_floor(monster_max_hp)
    return max(raw_damage, floor)