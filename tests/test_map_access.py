"""Tests for map access value objects."""

import pytest
from src.domain.value_objects.map_access import MapAccessRequest


class TestMapAccessRequest:
    """Tests for MapAccessRequest dataclass."""

    def test_default_values(self):
        request = MapAccessRequest(requester_id="entity_001", reason="level_creation", access_type="full")
        assert request.requester_id == "entity_001"
        assert request.reason == "level_creation"
        assert request.access_type == "full"
        assert request.area is None
        assert request.duration_ticks == 1
        assert request.granted is False

    def test_with_access_type(self):
        request = MapAccessRequest(
            requester_id="entity_002",
            reason="spell_clairvoyance",
            access_type="fog_of_war"
        )
        assert request.access_type == "fog_of_war"

    def test_with_area(self):
        request = MapAccessRequest(
            requester_id="entity_003",
            reason="commander_coordination",
            access_type="specific_area",
            area=(10, 20, 30, 40)
        )
        assert request.area == (10, 20, 30, 40)

    def test_with_duration(self):
        request = MapAccessRequest(
            requester_id="entity_004",
            reason="debug",
            access_type="full",
            duration_ticks=10
        )
        assert request.duration_ticks == 10

    def test_granted_flag(self):
        request = MapAccessRequest(
            requester_id="entity_005",
            reason="level_creation",
            access_type="full",
            granted=True
        )
        assert request.granted is True

    def test_reason_types(self):
        reasons = ["level_creation", "spell_clairvoyance", "commander_coordination", "debug"]
        for reason in reasons:
            request = MapAccessRequest(requester_id="test", reason=reason, access_type="full")
            assert request.reason == reason

    def test_access_type_values(self):
        access_types = ["full", "fog_of_war", "specific_area"]
        for access_type in access_types:
            request = MapAccessRequest(
                requester_id="test",
                reason="debug",
                access_type=access_type
            )
            assert request.access_type == access_type