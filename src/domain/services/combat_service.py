"""
Combat service for handling combat-related operations.
"""
import random
from typing import List, Dict, Any, Optional, Tuple
from ..entities.player import Player
from ..entities.mob import Mob
from ..components.combat import Combat
from ..value_objects.combat_event import CombatEvent, CombatEventType
from ..value_objects.stats import Stats
from src.shared.interfaces.service import ICombatService
from src.domain.value_objects.combat_config import COMBAT_CONFIG
from src.shared.utils.dice import parse_dice


def _reflex_mod(entity) -> int:
    stats = getattr(entity, 'stats', None)
    if stats is None:
        return 0
    if hasattr(stats, 'get_modifier'):
        return stats.get_modifier('dexterity')
    return (stats.get('dex', 10) - 10) // 2


class CombatService(ICombatService):
    """
    Service for handling combat operations and calculations.
    
    Implements the Service pattern for combat management.
    Implements ICombatService interface for dependency inversion.
    """
    
    def __init__(self):
        """Initialize the combat service."""
        self.combat_events: List[CombatEvent] = []
        self.active_combats: Dict[str, Dict[str, Any]] = {}
    
    def initiate_combat(self, attacker: Player, target: Mob) -> bool:
        """
        Initiate combat between a player and a mob.
        
        Args:
            attacker: The player initiating combat
            target: The mob being attacked
            
        Returns:
            bool: True if combat was initiated, False otherwise
        """
        if not self.can_attack(attacker, target):
            return False
        
        # Create combat instance
        combat_id = f"{attacker.id}_{target.id}"
        self.active_combats[combat_id] = {
            "attacker": attacker,
            "target": target,
            "turn": 0,
            "started": True,
            "ended": False
        }
        
        # Add combat event
        event = CombatEvent(
            event_type=CombatEventType.COMBAT_START,
            attacker_id=attacker.id,
            target_id=target.id,
            damage=0,
            message=f"{attacker.name} attacks {target.name}!"
        )
        self.combat_events.append(event)
        
        return True
    
    def execute_attack(self, attacker: Player, target: Mob, weapon_dice: str = "1d6") -> Dict[str, Any]:
        """
        Execute an attack from attacker to target.
        
        Args:
            attacker: The entity attacking
            target: The entity being attacked
            weapon_dice: Dice notation for weapon damage (default "1d6")
            
        Returns:
            Dict[str, Any]: Attack result information
        """
        if not self.can_attack(attacker, target):
            return {
                "success": False,
                "message": "Cannot attack target",
                "damage": 0,
                "hit": False,
                "critical": False
            }
        
        # Calculate attack roll (stores self._last_d10 for the crit check)
        attack_roll = self.calculate_attack_roll(attacker)
        # Calculate DEFENSE VALUE (renamed from calculate_defense_roll; update caller @ :85)
        defense_value = self.calculate_defense_value(target)
        
        # Hit test: use >= to match darkdelve.resolve_attack (was >)
        hit = attack_roll >= defense_value
        
        if hit:
            # Damage (weapon dice parsed inside; crit doubling done below)
            damage = self.calculate_damage(attacker, target, weapon_dice)
            # Critical determined from the SAME d10 used for the attack roll (caller unchanged)
            critical = self.is_critical_hit(attacker)
            if critical:
                damage *= 2
            
            # Apply damage
            target.health -= damage
            
            # Create combat event
            event_type = CombatEventType.CRITICAL_HIT if critical else CombatEventType.HIT
            event = CombatEvent(
                event_type=event_type,
                attacker_id=attacker.id,
                target_id=target.id,
                damage=damage,
                message=f"{attacker.name} hits {target.name} for {damage} damage{' (critical!)' if critical else ''}"
            )
            self.combat_events.append(event)
            
            # Check if target is defeated
            if target.health <= 0:
                self.handle_defeat(attacker, target)
            
            return {
                "success": True,
                "message": f"Attack hits for {damage} damage",
                "damage": damage,
                "hit": True,
                "critical": critical,
                "target_health": target.health
            }
        else:
            # Miss
            event = CombatEvent(
                event_type=CombatEventType.MISS,
                attacker_id=attacker.id,
                target_id=target.id,
                damage=0,
                message=f"{attacker.name} misses {target.name}"
            )
            self.combat_events.append(event)
            
            return {
                "success": True,
                "message": "Attack misses",
                "damage": 0,
                "hit": False,
                "critical": False,
                "target_health": target.health
            }
    
    def can_attack(self, attacker: Player, target: Mob) -> bool:
        """
        Check if an attacker can attack a target.
        
        Args:
            attacker: The entity attempting to attack
            target: The entity being targeted
            
        Returns:
            bool: True if attack is possible, False otherwise
        """
        # Check if target is alive
        if not target.is_alive():
            return False
        
        # Check if attacker is alive
        if not attacker.is_alive():
            return False
        
        # Check range (simplified - assumes adjacent)
        distance = attacker.position.distance_to(target.position)
        if distance > 1:
            return False
        
        return True
    
    def calculate_attack_roll(self, attacker) -> int:
        """
        Calculate attack roll for an attacker.
        
        Args:
            attacker: The entity attacking
            
        Returns:
            int: Attack roll value
        """
        d10 = random.randint(1, COMBAT_CONFIG.DIE_SIDES)
        self._last_d10 = d10                      # stored so crit uses the SAME d10
        base = getattr(attacker, 'attack_power', getattr(attacker, 'power', 0)) // 2
        return d10 + _reflex_mod(attacker) + base + attacker.get_equipped_attack_bonus()

    def calculate_defense_value(self, target) -> int:   # RENAMED from calculate_defense_roll
        """
        Calculate defense value for a target.
        
        Args:
            target: The entity defending
            
        Returns:
            int: Defense value
        """
        comp_def = int(target.defense * COMBAT_CONFIG.DEFENSE_COMPRESSION)
        return COMBAT_CONFIG.BASE_DV + _reflex_mod(target) + comp_def + getattr(target, 'dodge_bonus', 0)

    def calculate_damage(self, attacker, target, weapon_dice: str = "1d6") -> int:
        """
        Calculate damage for an attack.
        
        Args:
            attacker: The entity attacking
            target: The entity being attacked
            weapon_dice: Dice notation for weapon damage
            
        Returns:
            int: Damage amount
        """
        num, size, mod = parse_dice(weapon_dice)
        base = sum(random.randint(1, size) for _ in range(num)) + mod
        base += getattr(attacker, 'attack_power', getattr(attacker, 'power', 0)) // 2
        base += attacker.get_equipped_damage_bonus()
        av = target.get_equipped_defense_bonus()        # Armor Value
        return max(COMBAT_CONFIG.MIN_DMG, base - av)    # NOTE: no crit doubling here

    def is_critical_hit(self, attacker) -> bool:        # KEEP attacker param (caller @ :95 unchanged)
        """
        Check if an attack is a critical hit.
        
        Args:
            attacker: The entity attacking
            
        Returns:
            bool: True if critical hit, False otherwise
        """
        from src.domain.value_objects.combat_config import COMBAT_CONFIG
        return getattr(self, '_last_d10', 0) == COMBAT_CONFIG.DIE_SIDES
    
    def handle_defeat(self, attacker: Player, target: Mob) -> None:
        """
        Handle defeat of a target.
        
        Args:
            attacker: The entity that defeated the target
            target: The entity that was defeated
        """
        # Create defeat event
        event = CombatEvent(
            event_type=CombatEventType.DEFEAT,
            attacker_id=attacker.id,
            target_id=target.id,
            damage=0,
            message=f"{target.name} is defeated by {attacker.name}!"
        )
        self.combat_events.append(event)
        
        # Award experience
        experience_gained = target.calculate_experience_reward()
        attacker.gain_experience(experience_gained)
        
        # Handle loot
        self.handle_loot(attacker, target)
        
        # Remove from active combats
        combat_id = f"{attacker.id}_{target.id}"
        if combat_id in self.active_combats:
            self.active_combats[combat_id]["ended"] = True
    
    def handle_loot(self, attacker: Player, target: Mob) -> None:
        """
        Handle loot from defeated target.
        
        Args:
            attacker: The entity collecting loot
            target: The entity that was defeated
        """
        # Get loot from target
        loot_items = target.get_loot()
        
        # Add items to attacker's inventory
        for item in loot_items:
            attacker.add_item_to_inventory(item)
        
        # Create loot event
        event = CombatEvent(
            event_type=CombatEventType.LOOT,
            attacker_id=attacker.id,
            target_id=target.id,
            damage=0,
            message=f"{attacker.name} loots {len(loot_items)} items from {target.name}"
        )
        self.combat_events.append(event)
    
    def get_combat_events(self, limit: int = 50) -> List[CombatEvent]:
        """
        Get recent combat events.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List[CombatEvent]: List of combat events
        """
        return self.combat_events[-limit:]
    
    def get_active_combats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all active combats.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of active combats
        """
        return self.active_combats
    
    def end_combat(self, combat_id: str) -> bool:
        """
        End an active combat.
        
        Args:
            combat_id: ID of the combat to end
            
        Returns:
            bool: True if combat was ended, False otherwise
        """
        if combat_id in self.active_combats:
            self.active_combats[combat_id]["ended"] = True
            return True
        return False
    
    def calculate_win_probability(self, attacker: Player, target: Mob) -> float:
        """
        Calculate win probability for attacker against target.
        
        Args:
            attacker: The entity attacking
            target: The entity being attacked
            
        Returns:
            float: Win probability (0.0 to 1.0)
        """
        # Simple calculation based on stats
        attack_power = attacker.attack_power + attacker.stats.get_modifier("strength")
        defense_power = target.defense + target.stats.get_modifier("dexterity")
        
        # Calculate probability
        if attack_power + defense_power == 0:
            return 0.5
        
        probability = attack_power / (attack_power + defense_power)
        return min(1.0, max(0.0, probability))
    
    def get_combat_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all combat statistics.
        
        Returns:
            Dict[str, Any]: Combat summary
        """
        total_events = len(self.combat_events)
        hits = sum(1 for event in self.combat_events if event.event_type == CombatEventType.HIT)
        criticals = sum(1 for event in self.combat_events if event.event_type == CombatEventType.CRITICAL_HIT)
        misses = sum(1 for event in self.combat_events if event.event_type == CombatEventType.MISS)
        defeats = sum(1 for event in self.combat_events if event.event_type == CombatEventType.DEFEAT)
        
        return {
            "total_combats": len(self.active_combats),
            "active_combats": len([c for c in self.active_combats.values() if not c["ended"]]),
            "total_events": total_events,
            "hits": hits,
            "critical_hits": criticals,
            "misses": misses,
            "defeats": defeats,
            "hit_rate": hits / total_events if total_events > 0 else 0,
            "critical_rate": criticals / hits if hits > 0 else 0
        }