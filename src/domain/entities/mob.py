from typing import Dict, List, Optional
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
    
    def __init__(self, position: Position, name: str = "Mob", mob_type: str = "generic"):
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
        
        # Set default stats based on mob type
        self._set_default_stats()
        
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
        
    def get_attack_damage(self) -> int:
        """Get attack damage"""
        base_damage = self.stats.strength // 2
        return max(1, base_damage + self.combat.get_bonus_damage())
        
    def get_defense(self) -> int:
        """Get defense value"""
        return self.stats.constitution // 2 + self.combat.get_bonus_defense()
        
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
