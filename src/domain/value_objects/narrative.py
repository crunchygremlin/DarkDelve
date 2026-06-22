"""Narrative and story outline value objects."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


__all__ = [
    "LevelNarrative",
    "BossEncounter",
    "KeyItem",
    "StoryOutline",
    "NarrativeEvent",
]


@dataclass
class LevelNarrative:
    """Narrative information for a single dungeon level."""
    level_number: int
    title: str
    description: str
    hints_dropped: List[str] = field(default_factory=list)  # hints about future bosses/events
    boss_name: Optional[str] = None
    boss_hint: Optional[str] = None
    required_key_items: List[str] = field(default_factory=list)  # items from previous levels needed here


@dataclass
class BossEncounter:
    """Information about a boss encounter."""
    boss_id: str
    boss_type: str
    level_number: int
    name: str
    description: str
    weaknesses: List[str]      # damage types the boss is weak to
    resistances: List[str]     # damage types the boss resists
    special_loot: List[str]    # items the boss drops
    pre_level_hints: List[str] = field(default_factory=list)  # hints dropped in earlier levels


@dataclass
class KeyItem:
    """An item that appears across multiple levels."""
    item_id: str
    name: str
    item_type: str
    found_level: int           # which level it appears on
    used_level: int            # which level it's needed for
    description: str
    powers: List[str]


@dataclass
class StoryOutline:
    """The DM's plan for the entire dungeon run, created at game start."""
    outline_id: str
    title: str
    theme: str
    difficulty: str
    total_levels: int
    levels: List[LevelNarrative]
    bosses: List[BossEncounter]
    key_items: List[KeyItem]
    opening_narrative: str
    closing_narrative: str
    twist_narrative: Optional[str] = None  # mid-game twist

    def get_hints_for_level(self, level: int) -> List[str]:
        """Get all hints dropped up to this level."""
        hints = []
        for lvl in self.levels:
            if lvl.level_number <= level:
                hints.extend(lvl.hints_dropped)
        return hints

    def get_required_items_for_level(self, level: int) -> List[str]:
        """Get items from previous levels needed for this level."""
        for lvl in self.levels:
            if lvl.level_number == level:
                return lvl.required_key_items
        return []


@dataclass
class NarrativeEvent:
    """A narrative event that can trigger during gameplay."""
    event_id: str
    trigger: str               # "level_start", "boss_seen", "item_picked", "level_end"
    level_number: int
    text: str
    speaker: Optional[str] = None  # NPC or narrator
    requires_items: List[str] = field(default_factory=list)
    blocks_progress: bool = False  # if True, player must acknowledge