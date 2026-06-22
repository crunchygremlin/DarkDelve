"""Tests for level design service."""

import pytest
from unittest.mock import MagicMock

from src.domain.services.level_design_service import (
    LevelDesignService,
    SOCIAL_STRUCTURE_SCENARIOS
)
from src.domain.value_objects.power_levels import PlayerProfile, OffensivePower, DefensivePower, SkillSet
from src.domain.value_objects.map_access import MapAccessRequest
from src.domain.value_objects.llm_logging import LLMLogger


class TestLevelDesignService:
    """Tests for LevelDesignService class."""
    
    def test_init(self):
        """Test LevelDesignService initialization."""
        logger = MagicMock()
        service = LevelDesignService(logger)
        
        assert service._llm_logger == logger
        assert service._ollama_service is None
        
        ollama = MagicMock()
        service = LevelDesignService(logger, ollama)
        assert service._ollama_service == ollama
    
    def test_request_map_access_valid_reason(self):
        """Test map access request with valid reason."""
        logger = MagicMock()
        service = LevelDesignService(logger)
        
        request = MapAccessRequest(
            requester_id="entity_001",
            reason="level_creation",
            access_type="full"
        )
        
        result = service.request_map_access(request)
        
        assert result is True
        assert request.granted is True
    
    def test_request_map_access_invalid_reason(self):
        """Test map access request with invalid reason."""
        logger = MagicMock()
        service = LevelDesignService(logger)
        
        request = MapAccessRequest(
            requester_id="entity_001",
            reason="invalid_reason",
            access_type="full"
        )
        
        result = service.request_map_access(request)
        
        assert result is False
        assert request.granted is False
    
    def test_generate_level_layout_fallback(self):
        """Test level layout generation with fallback."""
        logger = MagicMock()
        service = LevelDesignService(logger)
        
        profile = PlayerProfile(
            offensive_power=OffensivePower(melee_strength=10.0),
            defensive_power=DefensivePower(physical_armor=8.0),
            skills=SkillSet(perception=10.0)
        )
        
        result = service.generate_level_layout(profile, 1, [[1, 1], [1, 1]])
        
        assert "description" in result
        assert "rooms" in result
        assert "entities" in result
        assert "items" in result
    
    def test_generate_mob_placement(self):
        """Test mob placement generation."""
        logger = MagicMock()
        service = LevelDesignService(logger)
        
        profile = PlayerProfile(
            offensive_power=OffensivePower(melee_strength=15.0),
            defensive_power=DefensivePower(physical_armor=10.0),
            skills=SkillSet(perception=10.0)
        )
        
        rooms = [
            {"id": "room_1", "position": (0, 0), "size": "medium"}
        ]
        
        placements = service.generate_mob_placement(profile, rooms)
        
        assert isinstance(placements, list)
        assert len(placements) > 0
        assert "type" in placements[0]
    
    def test_generate_item_seeding(self):
        """Test item seeding generation."""
        logger = MagicMock()
        service = LevelDesignService(logger)
        
        profile = PlayerProfile(
            offensive_power=OffensivePower(melee_strength=10.0),
            defensive_power=DefensivePower(physical_armor=8.0),
            skills=SkillSet(perception=10.0)
        )
        
        rooms = [
            {"id": "room_1", "position": (0, 0)},
            {"id": "room_2", "position": (10, 0)}
        ]
        
        items = service.generate_item_seeding(profile, rooms)
        
        assert isinstance(items, list)
    
    def test_select_social_structure(self):
        """Test social structure selection."""
        logger = MagicMock()
        service = LevelDesignService(logger)
        
        profile = PlayerProfile()
        
        # Test cycling through structures
        structure_0 = service.select_social_structure(profile, 0)
        structure_1 = service.select_social_structure(profile, 1)
        structure_2 = service.select_social_structure(profile, 2)
        
        assert structure_0 in [s["type"] for s in SOCIAL_STRUCTURE_SCENARIOS]
        assert structure_1 in [s["type"] for s in SOCIAL_STRUCTURE_SCENARIOS]
        assert structure_2 in [s["type"] for s in SOCIAL_STRUCTURE_SCENARIOS]
    
    def test_get_available_structures(self):
        """Test getting available social structures."""
        logger = MagicMock()
        service = LevelDesignService(logger)
        
        structures = service.get_available_structures()
        
        assert isinstance(structures, list)
        assert len(structures) == 6
        
        # Check each structure has required fields
        for s in structures:
            assert "type" in s
            assert "description" in s
            assert "min_mobs" in s
            assert "max_mobs" in s
            assert "loyalty_sensitive" in s


class TestSocialStructureScenarios:
    """Tests for social structure scenarios."""
    
    def test_scenarios_count(self):
        """Test that there are 6 social structure scenarios."""
        assert len(SOCIAL_STRUCTURE_SCENARIOS) == 6
    
    def test_goblin_kingdom_scenario(self):
        """Test goblin kingdom scenario."""
        scenario = next(s for s in SOCIAL_STRUCTURE_SCENARIOS if s["type"] == "goblin_kingdom")
        
        assert "hierarchical" in scenario["description"].lower()
        assert scenario["min_mobs"] == 5
        assert scenario["max_mobs"] == 12
        assert scenario["loyalty_sensitive"] is True
    
    def test_wolf_pack_scenario(self):
        """Test wolf pack scenario."""
        scenario = next(s for s in SOCIAL_STRUCTURE_SCENARIOS if s["type"] == "wolf_pack")
        
        assert scenario["min_mobs"] == 4
        assert scenario["max_mobs"] == 8
        assert scenario["loyalty_sensitive"] is False
    
    def test_spider_hive_scenario(self):
        """Test spider hive scenario."""
        scenario = next(s for s in SOCIAL_STRUCTURE_SCENARIOS if s["type"] == "spider_hive")
        
        assert scenario["min_mobs"] == 6
        assert scenario["max_mobs"] == 15
        assert scenario["loyalty_sensitive"] is False
    
    def test_mercenary_band_scenario(self):
        """Test mercenary band scenario."""
        scenario = next(s for s in SOCIAL_STRUCTURE_SCENARIOS if s["type"] == "mercenary_band")
        
        assert scenario["min_mobs"] == 3
        assert scenario["max_mobs"] == 8
        assert scenario["loyalty_sensitive"] is True
    
    def test_undead_court_scenario(self):
        """Test undead court scenario."""
        scenario = next(s for s in SOCIAL_STRUCTURE_SCENARIOS if s["type"] == "undead_court")
        
        assert scenario["min_mobs"] == 5
        assert scenario["max_mobs"] == 12
        assert scenario["loyalty_sensitive"] is False
    
    def test_merchant_guild_scenario(self):
        """Test merchant guild scenario."""
        scenario = next(s for s in SOCIAL_STRUCTURE_SCENARIOS if s["type"] == "merchant_guild")
        
        assert scenario["min_mobs"] == 3
        assert scenario["max_mobs"] == 6
        assert scenario["loyalty_sensitive"] is True


class TestParseLevelResponse:
    """Tests for parsing LLM level responses."""
    
    def test_parse_valid_json(self):
        """Test parsing valid JSON response."""
        logger = MagicMock()
        service = LevelDesignService(logger)
        
        response = '{"description": "Test level", "rooms": [], "entities": [], "items": []}'
        
        result = service._parse_level_response(response)
        
        assert result["description"] == "Test level"
        assert result["rooms"] == []
    
    def test_parse_json_with_extra_text(self):
        """Test parsing JSON with extra text around it."""
        logger = MagicMock()
        service = LevelDesignService(logger)
        
        response = 'Here is the level:\n{"description": "Test", "rooms": [], "entities": [], "items": []}\nEnd.'
        
        result = service._parse_level_response(response)
        
        assert result["description"] == "Test"
    
    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns default."""
        logger = MagicMock()
        service = LevelDesignService(logger)
        
        response = "This is not JSON"
        
        result = service._parse_level_response(response)
        
        assert "description" in result


class TestBuildLevelPrompt:
    """Tests for building level prompts."""
    
    def test_build_level_prompt(self):
        """Test building level prompt."""
        logger = MagicMock()
        service = LevelDesignService(logger)
        
        profile = PlayerProfile(
            offensive_power=OffensivePower(melee_strength=15.0),
            defensive_power=DefensivePower(physical_armor=10.0),
            skills=SkillSet(perception=10.0)
        )
        
        prompt = service._build_level_prompt(profile, 3)
        
        assert "Player Profile:" in prompt
        assert "Level: 3" in prompt
        assert "melee_strength" in str(profile.offensive_power.dominant_type())


class TestBuildItemPrompt:
    """Tests for building item prompts."""
    
    def test_build_item_prompt(self):
        """Test building item prompt."""
        logger = MagicMock()
        service = LevelDesignService(logger)
        
        profile = PlayerProfile()
        
        prompt = service._build_item_prompt(profile, 5)
        
        assert "5 items" in prompt


class TestFallbackLevel:
    """Tests for fallback level generation."""
    
    def test_generate_fallback_level(self):
        """Test generating fallback level."""
        logger = MagicMock()
        service = LevelDesignService(logger)
        
        profile = PlayerProfile()
        
        result = service._generate_fallback_level(profile, 5)
        
        assert result["description"] == "Level 5: A basic dungeon"
        assert len(result["rooms"]) == 2
        assert result["rooms"][0]["id"] == "room_1"
    
    def test_generate_fallback_level_with_profile(self):
        """Test generating fallback level with profile."""
        logger = MagicMock()
        service = LevelDesignService(logger)
        
        profile = PlayerProfile(
            offensive_power=OffensivePower(melee_strength=20.0)
        )
        
        result = service._generate_fallback_level(profile, 10)
        
        assert "Level 10" in result["description"]


class TestMobSelection:
    """Tests for mob type selection."""
    
    def test_select_mob_types_low_power(self):
        """Test selecting mobs for low power player."""
        logger = MagicMock()
        service = LevelDesignService(logger)
        
        placements = service.generate_mob_placement(
            PlayerProfile(offensive_power=OffensivePower(melee_strength=10.0)),
            [{"id": "r1", "position": (0, 0), "size": "medium"}]
        )
        
        for p in placements:
            assert p["type"] == "goblin"
    
    def test_select_mob_types_high_power(self):
        """Test selecting mobs for high power player."""
        logger = MagicMock()
        service = LevelDesignService(logger)
        
        placements = service.generate_mob_placement(
            PlayerProfile(offensive_power=OffensivePower(melee_strength=50.0)),
            [{"id": "r1", "position": (0, 0), "size": "large"}]
        )
        
        # Should have orc or dragon
        for p in placements:
            assert p["type"] in ["orc", "dragon"]


class TestItemSelection:
    """Tests for item type selection."""
    
    def test_select_item_type(self):
        """Test selecting item type."""
        logger = MagicMock()
        service = LevelDesignService(logger)
        
        profile = PlayerProfile()
        
        item_type = service._select_item_type(profile)
        
        # Default is potion
        assert item_type == "potion"