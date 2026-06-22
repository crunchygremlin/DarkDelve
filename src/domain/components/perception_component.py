"""Perception component for managing entity perception state."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from src.domain.value_objects.perception import PerceptionStatus, PerceptionModifiers
from src.domain.components.component import Component

__all__ = ["PerceptionComponent"]


@dataclass
class PerceptionComponent(Component):
    """Component that manages an entity's perception state."""
    entity_id: str = ""
    modifiers: PerceptionModifiers = field(default_factory=lambda: PerceptionModifiers("default"))
    current_status: Optional[PerceptionStatus] = None
    last_updated_tick: int = 0
    memory: Dict[str, Any] = field(default_factory=dict)
    # memory stores: last_known_player_pos, last_heard_player_time, etc.

    @property
    def component_type(self) -> str:
        return "perception"

    def update_status(self, status: PerceptionStatus, tick: int):
        """Update the perception status and tick."""
        self.current_status = status
        self.last_updated_tick = tick
        if status.can_see_player and status.player_last_known_position:
            self.memory["last_known_player_pos"] = status.player_last_known_position
            self.memory["last_seen_tick"] = tick
        if status.can_hear_player:
            self.memory["last_heard_tick"] = tick

    def get_last_known_player_pos(self):
        """Get the last known player position from memory."""
        return self.memory.get("last_known_player_pos")

    def ticks_since_player_seen(self, current_tick: int) -> int:
        """Calculate ticks since player was last seen."""
        last = self.memory.get("last_seen_tick", -1)
        return current_tick - last if last >= 0 else -1

    def update(self, delta_time: float, entity: Any) -> None:
        """Update component state (called each frame)."""
        pass  # Perception is updated via update_status() by the orchestrator