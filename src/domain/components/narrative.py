"""Narrative component for handling story progression."""
from typing import Any, Optional, List, Dict
from .component import Component
from ..value_objects.narrative import StoryOutline, NarrativeEvent, LevelNarrative


class NarrativeComponent(Component):
    """Handles story outline progression, hint distribution, and event emission."""

    def __init__(self, component_id: Optional[str] = None):
        super().__init__(component_id)
        self.story_outline: Optional[StoryOutline] = None
        self.current_level: int = 1
        self.events: List[NarrativeEvent] = []
        self.acknowledged_events: List[str] = []

    def set_story_outline(self, outline: StoryOutline) -> None:
        """Set the story outline for this run."""
        self.story_outline = outline

    def advance_level(self) -> None:
        """Advance to the next level."""
        self.current_level += 1

    def get_hints_for_level(self, level: int) -> List[str]:
        """Get all hints available up to a given level."""
        if not self.story_outline:
            return []
        return self.story_outline.get_hints_for_level(level)

    def get_required_items_for_level(self, level: int) -> List[str]:
        """Get items required for a specific level."""
        if not self.story_outline:
            return []
        return self.story_outline.get_required_items_for_level(level)

    def trigger_event(self, event: NarrativeEvent) -> None:
        """Trigger a narrative event."""
        self.events.append(event)

    def acknowledge_event(self, event_id: str) -> None:
        """Mark an event as acknowledged."""
        if event_id not in self.acknowledged_events:
            self.acknowledged_events.append(event_id)

    def is_event_acknowledged(self, event_id: str) -> bool:
        """Check if an event has been acknowledged."""
        return event_id in self.acknowledged_events

    def update(self, delta_time: float, entity: Any) -> None:
        """Update narrative state."""
        pass

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            "current_level": self.current_level,
            "events": [e.__dict__ for e in self.events],
            "acknowledged_events": self.acknowledged_events,
        })
        if self.story_outline:
            data["story_outline"] = self.story_outline.__dict__
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "NarrativeComponent":
        """Create from dictionary."""
        component = cls()
        component.enabled = data.get("enabled", True)
        component.current_level = data.get("current_level", 1)
        component.events = [NarrativeEvent(**e) for e in data.get("events", [])]
        component.acknowledged_events = data.get("acknowledged_events", [])
        return component