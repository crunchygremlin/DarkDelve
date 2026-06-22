"""Tests for PerceptionComponent."""

import pytest
from dataclasses import dataclass
from src.domain.components.perception_component import PerceptionComponent
from src.domain.value_objects.perception import PerceptionStatus, PerceptionModifiers


@dataclass
class MockPosition:
    """Mock position for testing."""
    x: int
    y: int


class TestPerceptionComponent:
    """Tests for PerceptionComponent."""

    def test_component_type(self):
        """Test component type is correct."""
        comp = PerceptionComponent(entity_id="test_entity")
        assert comp.component_type == "perception"

    def test_default_values(self):
        """Test default values are set correctly."""
        comp = PerceptionComponent(entity_id="test_entity")
        assert comp.entity_id == "test_entity"
        assert comp.current_status is None
        assert comp.last_updated_tick == 0
        assert comp.memory == {}

    def test_update_status_with_player_seen(self):
        """Test updating status when player is seen."""
        comp = PerceptionComponent(entity_id="test_entity")
        status = PerceptionStatus(
            entity_id="test_entity",
            can_see_player=True,
            player_last_known_position=MockPosition(x=10, y=15),
            can_hear_player=False
        )
        comp.update_status(status, tick=5)

        assert comp.current_status == status
        assert comp.last_updated_tick == 5
        assert comp.memory["last_known_player_pos"] == MockPosition(x=10, y=15)
        assert comp.memory["last_seen_tick"] == 5

    def test_update_status_with_player_heard(self):
        """Test updating status when player is heard."""
        comp = PerceptionComponent(entity_id="test_entity")
        status = PerceptionStatus(
            entity_id="test_entity",
            can_see_player=False,
            can_hear_player=True
        )
        comp.update_status(status, tick=10)

        assert comp.memory["last_heard_tick"] == 10

    def test_get_last_known_player_pos(self):
        """Test getting last known player position."""
        comp = PerceptionComponent(entity_id="test_entity")
        pos = MockPosition(x=5, y=7)
        comp.memory["last_known_player_pos"] = pos

        assert comp.get_last_known_player_pos() == pos

    def test_get_last_known_player_pos_empty(self):
        """Test getting last known player position when not set."""
        comp = PerceptionComponent(entity_id="test_entity")
        assert comp.get_last_known_player_pos() is None

    def test_ticks_since_player_seen(self):
        """Test calculating ticks since player was seen."""
        comp = PerceptionComponent(entity_id="test_entity")
        comp.memory["last_seen_tick"] = 20

        assert comp.ticks_since_player_seen(25) == 5
        assert comp.ticks_since_player_seen(30) == 10

    def test_ticks_since_player_seen_no_data(self):
        """Test ticks since player seen when never seen."""
        comp = PerceptionComponent(entity_id="test_entity")
        assert comp.ticks_since_player_seen(10) == -1

    def test_with_modifiers(self):
        """Test component with custom modifiers."""
        modifiers = PerceptionModifiers(
            entity_type="goblin",
            sight_range=10.0,
            hearing_range=15.0
        )
        comp = PerceptionComponent(
            entity_id="goblin_1",
            modifiers=modifiers
        )
        assert comp.modifiers.entity_type == "goblin"
        assert comp.modifiers.sight_range == 10.0