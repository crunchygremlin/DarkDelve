"""
Combat Damage Log - Persistent logging of combat damage events.

Records every combat event (hit, miss, critical) with timestamps,
attacker/defender names, and damage amounts during a game session,
then exports to a JSON file on game end.
"""

import json
import os
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class DamageEntry:
    """A single combat damage event entry."""
    timestamp: str          # ISO 8601 format: "2026-06-27T05:18:10.858Z"
    turn: int               # Game turn number
    attacker_name: str      # e.g. "Player", "Goblin"
    defender_name: str      # e.g. "Goblin", "Player"
    damage: int             # Damage dealt (0 for misses)
    hit: bool               # True if attack hit
    critical: bool          # True if critical hit
    event_type: str         # "hit", "miss", "critical", "critical_fail", "out_of_range"
    flavor_text: str        # Human-readable message from CombatEvent.__str__()


class CombatDamageLog:
    """
    Records all combat events during a game session and exports to JSON.
    
    Stores events in memory as DamageEntry objects. Call record_event()
    after each combat resolution. Call export_to_json() on game end to
    write the log file.
    """
    
    def __init__(self, output_dir: str = "logs"):
        """
        Initialize the combat damage log.
        
        Args:
            output_dir: Directory to write JSON files. Created if missing.
        """
        self.entries: List[DamageEntry] = []
        self.output_dir: str = output_dir
        self.session_id: str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    
    def record_event(self, event: Any, attacker: Any, defender: Any) -> None:
        """
        Record a combat event from a darkdelve CombatEvent object.
        
        Args:
            event: The CombatEvent dataclass from CombatResolver.resolve_attack()
            attacker: The attacking Entity (has .name attribute)
            defender: The defending Entity (has .name attribute)
        """
        # Map HitResult to event_type string
        # Deferred import to avoid circular dependencies
        from darkdelve import HitResult
        
        if event.result == HitResult.CRITICAL:
            event_type = "critical"
        elif event.result == HitResult.HIT:
            event_type = "hit"
        elif event.result == HitResult.MISS:
            event_type = "miss"
        elif event.result == HitResult.CRITICAL_FAIL:
            event_type = "critical_fail"
        else:
            event_type = "miss"
        
        # Override for out_of_range events
        if getattr(event, 'out_of_range', False):
            event_type = "out_of_range"
        
        # Determine hit boolean
        is_hit = event.result in (HitResult.HIT, HitResult.CRITICAL)
        
        entry = DamageEntry(
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            turn=event.turn,
            attacker_name=event.attacker_name,
            defender_name=event.defender_name,
            damage=event.damage,
            hit=is_hit,
            critical=(event.result == HitResult.CRITICAL),
            event_type=event_type,
            flavor_text=event.__str__("neutral")
        )
        self.entries.append(entry)
    
    def export_to_json(self, session_id: Optional[str] = None) -> str:
        """
        Export all recorded events to a JSON file.
        
        Args:
            session_id: Optional session identifier. Uses self.session_id if None.
            
        Returns:
            str: The file path that was written.
        """
        sid = session_id or self.session_id
        output_path = Path(self.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        file_path = output_path / f"combat_damage_{sid}.json"
        
        data = {
            "session_id": sid,
            "total_entries": len(self.entries),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "summary": self.get_summary(),
            "entries": [asdict(entry) for entry in self.entries]
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return str(file_path)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Calculate summary statistics for all recorded events.
        
        Returns:
            Dict with keys: total_damage_dealt, total_hits, total_misses,
            total_criticals, total_critical_fails, total_out_of_range,
            unique_attackers, unique_defenders
        """
        total_damage = sum(e.damage for e in self.entries)
        # CB-001 FIX B: count ALL successful attacks (HIT and CRITICAL) as hits.
        # `e.hit` is already True for both (set in record_event line 80), so this
        # includes criticals that the old `e.event_type == "hit"` filter excluded.
        hits = sum(1 for e in self.entries if e.hit)
        criticals = sum(1 for e in self.entries if e.critical)
        misses = sum(1 for e in self.entries if e.event_type == "miss")
        critical_fails = sum(1 for e in self.entries if e.event_type == "critical_fail")
        out_of_range = sum(1 for e in self.entries if e.event_type == "out_of_range")
        
        unique_attackers = list(set(e.attacker_name for e in self.entries))
        unique_defenders = list(set(e.defender_name for e in self.entries))
        
        return {
            "total_damage_dealt": total_damage,
            "total_hits": hits,
            "total_misses": misses,
            "total_critical_hits": criticals,
            "total_critical_fails": critical_fails,
            "total_out_of_range": out_of_range,
            "total_events": len(self.entries),
            "unique_attackers": unique_attackers,
            "unique_defenders": unique_defenders
        }
    
    def clear(self) -> None:
        """Clear all recorded entries."""
        self.entries = []