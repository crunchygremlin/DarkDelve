"""Map access value objects for the Entity AI system."""

from dataclasses import dataclass
from typing import Optional, Tuple

__all__ = ["MapAccessRequest"]


@dataclass
class MapAccessRequest:
    """Request for map access by an entity."""
    requester_id: str
    reason: str  # "level_creation", "spell_clairvoyance", "commander_coordination", "debug"
    access_type: str  # "full", "fog_of_war", "specific_area"
    area: Optional[Tuple[int, int, int, int]] = None  # x, y, w, h
    duration_ticks: int = 1
    granted: bool = False