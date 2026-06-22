"""Tests for playtest_analyzer module."""

import pytest
from playtest.playtest_analyzer import PlaytestAnalyzer, analyze_session
from playtest.telemetry_enhancements import (
    PlaytestSession,
    LevelSnapshot,
    DMInfluenceEvent,
    PowerLevelProgression,
)


def create_test_session() -> PlaytestSession:
    """Create a test session with sample data."""
    return PlaytestSession(
        session_id="test_session_001",
        start_time=0.0,
        end_time=100.0,
        difficulty="normal",
        total_levels=3,
        levels_cleared=2,
        total_ticks=200,
        final_status="died",
        level_snapshots=[
            LevelSnapshot(
                level_number=1,
                entry_tick=0,
                exit_tick=80,
                duration_ticks=80,
                player_hp_start=10,
                player_hp_end=6,
                player_max_hp=10,
                player_ac=12,
                player_gold_start=0,
                player_gold_end=100,
                items_collected=["potion", "scroll"],
                mobs_killed=5,
                traps_triggered=2,
                rooms_explored=7,
                total_rooms=10,
                exploration_pct=0.7,
                boss_encountered="Goblin King",
                boss_killed=True,
                dm_influence_events=["hint_dropped"],
                power_level_snapshot={"offensive": 15.0, "defensive": 10.0},
                key_items_found=["key"],
                puzzle_items_collected=[],
            ),
            LevelSnapshot(
                level_number=2,
                entry_tick=80,
                exit_tick=180,
                duration_ticks=100,
                player_hp_start=6,
                player_hp_end=4,
                player_max_hp=10,
                player_ac=14,
                player_gold_start=100,
                player_gold_end=200,
                items_collected=["sword"],
                mobs_killed=8,
                traps_triggered=1,
                rooms_explored=9,
                total_rooms=10,
                exploration_pct=0.9,
                boss_encountered="Dragon",
                boss_killed=False,
                dm_influence_events=["item_seeded"],
                power_level_snapshot={"offensive": 25.0, "defensive": 15.0},
                key_items_found=["artifact"],
                puzzle_items_collected=[],
            ),
        ],
        dm_influence_events=[
            DMInfluenceEvent(
                tick=10,
                level=1,
                event_type="hint_dropped",
                description="Find the key",
                impact="positive",
                details={}
            ),
            DMInfluenceEvent(
                tick=50,
                level=1,
                event_type="item_seeded",
                description="Placed a potion",
                impact="neutral",
                details={}
            ),
        ],
        power_progression=[
            PowerLevelProgression(
                level=1,
                offensive_total=15.0,
                defensive_total=10.0,
                dominant_offense="melee",
                dominant_defense="ac",
                strongest_skill="melee",
                weakest_skill="magic",
                equipment_summary=["potion", "scroll"],
                power_delta_from_last=25.0
            ),
            PowerLevelProgression(
                level=2,
                offensive_total=25.0,
                defensive_total=15.0,
                dominant_offense="melee",
                dominant_defense="ac",
                strongest_skill="melee",
                weakest_skill="magic",
                equipment_summary=["sword"],
                power_delta_from_last=10.0
            ),
        ],
        performance_metrics={
            "avg_turns_per_level": 100.0,
        },
        errors=[]
    )


class TestPlaytestAnalyzer:
    """Tests for PlaytestAnalyzer class."""

    def test_init(self):
        """Test analyzer initialization."""
        session = create_test_session()
        analyzer = PlaytestAnalyzer(session)
        assert analyzer.session == session

    def test_analyze_level_progression(self):
        """Test level progression analysis."""
        session = create_test_session()
        analyzer = PlaytestAnalyzer(session)
        result = analyzer.analyze_level_progression()
        
        assert result['total_levels'] == 2
        assert result['avg_duration_per_level'] == 90.0
        assert 0.5 <= result['avg_exploration'] <= 0.9

    def test_analyze_level_progression_empty(self):
        """Test level progression with no snapshots."""
        session = PlaytestSession(
            session_id="empty",
            start_time=0.0,
            end_time=0.0,
            difficulty="normal",
            total_levels=0,
            levels_cleared=0,
            total_ticks=0,
            final_status="quit",
        )
        analyzer = PlaytestAnalyzer(session)
        result = analyzer.analyze_level_progression()
        
        assert 'error' in result

    def test_analyze_dm_influence(self):
        """Test DM influence analysis."""
        session = create_test_session()
        analyzer = PlaytestAnalyzer(session)
        result = analyzer.analyze_dm_influence()
        
        assert result['total_events'] == 2
        assert 'hint_dropped' in result['by_type']
        assert 'item_seeded' in result['by_type']

    def test_analyze_dm_influence_empty(self):
        """Test DM influence with no events."""
        session = PlaytestSession(
            session_id="no_dm",
            start_time=0.0,
            end_time=0.0,
            difficulty="normal",
            total_levels=1,
            levels_cleared=1,
            total_ticks=10,
            final_status="won",
            level_snapshots=[],
            dm_influence_events=[],
            power_progression=[],
        )
        analyzer = PlaytestAnalyzer(session)
        result = analyzer.analyze_dm_influence()
        
        assert result['total_events'] == 0

    def test_analyze_power_scaling(self):
        """Test power scaling analysis."""
        session = create_test_session()
        analyzer = PlaytestAnalyzer(session)
        result = analyzer.analyze_power_scaling()
        
        # Total power gain = (25+15) - (15+10) = 40 - 25 = 15
        assert result['total_power_gain'] == 15.0
        assert result['power_curve'] in ['increasing', 'decreasing', 'variable']

    def test_analyze_power_scaling_empty(self):
        """Test power scaling with no data."""
        session = PlaytestSession(
            session_id="no_power",
            start_time=0.0,
            end_time=0.0,
            difficulty="normal",
            total_levels=1,
            levels_cleared=1,
            total_ticks=10,
            final_status="won",
            level_snapshots=[],
            dm_influence_events=[],
            power_progression=[],
        )
        analyzer = PlaytestAnalyzer(session)
        result = analyzer.analyze_power_scaling()
        
        assert 'error' in result

    def test_analyze_exploration(self):
        """Test exploration analysis."""
        session = create_test_session()
        analyzer = PlaytestAnalyzer(session)
        result = analyzer.analyze_exploration()
        
        assert result['total_rooms'] == 20
        assert result['total_explored'] == 16
        assert 0.5 <= result['overall_exploration_pct'] <= 0.9

    def test_analyze_exploration_empty(self):
        """Test exploration with no data."""
        session = PlaytestSession(
            session_id="no_explore",
            start_time=0.0,
            end_time=0.0,
            difficulty="normal",
            total_levels=1,
            levels_cleared=1,
            total_ticks=10,
            final_status="won",
            level_snapshots=[],
            dm_influence_events=[],
            power_progression=[],
        )
        analyzer = PlaytestAnalyzer(session)
        result = analyzer.analyze_exploration()
        
        assert 'error' in result

    def test_analyze_difficulty_balance(self):
        """Test difficulty balance analysis."""
        session = create_test_session()
        analyzer = PlaytestAnalyzer(session)
        result = analyzer.analyze_difficulty_balance()
        
        assert 'survival_by_level' in result
        assert 'recommended_difficulty' in result

    def test_analyze_difficulty_balance_empty(self):
        """Test difficulty balance with no data."""
        session = PlaytestSession(
            session_id="no_balance",
            start_time=0.0,
            end_time=0.0,
            difficulty="normal",
            total_levels=1,
            levels_cleared=1,
            total_ticks=10,
            final_status="won",
            level_snapshots=[],
            dm_influence_events=[],
            power_progression=[],
        )
        analyzer = PlaytestAnalyzer(session)
        result = analyzer.analyze_difficulty_balance()
        
        assert 'error' in result

    def test_generate_full_report(self):
        """Test generating full report."""
        session = create_test_session()
        analyzer = PlaytestAnalyzer(session)
        report = analyzer.generate_full_report()
        
        assert "PLAYTEST ANALYSIS REPORT" in report
        assert "test_session_001" in report
        assert "LEVEL PROGRESSION" in report
        assert "POWER SCALING" in report
        assert "DM INFLUENCE" in report

    def test_save_report(self):
        """Test saving report to file."""
        import tempfile
        import os
        
        session = create_test_session()
        analyzer = PlaytestAnalyzer(session)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "report.txt")
            analyzer.save_report(path)
            
            assert os.path.exists(path)
            with open(path) as f:
                content = f.read()
            assert "PLAYTEST ANALYSIS REPORT" in content


class TestAnalyzeSession:
    """Tests for analyze_session convenience function."""

    def test_analyze_session(self):
        """Test analyze_session function."""
        session = create_test_session()
        result = analyze_session(session)
        
        assert 'level_progression' in result
        assert 'dm_influence' in result
        assert 'power_scaling' in result
        assert 'exploration' in result
        assert 'difficulty_balance' in result