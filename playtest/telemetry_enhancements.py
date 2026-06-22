"""
Enhanced telemetry for multi-level DM-aware playtesting.
Tracks: level progression, DM influence, power scaling, exploration, performance.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class LevelSnapshot:
    """Snapshot of game state at a level transition."""
    level_number: int
    entry_tick: int
    exit_tick: int
    duration_ticks: int
    player_hp_start: int
    player_hp_end: int
    player_max_hp: int
    player_ac: int
    player_gold_start: int
    player_gold_end: int
    items_collected: List[str]
    mobs_killed: int
    traps_triggered: int
    rooms_explored: int
    total_rooms: int
    exploration_pct: float
    boss_encountered: Optional[str]
    boss_killed: bool
    dm_influence_events: List[str]  # DM events that affected this level
    power_level_snapshot: Dict[str, float]  # offensive/defensive totals
    key_items_found: List[str]
    puzzle_items_collected: List[str]

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "level_number": self.level_number,
            "entry_tick": self.entry_tick,
            "exit_tick": self.exit_tick,
            "duration_ticks": self.duration_ticks,
            "player_hp_start": self.player_hp_start,
            "player_hp_end": self.player_hp_end,
            "player_max_hp": self.player_max_hp,
            "player_ac": self.player_ac,
            "player_gold_start": self.player_gold_start,
            "player_gold_end": self.player_gold_end,
            "items_collected": self.items_collected,
            "mobs_killed": self.mobs_killed,
            "traps_triggered": self.traps_triggered,
            "rooms_explored": self.rooms_explored,
            "total_rooms": self.total_rooms,
            "exploration_pct": self.exploration_pct,
            "boss_encountered": self.boss_encountered,
            "boss_killed": self.boss_killed,
            "dm_influence_events": self.dm_influence_events,
            "power_level_snapshot": self.power_level_snapshot,
            "key_items_found": self.key_items_found,
            "puzzle_items_collected": self.puzzle_items_collected,
        }


@dataclass
class DMInfluenceEvent:
    """Records when the DM influenced gameplay."""
    tick: int
    level: int
    event_type: str  # "hint_dropped", "item_seeded", "mob_placed", "narrative_event", "loyalty_shift", "difficulty_adjust"
    description: str
    impact: str  # "positive", "negative", "neutral"
    details: Dict[str, Any]

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "tick": self.tick,
            "level": self.level,
            "event_type": self.event_type,
            "description": self.description,
            "impact": self.impact,
            "details": self.details,
        }


@dataclass
class PowerLevelProgression:
    """Tracks how player power changes over levels."""
    level: int
    offensive_total: float
    defensive_total: float
    dominant_offense: str
    dominant_defense: str
    strongest_skill: str
    weakest_skill: str
    equipment_summary: List[str]
    power_delta_from_last: float  # change since last level

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "level": self.level,
            "offensive_total": self.offensive_total,
            "defensive_total": self.defensive_total,
            "dominant_offense": self.dominant_offense,
            "dominant_defense": self.dominant_defense,
            "strongest_skill": self.strongest_skill,
            "weakest_skill": self.weakest_skill,
            "equipment_summary": self.equipment_summary,
            "power_delta_from_last": self.power_delta_from_last,
        }


@dataclass
class PlaytestSession:
    """Complete playtest session results."""
    session_id: str
    start_time: float
    end_time: float
    difficulty: str
    total_levels: int
    levels_cleared: int
    total_ticks: int
    final_status: str  # "won", "died", "quit", "max_levels"
    level_snapshots: List[LevelSnapshot] = field(default_factory=list)
    dm_influence_events: List[DMInfluenceEvent] = field(default_factory=list)
    power_progression: List[PowerLevelProgression] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def summary(self) -> str:
        """Generate a human-readable summary."""
        lines = [
            f"=== Playtest Session: {self.session_id} ===",
            f"Status: {self.final_status}",
            f"Difficulty: {self.difficulty}",
            f"Levels: {self.levels_cleared}/{self.total_levels} cleared",
            f"Duration: {self.total_ticks} turns",
            "",
        ]
        
        if self.level_snapshots:
            lines.append("=== Level Progression ===")
            for snap in self.level_snapshots:
                lines.append(
                    f"  Level {snap.level_number}: {snap.duration_ticks}t, "
                    f"HP {snap.player_hp_end}/{snap.player_max_hp}, "
                    f"Gold {snap.player_gold_end}, "
                    f"Exploration: {snap.exploration_pct:.1%}"
                )
            lines.append("")
        
        if self.power_progression:
            lines.append("=== Power Progression ===")
            for prog in self.power_progression:
                lines.append(
                    f"  Level {prog.level}: Offense={prog.offensive_total:.1f}, "
                    f"Defense={prog.defensive_total:.1f}, "
                    f"Delta={prog.power_delta_from_last:+.1f}"
                )
            lines.append("")
        
        if self.dm_influence_events:
            lines.append(f"=== DM Influence Events ({len(self.dm_influence_events)} total) ===")
            for event in self.dm_influence_events[:10]:  # Show first 10
                lines.append(f"  T{event.tick} L{event.level}: [{event.event_type}] {event.description}")
            if len(self.dm_influence_events) > 10:
                lines.append(f"  ... and {len(self.dm_influence_events) - 10} more")
            lines.append("")
        
        if self.errors:
            lines.append(f"=== Errors ({len(self.errors)}) ===")
            for err in self.errors[:5]:
                lines.append(f"  - {err}")
        
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "difficulty": self.difficulty,
            "total_levels": self.total_levels,
            "levels_cleared": self.levels_cleared,
            "total_ticks": self.total_ticks,
            "final_status": self.final_status,
            "level_snapshots": [s.to_dict() for s in self.level_snapshots],
            "dm_influence_events": [e.to_dict() for e in self.dm_influence_events],
            "power_progression": [p.to_dict() for p in self.power_progression],
            "performance_metrics": self.performance_metrics,
            "errors": self.errors,
        }


def create_level_snapshot(
    level_number: int,
    entry_tick: int,
    exit_tick: int,
    player_state: Dict[str, Any],
    items_collected: List[str],
    mobs_killed: int,
    traps_triggered: int,
    rooms_explored: int,
    total_rooms: int,
    boss_encountered: Optional[str],
    boss_killed: bool,
    dm_events: List[str],
    power_snapshot: Dict[str, float],
    key_items: List[str],
    puzzle_items: List[str],
) -> LevelSnapshot:
    """Factory function to create a LevelSnapshot."""
    duration = exit_tick - entry_tick if exit_tick > entry_tick else 0
    exploration = rooms_explored / total_rooms if total_rooms > 0 else 0.0
    
    return LevelSnapshot(
        level_number=level_number,
        entry_tick=entry_tick,
        exit_tick=exit_tick,
        duration_ticks=duration,
        player_hp_start=player_state.get("hp_start", 0),
        player_hp_end=player_state.get("hp", 0),
        player_max_hp=player_state.get("max_hp", 0),
        player_ac=player_state.get("ac", 0),
        player_gold_start=player_state.get("gold_start", 0),
        player_gold_end=player_state.get("gold", 0),
        items_collected=items_collected,
        mobs_killed=mobs_killed,
        traps_triggered=traps_triggered,
        rooms_explored=rooms_explored,
        total_rooms=total_rooms,
        exploration_pct=exploration,
        boss_encountered=boss_encountered,
        boss_killed=boss_killed,
        dm_influence_events=dm_events,
        power_level_snapshot=power_snapshot,
        key_items_found=key_items,
        puzzle_items_collected=puzzle_items,
    )