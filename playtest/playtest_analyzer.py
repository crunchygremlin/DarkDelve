"""
Advanced playtest analysis with per-level breakdown,
DM influence analysis, and power progression charts.
"""

from typing import Any, Dict, List, Optional
from playtest.telemetry_enhancements import PlaytestSession, LevelSnapshot, DMInfluenceEvent, PowerLevelProgression


class PlaytestAnalyzer:
    """Analyzes multi-level playtest results."""

    def __init__(self, session: PlaytestSession):
        self.session = session

    def analyze_level_progression(self) -> Dict[str, Any]:
        """Analyze how the player progressed through levels."""
        if not self.session.level_snapshots:
            return {"error": "No level snapshots available"}
        
        levels = self.session.level_snapshots
        total_duration = sum(s.duration_ticks for s in levels)
        avg_duration = total_duration / len(levels)
        
        hp_changes = []
        gold_changes = []
        exploration_rates = []
        
        for i, snap in enumerate(levels):
            hp_change = snap.player_hp_end - snap.player_hp_start
            gold_change = snap.player_gold_end - snap.player_gold_start
            hp_changes.append(hp_change)
            gold_changes.append(gold_change)
            exploration_rates.append(snap.exploration_pct)
        
        return {
            "total_levels": len(levels),
            "total_duration_ticks": total_duration,
            "avg_duration_per_level": avg_duration,
            "hp_changes": hp_changes,
            "gold_changes": gold_changes,
            "exploration_rates": exploration_rates,
            "avg_exploration": sum(exploration_rates) / len(exploration_rates) if exploration_rates else 0,
            "completion_rate": len([s for s in levels if s.exploration_pct >= 0.8]) / len(levels),
        }

    def analyze_dm_influence(self) -> Dict[str, Any]:
        """Analyze DM influence patterns."""
        events = self.session.dm_influence_events
        if not events:
            return {"total_events": 0, "by_type": {}, "by_level": {}, "impact_summary": {}}
        
        by_type: Dict[str, int] = {}
        by_level: Dict[int, int] = {}
        by_impact: Dict[str, int] = {}
        
        for event in events:
            by_type[event.event_type] = by_type.get(event.event_type, 0) + 1
            by_level[event.level] = by_level.get(event.level, 0) + 1
            by_impact[event.impact] = by_impact.get(event.impact, 0) + 1
        
        return {
            "total_events": len(events),
            "by_type": by_type,
            "by_level": by_level,
            "impact_summary": by_impact,
            "event_frequency": len(events) / max(self.session.total_ticks, 1) * 100,
        }

    def analyze_power_scaling(self) -> Dict[str, Any]:
        """Analyze power level changes across levels."""
        progression = self.session.power_progression
        if not progression:
            return {"error": "No power progression data available"}
        
        offensive_values = [p.offensive_total for p in progression]
        defensive_values = [p.defensive_total for p in progression]
        deltas = [p.power_delta_from_last for p in progression]
        
        return {
            "offensive_progression": offensive_values,
            "defensive_progression": defensive_values,
            "power_deltas": deltas,
            "total_power_gain": (offensive_values[-1] + defensive_values[-1]) - (offensive_values[0] + defensive_values[0]) if len(offensive_values) > 1 else 0,
            "avg_power_gain_per_level": sum(deltas) / len(deltas) if deltas else 0,
            "power_curve": "increasing" if all(d > 0 for d in deltas[1:]) else "decreasing" if all(d < 0 for d in deltas[1:]) else "variable",
        }

    def analyze_exploration(self) -> Dict[str, Any]:
        """Analyze map exploration patterns."""
        snapshots = self.session.level_snapshots
        if not snapshots:
            return {"error": "No level snapshots available"}
        
        total_rooms = sum(s.total_rooms for s in snapshots)
        total_explored = sum(s.rooms_explored for s in snapshots)
        
        return {
            "total_rooms": total_rooms,
            "total_explored": total_explored,
            "overall_exploration_pct": total_explored / total_rooms if total_rooms > 0 else 0,
            "by_level": {s.level_number: s.exploration_pct for s in snapshots},
            "boss_encounters": len([s for s in snapshots if s.boss_encountered]),
            "boss_kill_rate": len([s for s in snapshots if s.boss_killed]) / max(len([s for s in snapshots if s.boss_encountered]), 1),
        }

    def analyze_difficulty_balance(self) -> Dict[str, Any]:
        """Analyze if difficulty was appropriate."""
        progression = self.session.power_progression
        snapshots = self.session.level_snapshots
        
        if not progression or not snapshots:
            return {"error": "Insufficient data"}
        
        # Calculate survival rate per level
        survival_by_level = {}
        for snap in snapshots:
            survival_by_level[snap.level_number] = snap.player_hp_end > 0
        
        # Calculate power efficiency (power gained vs resources spent)
        power_efficiency = []
        for i, prog in enumerate(progression):
            if i > 0:
                prev = progression[i-1]
                efficiency = prog.power_delta_from_last / max(snap.rooms_explored, 1)
                power_efficiency.append(efficiency)
        
        return {
            "survival_by_level": survival_by_level,
            "overall_survival_rate": sum(1 for s in snapshots if s.player_hp_end > 0) / len(snapshots),
            "power_efficiency": power_efficiency,
            "recommended_difficulty": self._recommend_difficulty(),
        }

    def _recommend_difficulty(self) -> str:
        """Recommend difficulty based on session data."""
        if not self.session.level_snapshots:
            return "unknown"
        
        avg_exploration = sum(s.exploration_pct for s in self.session.level_snapshots) / len(self.session.level_snapshots)
        avg_power_gain = sum(p.power_delta_from_last for p in self.session.power_progression) / max(len(self.session.power_progression), 1)
        
        if avg_exploration < 0.3 and avg_power_gain < 0:
            return "too_hard"
        elif avg_exploration > 0.8 and avg_power_gain > 10:
            return "too_easy"
        else:
            return "appropriate"

    def generate_full_report(self) -> str:
        """Generate comprehensive analysis report."""
        lines = [
            "=" * 60,
            "PLAYTEST ANALYSIS REPORT",
            "=" * 60,
            "",
            f"Session ID: {self.session.session_id}",
            f"Status: {self.session.final_status}",
            f"Difficulty: {self.session.difficulty}",
            f"Levels: {self.session.levels_cleared}/{self.session.total_levels}",
            f"Total Turns: {self.session.total_ticks}",
            "",
        ]
        
        # Level Progression
        level_prog = self.analyze_level_progression()
        lines.extend([
            "--- LEVEL PROGRESSION ---",
            f"Total Levels: {level_prog.get('total_levels', 0)}",
            f"Average Duration: {level_prog.get('avg_duration_per_level', 0):.1f} turns",
            f"Average Exploration: {level_prog.get('avg_exploration', 0):.1%}",
            f"Completion Rate: {level_prog.get('completion_rate', 0):.1%}",
            "",
        ])
        
        # Power Scaling
        power = self.analyze_power_scaling()
        lines.extend([
            "--- POWER SCALING ---",
            f"Total Power Gain: {power.get('total_power_gain', 0):.1f}",
            f"Average Gain/Level: {power.get('avg_power_gain_per_level', 0):.1f}",
            f"Power Curve: {power.get('power_curve', 'unknown')}",
            "",
        ])
        
        # DM Influence
        dm = self.analyze_dm_influence()
        lines.extend([
            "--- DM INFLUENCE ---",
            f"Total Events: {dm.get('total_events', 0)}",
            f"Events by Type: {dm.get('by_type', {})}",
            f"Event Frequency: {dm.get('event_frequency', 0):.2f}%",
            "",
        ])
        
        # Exploration
        exploration = self.analyze_exploration()
        lines.extend([
            "--- EXPLORATION ---",
            f"Overall Exploration: {exploration.get('overall_exploration_pct', 0):.1%}",
            f"Boss Encounters: {exploration.get('boss_encounters', 0)}",
            f"Boss Kill Rate: {exploration.get('boss_kill_rate', 0):.1%}",
            "",
        ])
        
        # Difficulty Balance
        difficulty = self.analyze_difficulty_balance()
        lines.extend([
            "--- DIFFICULTY BALANCE ---",
            f"Recommended Difficulty: {difficulty.get('recommended_difficulty', 'unknown')}",
            "",
        ])
        
        return "\n".join(lines)

    def save_report(self, path: str) -> None:
        """Save report to file."""
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(self.generate_full_report())


def analyze_session(session: PlaytestSession) -> Dict[str, Any]:
    """Convenience function to analyze a session."""
    analyzer = PlaytestAnalyzer(session)
    return {
        "level_progression": analyzer.analyze_level_progression(),
        "dm_influence": analyzer.analyze_dm_influence(),
        "power_scaling": analyzer.analyze_power_scaling(),
        "exploration": analyzer.analyze_exploration(),
        "difficulty_balance": analyzer.analyze_difficulty_balance(),
    }