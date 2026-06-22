"""Tests for telemetry_enhancements module."""

import pytest
from playtest.telemetry_enhancements import (
    LevelSnapshot,
    DMInfluenceEvent,
    PowerLevelProgression,
    PlaytestSession,
    create_level_snapshot,
)


class TestLevelSnapshot:
    """Tests for LevelSnapshot dataclass."""

    def test_level_snapshot_creation(self):
        """Test creating a LevelSnapshot."""
        snap = LevelSnapshot(
            level_number=1,
            entry_tick=0,
            exit_tick=100,
            duration_ticks=100,
            player_hp_start=10,
            player_hp_end=8,
            player_max_hp=10,
            player_ac=12,
            player_gold_start=0,
            player_gold_end=50,
            items_collected=["potion", "scroll"],
            mobs_killed=3,
            traps_triggered=1,
            rooms_explored=5,
            total_rooms=10,
            exploration_pct=0.5,
            boss_encountered="Goblin King",
            boss_killed=True,
            dm_influence_events=["hint_dropped: found key"],
            power_level_snapshot={"offensive": 15.0, "defensive": 10.0},
            key_items_found=["key"],
            puzzle_items_collected=["rune"],
        )
        assert snap.level_number == 1
        assert snap.duration_ticks == 100
        assert snap.exploration_pct == 0.5

    def test_level_snapshot_to_dict(self):
        """Test serializing LevelSnapshot to dict."""
        snap = LevelSnapshot(
            level_number=2,
            entry_tick=100,
            exit_tick=200,
            duration_ticks=100,
            player_hp_start=8,
            player_hp_end=6,
            player_max_hp=10,
            player_ac=12,
            player_gold_start=50,
            player_gold_end=75,
            items_collected=[],
            mobs_killed=2,
            traps_triggered=0,
            rooms_explored=8,
            total_rooms=10,
            exploration_pct=0.8,
            boss_encountered=None,
            boss_killed=False,
            dm_influence_events=[],
            power_level_snapshot={},
            key_items_found=[],
            puzzle_items_collected=[],
        )
        d = snap.to_dict()
        assert d["level_number"] == 2
        assert d["exploration_pct"] == 0.8
        assert isinstance(d, dict)


class TestDMInfluenceEvent:
    """Tests for DMInfluenceEvent dataclass."""

    def test_dm_event_creation(self):
        """Test creating a DMInfluenceEvent."""
        event = DMInfluenceEvent(
            tick=50,
            level=1,
            event_type="hint_dropped",
            description="Found a secret passage",
            impact="positive",
            details={"location": "north corridor"}
        )
        assert event.tick == 50
        assert event.event_type == "hint_dropped"
        assert event.impact == "positive"

    def test_dm_event_to_dict(self):
        """Test serializing DMInfluenceEvent to dict."""
        event = DMInfluenceEvent(
            tick=100,
            level=2,
            event_type="item_seeded",
            description="DM placed a magic sword",
            impact="neutral",
            details={}
        )
        d = event.to_dict()
        assert d["tick"] == 100
        assert d["event_type"] == "item_seeded"


class TestPowerLevelProgression:
    """Tests for PowerLevelProgression dataclass."""

    def test_power_progression_creation(self):
        """Test creating a PowerLevelProgression."""
        prog = PowerLevelProgression(
            level=1,
            offensive_total=10.0,
            defensive_total=5.0,
            dominant_offense="melee",
            dominant_defense="ac",
            strongest_skill="melee",
            weakest_skill="magic",
            equipment_summary=["dagger", "leather armor"],
            power_delta_from_last=5.0
        )
        assert prog.level == 1
        assert prog.offensive_total == 10.0
        assert prog.power_delta_from_last == 5.0

    def test_power_progression_to_dict(self):
        """Test serializing PowerLevelProgression to dict."""
        prog = PowerLevelProgression(
            level=3,
            offensive_total=25.0,
            defensive_total=15.0,
            dominant_offense="magic",
            dominant_defense="hp",
            strongest_skill="magic",
            weakest_skill="melee",
            equipment_summary=["staff", "robe"],
            power_delta_from_last=10.0
        )
        d = prog.to_dict()
        assert d["level"] == 3
        assert d["offensive_total"] == 25.0


class TestPlaytestSession:
    """Tests for PlaytestSession dataclass."""

    def test_session_creation(self):
        """Test creating a PlaytestSession."""
        session = PlaytestSession(
            session_id="test_001",
            start_time=0.0,
            end_time=100.0,
            difficulty="normal",
            total_levels=5,
            levels_cleared=3,
            total_ticks=200,
            final_status="died",
        )
        assert session.session_id == "test_001"
        assert session.final_status == "died"
        assert len(session.level_snapshots) == 0

    def test_session_summary(self):
        """Test generating session summary."""
        session = PlaytestSession(
            session_id="test_002",
            start_time=0.0,
            end_time=50.0,
            difficulty="hard",
            total_levels=5,
            levels_cleared=2,
            total_ticks=100,
            final_status="won",
            level_snapshots=[
                LevelSnapshot(
                    level_number=1,
                    entry_tick=0,
                    exit_tick=50,
                    duration_ticks=50,
                    player_hp_start=10,
                    player_hp_end=10,
                    player_max_hp=10,
                    player_ac=12,
                    player_gold_start=0,
                    player_gold_end=100,
                    items_collected=["potion"],
                    mobs_killed=2,
                    traps_triggered=0,
                    rooms_explored=5,
                    total_rooms=10,
                    exploration_pct=0.5,
                    boss_encountered=None,
                    boss_killed=False,
                    dm_influence_events=[],
                    power_level_snapshot={},
                    key_items_found=[],
                    puzzle_items_collected=[],
                )
            ],
            dm_influence_events=[],
            power_progression=[],
        )
        summary = session.summary()
        assert "test_002" in summary
        assert "won" in summary
        assert "Level 1" in summary

    def test_session_to_dict(self):
        """Test serializing PlaytestSession to dict."""
        session = PlaytestSession(
            session_id="test_003",
            start_time=0.0,
            end_time=30.0,
            difficulty="normal",
            total_levels=3,
            levels_cleared=1,
            total_ticks=50,
            final_status="quit",
        )
        d = session.to_dict()
        assert d["session_id"] == "test_003"
        assert d["final_status"] == "quit"
        assert "level_snapshots" in d


class TestCreateLevelSnapshot:
    """Tests for create_level_snapshot factory function."""

    def test_create_level_snapshot(self):
        """Test creating a LevelSnapshot using factory function."""
        snap = create_level_snapshot(
            level_number=1,
            entry_tick=0,
            exit_tick=100,
            player_state={
                "hp_start": 10,
                "hp": 8,
                "max_hp": 10,
                "ac": 12,
                "gold_start": 0,
                "gold": 50,
            },
            items_collected=["potion"],
            mobs_killed=3,
            traps_triggered=1,
            rooms_explored=5,
            total_rooms=10,
            boss_encountered="Dragon",
            boss_killed=True,
            dm_events=["hint_dropped"],
            power_snapshot={"offensive": 15.0, "defensive": 10.0},
            key_items=["key"],
            puzzle_items=["puzzle_piece"],
        )
        assert snap.level_number == 1
        assert snap.duration_ticks == 100
        assert snap.exploration_pct == 0.5
        assert snap.boss_encountered == "Dragon"
        assert snap.boss_killed is True

    def test_create_level_snapshot_zero_rooms(self):
        """Test creating snapshot with zero rooms (avoid division by zero)."""
        snap = create_level_snapshot(
            level_number=1,
            entry_tick=0,
            exit_tick=0,
            player_state={},
            items_collected=[],
            mobs_killed=0,
            traps_triggered=0,
            rooms_explored=0,
            total_rooms=0,
            boss_encountered=None,
            boss_killed=False,
            dm_events=[],
            power_snapshot={},
            key_items=[],
            puzzle_items=[],
        )
        assert snap.exploration_pct == 0.0