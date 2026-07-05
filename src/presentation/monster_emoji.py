"""Monster emoji lookup table for presentation layer."""
from __future__ import annotations

__all__ = ["get_monster_emoji", "MONSTER_EMOJI_MAP"]

# Map monster type/role identifiers to emoji
MONSTER_EMOJI_MAP: dict[str, str] = {
    # Floor 1 monsters
    "dungeon_guard": "💂",
    "guard_sergeant": "�",
    "giant_spider": "🕸️",
    "spider_queen": "🕸️",
    "cave_rat": "🐀",
    "rat_king": "��",
    "troll_scavenger": "�",
    "fungal_creeper": "�",
    "cave_bat": "🦇",
    # Generic tiers
    "minion": "�",
    "soldier": "⚔️",
    "elite": "💀",
    "boss": "🐉",
    # Classic roguelike types
    "goblin": "👺",
    "orc": "👹",
    "dragon": "🐉",
    "skeleton": "💀",
    "zombie": "🧟",
    "ghost": "👻",
    "slime": "�",
    "wolf": "🐺",
    "snake": "�",
    "kobold": "🦎",
    "imp": "�",
    "demon": "👿",
    "lich": "�️",
    "vampire": "�",
    "werewolf": "🐺",
    "golem": "🗿",
    "mimic": "�",
    "mushroom": "�",
    "eyeball": "👁️",
    "tentacle": "�",
    "wraith": "�",
    "centipede": "�",
    "scorpion": "🦂",
    "mantis": "🦗",
    "rat": "🐀",
    "bat": "🦇",
    "rat_king": "�",
}


def get_monster_emoji(monster_type: str) -> str:
    """Get emoji for a monster type string. Falls back to '❓'."""
    return MONSTER_EMOJI_MAP.get(monster_type.lower(), "❓")