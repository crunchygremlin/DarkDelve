from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class SlotType(Enum):
    """Inventory slot types"""
    MAIN_HAND = "main_hand"
    OFF_HAND = "off_hand"
    HEAD = "head"
    CHEST = "chest"
    LEGS = "legs"
    FEET = "feet"
    HANDS = "hands"
    NECK = "neck"
    RING = "ring"
    AMMO = "ammo"
    BACKPACK = "backpack"
    QUEST = "quest"
    SPECIAL = "special"


@dataclass
class InventorySlot:
    """Inventory slot value object"""
    slot_type: SlotType
    capacity: int = 1
    item_id: Optional[str] = None
    quantity: int = 0
    equipped: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate inventory slot"""
        if not isinstance(self.slot_type, SlotType):
            raise TypeError("slot_type must be a SlotType enum")
        if not isinstance(self.capacity, int):
            raise TypeError("capacity must be an integer")
        if self.capacity < 0:
            raise ValueError("capacity cannot be negative")
        if self.item_id is not None and not isinstance(self.item_id, str):
            raise TypeError("item_id must be a string or None")
        if not isinstance(self.quantity, int):
            raise TypeError("quantity must be an integer")
        if self.quantity < 0:
            raise ValueError("quantity cannot be negative")
        if not isinstance(self.equipped, bool):
            raise TypeError("equipped must be a boolean")
            
    def is_empty(self) -> bool:
        """Check if slot is empty"""
        return self.item_id is None
        
    def is_full(self) -> bool:
        """Check if slot is full"""
        return self.quantity >= self.capacity
        
    def can_accept_item(self, item_id: str, quantity: int = 1) -> bool:
        """Check if slot can accept an item"""
        if self.is_empty():
            return True
        if self.item_id != item_id:
            return False
        if self.is_full():
            return False
        return (self.quantity + quantity) <= self.capacity
        
    def add_item(self, item_id: str, quantity: int = 1) -> bool:
        """Add item to slot"""
        if not self.can_accept_item(item_id, quantity):
            return False
            
        if self.is_empty():
            self.item_id = item_id
            self.quantity = quantity
        else:
            self.quantity += quantity
            
        return True
        
    def remove_item(self, quantity: int = 1) -> bool:
        """Remove item from slot"""
        if self.is_empty() or quantity <= 0:
            return False
            
        if self.quantity <= quantity:
            # Remove all items from slot
            self.item_id = None
            self.quantity = 0
        else:
            # Remove specified quantity
            self.quantity -= quantity
            
        return True
        
    def set_equipped(self, equipped: bool) -> None:
        """Set equipped status"""
        self.equipped = equipped
        
    def get_available_capacity(self) -> int:
        """Get available capacity in slot"""
        return self.capacity - self.quantity
        
    def get_slot_info(self) -> Dict[str, Any]:
        """Get slot information"""
        return {
            "slot_type": self.slot_type.value,
            "capacity": self.capacity,
            "item_id": self.item_id,
            "quantity": self.quantity,
            "equipped": self.equipped,
            "available_capacity": self.get_available_capacity(),
            "is_empty": self.is_empty(),
            "is_full": self.is_full()
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "slot_type": self.slot_type.value,
            "capacity": self.capacity,
            "item_id": self.item_id,
            "quantity": self.quantity,
            "equipped": self.equipped,
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InventorySlot':
        """Create inventory slot from dictionary"""
        # Convert string slot_type to enum
        if isinstance(data["slot_type"], str):
            data["slot_type"] = SlotType(data["slot_type"])
            
        return cls(
            slot_type=data["slot_type"],
            capacity=data.get("capacity", 1),
            item_id=data.get("item_id"),
            quantity=data.get("quantity", 0),
            equipped=data.get("equipped", False),
            metadata=data.get("metadata", {})
        )
        
    def __eq__(self, other: object) -> bool:
        """Check if slots are equal"""
        if not isinstance(other, InventorySlot):
            return False
        return (self.slot_type == other.slot_type and 
                self.capacity == other.capacity and
                self.item_id == other.item_id and
                self.quantity == other.quantity and
                self.equipped == other.equipped)
        
    def __str__(self) -> str:
        """String representation"""
        if self.is_empty():
            return f"InventorySlot({self.slot_type.value}): Empty"
        else:
            return f"InventorySlot({self.slot_type.value}): {self.item_id} x{self.quantity}"
        
    def __repr__(self) -> str:
        """Detailed string representation"""
        return (f"InventorySlot(slot_type={self.slot_type.value}, capacity={self.capacity}, "
                f"item_id={self.item_id}, quantity={self.quantity}, equipped={self.equipped})")