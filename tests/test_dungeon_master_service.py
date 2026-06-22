"""Tests for DungeonMasterService."""
import pytest
from unittest.mock import MagicMock
from src.domain.services.dungeon_master_service import DungeonMasterService
from src.domain.value_objects.difficulty import (
    DifficultyMode, LevelNarrative, BossEncounter, KeyItem, DungeonMasterPlan
)


class TestDungeonMasterService:
    """Tests for DungeonMasterService."""

    def test_create_plan(self):
        """Test creating a dungeon master plan."""
        mock_level_design = MagicMock()
        service = DungeonMasterService(level_design_service=mock_level_design)
        plan = service.create_plan(
            difficulty=DifficultyMode.NORMAL,
            total_levels=5,
            theme="goblin_warren",
            story_outline=[],
            boss_chain=[],
            key_items=[]
        )
        assert plan.difficulty == DifficultyMode.NORMAL
        assert plan.total_levels == 5
        assert plan.theme == "goblin_warren"

    def test_get_scaling_factor(self):
        """Test scaling factor retrieval."""
        mock_level_design = MagicMock()
        service = DungeonMasterService(level_design_service=mock_level_design)
        assert service.get_scaling_factor(DifficultyMode.STORY) == 0.5
        assert service.get_scaling_factor(DifficultyMode.NORMAL) == 1.0
        assert service.get_scaling_factor(DifficultyMode.HARD) == 1.5
        assert service.get_scaling_factor(DifficultyMode.NIGHTMARE) == 2.0
        assert service.get_scaling_factor(DifficultyMode.IRONMAN) == 3.0

    def test_get_loot_modifier(self):
        """Test loot modifier retrieval."""
        mock_level_design = MagicMock()
        service = DungeonMasterService(level_design_service=mock_level_design)
        assert service.get_loot_modifier(DifficultyMode.STORY) == 1.5
        assert service.get_loot_modifier(DifficultyMode.NORMAL) == 1.0
        assert service.get_loot_modifier(DifficultyMode.HARD) == 0.7
        assert service.get_loot_modifier(DifficultyMode.NIGHTMARE) == 0.4
        assert service.get_loot_modifier(DifficultyMode.IRONMAN) == 0.3

    def test_generate_dungeon(self):
        """Test dungeon generation."""
        mock_level_design = MagicMock()
        mock_level_design.generate_level.return_value = {
            "width": 80, "height": 40, "rooms": [], "corridors": [],
            "mobs": [], "items": [], "traps": [], "exits": []
        }
        service = DungeonMasterService(level_design_service=mock_level_design)
        plan = service.create_plan(
            difficulty=DifficultyMode.NORMAL,
            total_levels=3,
            theme="test_dungeon",
            story_outline=[
                LevelNarrative(level_number=1, title="Level 1", description="Test"),
                LevelNarrative(level_number=2, title="Level 2", description="Test"),
                LevelNarrative(level_number=3, title="Level 3", description="Test"),
            ],
            boss_chain=[],
            key_items=[]
        )
        levels = service.generate_dungeon(plan)
        assert len(levels) == 3