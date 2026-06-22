"""Difficulty and dungeon level control value objects."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from ..position import Position
    from ..corridor import Corridor
    from ..trap import TrapSpawn
    from ..exit import Exit


__all__ = [
    "DifficultyMode",
    "Room",
    "MobSpawn",
    "ItemSpawn",
    "DungeonLevel",
    "LevelNarrative",
    "BossEncounter",
    "KeyItem",
    "DungeonMasterPlan",
]


class DifficultyMode(Enum):
    """Difficulty modes for dungeon generation."""
    STORY = "story"           # easy, focus on narrative
    NORMAL = "normal"         # balanced challenge + loot
    HARD = "hard"             # challenging, less loot
    NIGHTMARE = "nightmare"   # brutal, minimal loot
    IRONMAN = "ironman"       # permadeath, hardcore


@dataclass
class Room:
    """Represents a room in the dungeon."""
    x: int
    y: int
    width: int
    height: int
    room_type: str            # "normal", "treasure", "boss", "puzzle", "shrine", "trap"
    connected_rooms: List[int] = field(default_factory=list)  # indices of connected rooms
    description: str = ""


@dataclass
class MobSpawn:
    """Represents a mob spawn point in a dungeon level."""
    mob_type: str
    position: "Position"
    social_structure_hint: str  # what group this mob belongs to
    behavior_override: Optional[str] = None


@dataclass
class ItemSpawn:
    """Represents an item spawn point in a dungeon level."""
    item_id: str
    position: "Position"
    is_ground: bool = True     # on floor vs in container
    container_id: Optional[str] = None
    is_trash: bool = False     # non-ordinary but potentially useful later
    puzzle_role: Optional[str] = None  # if this item is needed later


@dataclass
class DungeonLevel:
    """Represents a single level in the dungeon."""
    level_number: int
    difficulty: DifficultyMode
    width: int
    height: int
    rooms: List[Room]
    corridors: List["Corridor"]
    mobs: List[MobSpawn]
    items: List[ItemSpawn]
    traps: List["TrapSpawn"]
    exits: List["Exit"]
    narrative_id: str         # links to story outline
    boss_id: Optional[str] = None    # if this level has a boss
    hints: List[str] = field(default_factory=list)  # hints about future levels/bosses
    required_items: List[str] = field(default_factory=list)  # items player needs to progress
    tags: List[str] = field(default_factory=list)  # "dark", "water", "lava", "library", etc.


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
class DungeonMasterPlan:
    """The DM's overall plan for the dungeon run."""
    difficulty: DifficultyMode
    total_levels: int
    theme: str                # "goblin_warren", "undead_crypt", "dragon_lair", etc.
    story_outline: List[LevelNarrative]
    boss_chain: List[BossEncounter]
    key_items: List[KeyItem]   # items that appear across levels
    player_power_target: Dict[str, float]  # what power level to challenge