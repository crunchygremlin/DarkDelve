from typing import Dict, Any, Optional, List
from .component import Component
from ..value_objects.combat_event import CombatEvent, EventType


class Combat(Component):
    """Combat component for handling combat mechanics"""
    
    def __init__(self, component_id: Optional[str] = None):
        super().__init__(component_id)
        self.attack_power = 10
        self.defense = 5
        self.critical_chance = 0.1  # 10% chance
        self.critical_multiplier = 2.0
        self.attack_speed = 1.0  # attacks per second
        self.last_attack_time = 0.0
        self.combat_events: List[CombatEvent] = []
        self.status_effects: Dict[str, Dict[str, Any]] = {}
        self.bonus_damage = 0
        self.bonus_defense = 0
        
    def can_attack(self, current_time: float) -> bool:
        """Check if entity can attack based on attack speed"""
        time_since_last_attack = current_time - self.last_attack_time
        return time_since_last_attack >= (1.0 / self.attack_speed)
        
    def attack(self, target_id: str, current_time: float) -> Optional[CombatEvent]:
        """Perform an attack on a target"""
        if not self.can_attack(current_time):
            return None
            
        self.last_attack_time = current_time
        
        # Create attack event
        attack_event = CombatEvent(
            event_type=EventType.ATTACK,
            source_id=self.id,
            target_id=target_id,
            timestamp=current_time
        )
        
        # Check for critical hit
        import random
        is_critical = random.random() < self.critical_chance
        
        if is_critical:
            attack_event.critical = True
            
        # Calculate damage
        base_damage = self.attack_power + self.bonus_damage
        if is_critical:
            damage = int(base_damage * self.critical_multiplier)
        else:
            damage = base_damage
            
        attack_event.damage_amount = damage
        
        self.combat_events.append(attack_event)
        return attack_event
        
    def take_damage(self, damage: int, source_id: str, current_time: float) -> CombatEvent:
        """Take damage from an attack"""
        # Apply defense
        actual_damage = max(1, damage - (self.defense + self.bonus_defense))
        
        # Create damage event
        damage_event = CombatEvent(
            event_type=EventType.DAMAGE,
            source_id=source_id,
            target_id=self.id,
            timestamp=current_time,
            damage_amount=actual_damage
        )
        
        self.combat_events.append(damage_event)
        return damage_event
        
    def heal(self, amount: int, source_id: str, current_time: float) -> CombatEvent:
        """Receive healing"""
        heal_event = CombatEvent(
            event_type=EventType.HEAL,
            source_id=source_id,
            target_id=self.id,
            timestamp=current_time,
            heal_amount=amount
        )
        
        self.combat_events.append(heal_event)
        return heal_event
        
    def add_status_effect(self, effect_name: str, duration: float, 
                         effect_data: Dict[str, Any]) -> None:
        """Add a status effect"""
        self.status_effects[effect_name] = {
            "duration": duration,
            "data": effect_data,
            "start_time": 0.0  # Will be set when applied
        }
        
    def remove_status_effect(self, effect_name: str) -> bool:
        """Remove a status effect"""
        if effect_name in self.status_effects:
            del self.status_effects[effect_name]
            return True
        return False
        
    def has_status_effect(self, effect_name: str) -> bool:
        """Check if entity has a status effect"""
        return effect_name in self.status_effects
        
    def get_status_effects(self) -> Dict[str, Dict[str, Any]]:
        """Get all active status effects"""
        return self.status_effects.copy()
        
    def update_status_effects(self, current_time: float) -> List[str]:
        """Update status effects and remove expired ones"""
        expired_effects = []
        
        for effect_name, effect_data in list(self.status_effects.items()):
            if effect_data["start_time"] == 0.0:
                effect_data["start_time"] = current_time
                
            elapsed_time = current_time - effect_data["start_time"]
            if elapsed_time >= effect_data["duration"]:
                expired_effects.append(effect_name)
                del self.status_effects[effect_name]
                
        return expired_effects
        
    def get_bonus_damage(self) -> int:
        """Get bonus damage from equipment and effects"""
        bonus = self.bonus_damage
        
        # Add bonus from status effects
        for effect_data in self.status_effects.values():
            bonus += effect_data["data"].get("damage_bonus", 0)
            
        return bonus
        
    def get_bonus_defense(self) -> int:
        """Get bonus defense from equipment and effects"""
        bonus = self.bonus_defense
        
        # Add bonus from status effects
        for effect_data in self.status_effects.values():
            bonus += effect_data["data"].get("defense_bonus", 0)
            
        return bonus
        
    def set_attack_power(self, power: int) -> None:
        """Set attack power"""
        self.attack_power = max(0, power)
        
    def set_defense(self, defense: int) -> None:
        """Set defense"""
        self.defense = max(0, defense)
        
    def set_critical_chance(self, chance: float) -> None:
        """Set critical hit chance (0.0 to 1.0)"""
        self.critical_chance = max(0.0, min(1.0, chance))
        
    def set_critical_multiplier(self, multiplier: float) -> None:
        """Set critical hit multiplier"""
        self.critical_multiplier = max(1.0, multiplier)
        
    def set_attack_speed(self, speed: float) -> None:
        """Set attack speed (attacks per second)"""
        self.attack_speed = max(0.1, speed)
        
    def add_bonus_damage(self, amount: int) -> None:
        """Add bonus damage"""
        self.bonus_damage += amount
        
    def add_bonus_defense(self, amount: int) -> None:
        """Add bonus defense"""
        self.bonus_defense += amount
        
    def clear_combat_events(self) -> None:
        """Clear all combat events"""
        self.combat_events.clear()
        
    def get_combat_events(self, limit: Optional[int] = None) -> List[CombatEvent]:
        """Get combat events, optionally limited to recent events"""
        if limit is None:
            return self.combat_events.copy()
        return self.combat_events[-limit:]
        
    def update(self, delta_time: float, entity: Any) -> None:
        """Update combat component"""
        current_time = getattr(entity, 'current_time', 0.0)
        
        # Update status effects
        self.update_status_effects(current_time)
        
        # Apply status effect updates to entity if needed
        for effect_name, effect_data in self.status_effects.items():
            # Here you could apply ongoing effects
            pass
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "attack_power": self.attack_power,
            "defense": self.defense,
            "critical_chance": self.critical_chance,
            "critical_multiplier": self.critical_multiplier,
            "attack_speed": self.attack_speed,
            "bonus_damage": self.bonus_damage,
            "bonus_defense": self.bonus_defense,
            "status_effects": self.status_effects,
            "combat_events": [event.to_dict() for event in self.combat_events]
        })
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Combat':
        """Create combat component from dictionary"""
        combat = cls()
        combat.enabled = data.get("enabled", True)
        combat.attack_power = data.get("attack_power", 10)
        combat.defense = data.get("defense", 5)
        combat.critical_chance = data.get("critical_chance", 0.1)
        combat.critical_multiplier = data.get("critical_multiplier", 2.0)
        combat.attack_speed = data.get("attack_speed", 1.0)
        combat.bonus_damage = data.get("bonus_damage", 0)
        combat.bonus_defense = data.get("bonus_defense", 0)
        combat.status_effects = data.get("status_effects", {})
        combat.combat_events = [CombatEvent.from_dict(event_data) 
                               for event_data in data.get("combat_events", [])]
        return combat