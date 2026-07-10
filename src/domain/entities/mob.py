from typing import Dict, List, Optional, Any
from .entity import Entity
from ..value_objects.position import Position
from ..value_objects.stats import Stats
from ..components.inventory import Inventory
from ..components.combat import Combat
from ..components.movement import Movement
from ..components.perception_component import PerceptionComponent
from ..value_objects.perception import PerceptionModifiers


class Mob(Entity):
    """Mobile entity (monster/NPC) class"""
    
    def __init__(self, position: Position, name: str = "Mob", mob_type: str = "generic",
                 power: int = 0, defense: int = 0, level: int = 1, tier: Any = None,
                 skills: List[str] = None, armor_value: int = 0, dodge_bonus: int = 0,
                 to_hit_bonus: int = 0, damage_bonus: int = 0):
        super().__init__(name=name)
        self.position = position
        self.mob_type = mob_type
        self.stats = Stats()
        self.inventory = Inventory()
        self.combat = Combat()
        self.movement = Movement()
        
        # Add components
        self.add_component("inventory", self.inventory)
        self.add_component("combat", self.combat)
        self.add_component("stats", self.stats)
        self.add_component("position", self.position)
        self.add_component("movement", self.movement)
        # Attach a perception component so AI can respect visibility rules.
        perception = PerceptionComponent(entity_id=self.id, modifiers=PerceptionModifiers("default"))
        self.add_component("perception", perception)
        
        # B1 FIX: set mob-type stats FIRST so power/defense derive from FINAL stats,
        # not the default Stats() (strength=10). _set_default_stats overwrites self.stats.
        self._set_default_stats()
        # NEW combat attributes (fix System B AttributeError in CombatService).
        # power/defense derived from FINAL mob-type stats (orc strength=16 -> power=8).
        self.power = power if power else (self.stats.strength // 2)
        self.defense = defense if defense else (self.stats.constitution // 2)
        self.level = level
        self.tier = tier
        self.skills = list(skills or [])
        self.armor_value_override = armor_value
        self.dodge_bonus = dodge_bonus
        self.to_hit_bonus = to_hit_bonus
        self.damage_bonus = damage_bonus
        self.combat_dv_modifier = 1.0
        self.combat_av_modifier = 1.0
        self.combat_attack_modifier = 1.0
        
    def _set_default_stats(self) -> None:
        """Set default stats based on mob type"""
        if self.mob_type == "goblin":
            self.stats.strength = 8
            self.stats.dexterity = 12
            self.stats.constitution = 10
            self.stats.intelligence = 6
            self.stats.wisdom = 8
            self.stats.charisma = 6
            self.health = 30
            self.max_health = 30
        elif self.mob_type == "orc":
            self.stats.strength = 16
            self.stats.dexterity = 8
            self.stats.constitution = 14
            self.stats.intelligence = 6
            self.stats.wisdom = 8
            self.stats.charisma = 6
            self.health = 50
            self.max_health = 50
        elif self.mob_type == "dragon":
            self.stats.strength = 24
            self.stats.dexterity = 16
            self.stats.constitution = 20
            self.stats.intelligence = 18
            self.stats.wisdom = 16
            self.stats.charisma = 14
            self.health = 200
            self.max_health = 200
        else:  # generic
            self.stats.strength = 10
            self.stats.dexterity = 10
            self.stats.constitution = 10
            self.stats.intelligence = 10
            self.stats.wisdom = 10
            self.stats.charisma = 10
            self.health = 20
            self.max_health = 20
            
    def move_to(self, new_position: Position) -> None:
        """Move mob to new position"""
        # Use movement component if available
        movement_comp = self.get_component("movement")
        if movement_comp:
            movement_comp.set_position(new_position)
        else:
            # Fallback to direct position update
            self.position = new_position
            
    def take_damage(self, amount: int) -> None:
        """Take damage"""
        self.health = max(0, self.health - amount)
        
    def heal(self, amount: int) -> None:
        """Heal mob"""
        self.health = min(self.max_health, self.health + amount)
        
    def is_alive(self) -> bool:
        """Check if mob is alive"""
        return self.health > 0
        
    def get_attack_damage(self, weapon_dice: str = "1d6") -> int:
        from src.domain.services.combat_factors import get_base_damage
        return get_base_damage(self, weapon_dice)
        
    def get_defense(self) -> int:
        from src.domain.services.combat_factors import calculate_defense_value
        return calculate_defense_value(self)
        
    def update(self, delta_time: float) -> None:
        """Update mob state"""
        # Update AI behavior
        
        # Update movement component
        movement_comp = self.get_component("movement")
        if movement_comp:
            movement_comp.update(delta_time, self)
        
        # Regenerate health slowly
        if self.health < self.max_health:
            self.heal(1)
            
            
    def get_drops(self) -> List[str]:
        """Get possible loot drops"""
        return self.inventory.get_items()
        
    def add_loot(self, item_id: str) -> None:
        """Add loot to mob's inventory"""
        self.inventory.add_item(item_id)
        
    def to_dict(self) -> Dict:
        """Convert mob to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "mob_type": self.mob_type,
            "position": self.position.to_dict(),
            "health": self.health,
            "max_health": self.max_health,
            "stats": self.stats.to_dict(),
            "inventory": self.inventory.to_dict(),
            "combat": self.combat.to_dict(),
        }
