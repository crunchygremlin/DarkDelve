"""
Multi-level playtest system with DM influence tracking,
power progression, and per-level analysis.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from playtest.game_state_reader import GameStateReader
from playtest.telemetry_enhancements import (
    DMInfluenceEvent,
    LevelSnapshot,
    PlaytestSession,
    PowerLevelProgression,
    create_level_snapshot,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class MultiLevelPlaytestConfig:
    """Configuration for multi-level playtesting."""
    game_command: List[str] = field(
        default_factory=lambda: [sys.executable, str(PROJECT_ROOT / "darkdelve.py")]
    )
    max_levels: int = 5
    max_turns: int = 500
    max_duration_seconds: int = 600
    telemetry_path: str = "playtest/telemetry/session.json"
    difficulty: str = "normal"
    record_frames: bool = True


class MultiLevelPlaytester:
    """
    Enhanced playtester that:
    - Tracks level progression
    - Records DM influence events
    - Monitors power level scaling
    - Analyzes map exploration
    - Generates per-level reports
    """

    def __init__(self, config: Optional[MultiLevelPlaytestConfig] = None):
        self.config = config or MultiLevelPlaytestConfig()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.game_state_reader = GameStateReader()
        self.level_snapshots: List[LevelSnapshot] = []
        self.dm_events: List[DMInfluenceEvent] = []
        self.power_progression: List[PowerLevelProgression] = []
        self.current_level_data: Optional[Dict[str, Any]] = None
        self.performance_samples: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        
        # Level tracking state
        self._level_start_tick: int = 0
        self._level_start_hp: int = 0
        self._level_start_gold: int = 0
        self._level_items: List[str] = []
        self._level_mobs_killed: int = 0
        self._level_traps: int = 0
        self._level_boss: Optional[str] = None
        self._level_boss_killed: bool = False
        self._level_dm_events: List[str] = []
        self._level_power_snapshot: Dict[str, float] = {}
        self._level_key_items: List[str] = []
        self._level_puzzle_items: List[str] = []
        self._total_rooms: int = 0
        self._rooms_explored: int = 0

    def run_session(self, max_levels: Optional[int] = None, max_turns: Optional[int] = None) -> PlaytestSession:
        """Run a full multi-level playtest session."""
        max_l = max_levels or self.config.max_levels
        max_t = max_turns or self.config.max_turns
        
        process = None
        stdout_buffer = ""
        turn_number = 0
        status = "running"
        start_time = time.time()
        
        try:
            process = self._start_game()
            self._reset_level_state(level=1, tick=0)
            
            while True:
                elapsed = time.time() - start_time
                if elapsed > self.config.max_duration_seconds:
                    status = "timeout"
                    self.errors.append(f"Session exceeded {self.config.max_duration_seconds}s limit")
                    break
                
                if turn_number >= max_t:
                    status = "max_turns"
                    break
                
                if process.poll() is not None:
                    status = "won" if process.returncode == 0 else "died"
                    break
                
                chunk = self._read_available(process.stdout)
                if chunk:
                    stdout_buffer += chunk
                    frames, stdout_buffer = self._parse_frames(stdout_buffer)
                    
                    for frame in frames:
                        turn_number = self._process_frame(frame, turn_number)
                        
                        # Check for level completion
                        if self.game_state_reader.current_level > len(self.level_snapshots):
                            self._finalize_level(self.game_state_reader.current_level - 1)
                        
                        if self.game_state_reader.current_level > max_l:
                            status = "max_levels"
                            break
                
                if status == "max_levels":
                    break
                    
                time.sleep(0.01)
                
        except Exception as e:
            status = "error"
            self.errors.append(str(e))
        finally:
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        
        # Finalize any in-progress level
        if self.game_state_reader.current_level > len(self.level_snapshots):
            self._finalize_level(self.game_state_reader.current_level)
        
        return self._generate_session_report(status, turn_number, start_time)

    def _start_game(self) -> subprocess.Popen:
        """Launch the game subprocess."""
        return subprocess.Popen(
            self.config.game_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=str(PROJECT_ROOT)
        )

    def _process_frame(self, frame: str, turn: int) -> int:
        """Process a single frame, extracting all telemetry."""
        state = self.game_state_reader.read_frame(frame)
        
        # Update tick
        if state.get('turn'):
            self.game_state_reader.current_tick = state['turn']
        
        # Detect level changes
        if state.get('level_changed'):
            new_level = state['new_level']
            self._detect_level_change(new_level, state.get('turn', turn))
        
        # Detect DM influence
        if state.get('dm_narrative'):
            self._detect_dm_influence(state['dm_narrative'], state.get('turn', turn))
        
        # Capture power snapshot
        if any(state.get(k) for k in ['melee_power', 'magic_power', 'defense']):
            self._capture_power_snapshot(state)
        
        # Track exploration
        if state.get('rooms_explored') is not None:
            self._rooms_explored = state['rooms_explored']
        if state.get('total_rooms') is not None:
            self._total_rooms = state['total_rooms']
        
        return turn + 1

    def _detect_level_change(self, new_level: int, tick: int) -> None:
        """Detect and record level transitions."""
        if self.game_state_reader.current_level > 1:
            # Finalize previous level
            self._finalize_level(self.game_state_reader.current_level - 1)
        
        self.game_state_reader.set_level_start(new_level, tick)
        self._reset_level_state(level=new_level, tick=tick)

    def _detect_dm_influence(self, narrative: str, tick: int) -> None:
        """Detect DM influence events from frame text."""
        # Parse DM event types
        event_patterns = {
            'hint_dropped': r'hint|clue|tip',
            'item_seeded': r'item|treasure|loot',
            'mob_placed': r'mob|enemy|creature|spawn',
            'narrative_event': r'story|tale|legend|ancient',
            'loyalty_shift': r'loyalty|faith|devotion',
            'difficulty_adjust': r'difficulty|harder|easier|challenge'
        }
        
        for event_type, pattern in event_patterns.items():
            if re.search(pattern, narrative, re.IGNORECASE):
                event = DMInfluenceEvent(
                    tick=tick,
                    level=self.game_state_reader.current_level,
                    event_type=event_type,
                    description=narrative[:100],
                    impact="neutral",
                    details={"narrative": narrative}
                )
                self.dm_events.append(event)
                self._level_dm_events.append(f"{event_type}: {narrative[:50]}")
                break

    def _capture_power_snapshot(self, state: Dict[str, Any]) -> None:
        """Capture current power level state."""
        offensive = (state.get('melee_power', 0) or 0) + (state.get('magic_power', 0) or 0)
        defensive = state.get('defense', 0) or 0
        
        self.game_state_reader.update_power_levels(
            offensive=offensive,
            defensive=defensive,
            skills={'melee': state.get('melee_power', 0) or 0, 'magic': state.get('magic_power', 0) or 0}
        )
        
        self._level_power_snapshot = {
            'offensive': offensive,
            'defensive': defensive
        }

    def _reset_level_state(self, level: int, tick: int) -> None:
        """Reset tracking state for a new level."""
        self.game_state_reader.current_level = level
        self._level_start_tick = tick
        self._level_start_hp = self.game_state_reader.current_tick  # Will be updated from frame
        self._level_start_gold = 0
        self._level_items = []
        self._level_mobs_killed = 0
        self._level_traps = 0
        self._level_boss = None
        self._level_boss_killed = False
        self._level_dm_events = []
        self._level_power_snapshot = {}
        self._level_key_items = []
        self._level_puzzle_items = []

    def _finalize_level(self, level: int) -> None:
        """Generate and store a level snapshot."""
        # Get current player state
        state = self.game_state_reader.power_levels
        
        snapshot = create_level_snapshot(
            level_number=level,
            entry_tick=self._level_start_tick,
            exit_tick=self.game_state_reader.current_tick,
            player_state={
                'hp_start': self._level_start_hp,
                'hp': state.get('hp', 0),
                'max_hp': state.get('max_hp', 0),
                'ac': state.get('ac', 0),
                'gold_start': self._level_start_gold,
                'gold': state.get('gold', 0)
            },
            items_collected=self._level_items,
            mobs_killed=self._level_mobs_killed,
            traps_triggered=self._level_traps,
            rooms_explored=self._rooms_explored,
            total_rooms=self._total_rooms,
            boss_encountered=self._level_boss,
            boss_killed=self._level_boss_killed,
            dm_events=self._level_dm_events,
            power_snapshot=self._level_power_snapshot,
            key_items=self._level_key_items,
            puzzle_items=self._level_puzzle_items
        )
        
        self.level_snapshots.append(snapshot)
        
        # Update power progression
        if self._level_power_snapshot:
            prev_power = 0.0
            if self.power_progression:
                prev_power = self.power_progression[-1].offensive_total + self.power_progression[-1].defensive_total
            
            total_power = self._level_power_snapshot.get('offensive', 0) + self._level_power_snapshot.get('defensive', 0)
            
            progression = PowerLevelProgression(
                level=level,
                offensive_total=self._level_power_snapshot.get('offensive', 0),
                defensive_total=self._level_power_snapshot.get('defensive', 0),
                dominant_offense="melee" if self._level_power_snapshot.get('melee_power', 0) > self._level_power_snapshot.get('magic_power', 0) else "magic",
                dominant_defense="ac" if self._level_power_snapshot.get('defense', 0) > 0 else "hp",
                strongest_skill=max(['melee', 'magic'], key=lambda s: self._level_power_snapshot.get(f'{s}_power', 0)),
                weakest_skill=min(['melee', 'magic'], key=lambda s: self._level_power_snapshot.get(f'{s}_power', 0)),
                equipment_summary=self._level_items,
                power_delta_from_last=total_power - prev_power
            )
            self.power_progression.append(progression)

    def _generate_session_report(self, status: str, turns: int, start_time: float) -> PlaytestSession:
        """Generate the full session report."""
        return PlaytestSession(
            session_id=self.session_id,
            start_time=start_time,
            end_time=time.time(),
            difficulty=self.config.difficulty,
            total_levels=self.game_state_reader.current_level,
            levels_cleared=len(self.level_snapshots),
            total_ticks=turns,
            final_status=status,
            level_snapshots=self.level_snapshots,
            dm_influence_events=self.dm_events,
            power_progression=self.power_progression,
            performance_metrics={
                "avg_turns_per_level": turns / max(len(self.level_snapshots), 1),
                "exploration_rate": self._calculate_overall_exploration(),
            },
            errors=self.errors
        )

    def _calculate_overall_exploration(self) -> float:
        """Calculate overall exploration rate."""
        if not self.level_snapshots:
            return 0.0
        return sum(s.exploration_pct for s in self.level_snapshots) / len(self.level_snapshots)

    def _read_available(self, stream) -> str:
        """Read available data from stream."""
        if stream is None or stream.closed:
            return ""
        try:
            import select
            ready, _, _ = select.select([stream], [], [], 0)
            if not ready:
                return ""
            return stream.read() or ""
        except Exception:
            return ""

    def _parse_frames(self, buffer: str) -> Tuple[List[str], str]:
        """Parse console frames from buffer."""
        FRAME_CLEAR = "\033[H\033[2J"
        FRAME_END = "\033[0m"
        ANSI_RE = __import__("re").compile(r"\033\[[0-?]*[ -/]*[@-~]")
        
        if FRAME_CLEAR not in buffer:
            return [], buffer
        
        parts = buffer.split(FRAME_CLEAR)
        frames: List[str] = []
        remaining = parts[0]
        
        for part in parts[1:]:
            if FRAME_END not in part:
                remaining = FRAME_CLEAR + part
                break
            frame_text, after = part.split(FRAME_END, 1)
            frame_text = ANSI_RE.sub("", frame_text).rstrip("\n")
            frames.append(frame_text)
            remaining = after.lstrip("\n")
        
        return frames, remaining

    def save_telemetry(self, output_dir: str = "playtest/telemetry") -> None:
        """Save all telemetry to files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save session data
        session_file = output_path / f"session_{self.session_id}.json"
        with open(session_file, 'w') as f:
            json.dump({
                "level_snapshots": [s.to_dict() for s in self.level_snapshots],
                "dm_events": [e.to_dict() for e in self.dm_events],
                "power_progression": [p.to_dict() for p in self.power_progression],
            }, f, indent=2)


def load_config(path: str = "playtest/playtest_config_enhanced.yaml") -> MultiLevelPlaytestConfig:
    """Load configuration from YAML file."""
    config_path = Path(path)
    if not config_path.exists():
        return MultiLevelPlaytestConfig()
    
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f) or {}
    
    return MultiLevelPlaytestConfig(
        game_command=data.get('game_command', []),
        max_levels=data.get('max_levels', 5),
        max_turns=data.get('max_turns', 500),
        max_duration_seconds=data.get('max_duration_seconds', 600),
        telemetry_path=data.get('telemetry_path', 'playtest/telemetry/session.json'),
        difficulty=data.get('difficulty', 'normal'),
    )