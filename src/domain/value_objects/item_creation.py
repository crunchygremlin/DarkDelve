"""Item creation system value objects."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional


__all__ = [
    "ItemType",
    "ItemPower",
    "ItemDefense",
    "ItemModifier",
    "ItemCurse",
    "ItemStats",
    "Item",
]


class ItemType(Enum):
    """Types of items in the game."""
    SWORD = "sword"
    AXE = "axe"
    MACE = "mace"
    DAGGER = "dagger"
    SPEAR = "spear"
    BOW = "bow"
    SHIELD = "shield"
    POTION = "potion"
    WAND = "wand"
    RING = "ring"
    AMULET = "amulet"
    SCROLL = "scroll"


class ItemPower(Enum):
    """Elemental/power types for item effects."""
    FIRE = "fire"
    ICE = "ice"
    LIGHTNING = "lightning"
    POISON = "poison"
    HOLY = "holy"
    SHADOW = "shadow"
    BLOOD = "blood"
    ARCANE = "arcane"
    NECROTIC = "necrotic"
    RADIANT = "radiant"
    THUNDER = "thunder"
    ACID = "acid"


class ItemDefense(Enum):
    """Defensive types for item resistances."""
    PHYSICAL = "physical"
    FIRE_DEF = "fire"
    ICE_DEF = "ice"
    LIGHTNING_DEF = "lightning"
    POISON_DEF = "poison"
    HOLY_DEF = "holy"
    SHADOW_DEF = "shadow"
    BLOOD_DEF = "blood"
    ARCANE_DEF = "arcane"
    NECROTIC_DEF = "necrotic"
    RADIANT_DEF = "radiant"
    THUNDER_DEF = "thunder"


class ItemModifier(Enum):
    """Modifiers that enhance item properties."""
    SHARP = "sharp"            # +piercing damage
    HEAVY = "heavy"            # +bludgeoning damage
    SWIFT = "swift"            # +attack speed
    PRECISE = "precise"       # +critical chance
    VAMPIRIC = "vampiric"      # heal on hit
    BERSERK = "berserk"        # more damage when low health
    GUARDIAN = "guardian"      # +defense when blocking
    ETHEREAL = "ethereal"      # can hit incorporeal
    EXPLOSIVE = "explosive"    # area damage on crit
    CHAINED = "chained"        # chain lightning on hit
    MIRROR = "mirror"          # reflect spells
    ECHOING = "echoing"        # attacks echo to nearby enemies


class ItemCurse(Enum):
    """Curses that afflict items."""
    BLOODTHIRSTY = "bloodthirsty"    # drains player health slowly
    HEAVY = "heavy"                  # slows movement
    CURSED = "cursed"                # can't unequip
    FRAGILE = "fragile"              # breaks faster
    HUNGRY = "hungry"                # consumes gold to stay equipped
    TREACHEROUS = "treacherous"      # chance to misfire in combat
    BINDING = "binding"              # teleports player back if they flee
    DOOMED = "doomed"                # player takes damage at intervals
    HOLLOW = "hollow"                # reduces max health
    PARASITIC = "parasitic"          # shares damage taken with allies
    VENGEFUL = "vengeful"            # boss enrages when this item is used
    UNSTABLE = "unstable"            # random effect on each use


@dataclass
class ItemStats:
    """Combat stats for an item."""
    damage: float = 0.0
    damage_type: str = "physical"
    defense: float = 0.0
    defense_type: str = "physical"
    attack_speed: float = 1.0
    critical_chance: float = 0.05
    critical_damage: float = 1.5
    range: float = 1.0
    block_chance: float = 0.0
    durability_max: int = 100
    durability_current: int = 100
    uses_remaining: int = -1     # -1 = unlimited
    weight: float = 1.0
    required_level: int = 1
    required_stats: Dict[str, float] = field(default_factory=dict)


@dataclass
class Item:
    """Represents an item in the game."""
    item_id: str
    name: str
    description: str
    item_type: str             # ItemType value
    rarity: str                # "common", "uncommon", "rare", "epic", "legendary", "unique"
    powers: List[str]          # ItemPower values
    defenses: List[str]        # ItemDefense values
    modifiers: List[str]       # ItemModifier values
    curses: List[str]          # ItemCurse values
    stats: ItemStats
    special_abilities: List[str] = field(default_factory=list)
    lore_text: str = ""
    is_quest_item: bool = False
    puzzle_role: Optional[str] = None
    boss_bonus: Optional[str] = None  # damage type this item is strong against
    level_origin: int = 0
    value_gold: int = 0
    is_identified: bool = True

    @property
    def is_degraded(self) -> bool:
        """Check if item is degraded (below 50% durability)."""
        return self.stats.durability_current < self.stats.durability_max * 0.5

    @property
    def is_destroyed(self) -> bool:
        """Check if item is destroyed (0 durability)."""
        return self.stats.durability_current <= 0

    @property
    def has_limited_uses(self) -> bool:
        """Check if item has limited uses (consumables)."""
        return self.stats.uses_remaining > 0

    def use(self) -> bool:
        """Use the item (for consumables). Returns True if consumed."""
        if self.stats.uses_remaining > 0:
            self.stats.uses_remaining -= 1
            return self.stats.uses_remaining <= 0
        return False

    def take_durability_damage(self, amount: int) -> bool:
        """Apply durability damage. Returns True if item breaks."""
        self.stats.durability_current = max(0, self.stats.durability_current - amount)
        return self.is_destroyed

    def repair(self, amount: int):
        """Repair the item's durability."""
        self.stats.durability_current = min(
            self.stats.durability_max,
            self.stats.durability_current + amount
        )