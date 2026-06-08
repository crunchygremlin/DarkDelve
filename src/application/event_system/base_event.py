"""
Base event class for the application layer event system.
"""
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Event:
    """
    Base event class for all game events.
    
    Implements the Event pattern for communication between system components.
    """
    
    def __init__(self, event_type: str, source: str, data: Optional[Dict[str, Any]] = None):
        """
        Initialize the event.
        
        Args:
            event_type: Type of the event
            source: Source of the event (component/system name)
            data: Optional event data
        """
        self.event_id = str(uuid.uuid4())
        self.event_type = event_type
        self.source = source
        self.data = data or {}
        self.timestamp = datetime.now()
        self.handled = False
        self.priority = 0  # Higher numbers = higher priority
    
    def __str__(self) -> str:
        """String representation of the event."""
        return f"Event({self.event_id}, {self.event_type}, {self.source})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the event."""
        return f"Event(id={self.event_id}, type={self.event_type}, source={self.source}, timestamp={self.timestamp})"
    
    def mark_handled(self) -> None:
        """Mark the event as handled."""
        self.handled = True
    
    def is_handled(self) -> bool:
        """
        Check if the event has been handled.
        
        Returns:
            bool: True if event has been handled, False otherwise
        """
        return self.handled
    
    def get_priority(self) -> int:
        """
        Get the event priority.
        
        Returns:
            int: Event priority
        """
        return self.priority
    
    def set_priority(self, priority: int) -> None:
        """
        Set the event priority.
        
        Args:
            priority: Event priority (higher numbers = higher priority)
        """
        self.priority = priority
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the event to a dictionary.
        
        Returns:
            Dict[str, Any]: Event data as dictionary
        """
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "handled": self.handled,
            "priority": self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """
        Create an event from a dictionary.
        
        Args:
            data: Event data as dictionary
            
        Returns:
            Event: The created event
        """
        event = cls(
            event_type=data["event_type"],
            source=data["source"],
            data=data.get("data", {})
        )
        event.event_id = data["event_id"]
        event.timestamp = datetime.fromisoformat(data["timestamp"])
        event.handled = data.get("handled", False)
        event.priority = data.get("priority", 0)
        return event


class EventCategory:
    """Constants for event categories."""
    
    # Game events
    GAME_START = "game_start"
    GAME_PAUSE = "game_pause"
    GAME_RESUME = "game_resume"
    GAME_END = "game_end"
    GAME_SAVE = "game_save"
    GAME_LOAD = "game_load"
    
    # Player events
    PLAYER_MOVE = "player_move"
    PLAYER_ATTACK = "player_attack"
    PLAYER_PICKUP = "player_pickup"
    PLAYER_DROP = "player_drop"
    PLAYER_USE = "player_use"
    PLAYER_EQUIP = "player_equip"
    PLAYER_LEVEL_UP = "player_level_up"
    PLAYER_DEATH = "player_death"
    PLAYER_DAMAGE = "player_damage"
    PLAYER_HEAL = "player_heal"
    
    # Entity events
    ENTITY_SPAWN = "entity_spawn"
    ENTITY_DEATH = "entity_death"
    ENTITY_MOVE = "entity_move"
    ENTITY_DAMAGE = "entity_damage"
    ENTITY_ATTACK = "entity_attack"
    
    # Item events
    ITEM_PICKUP = "item_pickup"
    ITEM_DROP = "item_drop"
    ITEM_USE = "item_use"
    ITEM_EQUIP = "item_equip"
    ITEM_CREATE = "item_create"
    ITEM_DESTROY = "item_destroy"
    
    # Combat events
    COMBAT_START = "combat_start"
    COMBAT_END = "combat_end"
    COMBAT_HIT = "combat_hit"
    COMBAT_MISS = "combat_miss"
    COMBAT_CRITICAL = "combat_critical"
    
    # Environment events
    AREA_ENTER = "area_enter"
    AREA_LEAVE = "area_leave"
    ENVIRONMENT_CHANGE = "environment_change"
    WEATHER_CHANGE = "weather_change"
    TIME_CHANGE = "time_change"
    
    # UI events
    UI_SHOW = "ui_show"
    UI_HIDE = "ui_hide"
    UI_UPDATE = "ui_update"
    UI_INPUT = "ui_input"
    
    # System events
    SYSTEM_ERROR = "system_error"
    SYSTEM_WARNING = "system_warning"
    SYSTEM_INFO = "system_info"
    SYSTEM_DEBUG = "system_debug"


class EventPriority:
    """Constants for event priorities."""
    
    LOWEST = 0
    LOW = 1
    NORMAL = 2
    HIGH = 3
    HIGHEST = 4
    CRITICAL = 5