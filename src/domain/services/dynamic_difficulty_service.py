"""Dynamic difficulty adjustment service for evaluating player stats and adjusting monster generation."""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from src.domain.services.dungeon_master_service import DungeonMasterService
from src.application.services.llm_worker import LLMWorker
from src.domain.services.player_profile_service import PlayerProfileService
from src.domain.entities.entity import Entity


@dataclass(frozen=True)
class DifficultyAdjustment:
    """Represents adjustments to difficulty parameters."""
    spawn_rate_modifier: float = 1.0
    monster_health_modifier: float = 1.0
    monster_damage_modifier: float = 1.0
    experience_reward_modifier: float = 1.0
    loot_quality_modifier: float = 1.0

    @classmethod
    def no_change(cls) -> 'DifficultyAdjustment':
        """Create an adjustment that maintains current difficulty."""
        return cls(
            spawn_rate_modifier=1.0,
            monster_health_modifier=1.0,
            monster_damage_modifier=1.0,
            experience_reward_modifier=1.0,
            loot_quality_modifier=1.0
        )

    def is_significant_change(self, threshold: float = 0.1) -> bool:
        """Check if this adjustment represents a significant change from normal."""
        return (
            abs(self.spawn_rate_modifier - 1.0) > threshold or
            abs(self.monster_health_modifier - 1.0) > threshold or
            abs(self.monster_damage_modifier - 1.0) > threshold
        )

    def is_no_change(self) -> bool:
        """Check if this adjustment represents no change from normal."""
        return (
            self.spawn_rate_modifier == 1.0 and
            self.monster_health_modifier == 1.0 and
            self.monster_damage_modifier == 1.0
        )


class DynamicDifficultyService:
    """Service for dynamically adjusting difficulty based on player stats and DM LLM evaluation."""

    def __init__(
        self,
        dungeon_master_service: 'DungeonMasterService',
        llm_worker: 'LLMWorker',
        player_profile_service: 'PlayerProfileService'
    ):
        self.dungeon_master_service = dungeon_master_service
        self.llm_worker = llm_worker
        self.player_profile_service = player_profile_service
        self.last_evaluated_level = 0

    def evaluate_and_adjust_difficulty(
        self,
        player_entity: 'Entity',
        current_level: int
    ) -> DifficultyAdjustment:
        """
        Evaluate player stats using DM LLM and return difficulty adjustment.

        Args:
            player_entity: The player entity to evaluate
            current_level: The current level the player is on

        Returns:
            DifficultyAdjustment object containing recommended changes
        """
        # Check if we need to evaluate (level change)
        if current_level <= self.last_evaluated_level:
            return DifficultyAdjustment.no_change()

        # Get player's max stats
        player_stats = self._get_player_max_stats(player_entity)

        # Request evaluation from DM LLM
        llm_response = self.llm_worker.evaluate_player_stats(
            player_stats=player_stats,
            current_level=current_level
        )

        # Parse LLM response into difficulty adjustment
        adjustment = self._parse_llm_response(llm_response)

        # Update tracking
        self.last_evaluated_level = current_level

        return adjustment

    def _get_player_max_stats(self, player_entity: 'Entity') -> Dict[str, int]:
        """Extract maximum stats from player entity."""
        stats = {}
        # Get base stats from player components
        if hasattr(player_entity, 'fighter'):
            stats['health'] = player_entity.fighter.max_hp
            stats['attack'] = player_entity.fighter.power
            stats['defense'] = player_entity.fighter.defense
        if hasattr(player_entity, 'power'):
            stats['power_level'] = player_entity.power.level
        return stats

    def _parse_llm_response(self, llm_response: Dict[str, Any]) -> DifficultyAdjustment:
        """Parse LLM response into difficulty adjustment."""
        # Default to no change
        adjustment = DifficultyAdjustment.no_change()

        # Extract adjustment factors from LLM response
        if 'difficulty_modifier' in llm_response:
            modifier = llm_response['difficulty_modifier']
            adjustment = DifficultyAdjustment(
                spawn_rate_modifier=modifier,
                monster_health_modifier=modifier,
                monster_damage_modifier=modifier,
                experience_reward_modifier=adjustment.experience_reward_modifier,
                loot_quality_modifier=adjustment.loot_quality_modifier
            )

        if 'specific_adjustments' in llm_response:
            adjustments = llm_response['specific_adjustments']
            spawn_rate = adjustments.get('spawn_rate', adjustment.spawn_rate_modifier)
            monster_health = adjustments.get('monster_health', adjustment.monster_health_modifier)
            monster_damage = adjustments.get('monster_damage', adjustment.monster_damage_modifier)
            adjustment = DifficultyAdjustment(
                spawn_rate_modifier=spawn_rate,
                monster_health_modifier=monster_health,
                monster_damage_modifier=monster_damage,
                experience_reward_modifier=adjustment.experience_reward_modifier,
                loot_quality_modifier=adjustment.loot_quality_modifier
            )

        return adjustment