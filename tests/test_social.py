"""Tests for social value objects."""

import pytest
from src.domain.value_objects.social import (
    RelationshipType,
    SocialStructureType,
    SocialRelationship,
    SocialStructure,
    LoyaltyState,
)


class TestRelationshipType:
    """Tests for RelationshipType enum."""

    def test_loyalty_value(self):
        assert RelationshipType.LOYALTY.value == "loyalty"

    def test_fear_value(self):
        assert RelationshipType.FEAR.value == "fear"

    def test_rivalry_value(self):
        assert RelationshipType.RIVALRY.value == "rivalry"

    def test_friendship_value(self):
        assert RelationshipType.FRIENDSHIP.value == "friendship"

    def test_servitude_value(self):
        assert RelationshipType.SERVITUDE.value == "servitude"

    def test_domination_value(self):
        assert RelationshipType.DOMINATION.value == "domination"

    def test_hive_mind_value(self):
        assert RelationshipType.HIVE_MIND.value == "hive_mind"

    def test_contract_value(self):
        assert RelationshipType.CONTRACT.value == "contract"


class TestSocialStructureType:
    """Tests for SocialStructureType enum."""

    def test_goblin_kingdom_value(self):
        assert SocialStructureType.GOBLIN_KINGDOM.value == "goblin_kingdom"

    def test_wolf_pack_value(self):
        assert SocialStructureType.WOLF_PACK.value == "wolf_pack"

    def test_spider_hive_value(self):
        assert SocialStructureType.SPIDER_HIVE.value == "spider_hive"

    def test_mercenary_band_value(self):
        assert SocialStructureType.MERCENARY_BAND.value == "mercenary_band"

    def test_undead_court_value(self):
        assert SocialStructureType.UNDEAD_COURT.value == "undead_court"

    def test_merchant_guild_value(self):
        assert SocialStructureType.MERCHANT_GUILD.value == "merchant_guild"


class TestSocialRelationship:
    """Tests for SocialRelationship dataclass."""

    def test_default_values(self):
        rel = SocialRelationship(
            entity_a_id="entity_001",
            entity_b_id="entity_002",
            relationship_type="loyalty"
        )
        assert rel.entity_a_id == "entity_001"
        assert rel.entity_b_id == "entity_002"
        assert rel.relationship_type == "loyalty"
        assert rel.strength == 0.0
        assert rel.history == []

    def test_custom_strength(self):
        rel = SocialRelationship(
            entity_a_id="entity_001",
            entity_b_id="entity_002",
            relationship_type="friendship",
            strength=0.8
        )
        assert rel.strength == 0.8

    def test_with_history(self):
        rel = SocialRelationship(
            entity_a_id="entity_001",
            entity_b_id="entity_002",
            relationship_type="rivalry",
            history=["met_in_tavern", "fought_over_loot"]
        )
        assert len(rel.history) == 2


class TestSocialStructure:
    """Tests for SocialStructure dataclass."""

    def test_basic_structure(self):
        structure = SocialStructure(
            structure_id="goblin_kingdom_001",
            structure_type="goblin_kingdom",
            leader_id="king_001"
        )
        assert structure.structure_id == "goblin_kingdom_001"
        assert structure.structure_type == "goblin_kingdom"
        assert structure.leader_id == "king_001"
        assert structure.member_ids == []
        assert structure.hierarchy == {}
        assert structure.shared_goals == []
        assert structure.wealth_pool == 0.0

    def test_with_members(self):
        structure = SocialStructure(
            structure_id="wolf_pack_001",
            structure_type="wolf_pack",
            leader_id="alpha_001",
            member_ids=["beta_001", "beta_002", "omega_001"],
            hierarchy={"alpha_001": 0, "beta_001": 1, "beta_002": 1, "omega_001": 2}
        )
        assert len(structure.member_ids) == 3
        assert structure.hierarchy["alpha_001"] == 0

    def test_with_wealth(self):
        structure = SocialStructure(
            structure_id="merchant_guild_001",
            structure_type="merchant_guild",
            leader_id="guildmaster_001",
            wealth_pool=1000.0
        )
        assert structure.wealth_pool == 1000.0


class TestLoyaltyState:
    """Tests for LoyaltyState dataclass."""

    def test_default_values(self):
        state = LoyaltyState(minion_id="minion_001", leader_id="leader_001")
        assert state.minion_id == "minion_001"
        assert state.leader_id == "leader_001"
        assert state.loyalty_score == 0.5
        assert state.base_loyalty == 0.5
        assert state.modifiers == []

    def test_apply_modifier(self):
        state = LoyaltyState(minion_id="minion_001", leader_id="leader_001")
        state.apply_modifier("gift", 0.1, "received_potion", 10)
        assert len(state.modifiers) == 1
        assert state.loyalty_score == 0.6
        assert state.modifiers[0]["source"] == "gift"

    def test_loyalty_clamped_at_zero(self):
        state = LoyaltyState(minion_id="minion_001", leader_id="leader_001", loyalty_score=0.1)
        state.apply_modifier("damage", -0.5, "took_damage", 20)
        assert state.loyalty_score == 0.0  # clamped at 0.0

    def test_loyalty_clamped_at_one(self):
        state = LoyaltyState(minion_id="minion_001", leader_id="leader_001", loyalty_score=0.9)
        state.apply_modifier("promotion", 0.5, "promoted", 30)
        assert state.loyalty_score == 1.0  # clamped at 1.0

    def test_will_follow_orders(self):
        state = LoyaltyState(minion_id="minion_001", leader_id="leader_001", loyalty_score=0.3)
        assert state.will_follow_orders() is True

        state.loyalty_score = 0.1
        assert state.will_follow_orders() is False

    def test_will_desert(self):
        state = LoyaltyState(minion_id="minion_001", leader_id="leader_001", loyalty_score=0.09)
        assert state.will_desert() is True

        state.loyalty_score = 0.15
        assert state.will_desert() is False

    def test_will_betray(self):
        state = LoyaltyState(minion_id="minion_001", leader_id="leader_001", loyalty_score=0.04)
        assert state.will_betray() is True

        state.loyalty_score = 0.1
        assert state.will_betray() is False

    def test_is_fanatic(self):
        state = LoyaltyState(minion_id="minion_001", leader_id="leader_001", loyalty_score=0.95)
        assert state.is_fanatic() is True

        state.loyalty_score = 0.8
        assert state.is_fanatic() is False