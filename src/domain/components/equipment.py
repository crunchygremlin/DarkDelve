from typing import Dict, Any, Optional, List
from .component import Component
from ..value_objects.inventory_slot import InventorySlot, SlotType


class Equipment(Component):
    """Equipment component for managing entity equipment"""
    
    def __init__(self, component_id: Optional[str] = None):
        super().__init__(component_id)
        self.slots: Dict[str, InventorySlot] = {}
        self.bonuses: Dict[str, int] = {}  # Stat bonuses from equipment
        self.set_bonuses: Dict[str, int] = {}  # Set bonuses
        self.equipped_sets: Dict[str, List[str]] = {}  # Equipment sets
        self.max_durability: Dict[str, int] = {}  # Max durability for items
        self.current_durability: Dict[str, int] = {}  # Current durability
        
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
            
    def equip_item(self, item_id: str, slot_name: str) -> bool:
        """Equip item in specified slot"""
        slot = self.slots.get(slot_name)
        if not slot:
            return False
            
        # Check if slot is appropriate for the item
        if not self._is_slot_appropriate(slot_name, item_id):
            return False
            
        # Unequip current item if any
        current_item = slot.item_id
        if current_item:
            self._unequip_item_effects(current_item)
            
        # Equip new item
        slot.item_id = item_id
        slot.quantity = 1
        slot.equipped = True
        
        # Apply equipment effects
        self._equip_item_effects(item_id)
        
        # Update set bonuses
        self._update_set_bonuses()
        
        return True
        
    def unequip_item(self, slot_name: str) -> Optional[str]:
        """Unequip item from slot"""
        slot = self.slots.get(slot_name)
        if not slot or not slot.equipped or not slot.item_id:
            return None
            
        item_id = slot.item_id
        
        # Remove equipment effects
        self._unequip_item_effects(item_id)
        
        # Unequip item
        slot.item_id = None
        slot.quantity = 0
        slot.equipped = False
        
        # Update set bonuses
        self._update_set_bonuses()
        
        return item_id
        
    def get_equipped_items(self) -> Dict[str, Optional[str]]:
        """Get all equipped items"""
        return {slot_name: slot.item_id for slot_name, slot in self.slots.items() 
                if slot.equipped and slot.item_id}
                
    def get_equipped_item(self, slot_name: str) -> Optional[str]:
        """Get equipped item in specific slot"""
        slot = self.slots.get(slot_name)
        if slot and slot.equipped and slot.item_id:
            return slot.item_id
        return None
        
    def is_equipped(self, slot_name: str) -> bool:
        """Check if slot has equipped item"""
        slot = self.slots.get(slot_name)
        return slot and slot.equipped and slot.item_id is not None
        
    def get_slot_for_item(self, item_id: str) -> Optional[str]:
        """Get slot name for equipped item"""
        for slot_name, slot in self.slots.items():
            if slot.equipped and slot.item_id == item_id:
                return slot_name
        return None
        
    def get_equipped_bonuses(self) -> Dict[str, int]:
        """Get all stat bonuses from equipped items"""
        return self.bonuses.copy()
        
    def get_bonus(self, stat_name: str) -> int:
        """Get specific stat bonus"""
        return self.bonuses.get(stat_name, 0)
        
    def get_set_bonuses(self) -> Dict[str, int]:
        """Get set bonuses"""
        return self.set_bonuses.copy()
        
    def add_equipment_set(self, set_name: str, required_slots: List[str], 
                         bonuses: Dict[str, int]) -> None:
        """Add equipment set definition"""
        self.equipped_sets[set_name] = {
            "required_slots": required_slots,
            "bonuses": bonuses
        }
        
    def check_equipment_sets(self) -> Dict[str, bool]:
        """Check which equipment sets are equipped"""
        equipped_sets = {}
        
        for set_name, set_data in self.equipped_sets.items():
            equipped = True
            for slot_name in set_data["required_slots"]:
                if not self.is_equipped(slot_name):
                    equipped = False
                    break
                    
            equipped_sets[set_name] = equipped
            
        return equipped_sets
        
    def get_durability(self, item_id: str) -> Optional[int]:
        """Get current durability of item"""
        return self.current_durability.get(item_id)
        
    def get_max_durability(self, item_id: str) -> Optional[int]:
        """Get max durability of item"""
        return self.max_durability.get(item_id)
        
    def set_durability(self, item_id: str, current: int, maximum: int) -> None:
        """Set item durability"""
        self.max_durability[item_id] = maximum
        self.current_durability[item_id] = current
        
    def damage_item(self, item_id: str, amount: int) -> bool:
        """Damage item durability"""
        if item_id not in self.current_durability:
            return False
            
        self.current_durability[item_id] = max(0, self.current_durability[item_id] - amount)
        
        # Check if item is broken
        if self.current_durability[item_id] <= 0:
            # Unequip broken item
            slot_name = self.get_slot_for_item(item_id)
            if slot_name:
                self.unequip_item(slot_name)
            return False
            
        return True
        
    def repair_item(self, item_id: str, amount: int) -> bool:
        """Repair item durability"""
        if item_id not in self.current_durability:
            return False
            
        max_durability = self.max_durability.get(item_id, 100)
        self.current_durability[item_id] = min(
            max_durability, 
            self.current_durability[item_id] + amount
        )
        return True
        
    def is_item_broken(self, item_id: str) -> bool:
        """Check if item is broken"""
        return (item_id in self.current_durability and 
                self.current_durability[item_id] <= 0)
                
    def _is_slot_appropriate(self, slot_name: str, item_id: str) -> bool:
        """Check if item is appropriate for slot"""
        # This would normally check item type vs slot type
        # For now, assume all items can go in all slots
        return True
        
    def _equip_item_effects(self, item_id: str) -> None:
        """Apply effects of equipped item"""
        # This would normally look up item effects and apply them
        # For now, just add some generic bonuses
        self.bonuses["attack"] = self.bonuses.get("attack", 0) + 1
        self.bonuses["defense"] = self.bonuses.get("defense", 0) + 1
        
    def _unequip_item_effects(self, item_id: str) -> None:
        """Remove effects of unequipped item"""
        # This would normally remove item effects
        # For now, just remove generic bonuses
        self.bonuses["attack"] = max(0, self.bonuses.get("attack", 0) - 1)
        self.bonuses["defense"] = max(0, self.bonuses.get("defense", 0) - 1)
        
    def _update_set_bonuses(self) -> None:
        """Update set bonuses based on equipped sets"""
        # Clear existing set bonuses
        self.set_bonuses.clear()
        
        # Check each set
        for set_name, set_data in self.equipped_sets.items():
            equipped = True
            for slot_name in set_data["required_slots"]:
                if not self.is_equipped(slot_name):
                    equipped = False
                    break
                    
            if equipped:
                # Apply set bonuses
                for stat_name, bonus in set_data["bonuses"].items():
                    self.set_bonuses[stat_name] = self.set_bonuses.get(stat_name, 0) + bonus
                    
    def get_equipment_info(self) -> Dict[str, Any]:
        """Get equipment information"""
        equipped_items = self.get_equipped_items()
        total_bonuses = self.get_equipped_bonuses()
        set_bonuses = self.get_set_bonuses()
        
        return {
            "equipped_items": equipped_items,
            "total_bonuses": total_bonuses,
            "set_bonuses": set_bonuses,
            "item_count": len(equipped_items),
            "broken_items": [item_id for item_id in self.current_durability 
                           if self.is_item_broken(item_id)]
        }
        
    def get_all_slots(self) -> Dict[str, InventorySlot]:
        """Get all equipment slots"""
        return self.slots.copy()
        
    def get_slot(self, slot_name: str) -> Optional[InventorySlot]:
        """Get specific equipment slot"""
        return self.slots.get(slot_name)
        
    def update(self, delta_time: float, entity: Any) -> None:
        """Update equipment component"""
        # Equipment doesn't need regular updates in basic implementation
        pass
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = super().to_dict()
        data.update({
            "slots": {slot_name: slot.to_dict() for slot_name, slot in self.slots.items()},
            "bonuses": self.bonuses,
            "set_bonuses": self.set_bonuses,
            "equipped_sets": self.equipped_sets,
            "max_durability": self.max_durability,
            "current_durability": self.current_durability
        })
        return data
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Equipment':
        """Create equipment component from dictionary"""
        equipment = cls()
        equipment.enabled = data.get("enabled", True)
        equipment.bonuses = data.get("bonuses", {})
        equipment.set_bonuses = data.get("set_bonuses", {})
        equipment.equipped_sets = data.get("equipped_sets", {})
        equipment.max_durability = data.get("max_durability", {})
        equipment.current_durability = data.get("current_durability", {})
        
        # Load slots
        for slot_name, slot_data in data.get("slots", {}).items():
            equipment.slots[slot_name] = InventorySlot.from_dict(slot_data)
            
        return equipment