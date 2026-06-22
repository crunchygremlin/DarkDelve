"""Tests for SocialComponent."""

import pytest
from src.domain.components.social_component import SocialComponent
from src.domain.value_objects.social import LoyaltyState


class TestSocialComponent:
    """Tests for SocialComponent."""

    def test_component_type(self):
        """Test component type is correct."""
        comp = SocialComponent(entity_id="test_entity")
        assert comp.component_type == "social"

    def test_default_values(self):
        """Test default values are set correctly."""
        comp = SocialComponent(entity_id="test_entity")
        assert comp.entity_id == "test_entity"
        assert comp.structure_id is None
        assert comp.rank == 99
        assert comp.role == "minion"
        assert comp.loyalty is None
        assert comp.is_leader is False
        assert comp.personal_wealth == 0.0
        assert comp.desired_items == []

    def test_can_give_orders_leader(self):
        """Test leader can give orders."""
        comp = SocialComponent(entity_id="leader", is_leader=True)
        assert comp.can_give_orders() is True

    def test_can_give_orders_guard(self):
        """Test guard can give orders."""
        comp = SocialComponent(entity_id="guard", role="guard")
        assert comp.can_give_orders() is True

    def test_can_give_orders_minion(self):
        """Test minion cannot give orders."""
        comp = SocialComponent(entity_id="minion", role="minion")
        assert comp.can_give_orders() is False

    def test_will_follow_orders_leader(self):
        """Test leader always follows orders."""
        comp = SocialComponent(entity_id="leader", is_leader=True)
        assert comp.will_follow_orders() is True

    def test_will_follow_orders_no_loyalty(self):
        """Test follows orders when no loyalty system."""
        comp = SocialComponent(entity_id="entity", loyalty=None)
        assert comp.will_follow_orders() is True

    def test_will_follow_orders_high_loyalty(self):
        """Test follows orders with high loyalty."""
        loyalty = LoyaltyState(
            minion_id="entity",
            leader_id="leader",
            loyalty_score=0.8
        )
        comp = SocialComponent(entity_id="entity", loyalty=loyalty)
        assert comp.will_follow_orders() is True

    def test_will_follow_orders_low_loyalty(self):
        """Test may not follow orders with low loyalty."""
        loyalty = LoyaltyState(
            minion_id="entity",
            leader_id="leader",
            loyalty_score=0.05
        )
        comp = SocialComponent(entity_id="entity", loyalty=loyalty)
        # Loyalty 0.05 means will_follow_orders returns False (threshold is 0.2)
        assert comp.will_follow_orders() is False

    def test_with_loyalty(self):
        """Test component with loyalty state."""
        loyalty = LoyaltyState(
            minion_id="minion_1",
            leader_id="leader_1",
            loyalty_score=0.75
        )
        comp = SocialComponent(
            entity_id="minion_1",
            loyalty=loyalty,
            rank=2,
            role="guard"
        )
        assert comp.loyalty.loyalty_score == 0.75
        assert comp.rank == 2
        assert comp.role == "guard"

    def test_personal_wealth(self):
        """Test personal wealth tracking."""
        comp = SocialComponent(entity_id="entity", personal_wealth=50.0)
        assert comp.personal_wealth == 50.0

    def test_desired_items(self):
        """Test desired items list."""
        comp = SocialComponent(
            entity_id="entity",
            desired_items=["sword", "shield", "potion"]
        )
        assert len(comp.desired_items) == 3
        assert "sword" in comp.desired_items