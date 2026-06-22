"""Tests for difficulty and dungeon level control value objects."""
import pytest
from src.domain.value_objects.difficulty import (
    DifficultyMode, Room, MobSpawn, ItemSpawn, DungeonLevel,
    LevelNarrative, BossEncounter, KeyItem, DungeonMasterPlan
)
from src.domain.value_objects.position import Position


class TestDifficultyMode:
    """Tests for DifficultyMode enum."""

    def test_difficulty_mode_values(self):
        """Test that all difficulty modes have correct values."""
        assert DifficultyMode.STORY.value == "story"
        assert DifficultyMode.NORMAL.value == "normal"
        assert DifficultyMode.HARD.value == "hard"
        assert DifficultyMode.NIGHTMARE.value == "nightmare"
        assert DifficultyMode.IRONMAN.value == "ironman"


class TestRoom:
    """Tests for Room dataclass."""

    def test_room_creation(self):
        """Test creating a room with all fields."""
        room = Room(
            x=10, y=20, width=5, height=7,
            room_type="treasure",
            connected_rooms=[1, 2, 3]
        )
        assert room.x == 10
        assert room.y == 20
        assert room.width == 5
        assert room.height == 7
        assert room.room_type == "treasure"
        assert room.connected_rooms == [1, 2, 3]
        assert room.description == ""

    def test_room_with_description(self):
        """Test creating a room with description."""
        room = Room(
            x=0, y=0, width=3, height=3,
            room_type="normal",
            connected_rooms=[],
            description="A small starting room"
        )
        assert room.description == "A small starting room"


class TestMobSpawn:
    """Tests for MobSpawn dataclass."""

    def test_mob_spawn_creation(self):
        """Test creating a mob spawn."""
        position = Position(5, 10)
        spawn = MobSpawn(
            mob_type="goblin",
            position=position,
            social_structure_hint="goblin_kingdom"
        )
        assert spawn.mob_type == "goblin"
        assert spawn.position == position
        assert spawn.social_structure_hint == "goblin_kingdom"
        assert spawn.behavior_override is None


class TestItemSpawn:
    """Tests for ItemSpawn dataclass."""

    def test_item_spawn_ground(self):
        """Test creating a ground item spawn."""
        position = Position(3, 4)
        spawn = ItemSpawn(
            item_id="sword_001",
            position=position,
            is_ground=True
        )
        assert spawn.item_id == "sword_001"
        assert spawn.is_ground is True
        assert spawn.container_id is None
        assert spawn.is_trash is False

    def test_item_spawn_container(self):
        """Test creating a container item spawn."""
        position = Position(7, 8)
        spawn = ItemSpawn(
            item_id="potion_001",
            position=position,
            is_ground=False,
            container_id="chest_001",
            is_trash=True
        )
        assert spawn.is_ground is False
        assert spawn.container_id == "chest_001"
        assert spawn.is_trash is True


class TestDungeonMasterPlan:
    """Tests for DungeonMasterPlan dataclass."""

    def test_plan_creation(self):
        """Test creating a dungeon master plan."""
        plan = DungeonMasterPlan(
            difficulty=DifficultyMode.NORMAL,
            total_levels=5,
            theme="goblin_warren",
            story_outline=[],
            boss_chain=[],
            key_items=[],
            player_power_target={"melee": 10.0, "ranged": 8.0}
        )
        assert plan.difficulty == DifficultyMode.NORMAL
        assert plan.total_levels == 5
        assert plan.theme == "goblin_warren"
        assert plan.player_power_target["melee"] == 10.0