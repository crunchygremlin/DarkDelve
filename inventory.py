"""
Inventory System - Player items, equipment, and inventory management
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class ItemType(Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    POTION = "potion"
    SCROLL = "scroll"
    MISC = "misc"


class EquipmentSlot(Enum):
    HEAD = "head"
    CHEST = "chest"
    HANDS = "hands"
    LEGS = "legs"
    FEET = "feet"
    MAIN_HAND = "main_hand"
    OFF_HAND = "off_hand"


@dataclass
class Item:
    """Represents a single item"""
    id: str  # Unique identifier
    name: str
    item_type: ItemType
    symbol: str  # Single ASCII character
    weight: int  # In arbitrary units
    value: int  # Gold value
    
    # Mechanical properties
    damage_bonus: int = 0      # For weapons
    defense_bonus: int = 0     # For armor
    to_hit_bonus: int = 0      # For weapons
    encumbrance: int = 0       # For armor
    
    # Special properties
    special_effect: Optional[str] = None  # e.g., "lifesteal", "fire_damage"
    effect_strength: int = 0
    
    # Flavor text
    description: str = ""
    
    # Status
    equipped: bool = False
    equipped_slot: Optional[EquipmentSlot] = None
    
    def get_stat_string(self) -> str:
        """Get item stats as string"""
        stats = []
        if self.damage_bonus > 0:
            stats.append(f"+{self.damage_bonus} DMG")
        if self.to_hit_bonus > 0:
            stats.append(f"+{self.to_hit_bonus} HIT")
        if self.defense_bonus > 0:
            stats.append(f"+{self.defense_bonus} DEF")
        if self.special_effect:
            stats.append(f"{self.special_effect}")
        return " [" + ", ".join(stats) + "]" if stats else ""
    
    def __str__(self) -> str:
        equipped_mark = " (equipped)" if self.equipped else ""
        return f"{self.name}{self.get_stat_string()}{equipped_mark}"


class Inventory:
    """Player inventory with equipment slots"""
    
    def __init__(self, max_weight: int = 100):
        self.items: List[Item] = []
        self.max_weight = max_weight
        self.equipment: Dict[EquipmentSlot, Optional[Item]] = {
            slot: None for slot in EquipmentSlot
        }
    
    def add_item(self, item: Item) -> bool:
        """Add item to inventory"""
        if self.get_total_weight() + item.weight > self.max_weight:
            return False
        self.items.append(item)
        return True
    
    def remove_item(self, item_id: str) -> bool:
        """Remove item from inventory by ID"""
        for i, item in enumerate(self.items):
            if item.id == item_id:
                if item.equipped:
                    self.unequip(item_id)
                self.items.pop(i)
                return True
        return False
    
    def find_item(self, item_id: str) -> Optional[Item]:
        """Find item by ID"""
        for item in self.items:
            if item.id == item_id:
                return item
        return None
    
    def equip(self, item_id: str, slot: EquipmentSlot) -> bool:
        """Equip an item to a slot"""
        item = self.find_item(item_id)
        if not item:
            return False
        
        # Can't equip if wrong slot type
        valid_slots = self._get_valid_slots_for_item(item)
        if slot not in valid_slots:
            return False
        
        # Unequip current item in slot if exists
        if self.equipment[slot] is not None:
            old_item = self.equipment[slot]
            old_item.equipped = False
            old_item.equipped_slot = None
        
        # Equip new item
        item.equipped = True
        item.equipped_slot = slot
        self.equipment[slot] = item
        return True
    
    def unequip(self, item_id: str) -> bool:
        """Unequip an item"""
        item = self.find_item(item_id)
        if not item or not item.equipped:
            return False
        
        if item.equipped_slot:
            self.equipment[item.equipped_slot] = None
        item.equipped = False
        item.equipped_slot = None
        return True
    
    def _get_valid_slots_for_item(self, item: Item) -> List[EquipmentSlot]:
        """Get valid equipment slots for an item type"""
        slots = {
            ItemType.WEAPON: [EquipmentSlot.MAIN_HAND, EquipmentSlot.OFF_HAND],
            ItemType.ARMOR: {
                "helm": [EquipmentSlot.HEAD],
                "chest": [EquipmentSlot.CHEST],
                "hands": [EquipmentSlot.HANDS],
                "legs": [EquipmentSlot.LEGS],
                "feet": [EquipmentSlot.FEET],
                "shield": [EquipmentSlot.OFF_HAND],
            },
            ItemType.MISC: [],
            ItemType.POTION: [],
            ItemType.SCROLL: [],
        }
        
        if item.item_type == ItemType.WEAPON:
            return slots[ItemType.WEAPON]
        elif item.item_type == ItemType.ARMOR:
            # Try to infer armor type from name
            name_lower = item.name.lower()
            for armor_type, armor_slots in slots[ItemType.ARMOR].items():
                if armor_type in name_lower:
                    return armor_slots
            return []
        else:
            return []
    
    def get_total_weight(self) -> int:
        """Get total weight of all items"""
        return sum(item.weight for item in self.items)
    
    def get_defense_bonus(self) -> int:
        """Sum all defense bonuses from equipped armor"""
        return sum(
            item.defense_bonus for item in self.equipment.values()
            if item and item.equipped
        )
    
    def get_damage_bonus(self) -> int:
        """Get damage bonus from equipped weapon"""
        weapon = self.equipment[EquipmentSlot.MAIN_HAND]
        return weapon.damage_bonus if weapon and weapon.equipped else 0
    
    def get_to_hit_bonus(self) -> int:
        """Get to-hit bonus from equipped weapon"""
        weapon = self.equipment[EquipmentSlot.MAIN_HAND]
        return weapon.to_hit_bonus if weapon and weapon.equipped else 0
    
    def display(self) -> str:
        """Format inventory for display"""
        lines = [
            f"═ INVENTORY (Weight: {self.get_total_weight()}/{self.max_weight}) ═",
        ]
        
        # Equipment slots
        lines.append("\n▼ EQUIPPED:")
        for slot in EquipmentSlot:
            item = self.equipment[slot]
            if item:
                lines.append(f"  {slot.value:12} : {item}")
            else:
                lines.append(f"  {slot.value:12} : [empty]")
        
        # Backpack
        if self.items:
            lines.append("\n▼ BACKPACK:")
            for item in self.items:
                status = " (E)" if item.equipped else ""
                lines.append(f"  □ {item}{status}")
        else:
            lines.append("\n▼ BACKPACK: (empty)")
        
        return "\n".join(lines)


class ItemFactory:
    """Helper to create common items"""
    
    @staticmethod
    def create_weapon(
        name: str,
        item_id: str,
        damage: int = 1,
        to_hit: int = 0,
        weight: int = 5,
        value: int = 50,
        description: str = ""
    ) -> Item:
        return Item(
            id=item_id,
            name=name,
            item_type=ItemType.WEAPON,
            symbol="/",
            damage_bonus=damage,
            to_hit_bonus=to_hit,
            weight=weight,
            value=value,
            description=description,
        )
    
    @staticmethod
    def create_armor(
        name: str,
        item_id: str,
        defense: int = 1,
        weight: int = 10,
        value: int = 50,
        encumbrance: int = 1,
        description: str = ""
    ) -> Item:
        return Item(
            id=item_id,
            name=name,
            item_type=ItemType.ARMOR,
            symbol="[",
            defense_bonus=defense,
            weight=weight,
            value=value,
            encumbrance=encumbrance,
            description=description,
        )
    
    @staticmethod
    def create_potion(
        name: str,
        item_id: str,
        effect: str,
        strength: int = 10,
        weight: int = 1,
        value: int = 25,
        description: str = ""
    ) -> Item:
        return Item(
            id=item_id,
            name=name,
            item_type=ItemType.POTION,
            symbol="!",
            special_effect=effect,
            effect_strength=strength,
            weight=weight,
            value=value,
            description=description,
        )
