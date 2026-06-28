"""Perception value objects for the Entity AI system."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

__all__ = [
    "PerceptionSense",
    "PerceptionModifiers",
    "PerceptionStatus",
]


class PerceptionSense(Enum):
    """Enumeration of perception types an entity can possess."""
    SIGHT = "sight"
    HEARING = "hearing"
    SMELL = "smell"
    VIBRATION = "vibration"
    ECHOLOCATION = "echolocation"
    MAGIC_SENSE = "magic_sense"


@dataclass
class PerceptionModifiers:
    """Defines how a mob type perceives the world."""
    entity_type: str
    sight_range: float = 8.0
    hearing_range: float = 12.0
    smell_range: float = 4.0
    vibration_range: float = 6.0
    echolocation_range: float = 10.0
    magic_sense_range: float = 5.0
    darkvision: bool = False
    see_invisible: bool = False
    ignore_walls_hearing: bool = False  # hear through walls
    ignore_walls_vibration: bool = False  # feel vibrations through walls
    noise_sensitivity: float = 1.0  # multiplier for hearing
    light_sensitivity: float = 1.0  # multiplier for sight in light
    darkness_penalty: float = 0.5  # multiplier for sight in darkness


@dataclass
class PerceptionStatus:
    """What an entity currently perceives — given to LLM instead of full map."""
    entity_id: str
    can_see_player: bool = False
    can_hear_player: bool = False
    can_smell_player: bool = False
    player_last_known_position: Optional[Any] = None  # Position
    player_noise_level: float = 0.0  # 0.0 silent to 1.0 running
    player_distance_estimate: float = -1.0  # -1 = unknown
    visible_threats: List[str] = field(default_factory=list)  # entity IDs
    visible_items: List[str] = field(default_factory=list)  # item IDs
    visible_allies: List[str] = field(default_factory=list)
    visible_enemies: List[str] = field(default_factory=list)
    environment_danger: float = 0.0  # 0.0 safe to 1.0 extreme danger
    light_level: float = 1.0  # 0.0 pitch black to 1.0 bright
    nearby_traps: int = 0
    nearby_exits: int = 0
    combat_occurring_nearby: bool = False
    ally_health_status: str = "unknown"  # "healthy", "wounded", "critical", "unknown"
    time_since_player_seen: float = -1.0  # seconds, -1 = never seen
    custom_flags: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "entity_id": self.entity_id,
            "can_see_player": self.can_see_player,
            "can_hear_player": self.can_hear_player,
            "can_smell_player": self.can_smell_player,
            "player_last_known_position": (
                self.player_last_known_position.to_dict()
                if hasattr(self.player_last_known_position, 'to_dict')
                else self.player_last_known_position
            ),
            "player_noise_level": self.player_noise_level,
            "player_distance_estimate": self.player_distance_estimate,
            "visible_threats": self.visible_threats,
            "visible_items": self.visible_items,
            "visible_allies": self.visible_allies,
            "visible_enemies": self.visible_enemies,
            "environment_danger": self.environment_danger,
            "light_level": self.light_level,
            "nearby_traps": self.nearby_traps,
            "nearby_exits": self.nearby_exits,
            "combat_occurring_nearby": self.combat_occurring_nearby,
            "ally_health_status": self.ally_health_status,
            "time_since_player_seen": self.time_since_player_seen,
            "custom_flags": self.custom_flags,
        }