"""
Combat query for combat-related information.
"""
from typing import Optional, Dict, Any, List, Tuple
from .base_query import BaseQuery, QueryResult
from ...domain.entities.player import Player
from ...domain.entities.mob import Mob
from ...domain.value_objects.position import Position


class CombatQuery(BaseQuery):
    """
    Query for combat-related information.
    
    Implements the Query pattern for combat calculations and information.
    """
    
    def __init__(self, player: Player):
        """
        Initialize the combat query.
        
        Args:
            player: The player entity for combat calculations
        """
        super().__init__("combat")
        self.player = player
    
    def execute(self, *args, **kwargs) -> QueryResult:
        """
        Execute the combat query.
        
        Args:
            *args: Additional arguments (target entity)
            **kwargs: Additional keyword arguments (not used)
            
        Returns:
            QueryResult: The result of the combat query
        """
        # Check cache first
        cached_result = self.get_cached_result(*args, **kwargs)
        if cached_result:
            return cached_result
        
        target = args[0] if args else None
        
        try:
            if target:
                # Combat information for a specific target
                result = self.get_combat_info(target)
            else:
                # General combat information
                result = self.get_general_combat_info()
            
            self.cache_result(result)
            return result
            
        except Exception as e:
            return QueryResult(
                success=False,
                error_message=f"Failed to execute combat query: {str(e)}"
            )
    
    def get_combat_info(self, target: Mob) -> QueryResult:
        """
        Get combat information for a specific target.
        
        Args:
            target: The target entity
            
        Returns:
            QueryResult: Combat information for the target
        """
        # Calculate combat statistics
        distance = Position(self.player.x, self.player.y).distance_to(Position(target.x, target.y))
        can_attack = distance <= 5  # Assuming 5 tile attack range
        
        # Calculate expected damage
        expected_damage = self.calculate_expected_damage(target)
        
        # Calculate win probability
        win_probability = self.calculate_win_probability(target)
        
        return QueryResult(
            success=True,
            data={
                "target_id": target.id,
                "target_name": target.name,
                "target_health": target.health,
                "target_max_health": target.max_health,
                "distance": distance,
                "can_attack": can_attack,
                "expected_damage": expected_damage,
                "win_probability": win_probability
            },
            metadata={
                "target_attack_power": target.attack_power,
                "target_defense": target.defense,
                "player_attack_power": self.player.attack_power,
                "player_defense": self.player.defense
            }
        )
    
    def get_general_combat_info(self) -> QueryResult:
        """
        Get general combat information.
        
        Returns:
            QueryResult: General combat information
        """
        return QueryResult(
            success=True,
            data={
                "player_health": self.player.health,
                "player_max_health": self.player.max_health,
                "player_attack_power": self.player.attack_power,
                "player_defense": self.player.defense,
                "player_level": self.player.level
            },
            metadata={
                "combat_ready": self.player.health > 0,
                "is_alive": self.player.is_alive()
            }
        )
    
    def calculate_expected_damage(self, target: Mob) -> int:
        """
        Calculate expected damage against a target.
        
        Args:
            target: The target entity
            
        Returns:
            int: Expected damage
        """
        # Simple damage calculation
        base_damage = self.player.attack_power
        target_defense = target.defense
        
        # Apply defense reduction
        damage = max(1, base_damage - target_defense // 2)
        
        # Add some randomness (±25%)
        import random
        damage = int(damage * (0.75 + random.random() * 0.5))
        
        return damage
    
    def calculate_win_probability(self, target: Mob) -> float:
        """
        Calculate win probability against a target.
        
        Args:
            target: The target entity
            
        Returns:
            float: Win probability (0.0 to 1.0)
        """
        # Simple win probability calculation
        player_power = self.player.attack_power + self.player.defense
        target_power = target.attack_power + target.defense
        
        # Account for health difference
        player_health_ratio = self.player.health / self.player.max_health
        target_health_ratio = target.health / target.max_health
        
        # Calculate probability
        power_ratio = player_power / (player_power + target_power)
        health_factor = (player_health_ratio + target_health_ratio) / 2
        
        win_probability = (power_ratio * 0.7 + health_factor * 0.3)
        
        return max(0.0, min(1.0, win_probability))
    
    def get_attackable_targets(self, mobs: List[Mob]) -> List[Mob]:
        """
        Get all mobs within attack range.
        
        Args:
            mobs: List of mobs to check
            
        Returns:
            List[Mob]: List of attackable mobs
        """
        attackable = []
        for mob in mobs:
            distance = Position(self.player.x, self.player.y).distance_to(Position(mob.x, mob.y))
            if distance <= 5:  # Assuming 5 tile attack range
                attackable.append(mob)
        
        return attackable
    
    def get_combat_log(self, combat_events: List[Dict]) -> QueryResult:
        """
        Get combat log information.
        
        Args:
            combat_events: List of combat events
            
        Returns:
            QueryResult: Combat log information
        """
        return QueryResult(
            success=True,
            data=combat_events,
            metadata={
                "event_count": len(combat_events),
                "player_events": [e for e in combat_events if e.get("player_id") == self.player.id],
                "target_events": [e for e in combat_events if e.get("target_id") != self.player.id]
            }
        )