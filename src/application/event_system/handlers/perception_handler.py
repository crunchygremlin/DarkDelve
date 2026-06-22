"""Perception event handler for processing perception-related events."""

from typing import Dict, Any
from src.application.event_system.event_handler import EventHandler
from src.application.event_system.base_event import Event
from src.domain.services.perception_service import PerceptionService

__all__ = ["PerceptionEventHandler"]


class PerceptionEventHandler(EventHandler):
    """Handles perception update events."""

    def __init__(self, perception_service: PerceptionService):
        """Initialize the perception event handler."""
        super().__init__(
            handler_id="perception_handler",
            event_types=[
                "entity_moved",
                "combat_started",
                "combat_ended",
                "item_dropped"
            ]
        )
        self.perception_service = perception_service

    def handle_event(self, event: Event) -> bool:
        """Handle a perception event."""
        event_type = event.event_type

        if event_type == "entity_moved":
            # Trigger perception recalculation for nearby entities
            pass  # Actual recalculation happens in game loop tick
        elif event.event_type == "combat_started":
            # Increase noise level in area
            pass
        elif event.event_type == "combat_ended":
            # Decrease noise level in area
            pass
        elif event.event_type == "item_dropped":
            # Item visible to nearby entities
            pass

        return True

    def can_handle(self, event: Event) -> bool:
        """Check if this handler can handle the given event."""
        return event.event_type in ("entity_moved", "combat_started", "combat_ended", "item_dropped")