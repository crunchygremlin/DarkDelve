"""Dungeon master service for orchestrating dungeon generation."""
from typing import List, Optional, Dict, Any
from ..value_objects.difficulty import (
    DungeonMasterPlan, DungeonLevel, DifficultyMode,
    LevelNarrative, BossEncounter, KeyItem
)
from ..value_objects.narrative import StoryOutline
from .level_design_service import LevelDesignService
from .content_generation_service import ContentGenerationService


__all__ = [
    "DungeonMasterService",
]


class DungeonMasterService:
    """Orchestrates level generation, difficulty scaling, and boss chain creation."""

    def __init__(
        self,
        level_design_service: Optional[LevelDesignService] = None,
        content_generation_service: Optional[ContentGenerationService] = None,  # NEW
    ):
        self.level_design_service = level_design_service or LevelDesignService()
        self.content_generation_service = content_generation_service  # NEW
        self.current_plan: Optional[DungeonMasterPlan] = None
        self.current_level: Optional[DungeonLevel] = None

    def create_plan(
        self,
        difficulty: DifficultyMode,
        total_levels: int,
        theme: str,
        story_outline: List[LevelNarrative],
        boss_chain: List[BossEncounter],
        key_items: List[KeyItem],
        player_power_target: Optional[Dict[str, float]] = None,
    ) -> DungeonMasterPlan:
        """Create a new dungeon master plan."""
        self.current_plan = DungeonMasterPlan(
            difficulty=difficulty,
            total_levels=total_levels,
            theme=theme,
            story_outline=story_outline,
            boss_chain=boss_chain,
            key_items=key_items,
            player_power_target=player_power_target or {},
        )
        return self.current_plan

    def generate_dungeon(self, plan: DungeonMasterPlan) -> List[DungeonLevel]:
        """Generate the entire dungeon based on the plan."""
        self.current_plan = plan
        levels = []

        for level_narrative in plan.story_outline:
            level = self._generate_level(level_narrative, plan.difficulty)
            levels.append(level)

        return levels

    def _generate_level(self, narrative: LevelNarrative, difficulty: DifficultyMode) -> DungeonLevel:
        """Generate a single level based on narrative and difficulty."""
        # Use existing LevelDesignService to create the level structure
        level_data = self.level_design_service.generate_level(
            level_number=narrative.level_number,
            width=80,
            height=40,
            difficulty=difficulty.value,
        )

        # Create DungeonLevel from the generated data
        level = DungeonLevel(
            level_number=narrative.level_number,
            difficulty=difficulty,
            width=level_data.get("width", 80),
            height=level_data.get("height", 40),
            rooms=level_data.get("rooms", []),
            corridors=level_data.get("corridors", []),
            mobs=level_data.get("mobs", []),
            items=level_data.get("items", []),
            traps=level_data.get("traps", []),
            exits=level_data.get("exits", []),
            narrative_id=f"narrative_{narrative.level_number}",
            hints=narrative.hints_dropped,
            required_items=narrative.required_key_items,
        )

        # NEW: Attach generated content if available
        if self.content_generation_service:
            try:
                generated = self.content_generation_service.generate_game_content(
                    item_tags=["arcane", "divine"],
                    monster_tags=["undead", "demon"],
                    level_tags=["dungeon"],
                )
                level.metadata["generated_content"] = generated
            except Exception:
                pass  # Non-fatal

        self.current_level = level
        return level

    def get_scaling_factor(self, difficulty: DifficultyMode) -> float:
        """Get the scaling factor for a given difficulty."""
        factors = {
            DifficultyMode.STORY: 0.5,
            DifficultyMode.NORMAL: 1.0,
            DifficultyMode.HARD: 1.5,
            DifficultyMode.NIGHTMARE: 2.0,
            DifficultyMode.IRONMAN: 3.0,
        }
        return factors.get(difficulty, 1.0)

    def get_loot_modifier(self, difficulty: DifficultyMode) -> float:
        """Get the loot modifier for a given difficulty."""
        modifiers = {
            DifficultyMode.STORY: 1.5,    # More loot
            DifficultyMode.NORMAL: 1.0,
            DifficultyMode.HARD: 0.7,     # Less loot
            DifficultyMode.NIGHTMARE: 0.4,
            DifficultyMode.IRONMAN: 0.3,
        }
        return modifiers.get(difficulty, 1.0)

    def get_plan(self) -> Optional[DungeonMasterPlan]:
        """Get the current plan."""
        return self.current_plan

    def get_level(self) -> Optional[DungeonLevel]:
        """Get the current level."""
        return self.current_level

    def apply_difficulty_adjustment(
        self,
        base_monster_count: int,
        adjustment: Any
    ) -> int:
        """Apply difficulty adjustment to monster count.

        Args:
            base_monster_count: The base number of monsters to spawn
            adjustment: DifficultyAdjustment object with spawn_rate_modifier

        Returns:
            Adjusted monster count
        """
        if adjustment is None:
            return base_monster_count
        modifier = getattr(adjustment, 'spawn_rate_modifier', 1.0)
        return max(1, int(base_monster_count * modifier))

    def apply_monster_health_adjustment(
        self,
        base_health: int,
        adjustment: Any
    ) -> int:
        """Apply difficulty adjustment to monster health.

        Args:
            base_health: The base health value
            adjustment: DifficultyAdjustment object with monster_health_modifier

        Returns:
            Adjusted health value
        """
        if adjustment is None:
            return base_health
        modifier = getattr(adjustment, 'monster_health_modifier', 1.0)
        return max(1, int(base_health * modifier))

    def apply_monster_damage_adjustment(
        self,
        base_damage: int,
        adjustment: Any
    ) -> int:
        """Apply difficulty adjustment to monster damage.

        Args:
            base_damage: The base damage value
            adjustment: DifficultyAdjustment object with monster_damage_modifier

        Returns:
            Adjusted damage value
        """
        if adjustment is None:
            return base_damage
        modifier = getattr(adjustment, 'monster_damage_modifier', 1.0)
        return max(1, int(base_damage * modifier))