"""
Combat System - Handles all combat calculations, logging, and display
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
import random


class HitResult(Enum):
    MISS = 0
    HIT = 1
    CRITICAL = 2
    CRITICAL_FAIL = 3


@dataclass
class CombatEvent:
    """Represents a single combat action"""
    turn: int
    attacker_name: str
    defender_name: str
    
    # Attack roll details
    to_hit_bonus: int  # modifier from attacker
    target_ac: int    # armor class of defender
    d20_roll: int     # 1-20 roll
    total_roll: int   # d20_roll + to_hit_bonus
    
    result: HitResult
    damage: int = 0
    
    # Narrative
    flavor_text: str = ""
    
    def __str__(self) -> str:
        """Generate human-readable combat message"""
        roll_text = f"[Roll: {self.total_roll} vs AC {self.target_ac}]"
        
        if self.result == HitResult.CRITICAL:
            return f"{self.attacker_name} strikes critically! {roll_text} CRITICAL HIT! Damage: {self.damage}"
        elif self.result == HitResult.HIT:
            return f"{self.attacker_name} attacks! {roll_text} HIT! Damage: {self.damage}"
        elif self.result == HitResult.MISS:
            return f"{self.attacker_name} attacks... {roll_text} MISS!"
        elif self.result == HitResult.CRITICAL_FAIL:
            return f"{self.attacker_name} attempts strike... {roll_text} CRITICAL MISS!"
        return f"Combat: {self.attacker_name} vs {self.defender_name}"


class CombatLog:
    """Tracks combat history for display and narrative"""
    
    def __init__(self, max_history: int = 20):
        self.events: List[CombatEvent] = []
        self.max_history = max_history
        self.turn_counter = 0
    
    def add_event(self, event: CombatEvent) -> None:
        """Record a combat event"""
        event.turn = self.turn_counter
        self.events.append(event)
        if len(self.events) > self.max_history:
            self.events.pop(0)
    
    def get_recent(self, count: int = 5) -> List[CombatEvent]:
        """Get most recent combat events"""
        return self.events[-count:]
    
    def get_for_display(self) -> str:
        """Format recent combat for display"""
        if not self.events:
            return "No recent combat."
        
        lines = []
        for event in self.get_recent(3):
            lines.append(f"  • {event}")
        return "\n".join(lines)
    
    def new_turn(self) -> None:
        """Increment turn counter"""
        self.turn_counter += 1


class CombatResolver:
    """Calculates hit/miss/damage"""
    
    @staticmethod
    def resolve_attack(
        attacker_name: str,
        attacker_power: int,
        attacker_to_hit: int = 0,
        defender_name: str = "Enemy",
        defender_ac: int = 10,
        weapon_damage: int = 5,
        weapon_dice: str = "1d6"
    ) -> CombatEvent:
        """
        Resolve a single attack
        
        Args:
            attacker_name: Name of attacker
            attacker_power: Power stat (adds to damage)
            attacker_to_hit: Bonus to hit
            defender_name: Name of defender
            defender_ac: Armor class (harder to hit)
            weapon_damage: Flat damage bonus
            weapon_dice: Dice roll like "1d6" or "1d8+1"
        
        Returns:
            CombatEvent with result
        """
        # Roll d20
        d20_roll = random.randint(1, 20)
        total_roll = d20_roll + attacker_to_hit
        
        # Determine hit result
        if d20_roll == 20:
            result = HitResult.CRITICAL
        elif d20_roll == 1:
            result = HitResult.CRITICAL_FAIL
        elif total_roll >= defender_ac:
            result = HitResult.HIT
        else:
            result = HitResult.MISS
        
        # Calculate damage
        damage = 0
        if result in [HitResult.HIT, HitResult.CRITICAL]:
            # Parse weapon dice (e.g., "1d8+2")
            try:
                parts = weapon_dice.replace('d', ' ').split()
                num_dice = int(parts[0])
                dice_size = int(parts[1])
                modifier = int(parts[2]) if len(parts) > 2 else 0
            except:
                num_dice, dice_size, modifier = 1, 6, 0
            
            # Roll damage
            damage = sum(random.randint(1, dice_size) for _ in range(num_dice))
            damage += modifier + (attacker_power // 2) + weapon_damage
            
            # Critical does double damage
            if result == HitResult.CRITICAL:
                damage *= 2
        
        return CombatEvent(
            turn=0,
            attacker_name=attacker_name,
            defender_name=defender_name,
            to_hit_bonus=attacker_to_hit,
            target_ac=defender_ac,
            d20_roll=d20_roll,
            total_roll=total_roll,
            result=result,
            damage=damage,
        )


def format_combat_display(combat_log: CombatLog, entity_health: dict) -> str:
    """
    Format combat information for game display
    
    Args:
        combat_log: The combat log object
        entity_health: Dict of {entity_name: (current_hp, max_hp)}
    
    Returns:
        Formatted string for display
    """
    lines = []
    
    # Recent combat
    if combat_log.events:
        lines.append("═" * 50)
        lines.append("RECENT COMBAT:")
        for event in combat_log.get_recent(3):
            lines.append(f"  {event}")
    
    # Entity health status
    if entity_health:
        lines.append("═" * 50)
        lines.append("HEALTH STATUS:")
        for name, (current, maximum) in entity_health.items():
            pct = (current / maximum * 100) if maximum > 0 else 0
            bar_filled = int(pct / 5)
            bar_empty = 20 - bar_filled
            bar = "█" * bar_filled + "░" * bar_empty
            lines.append(f"  {name:20} {bar} {current:3}/{maximum:3}")
    
    return "\n".join(lines)
