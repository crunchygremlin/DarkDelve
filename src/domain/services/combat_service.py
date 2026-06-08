"""
Combat service for handling combat-related operations.
"""
from typing import List, Dict, Any, Optional, Tuple
from random import randint
from ..entities.player import Player
from ..entities.mob import Mob
from ..components.combat import Combat
from ..value_objects.combat_event import CombatEvent, CombatEventType
from ..value_objects.stats import Stats


class CombatService:
    """
    Service for handling combat operations and calculations.
    
    Implements the Service pattern for combat management.
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
    
    def execute_attack(self, attacker: Player, target: Mob) -> Dict[str, Any]:
        """
        Execute an attack from attacker to target.
        
        Args:
            attacker: The entity attacking
            target: The entity being attacked
            
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
        
        # Calculate attack roll
        attack_roll = self.calculate_attack_roll(attacker)
        defense_roll = self.calculate_defense_roll(target)
        
        # Determine if attack hits
        hit = attack_roll > defense_roll
        
        if hit:
            # Calculate damage
            damage = self.calculate_damage(attacker, target)
            
            # Check for critical hit
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
    
    def calculate_attack_roll(self, attacker: Player) -> int:
        """
        Calculate attack roll for an attacker.
        
        Args:
            attacker: The entity attacking
            
        Returns:
            int: Attack roll value
        """
        # Base attack + dexterity modifier + weapon bonus
        base_attack = attacker.attack_power
        dex_modifier = attacker.stats.get_modifier("dexterity")
        weapon_bonus = attacker.get_equipped_attack_bonus()
        
        # Add random factor
        attack_roll = base_attack + dex_modifier + weapon_bonus + randint(1, 20)
        
        return attack_roll
    
    def calculate_defense_roll(self, target: Mob) -> int:
        """
        Calculate defense roll for a target.
        
        Args:
            target: The entity defending
            
        Returns:
            int: Defense roll value
        """
        # Base defense + dexterity modifier + armor bonus
        base_defense = target.defense
        dex_modifier = target.stats.get_modifier("dexterity")
        armor_bonus = target.get_equipped_defense_bonus()
        
        # Add random factor
        defense_roll = base_defense + dex_modifier + armor_bonus + randint(1, 20)
        
        return defense_roll
    
    def calculate_damage(self, attacker: Player, target: Mob) -> int:
        """
        Calculate damage for an attack.
        
        Args:
            attacker: The entity attacking
            target: The entity being attacked
            
        Returns:
            int: Damage amount
        """
        # Base damage + strength modifier + weapon damage
        base_damage = attacker.attack_power
        str_modifier = attacker.stats.get_modifier("strength")
        weapon_damage = attacker.get_equipped_damage_bonus()
        
        # Calculate total damage
        damage = base_damage + str_modifier + weapon_damage
        
        # Ensure minimum damage
        damage = max(1, damage)
        
        # Apply damage reduction from target's armor
        damage_reduction = target.get_equipped_damage_reduction()
        damage = max(1, damage - damage_reduction)
        
        return damage
    
    def is_critical_hit(self, attacker: Player) -> bool:
        """
        Check if an attack is a critical hit.
        
        Args:
            attacker: The entity attacking
            
        Returns:
            bool: True if critical hit, False otherwise
        """
        # Critical hit on natural 20 or high enough roll
        critical_threshold = 19  # Natural 19 or 20
        return randint(1, 20) >= critical_threshold
    
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