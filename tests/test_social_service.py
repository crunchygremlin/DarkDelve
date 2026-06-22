"""Tests for social service."""

import pytest
from unittest.mock import MagicMock

from src.domain.services.social_service import SocialService
from src.domain.value_objects.social import (
    SocialStructure, LoyaltyState, RelationshipType, SocialStructureType
)


class TestSocialService:
    """Tests for SocialService class."""
    
    def test_init(self):
        """Test SocialService initialization."""
        service = SocialService()
        
        assert service._structures == {}
        assert service._loyalty_states == {}
        assert service._relationships == {}
    
    def test_create_structure(self):
        """Test creating a social structure."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="goblin_kingdom",
            leader_id="king_001",
            member_ids=["guard_001", "minion_001"]
        )
        
        assert isinstance(structure, SocialStructure)
        assert structure.structure_type == "goblin_kingdom"
        assert structure.leader_id == "king_001"
        assert len(structure.member_ids) == 2
        assert structure.hierarchy["king_001"] == 0
    
    def test_add_member(self):
        """Test adding a member to a structure."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="goblin_kingdom",
            leader_id="king_001",
            member_ids=[]
        )
        
        result = service.add_member(structure.structure_id, "new_member", rank=1)
        
        assert result is True
        assert "new_member" in structure.member_ids
        assert "new_member" in service._loyalty_states
    
    def test_add_member_already_exists(self):
        """Test adding a member that already exists."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="goblin_kingdom",
            leader_id="king_001",
            member_ids=["member_001"]
        )
        
        result = service.add_member(structure.structure_id, "member_001")
        
        assert result is False
    
    def test_remove_member(self):
        """Test removing a member from a structure."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="goblin_kingdom",
            leader_id="king_001",
            member_ids=["member_001"]
        )
        
        result = service.remove_member(structure.structure_id, "member_001")
        
        assert result is True
        assert "member_001" not in structure.member_ids
        assert "member_001" not in service._loyalty_states
    
    def test_get_structure(self):
        """Test getting a structure by ID."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="wolf_pack",
            leader_id="alpha_001",
            member_ids=["beta_001"]
        )
        
        result = service.get_structure(structure.structure_id)
        
        assert result == structure
    
    def test_get_structure_not_found(self):
        """Test getting a non-existent structure."""
        service = SocialService()
        
        result = service.get_structure("nonexistent")
        
        assert result is None
    
    def test_get_structure_for_entity(self):
        """Test getting structure for an entity."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="goblin_kingdom",
            leader_id="king_001",
            member_ids=["member_001"]
        )
        
        result = service.get_structure_for_entity("king_001")
        assert result == structure
        
        result = service.get_structure_for_entity("member_001")
        assert result == structure
    
    def test_get_leader(self):
        """Test getting the leader of a structure."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="goblin_kingdom",
            leader_id="king_001",
            member_ids=[]
        )
        
        leader = service.get_leader(structure.structure_id)
        
        assert leader == "king_001"
    
    def test_get_members(self):
        """Test getting members of a structure."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="wolf_pack",
            leader_id="alpha_001",
            member_ids=["beta_001", "beta_002"]
        )
        
        members = service.get_members(structure.structure_id)
        
        assert len(members) == 2
        assert "beta_001" in members
        assert "beta_002" in members
    
    def test_get_rank(self):
        """Test getting rank of an entity."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="goblin_kingdom",
            leader_id="king_001",
            member_ids=["member_001"]
        )
        
        rank = service.get_rank(structure.structure_id, "king_001")
        assert rank == 0
        
        rank = service.get_rank(structure.structure_id, "member_001")
        assert rank == 1
    
    def test_seed_loyalty(self):
        """Test seeding loyalty for all members."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="goblin_kingdom",
            leader_id="king_001",
            member_ids=["member_001", "member_002"]
        )
        
        service.seed_loyalty(structure.structure_id, base_loyalty=0.7)
        
        for member_id in ["member_001", "member_002"]:
            loyalty = service.get_loyalty(member_id)
            assert loyalty is not None
            assert loyalty.loyalty_score == 0.7


class TestLoyaltyModification:
    """Tests for loyalty modification."""
    
    def test_modify_loyalty(self):
        """Test modifying loyalty."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="goblin_kingdom",
            leader_id="king_001",
            member_ids=["member_001"]
        )
        
        result = service.modify_loyalty("member_001", 0.1, "gift", "Received potion", 10)
        
        assert result is True
        loyalty = service.get_loyalty("member_001")
        assert loyalty.loyalty_score == 0.6
    
    def test_modify_loyalty_clamp_at_zero(self):
        """Test loyalty is clamped at 0.0."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="goblin_kingdom",
            leader_id="king_001",
            member_ids=["member_001"]
        )
        
        service.modify_loyalty("member_001", -1.0, "damage", "Took damage", 10)
        
        loyalty = service.get_loyalty("member_001")
        assert loyalty.loyalty_score == 0.0
    
    def test_modify_loyalty_clamp_at_one(self):
        """Test loyalty is clamped at 1.0."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="goblin_kingdom",
            leader_id="king_001",
            member_ids=["member_001"]
        )
        
        service.seed_loyalty(structure.structure_id, base_loyalty=0.9)
        service.modify_loyalty("member_001", 0.5, "promotion", "Promoted", 10)
        
        loyalty = service.get_loyalty("member_001")
        assert loyalty.loyalty_score == 1.0


class TestSocialEvents:
    """Tests for social event processing."""
    
    def test_process_gift(self):
        """Test processing a gift."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="goblin_kingdom",
            leader_id="king_001",
            member_ids=["member_001"]
        )
        
        result = service.process_gift("king_001", "member_001", 50.0, 10)
        
        assert result["success"] is True
        assert result["loyalty_change"] > 0
    
    def test_process_combat_alongside(self):
        """Test processing combat alongside."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="goblin_kingdom",
            leader_id="king_001",
            member_ids=["member_001"]
        )
        
        service.process_combat_alongside("member_001", 10)
        
        loyalty = service.get_loyalty("member_001")
        assert loyalty.loyalty_score > 0.5
    
    def test_process_leader_fled(self):
        """Test processing leader fleeing."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="goblin_kingdom",
            leader_id="king_001",
            member_ids=["member_001", "member_002"]
        )
        
        service.seed_loyalty(structure.structure_id, base_loyalty=0.8)
        service.process_leader_fled("king_001", 10)
        
        for member_id in ["member_001", "member_002"]:
            loyalty = service.get_loyalty(member_id)
            assert loyalty.loyalty_score < 0.8
    
    def test_process_promotion(self):
        """Test processing a promotion."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="goblin_kingdom",
            leader_id="king_001",
            member_ids=["member_001"]
        )
        
        result = service.process_promotion(structure.structure_id, "member_001", 0, 10)
        
        assert result["success"] is True
        assert result["loyalty_change"] > 0
    
    def test_distribute_wealth(self):
        """Test distributing wealth."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="merchant_guild",
            leader_id="guildmaster_001",
            member_ids=["merchant_001", "guard_001"]
        )
        
        distribution = {
            "merchant_001": 50.0,
            "guard_001": 30.0
        }
        
        result = service.distribute_wealth(structure.structure_id, 100.0, distribution, 10)
        
        assert result["success"] is True
        assert len(result["loyalty_changes"]) == 2


class TestDesertionAndBetrayal:
    """Tests for desertion and betrayal checks."""
    
    def test_check_desertion_true(self):
        """Test desertion check when loyalty is very low."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="goblin_kingdom",
            leader_id="king_001",
            member_ids=["member_001"]
        )
        
        service.seed_loyalty(structure.structure_id, base_loyalty=0.05)
        
        assert service.check_desertion("member_001") is True
    
    def test_check_desertion_false(self):
        """Test desertion check when loyalty is sufficient."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="goblin_kingdom",
            leader_id="king_001",
            member_ids=["member_001"]
        )
        
        service.seed_loyalty(structure.structure_id, base_loyalty=0.5)
        
        assert service.check_desertion("member_001") is False
    
    def test_check_betrayal_true(self):
        """Test betrayal check when loyalty is very low."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="goblin_kingdom",
            leader_id="king_001",
            member_ids=["member_001"]
        )
        
        service.seed_loyalty(structure.structure_id, base_loyalty=0.04)
        
        assert service.check_betrayal("member_001") is True
    
    def test_check_betrayal_false(self):
        """Test betrayal check when loyalty is sufficient."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="goblin_kingdom",
            leader_id="king_001",
            member_ids=["member_001"]
        )
        
        service.seed_loyalty(structure.structure_id, base_loyalty=0.5)
        
        assert service.check_betrayal("member_001") is False


class TestStructureSummary:
    """Tests for structure summary."""
    
    def test_get_structure_summary(self):
        """Test getting structure summary."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="goblin_kingdom",
            leader_id="king_001",
            member_ids=["member_001"]
        )
        
        service.seed_loyalty(structure.structure_id, base_loyalty=0.7)
        
        summary = service.get_structure_summary(structure.structure_id)
        
        assert summary["structure_type"] == "goblin_kingdom"
        assert summary["leader_id"] == "king_001"
        assert summary["member_count"] == 1
        assert summary["average_loyalty"] == 0.7
    
    def test_get_social_context_for_llm(self):
        """Test getting social context for LLM."""
        service = SocialService()
        
        structure = service.create_structure(
            structure_type="wolf_pack",
            leader_id="alpha_001",
            member_ids=["beta_001"]
        )
        
        service.seed_loyalty(structure.structure_id, base_loyalty=0.6)
        
        context = service.get_social_context_for_llm("alpha_001")
        
        assert "Social Context:" in context
        assert "wolf_pack" in context
        assert "Leader" in context
        
        context = service.get_social_context_for_llm("beta_001")
        assert "Member" in context