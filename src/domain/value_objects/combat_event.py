from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from uuid import uuid4
from enum import Enum


class EventType(Enum):
    """Combat event types"""
    ATTACK = "attack"
    DAMAGE = "damage"
    HEAL = "heal"
    DEATH = "death"
    CRITICAL_HIT = "critical_hit"
    MISS = "miss"
    DODGE = "dodge"
    BLOCK = "block"
    SPELL_CAST = "spell_cast"
    EFFECT_APPLIED = "effect_applied"
    EFFECT_REMOVED = "effect_removed"


class CombatEventType(Enum):
    """Combat event types for services"""
    COMBAT_START = "combat_start"
    COMBAT_END = "combat_end"
    HIT = "hit"
    MISS = "miss"
    CRITICAL_HIT = "critical_hit"
    DEFEND = "defend"
    DODGE = "dodge"
    BLOCK = "block"
    DEFEAT = "defeat"
    LOOT = "loot"


@dataclass
class CombatEvent:
    """Combat event value object"""
    event_type: EventType
    source_id: str
    target_id: str
    timestamp: float
    event_id: Optional[str] = None
    damage_amount: Optional[int] = None
    heal_amount: Optional[int] = None
    critical: bool = False
    dodged: bool = False
    blocked: bool = False
    missed: bool = False
    spell_name: Optional[str] = None
    effects: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate combat event"""
        if not isinstance(self.event_type, EventType):
            raise TypeError("event_type must be an EventType enum")
        if not isinstance(self.source_id, str):
            raise TypeError("source_id must be a string")
        if not isinstance(self.target_id, str):
            raise TypeError("target_id must be a string")
        if not isinstance(self.timestamp, (int, float)):
            raise TypeError("timestamp must be a number")
            
        if self.event_id is None:
            self.event_id = str(uuid4())
            
        # Validate damage/heal amounts
        if self.damage_amount is not None and not isinstance(self.damage_amount, int):
            raise TypeError("damage_amount must be an integer")
        if self.heal_amount is not None and not isinstance(self.heal_amount, int):
            raise TypeError("heal_amount must be an integer")
            
    def is_damage_event(self) -> bool:
        """Check if this is a damage event"""
        return self.event_type == EventType.DAMAGE
        
    def is_heal_event(self) -> bool:
        """Check if this is a heal event"""
        return self.event_type == EventType.HEAL
        
    def is_attack_event(self) -> bool:
        """Check if this is an attack event"""
        return self.event_type == EventType.ATTACK
        
    def is_death_event(self) -> bool:
        """Check if this is a death event"""
        return self.event_type == EventType.DEATH
        
    def is_critical_hit(self) -> bool:
        """Check if this was a critical hit"""
        return self.critical
        
    def was_dodged(self) -> bool:
        """Check if attack was dodged"""
        return self.dodged
        
    def was_blocked(self) -> bool:
        """Check if attack was blocked"""
        return self.blocked
        
    def was_missed(self) -> bool:
        """Check if attack was missed"""
        return self.missed
        
    def add_effect(self, effect: Dict[str, Any]) -> None:
        """Add an effect to the event"""
        self.effects.append(effect)
        
    def get_effects(self) -> List[Dict[str, Any]]:
        """Get all effects"""
        return self.effects.copy()
        
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the event"""
        self.metadata[key] = value
        
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value"""
        return self.metadata.get(key, default)
        
    def get_damage_info(self) -> Dict[str, Any]:
        """Get damage information"""
        return {
            "amount": self.damage_amount,
            "critical": self.critical,
            "dodged": self.dodged,
            "blocked": self.blocked,
            "missed": self.missed
        }
        
    def get_heal_info(self) -> Dict[str, Any]:
        """Get heal information"""
        return {
            "amount": self.heal_amount,
            "effects": self.effects.copy()
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "timestamp": self.timestamp,
            "damage_amount": self.damage_amount,
            "heal_amount": self.heal_amount,
            "critical": self.critical,
            "dodged": self.dodged,
            "blocked": self.blocked,
            "missed": self.missed,
            "spell_name": self.spell_name,
            "effects": self.effects,
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CombatEvent':
        """Create combat event from dictionary"""
        # Convert string event_type to enum
        if isinstance(data["event_type"], str):
            data["event_type"] = EventType(data["event_type"])
            
        return cls(
            event_type=data["event_type"],
            source_id=data["source_id"],
            target_id=data["target_id"],
            timestamp=data["timestamp"],
            event_id=data.get("event_id"),
            damage_amount=data.get("damage_amount"),
            heal_amount=data.get("heal_amount"),
            critical=data.get("critical", False),
            dodged=data.get("dodged", False),
            blocked=data.get("blocked", False),
            missed=data.get("missed", False),
            spell_name=data.get("spell_name"),
            effects=data.get("effects", []),
            metadata=data.get("metadata", {})
        )
        
    def __str__(self) -> str:
        """String representation"""
        if self.is_damage_event():
            return f"CombatEvent: {self.source_id} dealt {self.damage_amount} damage to {self.target_id}"
        elif self.is_heal_event():
            return f"CombatEvent: {self.source_id} healed {self.heal_amount} to {self.target_id}"
        elif self.is_attack_event():
            return f"CombatEvent: {self.source_id} attacked {self.target_id}"
        elif self.is_death_event():
            return f"CombatEvent: {self.target_id} died"
        else:
            return f"CombatEvent: {self.event_type.value} from {self.source_id} to {self.target_id}"