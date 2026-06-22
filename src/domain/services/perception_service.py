"""Perception service for computing entity perception status."""

import math
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass

from src.domain.value_objects.perception import (
    PerceptionStatus, PerceptionModifiers, PerceptionSense
)
from src.domain.value_objects.position import Position


__all__ = ["PerceptionService"]


# Default PerceptionModifiers for mob types
DEFAULT_MOB_MODIFIERS: Dict[str, PerceptionModifiers] = {
    "goblin": PerceptionModifiers(
        entity_type="goblin",
        sight_range=6,
        hearing_range=14,
        noise_sensitivity=1.3,
        darkness_penalty=0.6
    ),
    "goblin_king": PerceptionModifiers(
        entity_type="goblin_king",
        sight_range=8,
        hearing_range=12,
        noise_sensitivity=1.0
    ),
    "wolf": PerceptionModifiers(
        entity_type="wolf",
        sight_range=8,
        hearing_range=18,
        smell_range=12,
        noise_sensitivity=1.5
    ),
    "spider": PerceptionModifiers(
        entity_type="spider",
        sight_range=4,
        hearing_range=6,
        vibration_range=10,
        ignore_walls_vibration=True
    ),
    "bat": PerceptionModifiers(
        entity_type="bat",
        sight_range=2,
        echolocation_range=14,
        darkvision=True
    ),
    "mercenary": PerceptionModifiers(
        entity_type="mercenary",
        sight_range=10,
        hearing_range=10,
        noise_sensitivity=1.0
    ),
    "undead": PerceptionModifiers(
        entity_type="undead",
        sight_range=8,
        hearing_range=4,
        magic_sense_range=8
    ),
    "lich": PerceptionModifiers(
        entity_type="lich",
        sight_range=12,
        hearing_range=8,
        magic_sense_range=15,
        see_invisible=True
    ),
    "default": PerceptionModifiers(
        entity_type="default",
        sight_range=8,
        hearing_range=8
    ),
}


class PerceptionService:
    """
    Service for computing PerceptionStatus for entities based on game world state.
    
    This service uses the FOV query for line-of-sight checks and computes
    perception based on entity type-specific modifiers.
    """
    
    def __init__(
        self,
        fov_query: Any,
        entity_repository: Any,
        item_repository: Any
    ):
        """
        Initialize the PerceptionService.
        
        Args:
            fov_query: Query object for computing field of view
            entity_repository: Repository for entity data access
            item_repository: Repository for item data access
        """
        self._fov_query = fov_query
        self._entity_repository = entity_repository
        self._item_repository = item_repository
        self._mob_modifiers = DEFAULT_MOB_MODIFIERS.copy()
    
    def compute_perception(
        self,
        entity: Any,
        all_entities: List[Any],
        items: List[Any],
        game_map: Any
    ) -> PerceptionStatus:
        """
        Compute PerceptionStatus for an entity based on game world state.
        
        Args:
            entity: The entity to compute perception for
            all_entities: List of all entities in the game
            items: List of all items in the game
            game_map: The game map object
            
        Returns:
            PerceptionStatus: The computed perception status
        """
        # Get modifiers for this entity's type
        mob_type = getattr(entity, 'mob_type', 'default')
        modifiers = self.get_perception_for_mob_type(mob_type)
        
        # Get entity position
        entity_pos = getattr(entity, 'position', Position(0, 0))
        
        # Compute player position and visibility
        player_pos = None
        player_entity = None
        for e in all_entities:
            if hasattr(e, 'player') or (hasattr(e, 'stats') and not hasattr(e, 'mob_type')):
                player_pos = getattr(e, 'position', Position(0, 0))
                player_entity = e
                break
        
        # Compute sight, hearing, smell, vibration for player
        can_see_player = False
        can_hear_player = False
        can_smell_player = False
        player_distance = -1.0
        player_noise = 0.0
        
        if player_pos:
            player_distance = entity_pos.distance_to(player_pos)
            player_noise = self._estimate_noise_level(entity, all_entities)
            
            can_see_player, _ = self._compute_sight(entity, player_pos, modifiers, game_map)
            can_hear_player, _ = self._compute_hearing(entity, player_pos, modifiers, player_noise)
            can_smell_player, _ = self._compute_smell(entity, player_pos, modifiers)
        
        # Get visible entities and items
        visible_threats = self._get_visible_entities(entity, all_entities, modifiers, game_map)
        visible_items = self._get_visible_items(entity, items, modifiers, game_map)
        
        # Get light level
        light_level = self._get_light_level(entity, game_map)
        
        # Determine environment danger
        environment_danger = self._compute_environment_danger(visible_threats, all_entities)
        
        # Get ally health status
        ally_health = self._compute_ally_health_status(entity, visible_threats, all_entities)
        
        return PerceptionStatus(
            entity_id=entity.id,
            can_see_player=can_see_player,
            can_hear_player=can_hear_player,
            can_smell_player=can_smell_player,
            player_last_known_position=player_pos,
            player_noise_level=player_noise,
            player_distance_estimate=player_distance,
            visible_threats=visible_threats,
            visible_items=visible_items,
            visible_allies=[],
            visible_enemies=visible_threats,
            environment_danger=environment_danger,
            light_level=light_level,
            nearby_traps=0,
            nearby_exits=0,
            combat_occurring_nearby=False,
            ally_health_status=ally_health,
            time_since_player_seen=-1.0,
            custom_flags={"mob_type": mob_type}
        )
    
    def _compute_sight(
        self,
        entity: Any,
        target_pos: Position,
        modifiers: PerceptionModifiers,
        game_map: Any
    ) -> Tuple[bool, float]:
        """
        Compute sight perception between entity and target position.
        
        Args:
            entity: The entity with perception
            target_pos: Target position to check
            modifiers: Perception modifiers for the entity
            game_map: The game map
            
        Returns:
            Tuple[bool, float]: (can_see, distance)
        """
        entity_pos = getattr(entity, 'position', Position(0, 0))
        distance = entity_pos.distance_to(target_pos)
        
        # Check if within sight range
        if distance > modifiers.sight_range:
            return False, distance
        
        # Check line of sight using FOV query
        if self._fov_query:
            try:
                fov_result = self._fov_query.execute(radius=int(modifiers.sight_range))
                if fov_result.success:
                    visible_positions = fov_result.data
                    target_tuple = (target_pos.x, target_pos.y)
                    if target_tuple in visible_positions:
                        return True, distance
            except Exception:
                pass
        
        # Fallback: simple distance check
        return distance <= modifiers.sight_range, distance
    
    def _compute_hearing(
        self,
        entity: Any,
        target_pos: Position,
        modifiers: PerceptionModifiers,
        noise_level: float
    ) -> Tuple[bool, float]:
        """
        Compute hearing perception between entity and target position.
        
        Args:
            entity: The entity with perception
            target_pos: Target position to check
            modifiers: Perception modifiers for the entity
            noise_level: Estimated noise level of the target
            
        Returns:
            Tuple[bool, float]: (can_hear, distance)
        """
        entity_pos = getattr(entity, 'position', Position(0, 0))
        distance = entity_pos.distance_to(target_pos)
        
        # Apply noise sensitivity
        effective_noise = noise_level * modifiers.noise_sensitivity
        
        # Check if within hearing range and noise is detectable
        if distance > modifiers.hearing_range:
            return False, distance
        
        # Hearing effectiveness decreases with distance
        hearing_factor = max(0.0, 1.0 - (distance / modifiers.hearing_range))
        
        return effective_noise * hearing_factor > 0.1, distance
    
    def _compute_smell(
        self,
        entity: Any,
        target_pos: Position,
        modifiers: PerceptionModifiers
    ) -> Tuple[bool, float]:
        """
        Compute smell perception between entity and target position.
        
        Args:
            entity: The entity with perception
            target_pos: Target position to check
            modifiers: Perception modifiers for the entity
            
        Returns:
            Tuple[bool, float]: (can_smell, distance)
        """
        entity_pos = getattr(entity, 'position', Position(0, 0))
        distance = entity_pos.distance_to(target_pos)
        
        # Check if within smell range
        if distance > modifiers.smell_range:
            return False, distance
        
        # Smell is effective up close
        smell_factor = max(0.0, 1.0 - (distance / modifiers.smell_range))
        
        return smell_factor > 0.2, distance
    
    def _compute_vibration(
        self,
        entity: Any,
        target_pos: Position,
        modifiers: PerceptionModifiers
    ) -> Tuple[bool, float]:
        """
        Compute vibration perception between entity and target position.
        
        Args:
            entity: The entity with perception
            target_pos: Target position to check
            modifiers: Perception modifiers for the entity
            
        Returns:
            Tuple[bool, float]: (can_feel, distance)
        """
        entity_pos = getattr(entity, 'position', Position(0, 0))
        distance = entity_pos.distance_to(target_pos)
        
        # Check if within vibration range (and vibration_range > 0)
        if modifiers.vibration_range <= 0 or distance > modifiers.vibration_range:
            return False, distance
        
        # Vibration is felt through walls if ignore_walls_vibration
        vibration_factor = max(0.0, 1.0 - (distance / modifiers.vibration_range))
        
        return vibration_factor > 0.2, distance
    
    def _get_visible_entities(
        self,
        entity: Any,
        entities: List[Any],
        modifiers: PerceptionModifiers,
        game_map: Any
    ) -> List[str]:
        """
        Get list of visible entity IDs for an entity.
        
        Args:
            entity: The entity to check visibility for
            entities: List of all entities
            modifiers: Perception modifiers
            game_map: The game map
            
        Returns:
            List[str]: List of visible entity IDs
        """
        visible_ids = []
        entity_pos = getattr(entity, 'position', Position(0, 0))
        
        for other in entities:
            if other.id == entity.id:
                continue
            
            other_pos = getattr(other, 'position', None)
            if not other_pos:
                continue
            
            # Check if within sight range
            distance = entity_pos.distance_to(other_pos)
            if distance > modifiers.sight_range:
                continue
            
            # Check line of sight
            can_see, _ = self._compute_sight(entity, other_pos, modifiers, game_map)
            if can_see:
                visible_ids.append(other.id)
        
        return visible_ids
    
    def _get_visible_items(
        self,
        entity: Any,
        items: List[Any],
        modifiers: PerceptionModifiers,
        game_map: Any
    ) -> List[str]:
        """
        Get list of visible item IDs for an entity.
        
        Args:
            entity: The entity to check visibility for
            items: List of all items
            modifiers: Perception modifiers
            game_map: The game map
            
        Returns:
            List[str]: List of visible item IDs
        """
        visible_ids = []
        entity_pos = getattr(entity, 'position', Position(0, 0))
        
        for item in items:
            item_pos = getattr(item, 'position', None)
            if not item_pos:
                continue
            
            # Check if within sight range
            distance = entity_pos.distance_to(item_pos)
            if distance > modifiers.sight_range:
                continue
            
            # Check line of sight
            can_see, _ = self._compute_sight(entity, item_pos, modifiers, game_map)
            if can_see:
                visible_ids.append(item.id)
        
        return visible_ids
    
    def _estimate_noise_level(
        self,
        entity: Any,
        all_entities: List[Any]
    ) -> float:
        """
        Estimate noise level based on entity movement and combat.
        
        Args:
            entity: The entity to estimate noise for
            all_entities: List of all entities
            
        Returns:
            float: Noise level (0.0 to 1.0)
        """
        # Base noise level
        noise = 0.0
        
        # Check for combat nearby
        for other in all_entities:
            if other.id == entity.id:
                continue
            
            other_pos = getattr(other, 'position', None)
            entity_pos = getattr(entity, 'position', Position(0, 0))
            
            if other_pos:
                distance = entity_pos.distance_to(other_pos)
                if distance < 10:
                    # Check if in combat
                    if hasattr(other, 'combat') and other.combat.is_in_combat():
                        noise += 0.3 * (1.0 - distance / 10.0)
        
        return min(1.0, noise)
    
    def _get_light_level(
        self,
        entity: Any,
        game_map: Any
    ) -> float:
        """
        Get the light level at an entity's position.
        
        Args:
            entity: The entity to check light for
            game_map: The game map
            
        Returns:
            float: Light level (0.0 to 1.0)
        """
        if not game_map:
            return 1.0
        
        entity_pos = getattr(entity, 'position', Position(0, 0))
        
        # Try to get light from map
        if hasattr(game_map, 'get_light_level'):
            try:
                return game_map.get_light_level(entity_pos.x, entity_pos.y)
            except Exception:
                pass
        
        # Default light level
        return 1.0
    
    def get_perception_for_mob_type(self, mob_type: str) -> PerceptionModifiers:
        """
        Get default perception modifiers for a mob type.
        
        Args:
            mob_type: The mob type string
            
        Returns:
            PerceptionModifiers: The modifiers for the mob type
        """
        return self._mob_modifiers.get(mob_type, self._mob_modifiers["default"])
    
    def _compute_environment_danger(
        self,
        visible_threats: List[str],
        all_entities: List[Any]
    ) -> float:
        """
        Compute environment danger level based on visible threats.
        
        Args:
            visible_threats: List of visible threat entity IDs
            all_entities: List of all entities
            
        Returns:
            float: Danger level (0.0 to 1.0)
        """
        if not visible_threats:
            return 0.0
        
        # Count visible threats
        return min(1.0, len(visible_threats) * 0.2)
    
    def _compute_ally_health_status(
        self,
        entity: Any,
        visible_threats: List[str],
        all_entities: List[Any]
    ) -> str:
        """
        Compute ally health status.
        
        Args:
            entity: The entity to check
            visible_threats: List of visible threat entity IDs
            all_entities: List of all entities
            
        Returns:
            str: Health status ("healthy", "wounded", "critical", "unknown")
        """
        # For now, return unknown as this would require more complex logic
        return "unknown"