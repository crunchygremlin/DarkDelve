from typing import Dict, List, Optional
from .entity import Entity
from ..value_objects.position import Position
from ..value_objects.stats import Stats
from ..components.inventory import Inventory
from ..components.equipment import Equipment


class Player(Entity):
    """Player entity class"""
    
    def __init__(self, position: Position, name: str = "Player"):
        super().__init__(name=name)
        self.position = position
        self.stats = Stats()
        self.inventory = Inventory()
        self.equipment = Equipment()
        self.level = 1
        self.experience = 0
        self.health = 100
        self.max_health = 100
        self.mana = 50
        self.max_mana = 50
        
        # Add components
        self.add_component("inventory", self.inventory)
        self.add_component("equipment", self.equipment)
        self.add_component("stats", self.stats)
        self.add_component("position", self.position)
        
    def move_to(self, new_position: Position) -> None:
        """Move player to new position"""
        self.position = new_position
        
    def gain_experience(self, amount: int) -> bool:
        """Add experience and check for level up"""
        self.experience += amount
        return self.check_level_up()
        
    def check_level_up(self) -> bool:
        """Check if player should level up"""
        exp_needed = self.level * 100
        if self.experience >= exp_needed:
            self.level += 1
            self.experience -= exp_needed
            self.max_health += 10
            self.max_mana += 5
            self.health = self.max_health
            self.mana = self.max_mana
            return True
        return False
        
    def take_damage(self, amount: int) -> None:
        """Take damage"""
        self.health = max(0, self.health - amount)
        
    def heal(self, amount: int) -> None:
        """Heal player"""
        self.health = min(self.max_health, self.health + amount)
        
    def use_mana(self, amount: int) -> bool:
        """Use mana if available"""
        if self.mana >= amount:
            self.mana -= amount
            return True
        return False
        
    def restore_mana(self, amount: int) -> None:
        """Restore mana"""
        self.mana = min(self.max_mana, self.mana + amount)
        
    def is_alive(self) -> bool:
        """Check if player is alive"""
        return self.health > 0
        
    def update(self, delta_time: float) -> None:
        """Update player state"""
        # Regenerate mana over time
        if self.mana < self.max_mana:
            self.restore_mana(1)
            
    def get_equipped_items(self) -> Dict[str, Optional[str]]:
        """Get all equipped items"""
        return self.equipment.get_equipped_items()
        
    def equip_item(self, item_id: str, slot: str) -> bool:
        """Equip an item"""
        return self.equipment.equip_item(item_id, slot)
        
    def unequip_item(self, slot: str) -> Optional[str]:
        """Unequip an item"""
        return self.equipment.unequip_item(slot)
        
    def get_inventory_items(self) -> List[str]:
        """Get all items in inventory"""
        return self.inventory.get_items()
        
    def add_item_to_inventory(self, item_id: str) -> bool:
        """Add item to inventory"""
        return self.inventory.add_item(item_id)
        
    def remove_item_from_inventory(self, item_id: str) -> bool:
        """Remove item from inventory"""
        return self.inventory.remove_item(item_id)
        
    def to_dict(self) -> Dict:
        """Convert player to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "position": self.position.to_dict(),
            "level": self.level,
            "experience": self.experience,
            "health": self.health,
            "max_health": self.max_health,
            "mana": self.mana,
            "max_mana": self.max_mana,
            "stats": self.stats.to_dict(),
            "inventory": self.inventory.to_dict(),
            "equipment": self.equipment.to_dict()
        }