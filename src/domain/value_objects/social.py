"""Social value objects for the Entity AI system."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

__all__ = [
    "RelationshipType",
    "SocialStructureType",
    "SocialRelationship",
    "SocialStructure",
    "LoyaltyState",
]


class RelationshipType(Enum):
    """Types of relationships between entities."""
    LOYALTY = "loyalty"
    FEAR = "fear"
    RIVALRY = "rivalry"
    FRIENDSHIP = "friendship"
    SERVITUDE = "servitude"
    DOMINATION = "domination"
    HIVE_MIND = "hive_mind"
    CONTRACT = "contract"


class SocialStructureType(Enum):
    """Types of social structures in the game."""
    GOBLIN_KINGDOM = "goblin_kingdom"
    WOLF_PACK = "wolf_pack"
    SPIDER_HIVE = "spider_hive"
    MERCENARY_BAND = "mercenary_band"
    UNDEAD_COURT = "undead_court"
    MERCHANT_GUILD = "merchant_guild"


@dataclass
class SocialRelationship:
    """Represents a relationship between two entities."""
    entity_a_id: str
    entity_b_id: str
    relationship_type: str  # RelationshipType value
    strength: float = 0.0  # -1.0 to 1.0
    history: List[str] = field(default_factory=list)


@dataclass
class SocialStructure:
    """Represents a social group or organization."""
    structure_id: str
    structure_type: str  # SocialStructureType value
    leader_id: str
    member_ids: List[str] = field(default_factory=list)
    hierarchy: Dict[str, int] = field(default_factory=dict)  # entity_id -> rank (0=leader)
    shared_goals: List[str] = field(default_factory=list)
    wealth_pool: float = 0.0
    relationships: List[SocialRelationship] = field(default_factory=list)


@dataclass
class LoyaltyState:
    """Tracks loyalty of a minion toward their leader."""
    minion_id: str
    leader_id: str
    loyalty_score: float = 0.5  # 0.0 to 1.0
    base_loyalty: float = 0.5   # seeded at level start
    modifiers: List[Dict[str, Any]] = field(default_factory=list)
    # Each modifier: {"source": str, "amount": float, "reason": str, "tick": int}

    def apply_modifier(self, source: str, amount: float, reason: str, tick: int):
        """Apply a loyalty modifier to this state."""
        self.modifiers.append({
            "source": source, "amount": amount,
            "reason": reason, "tick": tick
        })
        self.loyalty_score = max(0.0, min(1.0, self.loyalty_score + amount))

    def will_follow_orders(self) -> bool:
        """Check if the minion will follow orders."""
        return self.loyalty_score > 0.2

    def will_desert(self) -> bool:
        """Check if the minion will desert."""
        return self.loyalty_score < 0.1

    def will_betray(self) -> bool:
        """Check if the minion will betray their leader."""
        return self.loyalty_score < 0.05

    def is_fanatic(self) -> bool:
        """Check if the minion is fanatically loyal."""
        return self.loyalty_score > 0.9