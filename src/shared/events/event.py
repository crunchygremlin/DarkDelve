"""Event system for decoupled communication."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4


class EventCategory(Enum):
    """Categories for event classification."""
    COMBAT = "combat"
    MOVEMENT = "movement"
    INVENTORY = "inventory"
    SYSTEM = "system"
    PLAYER = "player"


class EventType(Enum):
    """Standardized event types for the game system.
    
    This enum provides type-safe event identifiers that can be used
    throughout the codebase instead of raw string literals.
    """
    # Combat events
    HIT = "HIT"
    MISS = "MISS"
    CRITICAL_HIT = "CRITICAL_HIT"
    COMBAT_START = "COMBAT_START"
    COMBAT_END = "COMBAT_END"
    
    # Movement events
    MOVEMENT = "MOVEMENT"
    ENTITY_FLED = "ENTITY_FLED"
    
    # Social events
    ALLY_CALLED = "ALLY_CALLED"
    ITEM_PICKED_UP = "ITEM_PICKED_UP"
    ITEM_DROPPED = "ITEM_DROPPED"
    
    # System events
    TURN = "TURN"
    ERROR = "ERROR"
    CRASH = "CRASH"


@dataclass
class Event:
    """Base event class."""
    event_id: str = field(default_factory=lambda: str(uuid4()))
    category: EventCategory = EventCategory.SYSTEM
    event_type: Optional[EventType] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: __import__('time').time())


class EventHandler:
    """Base event handler interface."""
    
    def handle(self, event: Event) -> None:
        """Handle an event."""
        raise NotImplementedError


class EventBus:
    """Event bus for publishing and subscribing to events."""
    
    def __init__(self):
        self._handlers: Dict[EventCategory, List[EventHandler]] = {
            cat: [] for cat in EventCategory
        }
    
    def subscribe(self, category: EventCategory, handler: EventHandler) -> None:
        """Subscribe a handler to an event category."""
        self._handlers[category].append(handler)
    
    def unsubscribe(self, category: EventCategory, handler: EventHandler) -> None:
        """Unsubscribe a handler from an event category."""
        if handler in self._handlers[category]:
            self._handlers[category].remove(handler)
    
    def publish(self, event: Event) -> None:
        """Publish an event to all subscribed handlers."""
        for handler in self._handlers[event.category]:
            try:
                handler.handle(event)
            except Exception:
                pass  # Log in production