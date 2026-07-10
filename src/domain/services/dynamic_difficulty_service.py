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
    monster_dv_modifier: float = 1.0       # NEW: scales monster DEFENSE VALUE
    monster_av_modifier: float = 1.0       # NEW: scales monster ARMOR VALUE
    monster_attack_modifier: float = 1.0     # NEW: scales monster ATTACK VALUE
    experience_reward_modifier: float = 1.0
    loot_quality_modifier: float = 1.0

    @classmethod
    def no_change(cls) -> 'DifficultyAdjustment':
        """Create an adjustment that maintains current difficulty."""
        return cls()   # all defaults are 1.0

    def is_significant_change(self, threshold: float = 0.1) -> bool:
        """Check if this adjustment represents a significant change from normal."""
        return (
            abs(self.spawn_rate_modifier - 1.0) > threshold or
            abs(self.monster_health_modifier - 1.0) > threshold or
            abs(self.monster_damage_modifier - 1.0) > threshold or
            abs(self.monster_dv_modifier - 1.0) > threshold or
            abs(self.monster_av_modifier - 1.0) > threshold or
            abs(self.monster_attack_modifier - 1.0) > threshold
        )

    def is_no_change(self) -> bool:
        """Check if this adjustment represents no change from normal."""
        return (self.spawn_rate_modifier == 1.0 and self.monster_health_modifier == 1.0
                and self.monster_damage_modifier == 1.0 and self.monster_dv_modifier == 1.0
                and self.monster_av_modifier == 1.0 and self.monster_attack_modifier == 1.0)


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
        Evaluate player stats using 50% of player's max stats to determine difficulty.
        
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
        
        # Calculate difficulty adjustment based on 50% of player stats
        adjustment = self._calculate_difficulty_from_stats(player_stats, current_level)

        # Update tracking
        self.last_evaluated_level = current_level

        return adjustment

    def _calculate_difficulty_from_stats(self, player_stats: Dict[str, int], current_level: int) -> DifficultyAdjustment:
        """
        Calculate difficulty adjustment based on 50% of player's max stats.
        
        Args:
            player_stats: Dictionary of player's maximum stats
            current_level: Current level the player is on
        
        Returns:
            DifficultyAdjustment object
        """
        # Calculate player's effective power level using 50% of max stats
        # This creates a baseline where monsters are scaled to half the player's potential
        base_power = player_stats.get('power_level', current_level * 10)
        
        # Calculate difficulty factor: higher player stats = easier monsters
        # Use 50% of player's stats as the target monster power level
        target_monster_power = base_power * 0.5
        
        # Normalize to a reasonable range (0.5 to 2.0 modifier)
        # Players with very low stats get harder monsters, very high stats get easier monsters
        difficulty_factor = 1.0
        if base_power > 0:
            # Scale based on power level - lower power = higher difficulty
            difficulty_factor = max(0.5, min(2.0, 50.0 / base_power))
        
        # Apply the difficulty factor to monster stats
        # Lower factor = easier monsters (less health/damage)
        # Higher factor = harder monsters (more health/damage)
        return DifficultyAdjustment(
            spawn_rate_modifier=difficulty_factor,
            monster_health_modifier=difficulty_factor,
            monster_damage_modifier=difficulty_factor,
            experience_reward_modifier=1.0 / difficulty_factor,  # More XP for easier monsters
            loot_quality_modifier=1.0 / difficulty_factor  # Better loot for easier monsters
        )

    def _get_player_max_stats(self, player_entity: 'Entity') -> Dict[str, int]:
        """Extract maximum stats from player entity."""
        stats = {}
        # FIX: no longer reference player_entity.fighter or player_entity.power.level
        stats['attack'] = getattr(player_entity, 'attack_power',
                                getattr(player_entity, 'power', 0))
        stats['level'] = getattr(player_entity, 'level', 1)
        stats['defense_value'] = getattr(player_entity, 'defense_value', 0)
        stats['power_level'] = stats['attack'] + stats['level'] * 10
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
                monster_dv_modifier=modifier,
                monster_av_modifier=modifier,
                monster_attack_modifier=modifier,
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
                monster_dv_modifier=modifier if 'difficulty_modifier' in llm_response else adjustment.monster_dv_modifier,
                monster_av_modifier=modifier if 'difficulty_modifier' in llm_response else adjustment.monster_av_modifier,
                monster_attack_modifier=modifier if 'difficulty_modifier' in llm_response else adjustment.monster_attack_modifier,
                experience_reward_modifier=adjustment.experience_reward_modifier,
                loot_quality_modifier=adjustment.loot_quality_modifier
            )

        return adjustment