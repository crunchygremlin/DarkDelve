"""Tests for perception value objects."""

import pytest
from src.domain.value_objects.perception import (
    PerceptionSense,
    PerceptionModifiers,
    PerceptionStatus,
)


class TestPerceptionSense:
    """Tests for PerceptionSense enum."""

    def test_sight_value(self):
        assert PerceptionSense.SIGHT.value == "sight"

    def test_hearing_value(self):
        assert PerceptionSense.HEARING.value == "hearing"

    def test_smell_value(self):
        assert PerceptionSense.SMELL.value == "smell"

    def test_vibration_value(self):
        assert PerceptionSense.VIBRATION.value == "vibration"

    def test_echolocation_value(self):
        assert PerceptionSense.ECHOLOCATION.value == "echolocation"

    def test_magic_sense_value(self):
        assert PerceptionSense.MAGIC_SENSE.value == "magic_sense"


class TestPerceptionModifiers:
    """Tests for PerceptionModifiers dataclass."""

    def test_default_values(self):
        modifiers = PerceptionModifiers(entity_type="goblin")
        assert modifiers.entity_type == "goblin"
        assert modifiers.sight_range == 8.0
        assert modifiers.hearing_range == 12.0
        assert modifiers.smell_range == 4.0
        assert modifiers.darkvision is False
        assert modifiers.see_invisible is False

    def test_custom_values(self):
        modifiers = PerceptionModifiers(
            entity_type="bat",
            sight_range=15.0,
            echolocation_range=20.0,
            darkvision=True
        )
        assert modifiers.entity_type == "bat"
        assert modifiers.sight_range == 15.0
        assert modifiers.echolocation_range == 20.0
        assert modifiers.darkvision is True

    def test_noise_sensitivity(self):
        modifiers = PerceptionModifiers(entity_type="dog", noise_sensitivity=2.0)
        assert modifiers.noise_sensitivity == 2.0

    def test_wall_penetration_flags(self):
        modifiers = PerceptionModifiers(
            entity_type="giant",
            ignore_walls_hearing=True,
            ignore_walls_vibration=True
        )
        assert modifiers.ignore_walls_hearing is True
        assert modifiers.ignore_walls_vibration is True


class TestPerceptionStatus:
    """Tests for PerceptionStatus dataclass."""

    def test_default_values(self):
        status = PerceptionStatus(entity_id="entity_001")
        assert status.entity_id == "entity_001"
        assert status.can_see_player is False
        assert status.can_hear_player is False
        assert status.player_noise_level == 0.0
        assert status.player_distance_estimate == -1.0
        assert status.visible_threats == []
        assert status.visible_items == []
        assert status.environment_danger == 0.0
        assert status.light_level == 1.0
        assert status.nearby_traps == 0
        assert status.nearby_exits == 0

    def test_player_detection_flags(self):
        status = PerceptionStatus(
            entity_id="entity_002",
            can_see_player=True,
            can_hear_player=True,
            can_smell_player=True
        )
        assert status.can_see_player is True
        assert status.can_hear_player is True
        assert status.can_smell_player is True

    def test_player_position_tracking(self):
        from dataclasses import dataclass

        @dataclass
        class Position:
            x: int
            y: int

        pos = Position(x=5, y=10)
        status = PerceptionStatus(
            entity_id="entity_003",
            player_last_known_position=pos,
            player_distance_estimate=7.5
        )
        assert status.player_last_known_position == pos
        assert status.player_distance_estimate == 7.5

    def test_custom_flags(self):
        status = PerceptionStatus(
            entity_id="entity_004",
            custom_flags={"is_stealthy": True, "has_magic": False}
        )
        assert status.custom_flags["is_stealthy"] is True
        assert status.custom_flags["has_magic"] is False

    def test_ally_health_status(self):
        status = PerceptionStatus(
            entity_id="entity_005",
            ally_health_status="wounded"
        )
        assert status.ally_health_status == "wounded"

    def test_time_since_player_seen(self):
        status = PerceptionStatus(
            entity_id="entity_006",
            time_since_player_seen=15.5
        )
        assert status.time_since_player_seen == 15.5

    def test_from_dict_basic(self):
        """Test creating PerceptionStatus from a basic dictionary."""
        data = {
            "entity_id": "entity_007",
            "can_see_player": True,
            "can_hear_player": False,
            "can_smell_player": True,
            "player_noise_level": 0.5,
            "player_distance_estimate": 10.0,
            "visible_threats": ["threat1", "threat2"],
            "visible_items": ["item1"],
            "visible_allies": ["ally1"],
            "visible_enemies": ["enemy1"],
            "environment_danger": 0.7,
            "light_level": 0.3,
            "nearby_traps": 2,
            "nearby_exits": 1,
            "combat_occurring_nearby": True,
            "ally_health_status": "wounded",
            "time_since_player_seen": 5.0,
            "custom_flags": {"flag1": True},
        }
        status = PerceptionStatus.from_dict(data)
        assert status.entity_id == "entity_007"
        assert status.can_see_player is True
        assert status.can_hear_player is False
        assert status.can_smell_player is True
        assert status.player_noise_level == 0.5
        assert status.player_distance_estimate == 10.0
        assert status.visible_threats == ["threat1", "threat2"]
        assert status.visible_items == ["item1"]
        assert status.visible_allies == ["ally1"]
        assert status.visible_enemies == ["enemy1"]
        assert status.environment_danger == 0.7
        assert status.light_level == 0.3
        assert status.nearby_traps == 2
        assert status.nearby_exits == 1
        assert status.combat_occurring_nearby is True
        assert status.ally_health_status == "wounded"
        assert status.time_since_player_seen == 5.0
        assert status.custom_flags == {"flag1": True}

    def test_from_dict_with_position(self):
        """Test creating PerceptionStatus from a dictionary with position."""
        from src.domain.value_objects.position import Position
        
        data = {
            "entity_id": "entity_008",
            "player_last_known_position": {"x": 15, "y": 20},
        }
        status = PerceptionStatus.from_dict(data)
        assert status.entity_id == "entity_008"
        assert isinstance(status.player_last_known_position, Position)
        assert status.player_last_known_position.x == 15
        assert status.player_last_known_position.y == 20

    def test_from_dict_empty(self):
        """Test creating PerceptionStatus from an empty dictionary uses defaults."""
        status = PerceptionStatus.from_dict({})
        assert status.entity_id == ""
        assert status.can_see_player is False
        assert status.can_hear_player is False
        assert status.player_noise_level == 0.0
        assert status.player_distance_estimate == -1.0
        assert status.visible_threats == []
        assert status.visible_items == []
        assert status.visible_allies == []
        assert status.visible_enemies == []
        assert status.environment_danger == 0.0
        assert status.light_level == 1.0
        assert status.nearby_traps == 0
        assert status.nearby_exits == 0
        assert status.combat_occurring_nearby is False
        assert status.ally_health_status == "unknown"
        assert status.time_since_player_seen == -1.0
        assert status.custom_flags == {}

    def test_from_dict_roundtrip(self):
        """Test that as_dict and from_dict are inverse operations."""
        original = PerceptionStatus(
            entity_id="entity_009",
            can_see_player=True,
            can_hear_player=True,
            player_noise_level=0.8,
            player_distance_estimate=12.5,
            visible_threats=["t1", "t2"],
            visible_items=["i1"],
            environment_danger=0.5,
            custom_flags={"key": "value"},
        )
        data = original.as_dict()
        restored = PerceptionStatus.from_dict(data)
        assert restored.entity_id == original.entity_id
        assert restored.can_see_player == original.can_see_player
        assert restored.can_hear_player == original.can_hear_player
        assert restored.player_noise_level == original.player_noise_level
        assert restored.player_distance_estimate == original.player_distance_estimate
        assert restored.visible_threats == original.visible_threats
        assert restored.visible_items == original.visible_items
        assert restored.environment_danger == original.environment_danger
        assert restored.custom_flags == original.custom_flags