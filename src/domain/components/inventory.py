from typing import Dict, Any, Optional, List
from .component import Component
from ..value_objects.inventory_slot import InventorySlot, SlotType


class Inventory(Component):
    """Inventory component for managing entity inventory"""
    
    def __init__(self, component_id: Optional[str] = None, max_capacity: int = 20):
        super().__init__(component_id)
        self.max_capacity = max_capacity
        self.slots: Dict[str, InventorySlot] = {}
        self.gold = 0
        self.weight_limit = 100.0  # kg
        self.current_weight = 0.0
        self.auto_stack = True
        self.sort_by = "name"  # name, type, value, weight
        
        # Initialize default slots
        self._initialize_default_slots()
        
    def _initialize_default_slots(self) -> None:
        """Initialize default equipment slots"""
        equipment_slots = [
            SlotType.MAIN_HAND,
            SlotType.OFF_HAND,
            SlotType.HEAD,
            SlotType.CHEST,
            SlotType.LEGS,
            SlotType.FEET,
            SlotType.HANDS,
            SlotType.NECK,
            SlotType.RING,
            SlotType.BACKPACK
        ]
        
        for slot_type in equipment_slots:
            self.slots[slot_type.value] = InventorySlot(slot_type)
            
    def add_item(self, item_id: str, quantity: int = 1, slot_type: Optional[SlotType] = None) -> bool:
        """Add item to inventory"""
        if quantity <= 0:
            return False
            
        # Check weight limit
        item_weight = self._get_item_weight(item_id)
        if self.current_weight + (item_weight * quantity) > self.weight_limit:
            return False
            
        # Try to add to existing stack or find empty slot
        if self.auto_stack:
            # Try to stack with existing items
            for slot in self.slots.values():
                if slot.can_accept_item(item_id, quantity):
                    slot.add_item(item_id, quantity)
                    self.current_weight += item_weight * quantity
                    return True
                    
        # Find empty slot
        if slot_type:
            target_slot = self.slots.get(slot_type.value)
            if target_slot and target_slot.is_empty():
                target_slot.add_item(item_id, quantity)
                self.current_weight += item_weight * quantity
                return True
                
        # Find any empty slot
        for slot in self.slots.values():
            if slot.is_empty():
                slot.add_item(item_id, quantity)
                self.current_weight += item_weight * quantity
                return True
                
        return False  # No space available
        
    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        """Remove item from inventory"""
        if quantity <= 0:
            return False
            
        # Find items to remove
        total_removed = 0
        for slot in self.slots.values():
            if slot.item_id == item_id:
                remove_amount = min(quantity - total_removed, slot.quantity)
                if remove_amount > 0:
                    slot.remove_item(remove_amount)
                    self.current_weight -= self._get_item_weight(item_id) * remove_amount
                    total_removed += remove_amount
                    
                    if total_removed >= quantity:
                        return True
                        
        return total_removed >= quantity
        
    def get_item_quantity(self, item_id: str) -> int:
        """Get total quantity of item in inventory"""
        total = 0
        for slot in self.slots.values():
            if slot.item_id == item_id:
                total += slot.quantity
        return total
        
    def has_item(self, item_id: str, quantity: int = 1) -> bool:
        """Check if inventory has item with sufficient quantity"""
        return self.get_item_quantity(item_id) >= quantity
        
    def get_empty_slots(self) -> List[str]:
        """Get list of empty slot names"""
        return [slot_name for slot_name, slot in self.slots.items() if slot.is_empty()]
        
    def get_full_slots(self) -> List[str]:
        """Get list of full slot names"""
        return [slot_name for slot_name, slot in self.slots.items() if slot.is_full()]
        
    def get_slot(self, slot_name: str) -> Optional[InventorySlot]:
        """Get specific slot"""
        return self.slots.get(slot_name)
        
    def get_equipped_items(self) -> Dict[str, Optional[str]]:
        """Get all equipped items"""
        equipped = {}
        for slot_name, slot in self.slots.items():
            if slot.equipped and slot.item_id:
                equipped[slot_name] = slot.item_id
        return equipped
        
    def equip_item(self, item_id: str, slot_name: str) -> bool:
        """Equip item in specific slot"""
        slot = self.slots.get(slot_name)
        if not slot or slot.is_empty() or slot.item_id != item_id:
            return False
            
        # Check if item can be equipped in this slot
        if not self._can_equip_in_slot(item_id, slot_name):
            return False
            
        slot.set_equipped(True)
        return True
        
    def unequip_item(self, slot_name: str) -> bool:
        """Unequip item from slot"""
        slot = self.slots.get(slot_name)
        if not slot or not slot.equipped:
            return False
            
        slot.set_equipped(False)
        return True
        
    def move_item(self, from_slot: str, to_slot: str, quantity: int = 1) -> bool:
        """Move item between slots"""
        from_slot_obj = self.slots.get(from_slot)
        to_slot_obj = self.slots.get(to_slot)
        
        if not from_slot_obj or not to_slot_obj:
            return False
            
        if from_slot_obj.is_empty() or from_slot_obj.item_id != to_slot_obj.item_id:
            return False
            
        if not to_slot_obj.can_accept_item(from_slot_obj.item_id, quantity):
            return False
            
        # Move items
        from_slot_obj.remove_item(quantity)
        to_slot_obj.add_item(from_slot_obj.item_id, quantity)
        return True
        
    def sort_inventory(self) -> None:
        """Sort inventory items"""
        if self.sort_by == "name":
            self._sort_by_name()
        elif self.sort_by == "type":
            self._sort_by_type()
        elif self.sort_by == "value":
            self._sort_by_value()
        elif self.sort_by == "weight":
            self._sort_by_weight()
            
    def _sort_by_name(self) -> None:
        """Sort items by name"""
        # Implementation would require item name lookup
        pass
        
    def _sort_by_type(self) -> None:
        """Sort items by type"""
        # Implementation would require item type lookup
        pass
        
    def _sort_by_value(self) -> None:
        """Sort items by value"""
        # Implementation would require item value lookup
        pass
        
    def _sort_by_weight(self) -> None:
        """Sort items by weight"""
        # Implementation would require item weight lookup
        pass
        
    def _get_item_weight(self, item_id: str) -> float:
        """Get item weight (placeholder)"""
        # This would normally look up item data
        return 1.0
        
    def _can_equip_in_slot(self, item_id: str, slot_name: str) -> bool:
        """Check if item can be equipped in slot (placeholder)"""
        # This would normally check item type vs slot type
        return True
        
    def add_gold(self, amount: int) -> None:
        """Add gold to inventory"""
        self.gold += max(0, amount)
        
    def remove_gold(self, amount: int) -> bool:
        """Remove gold from inventory"""
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False
        
    def get_inventory_info(self) -> Dict[str, Any]:
        """Get inventory information"""
        return {
            "max_capacity": self.max_capacity,
            "current_capacity": self.get_used_capacity(),
            "gold": self.gold,
            "current_weight": self.current_weight,
            "weight_limit": self.weight_limit,
            "empty_slots": len(self.get_empty_slots()),
            "full_slots": len(self.get_full_slots()),
            "auto_stack": self.auto_stack,
            "sort_by": self.sort_by
        }
        
    def get_used_capacity(self) -> int:
        """Get used capacity count"""
        used = 0
        for slot in self.slots.values():
            if not slot.is_empty():
                used += 1
        return used
        
    def get_items(self) -> List[str]:
        """Get all item IDs in inventory"""
        items = []
        for slot in self.slots.values():
            if slot.item_id:
                items.extend([slot.item_id] * slot.quantity)
        return items
        
    def clear_inventory(self) -> None:
        """Clear all items from inventory"""
        for slot in self.slots.values():
            slot.item_id = None
            slot.quantity = 0
            slot.equipped = False
        self.gold = 0
        self.current_weight = 0.0
        
    def update(self, delta_time: float, entity: Any) -> None:
        """Update inventory component"""
        # Inventory doesn't need regular updates in basic implementation
        pass
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "max_capacity": self.max_capacity,
            "gold": self.gold,
            "current_weight": self.current_weight,
            "weight_limit": self.weight_limit,
            "auto_stack": self.auto_stack,
            "sort_by": self.sort_by,
            "slots": {slot_name: slot.to_dict() for slot_name, slot in self.slots.items()}
        })
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Inventory':
        """Create inventory component from dictionary"""
        inventory = cls(
            max_capacity=data.get("max_capacity", 20),
            component_id=data.get("id")
        )
        inventory.enabled = data.get("enabled", True)
        inventory.gold = data.get("gold", 0)
        inventory.current_weight = data.get("current_weight", 0.0)
        inventory.weight_limit = data.get("weight_limit", 100.0)
        inventory.auto_stack = data.get("auto_stack", True)
        inventory.sort_by = data.get("sort_by", "name")
        
        # Load slots
        for slot_name, slot_data in data.get("slots", {}).items():
            inventory.slots[slot_name] = InventorySlot.from_dict(slot_data)
            
        return inventory