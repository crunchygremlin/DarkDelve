"""
Event handler that emits enhanced telemetry events for playtester.
"""

from typing import Any, Dict, List, Optional
from . import EventHandler
from ..base_event import Event


class TelemetryEventHandler(EventHandler):
    """Emits telemetry events for level tracking, DM influence, power monitoring."""

    def __init__(self, handler_id: str = "telemetry_handler"):
        super().__init__(handler_id, event_types=[
            "level_entered", "level_cleared", "mob_killed", "trap_triggered",
            "item_picked", "dm_narrative", "dm_hint", "dm_item_seeded",
            "power_changed", "equipment_changed", "boss_encountered"
        ])
        self.current_level: int = 1
        self.level_start_tick: int = 0
        self.mobs_killed_this_level: int = 0
        self.traps_triggered_this_level: int = 0
        self.items_collected_this_level: List[str] = []
        self.dm_events_this_level: List[str] = []
        self.telemetry_buffer: List[Dict[str, Any]] = []

    def handle_event(self, event: Event) -> bool:
        """Handle an event and record telemetry."""
        if not self.can_handle(event):
            return False
        
        handler = getattr(self, f"_handle_{event.event_type}", None)
        if handler:
            handler(event)
        
        event.mark_handled()
        return True

    def can_handle(self, event: Event) -> bool:
        """Check if this handler can handle the given event."""
        return (
            self.enabled and
            event.event_type in self.event_types and
            not event.is_handled()
        )

    def _handle_level_entered(self, event: Event) -> None:
        """Handle level entered event."""
        self.current_level = event.data.get("level", self.current_level)
        self.level_start_tick = event.data.get("tick", 0)
        self.mobs_killed_this_level = 0
        self.traps_triggered_this_level = 0
        self.items_collected_this_level = []
        self.dm_events_this_level = []

    def _handle_level_cleared(self, event: Event) -> None:
        """Handle level cleared event."""
        self._record_level_completion(event.data.get("level", self.current_level))

    def _handle_mob_killed(self, event: Event) -> None:
        """Handle mob killed event."""
        self.mobs_killed_this_level += 1

    def _handle_trap_triggered(self, event: Event) -> None:
        """Handle trap triggered event."""
        self.traps_triggered_this_level += 1

    def _handle_item_picked(self, event: Event) -> None:
        """Handle item picked event."""
        item_name = event.data.get("item", "unknown")
        self.items_collected_this_level.append(item_name)

    def _handle_dm_narrative(self, event: Event) -> None:
        """Handle DM narrative event."""
        narrative = event.data.get("text", "")
        self.dm_events_this_level.append(narrative)

    def _handle_dm_hint(self, event: Event) -> None:
        """Handle DM hint event."""
        self.dm_events_this_level.append(f"hint: {event.data.get('hint', '')}")

    def _handle_dm_item_seeded(self, event: Event) -> None:
        """Handle DM item seeded event."""
        self.dm_events_this_level.append(f"item_seeded: {event.data.get('item', '')}")

    def _handle_power_changed(self, event: Event) -> None:
        """Handle power changed event."""
        self._record_power_change(event.data)

    def _handle_equipment_changed(self, event: Event) -> None:
        """Handle equipment changed event."""
        self._record_equipment_change(event.data)

    def _handle_boss_encountered(self, event: Event) -> None:
        """Handle boss encountered event."""
        self._record_boss_event(event.data)

    def _record_level_completion(self, level: int) -> None:
        """Record level completion telemetry."""
        self.telemetry_buffer.append({
            "event_type": "level_complete",
            "level": level,
            "mobs_killed": self.mobs_killed_this_level,
            "traps_triggered": self.traps_triggered_this_level,
            "items_collected": len(self.items_collected_this_level),
            "dm_events": len(self.dm_events_this_level),
        })

    def _record_power_change(self, data: Dict[str, Any]) -> None:
        """Record power change telemetry."""
        self.telemetry_buffer.append({
            "event_type": "power_change",
            "level": self.current_level,
            "offensive": data.get("offensive", 0),
            "defensive": data.get("defensive", 0),
        })

    def _record_equipment_change(self, data: Dict[str, Any]) -> None:
        """Record equipment change telemetry."""
        self.telemetry_buffer.append({
            "event_type": "equipment_change",
            "level": self.current_level,
            "item": data.get("item", ""),
            "slot": data.get("slot", ""),
        })

    def _record_boss_event(self, data: Dict[str, Any]) -> None:
        """Record boss encounter telemetry."""
        self.telemetry_buffer.append({
            "event_type": "boss_event",
            "level": self.current_level,
            "boss": data.get("boss", ""),
            "killed": data.get("killed", False),
        })

    def get_telemetry(self) -> List[Dict[str, Any]]:
        """Get all recorded telemetry."""
        return self.telemetry_buffer.copy()

    def clear_telemetry(self) -> None:
        """Clear the telemetry buffer."""
        self.telemetry_buffer.clear()