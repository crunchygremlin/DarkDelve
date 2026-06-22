"""Narrative service for managing story progression."""
from typing import List, Optional
from ..value_objects.narrative import StoryOutline, NarrativeEvent
from ..components.narrative import NarrativeComponent


__all__ = [
    "NarrativeService",
]


class NarrativeService:
    """Updates StoryOutline, triggers NarrativeEvents, and stores hints."""

    def __init__(self, component: Optional[NarrativeComponent] = None):
        self.component = component or NarrativeComponent()

    def set_outline(self, outline: StoryOutline) -> None:
        """Set the story outline for this run."""
        self.component.set_story_outline(outline)

    def advance_level(self) -> None:
        """Advance to the next level."""
        self.component.advance_level()

    def get_hints_for_level(self, level: int) -> List[str]:
        """Get hints available up to a given level."""
        return self.component.get_hints_for_level(level)

    def get_required_items_for_level(self, level: int) -> List[str]:
        """Get items required for a specific level."""
        return self.component.get_required_items_for_level(level)

    def trigger_event(self, event: NarrativeEvent) -> None:
        """Trigger a narrative event."""
        self.component.trigger_event(event)

    def acknowledge_event(self, event_id: str) -> None:
        """Mark an event as acknowledged."""
        self.component.acknowledge_event(event_id)

    def is_event_acknowledged(self, event_id: str) -> bool:
        """Check if an event has been acknowledged."""
        return self.component.is_event_acknowledged(event_id)

    def get_current_level(self) -> int:
        """Get the current level number."""
        return self.component.current_level