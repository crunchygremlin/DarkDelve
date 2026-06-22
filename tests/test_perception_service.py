"""Tests for perception service."""

import pytest
from unittest.mock import MagicMock, patch

from src.domain.services.perception_service import (
    PerceptionService,
    DEFAULT_MOB_MODIFIERS
)
from src.domain.value_objects.perception import PerceptionModifiers, PerceptionStatus
from src.domain.value_objects.position import Position


class TestPerceptionService:
    """Tests for PerceptionService class."""
    
    def test_init(self):
        """Test PerceptionService initialization."""
        fov_query = MagicMock()
        entity_repo = MagicMock()
        item_repo = MagicMock()
        
        service = PerceptionService(fov_query, entity_repo, item_repo)
        
        assert service._fov_query == fov_query
        assert service._entity_repository == entity_repo
        assert service._item_repository == item_repo
    
    def test_get_perception_for_mob_type_goblin(self):
        """Test getting perception modifiers for goblin."""
        fov_query = MagicMock()
        entity_repo = MagicMock()
        item_repo = MagicMock()
        
        service = PerceptionService(fov_query, entity_repo, item_repo)
        modifiers = service.get_perception_for_mob_type("goblin")
        
        assert isinstance(modifiers, PerceptionModifiers)
        assert modifiers.entity_type == "goblin"
        assert modifiers.sight_range == 6
        assert modifiers.hearing_range == 14
        assert modifiers.noise_sensitivity == 1.3
        assert modifiers.darkness_penalty == 0.6
    
    def test_get_perception_for_mob_type_bat(self):
        """Test getting perception modifiers for bat."""
        fov_query = MagicMock()
        entity_repo = MagicMock()
        item_repo = MagicMock()
        
        service = PerceptionService(fov_query, entity_repo, item_repo)
        modifiers = service.get_perception_for_mob_type("bat")
        
        assert modifiers.sight_range == 2
        assert modifiers.echolocation_range == 14
        assert modifiers.darkvision is True
    
    def test_get_perception_for_mob_type_wolf(self):
        """Test getting perception modifiers for wolf."""
        fov_query = MagicMock()
        entity_repo = MagicMock()
        item_repo = MagicMock()
        
        service = PerceptionService(fov_query, entity_repo, item_repo)
        modifiers = service.get_perception_for_mob_type("wolf")
        
        assert modifiers.sight_range == 8
        assert modifiers.hearing_range == 18
        assert modifiers.smell_range == 12
        assert modifiers.noise_sensitivity == 1.5
    
    def test_get_perception_for_mob_type_spider(self):
        """Test getting perception modifiers for spider."""
        fov_query = MagicMock()
        entity_repo = MagicMock()
        item_repo = MagicMock()
        
        service = PerceptionService(fov_query, entity_repo, item_repo)
        modifiers = service.get_perception_for_mob_type("spider")
        
        assert modifiers.sight_range == 4
        assert modifiers.hearing_range == 6
        assert modifiers.vibration_range == 10
        assert modifiers.ignore_walls_vibration is True
    
    def test_get_perception_for_mob_type_lich(self):
        """Test getting perception modifiers for lich."""
        fov_query = MagicMock()
        entity_repo = MagicMock()
        item_repo = MagicMock()
        
        service = PerceptionService(fov_query, entity_repo, item_repo)
        modifiers = service.get_perception_for_mob_type("lich")
        
        assert modifiers.sight_range == 12
        assert modifiers.hearing_range == 8
        assert modifiers.magic_sense_range == 15
        assert modifiers.see_invisible is True
    
    def test_get_perception_for_unknown_mob_type(self):
        """Test getting perception modifiers for unknown mob type returns default."""
        fov_query = MagicMock()
        entity_repo = MagicMock()
        item_repo = MagicMock()
        
        service = PerceptionService(fov_query, entity_repo, item_repo)
        modifiers = service.get_perception_for_mob_type("unknown_type")
        
        assert modifiers.sight_range == 8
        assert modifiers.hearing_range == 8
    
    def test_compute_perception_basic(self):
        """Test basic perception computation."""
        fov_query = MagicMock()
        entity_repo = MagicMock()
        item_repo = MagicMock()
        
        service = PerceptionService(fov_query, entity_repo, item_repo)
        
        # Create mock entity
        entity = MagicMock()
        entity.id = "test_entity"
        entity.mob_type = "goblin"
        entity.position = Position(5, 5)
        
        # Create mock player
        player = MagicMock()
        player.position = Position(10, 5)
        player.stats = MagicMock()
        
        all_entities = [player]
        items = []
        game_map = MagicMock()
        
        # Mock FOV query result
        fov_result = MagicMock()
        fov_result.success = True
        fov_result.data = {(5, 5), (6, 5), (7, 5), (8, 5), (9, 5), (10, 5)}
        fov_query.execute.return_value = fov_result
        
        result = service.compute_perception(entity, all_entities, items, game_map)
        
        assert isinstance(result, PerceptionStatus)
        assert result.entity_id == "test_entity"
    
    def test_compute_perception_no_player(self):
        """Test perception computation with no player."""
        fov_query = MagicMock()
        entity_repo = MagicMock()
        item_repo = MagicMock()
        
        service = PerceptionService(fov_query, entity_repo, item_repo)
        
        entity = MagicMock()
        entity.id = "test_entity"
        entity.mob_type = "goblin"
        entity.position = Position(5, 5)
        
        result = service.compute_perception(entity, [], [], MagicMock())
        
        assert result.can_see_player is False
        assert result.can_hear_player is False
        assert result.player_distance_estimate == -1.0


class TestPerceptionServiceSight:
    """Tests for sight computation."""
    
    def test_compute_sight_within_range(self):
        """Test sight computation within range."""
        fov_query = MagicMock()
        entity_repo = MagicMock()
        item_repo = MagicMock()
        
        service = PerceptionService(fov_query, entity_repo, item_repo)
        
        entity = MagicMock()
        entity.position = Position(0, 0)
        
        modifiers = PerceptionModifiers(entity_type="test", sight_range=10)
        game_map = MagicMock()
        
        target_pos = Position(5, 5)
        
        can_see, distance = service._compute_sight(entity, target_pos, modifiers, game_map)
        
        assert distance == pytest.approx(7.07, rel=0.01)
    
    def test_compute_sight_out_of_range(self):
        """Test sight computation out of range."""
        fov_query = MagicMock()
        entity_repo = MagicMock()
        item_repo = MagicMock()
        
        service = PerceptionService(fov_query, entity_repo, item_repo)
        
        entity = MagicMock()
        entity.position = Position(0, 0)
        
        modifiers = PerceptionModifiers(entity_type="test", sight_range=5)
        game_map = MagicMock()
        
        target_pos = Position(10, 10)
        
        can_see, distance = service._compute_sight(entity, target_pos, modifiers, game_map)
        
        assert can_see is False
        assert distance == pytest.approx(14.14, rel=0.01)


class TestPerceptionServiceHearing:
    """Tests for hearing computation."""
    
    def test_compute_hearing_detectable(self):
        """Test hearing computation for detectable noise."""
        fov_query = MagicMock()
        entity_repo = MagicMock()
        item_repo = MagicMock()
        
        service = PerceptionService(fov_query, entity_repo, item_repo)
        
        entity = MagicMock()
        entity.position = Position(0, 0)
        
        modifiers = PerceptionModifiers(entity_type="test", hearing_range=20, noise_sensitivity=1.0)
        
        target_pos = Position(5, 5)
        noise_level = 0.5
        
        can_hear, distance = service._compute_hearing(entity, target_pos, modifiers, noise_level)
        
        assert distance == pytest.approx(7.07, rel=0.01)
    
    def test_compute_hearing_out_of_range(self):
        """Test hearing computation out of range."""
        fov_query = MagicMock()
        entity_repo = MagicMock()
        item_repo = MagicMock()
        
        service = PerceptionService(fov_query, entity_repo, item_repo)
        
        entity = MagicMock()
        entity.position = Position(0, 0)
        
        modifiers = PerceptionModifiers(entity_type="test", hearing_range=5, noise_sensitivity=1.0)
        
        target_pos = Position(10, 10)
        noise_level = 0.5
        
        can_hear, distance = service._compute_hearing(entity, target_pos, modifiers, noise_level)
        
        assert can_hear is False


class TestPerceptionServiceSmell:
    """Tests for smell computation."""
    
    def test_compute_smell_within_range(self):
        """Test smell computation within range."""
        fov_query = MagicMock()
        entity_repo = MagicMock()
        item_repo = MagicMock()
        
        service = PerceptionService(fov_query, entity_repo, item_repo)
        
        entity = MagicMock()
        entity.position = Position(0, 0)
        
        modifiers = PerceptionModifiers(entity_type="wolf", smell_range=12)
        
        target_pos = Position(5, 5)
        
        can_smell, distance = service._compute_smell(entity, target_pos, modifiers)
        
        assert can_smell is True
        assert distance == pytest.approx(7.07, rel=0.01)


class TestPerceptionServiceVibration:
    """Tests for vibration computation."""
    
    def test_compute_vibration_within_range(self):
        """Test vibration computation within range."""
        fov_query = MagicMock()
        entity_repo = MagicMock()
        item_repo = MagicMock()
        
        service = PerceptionService(fov_query, entity_repo, item_repo)
        
        entity = MagicMock()
        entity.position = Position(0, 0)
        
        # Use a spider with vibration_range=10
        modifiers = PerceptionModifiers(entity_type="spider", vibration_range=10)
        
        target_pos = Position(5, 5)
        
        can_feel, distance = service._compute_vibration(entity, target_pos, modifiers)
        
        assert can_feel is True
        assert distance == pytest.approx(7.07, rel=0.01)
    
    def test_compute_vibration_out_of_range(self):
        """Test vibration computation out of range."""
        fov_query = MagicMock()
        entity_repo = MagicMock()
        item_repo = MagicMock()
        
        service = PerceptionService(fov_query, entity_repo, item_repo)
        
        entity = MagicMock()
        entity.position = Position(0, 0)
        
        modifiers = PerceptionModifiers(entity_type="spider", vibration_range=5)
        
        target_pos = Position(10, 10)
        
        can_feel, distance = service._compute_vibration(entity, target_pos, modifiers)
        
        assert can_feel is False


class TestPerceptionServiceLightLevel:
    """Tests for light level computation."""
    
    def test_get_light_level_default(self):
        """Test default light level when map has no method."""
        fov_query = MagicMock()
        entity_repo = MagicMock()
        item_repo = MagicMock()
        
        service = PerceptionService(fov_query, entity_repo, item_repo)
        
        entity = MagicMock()
        entity.position = Position(0, 0)
        
        game_map = MagicMock()
        delattr(game_map, 'get_light_level')
        
        light = service._get_light_level(entity, game_map)
        
        assert light == 1.0
    
    def test_get_light_level_from_map(self):
        """Test light level from map method."""
        fov_query = MagicMock()
        entity_repo = MagicMock()
        item_repo = MagicMock()
        
        service = PerceptionService(fov_query, entity_repo, item_repo)
        
        entity = MagicMock()
        entity.position = Position(5, 5)
        
        game_map = MagicMock()
        game_map.get_light_level.return_value = 0.7
        
        light = service._get_light_level(entity, game_map)
        
        assert light == 0.7


class TestDefaultMobModifiers:
    """Tests for default mob modifiers dictionary."""
    
    def test_default_mob_modifiers_contains_all_types(self):
        """Test that default modifiers contains all expected mob types."""
        expected_types = [
            "goblin", "goblin_king", "wolf", "spider",
            "bat", "mercenary", "undead", "lich", "default"
        ]
        
        for mob_type in expected_types:
            assert mob_type in DEFAULT_MOB_MODIFIERS
    
    def test_goblin_modifiers_values(self):
        """Test goblin modifier values."""
        goblin = DEFAULT_MOB_MODIFIERS["goblin"]
        assert goblin.sight_range == 6
        assert goblin.hearing_range == 14
        assert goblin.noise_sensitivity == 1.3
        assert goblin.darkness_penalty == 0.6
    
    def test_bat_modifiers_values(self):
        """Test bat modifier values."""
        bat = DEFAULT_MOB_MODIFIERS["bat"]
        assert bat.sight_range == 2
        assert bat.echolocation_range == 14
        assert bat.darkvision is True
    
    def test_mercenary_modifiers_values(self):
        """Test mercenary modifier values."""
        mercenary = DEFAULT_MOB_MODIFIERS["mercenary"]
        assert mercenary.sight_range == 10
        assert mercenary.hearing_range == 10
        assert mercenary.noise_sensitivity == 1.0