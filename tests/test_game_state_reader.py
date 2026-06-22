"""Tests for game_state_reader module."""

import pytest
from playtest.game_state_reader import GameStateReader


class TestGameStateReader:
    """Tests for GameStateReader class."""

    def test_init(self):
        """Test GameStateReader initialization."""
        reader = GameStateReader()
        assert reader.current_level == 1
        assert reader.current_tick == 0
        assert reader.dm_events == []
        assert reader.power_levels == {}
        assert reader.explored_tiles == set()
        assert reader.visited_levels == set()

    def test_read_frame_basic_stats(self):
        """Test reading basic stats from a frame."""
        reader = GameStateReader()
        frame = "HP: 10/10 AC: 12 Gold: 50 Turn: 25 Depth: 3"
        state = reader.read_frame(frame)
        
        assert state['hp'] == 10
        assert state['max_hp'] == 10
        assert state['ac'] == 12
        assert state['gold'] == 50
        assert state['turn'] == 25
        assert state['depth'] == 3

    def test_read_frame_power_levels(self):
        """Test reading power level info from a frame."""
        reader = GameStateReader()
        frame = "Melee: 10.5 Magic: 15.3 Defense: 8.2"
        state = reader.read_frame(frame)
        
        assert state['melee_power'] == 10.5
        assert state['magic_power'] == 15.3
        assert state['defense'] == 8.2

    def test_read_frame_dm_narrative(self):
        """Test reading DM narrative from a frame."""
        reader = GameStateReader()
        frame = "[DM] The ancient sword gleams in the torchlight."
        state = reader.read_frame(frame)
        
        assert 'dm_narrative' in state
        assert "ancient sword" in state['dm_narrative']

    def test_read_frame_level_change(self):
        """Test detecting level changes."""
        reader = GameStateReader()
        frame = "Level 3"
        state = reader.read_frame(frame)
        
        assert state['level_changed'] is True
        assert state['new_level'] == 3
        assert reader.current_level == 3

    def test_read_frame_exploration(self):
        """Test reading exploration info."""
        reader = GameStateReader()
        frame = "Explored: 5/10"
        state = reader.read_frame(frame)
        
        assert state['rooms_explored'] == 5
        assert state['total_rooms'] == 10

    def test_read_frame_boss_info(self):
        """Test reading boss info."""
        reader = GameStateReader()
        frame = "Boss: Dragon"
        state = reader.read_frame(frame)
        
        assert state['boss'] == "Dragon"

    def test_extract_int(self):
        """Test _extract_int method."""
        reader = GameStateReader()
        assert reader._extract_int(r'HP:\s*(\d+)', "HP: 42") == 42
        assert reader._extract_int(r'HP:\s*(\d+)', "No HP here") is None
        assert reader._extract_int(r'Value:\s*(\d+)', "Value: ?") is None

    def test_extract_float(self):
        """Test _extract_float method."""
        reader = GameStateReader()
        assert reader._extract_float(r'Power:\s*([\d.]+)', "Power: 12.5") == 12.5
        assert reader._extract_float(r'Power:\s*([\d.]+)', "No power") is None

    def test_record_dm_event(self):
        """Test recording DM events."""
        reader = GameStateReader()
        event = reader.record_dm_event(
            tick=10,
            level=1,
            event_type="hint_dropped",
            description="Find the key",
            impact="positive",
            details={"location": "chest"}
        )
        
        assert len(reader.dm_events) == 1
        assert event['tick'] == 10
        assert event['event_type'] == "hint_dropped"

    def test_update_power_levels(self):
        """Test updating power levels."""
        reader = GameStateReader()
        result = reader.update_power_levels(
            offensive=20.0,
            defensive=15.0,
            skills={'melee': 10.0, 'magic': 10.0}
        )
        
        assert reader.power_levels['offensive'] == 20.0
        assert reader.power_levels['defensive'] == 15.0
        assert result['offensive'] == 20.0

    def test_mark_tile_explored(self):
        """Test marking tiles as explored."""
        reader = GameStateReader()
        reader.mark_tile_explored(5, 10)
        reader.mark_tile_explored(6, 10)
        
        assert (5, 10) in reader.explored_tiles
        assert (6, 10) in reader.explored_tiles
        assert len(reader.explored_tiles) == 2

    def test_mark_level_visited(self):
        """Test marking levels as visited."""
        reader = GameStateReader()
        reader.mark_level_visited(1)
        reader.mark_level_visited(2)
        
        assert 1 in reader.visited_levels
        assert 2 in reader.visited_levels

    def test_get_exploration_stats(self):
        """Test getting exploration statistics."""
        reader = GameStateReader()
        reader.mark_tile_explored(0, 0)
        reader.mark_tile_explored(1, 1)
        reader.mark_level_visited(1)
        reader.mark_level_visited(2)
        
        stats = reader.get_exploration_stats()
        assert stats['tiles_explored'] == 2
        assert stats['levels_visited'] == 2
        assert 1 in stats['visited_levels']

    def test_set_room_counts(self):
        """Test setting room counts."""
        reader = GameStateReader()
        reader.set_room_counts(7, 10)
        
        assert reader._rooms_explored == 7
        assert reader._total_rooms == 10

    def test_get_level_exploration_pct(self):
        """Test getting exploration percentage."""
        reader = GameStateReader()
        reader.set_room_counts(3, 5)
        
        assert reader.get_level_exploration_pct() == 0.6

    def test_get_level_exploration_pct_zero_rooms(self):
        """Test exploration percentage with zero rooms."""
        reader = GameStateReader()
        assert reader.get_level_exploration_pct() == 0.0

    def test_set_level_start(self):
        """Test setting level start."""
        reader = GameStateReader()
        reader.set_level_start(3, 100)
        
        assert reader.current_level == 3
        assert 3 in reader.visited_levels

    def test_get_level_duration(self):
        """Test getting level duration."""
        reader = GameStateReader()
        reader.set_level_start(1, 50)
        
        assert reader.get_level_duration(100) == 50
        assert reader.get_level_duration(50) == 0