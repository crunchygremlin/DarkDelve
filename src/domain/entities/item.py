from typing import Dict, Optional, List
from uuid import uuid4
from .entity import Entity
from ..value_objects.position import Position


class Item(Entity):
    """Item entity class"""
    
    def __init__(self, item_id: Optional[str] = None, name: str = "Item",
                 item_type: str = "generic", description: str = "",
                 value: int = 0, weight: float = 1.0, weapon_dice: str = "1d6"):
        super().__init__(entity_id=item_id, name=name)
        self.item_type = item_type
        self.description = description
        self.value = value
        self.weight = weight
        self.position = Position(0, 0)
        self.stackable = False
        self.quantity = 1
        self.equippable = False
        self.equipment_slot = None
        self.consumable = False
        self.effects = []
        self._effect = ""  # For healing/damage effects like "heal+20"
        self.attack_bonus = 0
        self.defense_bonus = 0
        self.health_bonus = 0
        self.speed_bonus = 0
        self.weapon_dice = weapon_dice
        # attack_bonus -> to-hit (attack value); defense_bonus -> AV (armor_value property)
        
    @property
    def is_equipment(self) -> bool:
        """Check if item is equipment (weapon, armor, accessory)"""
        return self.item_type in ["weapon", "armor", "accessory"]

    @property
    def is_droppable(self) -> bool:
        """Check if item can be dropped (all items are droppable unless equipped)"""
        return not getattr(self, 'equipped', False)

    @property
    def is_usable(self) -> bool:
        """Check if item is usable (consumable)"""
        return self.consumable or self.item_type in ["potion", "scroll", "food"]
    
    @property
    def effect(self) -> str:
        """Get the item's effect string"""
        return self._effect
    
    @effect.setter
    def effect(self, value: str) -> None:
        """Set the item's effect string"""
        self._effect = value
        
    def set_position(self, position: Position) -> None:
        """Set item position"""
        self.position = position
        
    def move_to(self, new_position: Position) -> None:
        """Move item to new position"""
        self.position = new_position
        
    def is_stackable(self) -> bool:
        """Check if item is stackable"""
        return self.stackable
        
    def can_stack_with(self, other_item: 'Item') -> bool:
        """Check if this item can stack with another item"""
        if not self.stackable or not other_item.stackable:
            return False
        if self.item_type != other_item.item_type:
            return False
        if self.equippable or other_item.equippable:
            return False
        return True
        
    def stack_with(self, other_item: 'Item') -> bool:
        """Stack with another item if possible"""
        if self.can_stack_with(other_item):
            self.quantity += other_item.quantity
            return True
        return False
        
    def split_stack(self, quantity: int) -> 'Item':
        """Split stack into new item"""
        if quantity <= 0 or quantity >= self.quantity:
            return None
            
        new_item = Item(
            name=self.name,
            item_type=self.item_type,
            description=self.description,
            value=self.value,
            weight=self.weight
        )
        new_item.stackable = True
        new_item.quantity = quantity
        self.quantity -= quantity
        
        return new_item
        
    @property
    def armor_value(self) -> int:
        """Armor Value - returns defense_bonus"""
        return self.defense_bonus

    def equip(self, slot: str) -> bool:
        """Mark item as equippable and set slot"""
        if self.item_type in ["weapon", "armor", "accessory"]:
            self.equippable = True
            self.equipment_slot = slot
            return True
        return False
        
    def consume(self) -> bool:
        """Mark item as consumable"""
        if self.item_type in ["potion", "scroll", "food"]:
            self.consumable = True
            return True
        return False
        
    def add_effect(self, effect: Dict) -> None:
        """Add an effect to the item"""
        self.effects.append(effect)
        
    def get_effects(self) -> List[Dict]:
        """Get all effects of the item"""
        return self.effects
        
    def update(self, delta_time: float) -> None:
        """Update item state"""
        # Items don't typically need updating
        pass
        
    def to_dict(self) -> Dict:
        """Convert item to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "item_type": self.item_type,
            "description": self.description,
            "value": self.value,
            "weight": self.weight,
            "position": self.position.to_dict(),
            "stackable": self.stackable,
            "quantity": self.quantity,
            "equippable": self.equippable,
            "equipment_slot": self.equipment_slot,
            "consumable": self.consumable,
            "effects": self.effects
        }