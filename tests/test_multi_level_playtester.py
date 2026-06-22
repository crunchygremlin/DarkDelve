"""Tests for multi_level_playtester module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import os

from playtest.multi_level_playtester import (
    MultiLevelPlaytestConfig,
    MultiLevelPlaytester,
    load_config,
)
from playtest.telemetry_enhancements import (
    LevelSnapshot,
    DMInfluenceEvent,
    PowerLevelProgression,
    PlaytestSession,
)


class TestMultiLevelPlaytestConfig:
    """Tests for MultiLevelPlaytestConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = MultiLevelPlaytestConfig()
        assert config.max_levels == 5
        assert config.max_turns == 500
        assert config.difficulty == "normal"

    def test_custom_config(self):
        """Test custom configuration values."""
        config = MultiLevelPlaytestConfig(
            max_levels=10,
            max_turns=1000,
            difficulty="hard"
        )
        assert config.max_levels == 10
        assert config.max_turns == 1000
        assert config.difficulty == "hard"


class TestMultiLevelPlaytester:
    """Tests for MultiLevelPlaytester class."""

    def test_init(self):
        """Test MultiLevelPlaytester initialization."""
        playtester = MultiLevelPlaytester()
        assert playtester.session_id is not None
        assert playtester.game_state_reader is not None
        assert playtester.level_snapshots == []
        assert playtester.dm_events == []
        assert playtester.power_progression == []

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = MultiLevelPlaytestConfig(max_levels=3, difficulty="easy")
        playtester = MultiLevelPlaytester(config=config)
        assert playtester.config.max_levels == 3
        assert playtester.config.difficulty == "easy"

    def test_reset_level_state(self):
        """Test resetting level state."""
        playtester = MultiLevelPlaytester()
        playtester._reset_level_state(level=2, tick=100)
        
        assert playtester.game_state_reader.current_level == 2
        assert playtester._level_start_tick == 100

    def test_detect_dm_influence(self):
        """Test DM influence detection."""
        playtester = MultiLevelPlaytester()
        playtester._detect_dm_influence("You found a hint about the secret door", 50)
        
        assert len(playtester.dm_events) == 1
        assert playtester.dm_events[0].event_type == "hint_dropped"

    def test_detect_dm_influence_item(self):
        """Test DM item seeding detection."""
        playtester = MultiLevelPlaytester()
        playtester._detect_dm_influence("DM seeded a treasure item for you", 75)
        
        assert len(playtester.dm_events) == 1
        assert playtester.dm_events[0].event_type == "item_seeded"

    def test_capture_power_snapshot(self):
        """Test capturing power snapshot."""
        playtester = MultiLevelPlaytester()
        state = {
            'melee_power': 10.0,
            'magic_power': 15.0,
            'defense': 8.0
        }
        playtester._capture_power_snapshot(state)
        
        assert 'offensive' in playtester._level_power_snapshot
        assert playtester._level_power_snapshot['offensive'] == 25.0

    def test_finalize_level(self):
        """Test level finalization."""
        playtester = MultiLevelPlaytester()
        playtester._level_start_tick = 0
        playtester._level_power_snapshot = {'offensive': 10.0, 'defensive': 5.0}
        playtester._level_items = ['potion']
        playtester._level_mobs_killed = 3
        playtester._level_traps = 1
        playtester._rooms_explored = 5
        playtester._total_rooms = 10
        playtester._level_boss = None
        playtester._level_boss_killed = False
        playtester._level_dm_events = []
        playtester._level_key_items = []
        playtester._level_puzzle_items = []
        
        playtester._finalize_level(1)
        
        assert len(playtester.level_snapshots) == 1
        assert playtester.level_snapshots[0].level_number == 1
        assert playtester.level_snapshots[0].mobs_killed == 3

    def test_generate_session_report(self):
        """Test session report generation."""
        playtester = MultiLevelPlaytester()
        playtester.game_state_reader.current_level = 2
        playtester.level_snapshots = [LevelSnapshot(
            level_number=1,
            entry_tick=0,
            exit_tick=50,
            duration_ticks=50,
            player_hp_start=10,
            player_hp_end=10,
            player_max_hp=10,
            player_ac=12,
            player_gold_start=0,
            player_gold_end=50,
            items_collected=[],
            mobs_killed=0,
            traps_triggered=0,
            rooms_explored=0,
            total_rooms=0,
            exploration_pct=0.0,
            boss_encountered=None,
            boss_killed=False,
            dm_influence_events=[],
            power_level_snapshot={},
            key_items_found=[],
            puzzle_items_collected=[],
        )]
        
        session = playtester._generate_session_report("won", 100, 0.0)
        
        assert isinstance(session, PlaytestSession)
        assert session.final_status == "won"
        assert session.levels_cleared == 1

    def test_save_telemetry(self):
        """Test saving telemetry to file."""
        playtester = MultiLevelPlaytester()
        playtester.level_snapshots = [LevelSnapshot(
            level_number=1,
            entry_tick=0,
            exit_tick=50,
            duration_ticks=50,
            player_hp_start=10,
            player_hp_end=10,
            player_max_hp=10,
            player_ac=12,
            player_gold_start=0,
            player_gold_end=50,
            items_collected=[],
            mobs_killed=0,
            traps_triggered=0,
            rooms_explored=0,
            total_rooms=0,
            exploration_pct=0.0,
            boss_encountered=None,
            boss_killed=False,
            dm_influence_events=[],
            power_level_snapshot={},
            key_items_found=[],
            puzzle_items_collected=[],
        )]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "telemetry")
            playtester.save_telemetry(output_path)
            
            # Check file was created
            files = os.listdir(output_path)
            assert len(files) > 0

    def test_parse_frames(self):
        """Test parsing console frames."""
        playtester = MultiLevelPlaytester()
        buffer = "\033[H\033[2JTest frame\033[0m"
        frames, remaining = playtester._parse_frames(buffer)
        
        assert len(frames) == 1
        assert "Test frame" in frames[0]

    def test_parse_frames_multiple(self):
        """Test parsing multiple frames."""
        playtester = MultiLevelPlaytester()
        buffer = "\033[H\033[2JFrame1\033[0m\n\033[H\033[2JFrame2\033[0m"
        frames, remaining = playtester._parse_frames(buffer)
        
        assert len(frames) == 2
        assert "Frame1" in frames[0]
        assert "Frame2" in frames[1]


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_missing_file(self):
        """Test loading config when file doesn't exist."""
        config = load_config("nonexistent_config.yaml")
        assert isinstance(config, MultiLevelPlaytestConfig)
        assert config.max_levels == 5  # Default value

    def test_load_config_existing_file(self):
        """Test loading config from existing file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("max_levels: 8\nmax_turns: 200\ndifficulty: easy\n")
            f.flush()
            
            config = load_config(f.name)
            assert config.max_levels == 8
            assert config.max_turns == 200
            assert config.difficulty == "easy"
            
            os.unlink(f.name)