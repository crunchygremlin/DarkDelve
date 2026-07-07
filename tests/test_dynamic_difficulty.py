"""Tests for dynamic difficulty adjustment system."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from src.domain.services.dynamic_difficulty_service import DynamicDifficultyService, DifficultyAdjustment
from src.application.services.llm_worker import LLMWorker
from src.domain.entities.entity import Entity
from src.domain.services.player_profile_service import PlayerProfileService
from src.domain.services.dungeon_master_service import DungeonMasterService


class TestDynamicDifficultyService(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.mock_dungeon_master_service = Mock(spec=DungeonMasterService)
        self.mock_llm_worker = Mock(spec=LLMWorker)
        self.mock_player_profile_service = Mock(spec=PlayerProfileService)

        self.service = DynamicDifficultyService(
            dungeon_master_service=self.mock_dungeon_master_service,
            llm_worker=self.mock_llm_worker,
            player_profile_service=self.mock_player_profile_service
        )

    def test_evaluate_and_adjust_difficulty_no_change_same_level(self):
        """Test that no adjustment is made when level hasn't changed."""
        # Arrange
        player_entity = Mock(spec=Entity)
        player_entity.fighter = Mock()
        player_entity.fighter.max_hp = 100
        player_entity.fighter.power = 10
        player_entity.fighter.defense = 5

        # Set to same level
        self.service.last_evaluated_level = 5

        # Act
        adjustment = self.service.evaluate_and_adjust_difficulty(
            player_entity=player_entity,
            current_level=5
        )

        # Assert
        self.assertTrue(adjustment.is_no_change())

    def test_evaluate_and_adjust_difficulty_level_increase(self):
        """Test that adjustment is made when level increases."""
        # Arrange
        player_entity = Mock(spec=Entity)
        player_entity.fighter = Mock()
        player_entity.fighter.max_hp = 100
        player_entity.fighter.power = 15
        player_entity.fighter.defense = 8

        self.mock_llm_worker.evaluate_player_stats.return_value = {
            "difficulty_modifier": 1.2,
            "specific_adjustments": {
                "spawn_rate": 1.1,
                "monster_health": 1.15,
                "monster_damage": 1.1
            },
            "reasoning": "Player stats are above average for level"
        }

        # Act
        adjustment = self.service.evaluate_and_adjust_difficulty(
            player_entity=player_entity,
            current_level=3
        )

        # Assert
        self.assertEqual(adjustment.spawn_rate_modifier, 1.1)
        self.assertEqual(adjustment.monster_health_modifier, 1.15)
        self.assertEqual(adjustment.monster_damage_modifier, 1.1)
        self.assertEqual(self.service.last_evaluated_level, 3)

    def test_parse_llm_response_default_values(self):
        """Test parsing of LLM response with missing values."""
        # Arrange
        llm_response = {
            "difficulty_modifier": 1.3
            # Missing specific_adjustments
        }

        # Act
        adjustment = self.service._parse_llm_response(llm_response)

        # Assert
        self.assertEqual(adjustment.spawn_rate_modifier, 1.3)
        self.assertEqual(adjustment.monster_health_modifier, 1.3)
        self.assertEqual(adjustment.monster_damage_modifier, 1.3)
        # Default values for missing specific adjustments
        self.assertEqual(adjustment.experience_reward_modifier, 1.0)
        self.assertEqual(adjustment.loot_quality_modifier, 1.0)

    def test_parse_llm_response_specific_values(self):
        """Test parsing of LLM response with specific values."""
        # Arrange
        llm_response = {
            "specific_adjustments": {
                "spawn_rate": 0.8,
                "monster_health": 1.2,
                "monster_damage": 0.9
            }
            # Missing difficulty_modifier
        }

        # Act
        adjustment = self.service._parse_llm_response(llm_response)

        # Assert
        self.assertEqual(adjustment.spawn_rate_modifier, 0.8)
        self.assertEqual(adjustment.monster_health_modifier, 1.2)
        self.assertEqual(adjustment.monster_damage_modifier, 0.9)
        # Default values for missing difficulty modifier
        self.assertEqual(adjustment.experience_reward_modifier, 1.0)
        self.assertEqual(adjustment.loot_quality_modifier, 1.0)

    def test_get_player_max_stats(self):
        """Test extraction of player max stats."""
        # Arrange
        player_entity = Mock(spec=Entity)
        player_entity.fighter = Mock()
        player_entity.fighter.max_hp = 120
        player_entity.fighter.power = 18
        player_entity.fighter.defense = 12
        player_entity.power = Mock()
        player_entity.power.level = 5

        # Act
        stats = self.service._get_player_max_stats(player_entity)

        # Assert
        self.assertEqual(stats['health'], 120)
        self.assertEqual(stats['attack'], 18)
        self.assertEqual(stats['defense'], 12)
        self.assertEqual(stats['power_level'], 5)

    def test_difficulty_adjustment_no_change(self):
        """Test DifficultyAdjustment.no_change() class method."""
        # Act
        adjustment = DifficultyAdjustment.no_change()

        # Assert
        self.assertEqual(adjustment.spawn_rate_modifier, 1.0)
        self.assertEqual(adjustment.monster_health_modifier, 1.0)
        self.assertEqual(adjustment.monster_damage_modifier, 1.0)
        self.assertEqual(adjustment.experience_reward_modifier, 1.0)
        self.assertEqual(adjustment.loot_quality_modifier, 1.0)

    def test_difficulty_adjustment_is_significant_change(self):
        """Test DifficultyAdjustment.is_significant_change() method."""
        # Test significant change
        adjustment = DifficultyAdjustment(
            spawn_rate_modifier=1.5,
            monster_health_modifier=1.0,
            monster_damage_modifier=1.0
        )
        self.assertTrue(adjustment.is_significant_change())

        # Test no significant change
        adjustment = DifficultyAdjustment(
            spawn_rate_modifier=1.05,
            monster_health_modifier=1.0,
            monster_damage_modifier=1.0
        )
        self.assertFalse(adjustment.is_significant_change())

    def test_difficulty_adjustment_is_no_change(self):
        """Test DifficultyAdjustment.is_no_change() method."""
        # Test no change
        adjustment = DifficultyAdjustment.no_change()
        self.assertTrue(adjustment.is_no_change())

        # Test with changes
        adjustment = DifficultyAdjustment(
            spawn_rate_modifier=1.2,
            monster_health_modifier=1.0,
            monster_damage_modifier=1.0
        )
        self.assertFalse(adjustment.is_no_change())


if __name__ == '__main__':
    unittest.main()