"""
Reads enhanced game state from the game console output.
Extracts power levels, DM events, level info beyond basic stats.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple


class GameStateReader:
    """Reads and parses enhanced game state from console frames."""

    def __init__(self):
        self.current_level: int = 1
        self.current_tick: int = 0
        self.dm_events: List[Dict[str, Any]] = []
        self.power_levels: Dict[str, float] = {}
        self.explored_tiles: Set[Tuple[int, int]] = set()
        self.visited_levels: Set[int] = set()
        self._level_start_tick: int = 0
        self._rooms_explored: int = 0
        self._total_rooms: int = 0

    def read_frame(self, frame: str) -> Dict[str, Any]:
        """
        Read enhanced state from a console frame.
        Looks for structured output markers from the game.
        """
        state: Dict[str, Any] = {}
        
        # Parse standard stats (HP can be "HP: 10" or "HP: 10/10")
        hp_match = re.search(r'HP:\s*(\d+)(?:/(\d+))?', frame)
        if hp_match:
            state['hp'] = int(hp_match.group(1))
            state['max_hp'] = int(hp_match.group(2)) if hp_match.group(2) else int(hp_match.group(1))
        state['ac'] = self._extract_int(r'AC:\s*(\d+)', frame)
        state['depth'] = self._extract_int(r'Depth:\s*(\d+)', frame)
        state['gold'] = self._extract_int(r'Gold:\s*(\d+)', frame)
        state['turn'] = self._extract_int(r'Turn:\s*(\d+)', frame)
        
        # Parse power level info if displayed
        state['melee_power'] = self._extract_float(r'Melee:\s*([\d.]+)', frame)
        state['magic_power'] = self._extract_float(r'Magic:\s*([\d.]+)', frame)
        state['defense'] = self._extract_float(r'Defense:\s*([\d.]+)', frame)
        
        # Parse DM narrative text if present
        dm_match = re.search(r'\[DM\]\s*(.+?)(?:\n|$)', frame)
        if dm_match:
            state['dm_narrative'] = dm_match.group(1)
        
        # Parse level transition markers
        level_match = re.search(r'Level\s+(\d+)', frame)
        if level_match:
            new_level = int(level_match.group(1))
            if new_level != self.current_level:
                state['level_changed'] = True
                state['new_level'] = new_level
                self.current_level = new_level
        
        # Parse exploration info
        explored_match = re.search(r'Explored:\s*(\d+)/(\d+)', frame)
        if explored_match:
            state['rooms_explored'] = int(explored_match.group(1))
            state['total_rooms'] = int(explored_match.group(2))
        
        # Parse boss info
        boss_match = re.search(r'Boss:\s*(\w+)', frame)
        if boss_match:
            state['boss'] = boss_match.group(1)
        
        # Parse items collected this turn
        items_match = re.search(r'Items:\s*(.+?)(?:\n|$)', frame)
        if items_match:
            state['items_this_turn'] = items_match.group(1).split(',')
        
        return state

    def _extract_int(self, pattern: str, text: str) -> Optional[int]:
        match = re.search(pattern, text)
        return int(match.group(1)) if match else None

    def _extract_float(self, pattern: str, text: str) -> Optional[float]:
        match = re.search(pattern, text)
        return float(match.group(1)) if match else None

    def record_dm_event(
        self,
        tick: int,
        level: int,
        event_type: str,
        description: str,
        impact: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Record a DM influence event."""
        event = {
            'tick': tick,
            'level': level,
            'event_type': event_type,
            'description': description,
            'impact': impact,
            'details': details or {}
        }
        self.dm_events.append(event)
        return event

    def update_power_levels(self, offensive: float, defensive: float, skills: Dict[str, float]) -> Dict[str, float]:
        """Update and return current power levels."""
        self.power_levels = {
            'offensive': offensive,
            'defensive': defensive,
            'skills': skills
        }
        return self.power_levels.copy()

    def mark_tile_explored(self, x: int, y: int) -> None:
        """Mark a tile as explored."""
        self.explored_tiles.add((x, y))

    def mark_level_visited(self, level: int) -> None:
        """Mark a level as visited."""
        self.visited_levels.add(level)

    def get_exploration_stats(self) -> Dict[str, Any]:
        """Get current exploration statistics."""
        return {
            'tiles_explored': len(self.explored_tiles),
            'levels_visited': len(self.visited_levels),
            'visited_levels': sorted(self.visited_levels)
        }

    def reset_level_tracking(self) -> None:
        """Reset level-specific tracking for a new level."""
        self._rooms_explored = 0
        self._total_rooms = 0

    def set_room_counts(self, explored: int, total: int) -> None:
        """Set the room counts for the current level."""
        self._rooms_explored = explored
        self._total_rooms = total

    def get_level_exploration_pct(self) -> float:
        """Get exploration percentage for current level."""
        if self._total_rooms == 0:
            return 0.0
        return self._rooms_explored / self._total_rooms

    def set_level_start(self, level: int, tick: int) -> None:
        """Set the start of a level."""
        self.current_level = level
        self._level_start_tick = tick
        self.visited_levels.add(level)

    def get_level_duration(self, current_tick: int) -> int:
        """Get the duration of the current level in ticks."""
        return current_tick - self._level_start_tick