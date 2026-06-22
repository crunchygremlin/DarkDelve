"""Social event handler for processing social-related events."""

from typing import Dict, Any
from src.application.event_system.event_handler import EventHandler
from src.application.event_system.base_event import Event
from src.domain.services.social_service import SocialService

__all__ = ["SocialEventHandler"]


class SocialEventHandler(EventHandler):
    """Handles social events: gifts, promotions, combat together, leader fleeing."""

    def __init__(self, social_service: SocialService):
        """Initialize the social event handler."""
        super().__init__(
            handler_id="social_handler",
            event_types=[
                "item_gifted",
                "combat_alongside",
                "leader_fled",
                "minion_promoted",
                "wealth_distributed"
            ]
        )
        self.social_service = social_service

    def handle_event(self, event: Event) -> bool:
        """Handle a social event."""
        event_type = event.event_type
        data = event.data

        if event_type == "item_gifted":
            self.social_service.process_gift(
                giver_id=data["giver_id"],
                receiver_id=data["receiver_id"],
                item_value=data.get("item_value", 0),
                tick=data.get("tick", 0)
            )
        elif event_type == "combat_alongside":
            self.social_service.process_combat_alongside(
                ally_id=data["ally_id"],
                tick=data.get("tick", 0)
            )
        elif event_type == "leader_fled":
            self.social_service.process_leader_fled(
                leader_id=data["leader_id"],
                tick=data.get("tick", 0)
            )
        elif event_type == "minion_promoted":
            self.social_service.process_promotion(
                structure_id=data["structure_id"],
                entity_id=data["entity_id"],
                new_rank=data["new_rank"],
                tick=data.get("tick", 0)
            )
        elif event_type == "wealth_distributed":
            self.social_service.distribute_wealth(
                structure_id=data["structure_id"],
                total_wealth=data["total_wealth"],
                distribution=data["distribution"],
                tick=data.get("tick", 0)
            )

        return True

    def can_handle(self, event: Event) -> bool:
        """Check if this handler can handle the given event."""
        return event.event_type in (
            "item_gifted", "combat_alongside", "leader_fled",
            "minion_promoted", "wealth_distributed"
        )