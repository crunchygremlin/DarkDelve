"""Item emoji lookup table for presentation layer."""
from __future__ import annotations

__all__ = ["get_item_emoji", "ITEM_EMOJI_MAP"]

# Map item types and names to emoji
ITEM_EMOJI_MAP: dict[str, str] = {
    # By ItemType value
    "weapon": "⚔️",
    "armor": "🛡️",
    "potion": "🧪",
    "scroll": "📜",
    "food": "🍖",
    "accessory": "💍",
    "misc": "📦",
    # Specific items (by name keyword)
    "sword": "⚔️",
    "axe": "🪓",
    "mace": "�",
    "dagger": "�",
    "spear": "�",
    "bow": "�",
    "shield": "🛡️",
    "staff": "�",
    "wand": "🪄",
    "ring": "💍",
    "amulet": "📿",
    "necklace": "�",
    "potion_heal": "❤️�",
    "potion_mana": "💙🧪",
    "gold": "💰",
    "key": "�",
    "gem": "💎",
    "book": "📖",
    "torch": "🔥",
    "rope": "�",
    "bomb": "💣",
}


def get_item_emoji(item_type: str, item_name: str = "") -> str:
    """Get emoji for an item. Checks name first, then type. Falls back to '📦'."""
    # Check by name keyword
    name_lower = item_name.lower()
    for keyword, emoji in ITEM_EMOJI_MAP.items():
        if keyword in name_lower:
            return emoji
    # Check by type
    return ITEM_EMOJI_MAP.get(item_type.lower(), "📦")