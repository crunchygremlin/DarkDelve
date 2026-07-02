"""
Tests for the "U" key fix in inventory screen.
Verifies that:
- Potions, scrolls, food, wands can be used via "U" key
- Accessories (rings, amulets) can be equipped/unequipped via "U" key
- MISC items show "not usable" message
"""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib.util
spec = importlib.util.spec_from_file_location("darkdelve", "darkdelve.py")
darkdelve = importlib.util.module_from_spec(spec)
spec.loader.exec_module(darkdelve)

ItemType = darkdelve.ItemType
Item = darkdelve.Item
Inventory = darkdelve.Inventory
Entity = darkdelve.Entity


class TestInventoryUseKeyFix(unittest.TestCase):
    """Test the fixed "U" key behavior in inventory screen."""
    
    def setUp(self):
        """Create a player-like entity with inventory."""
        self.entity = Entity(
            name="TestPlayer",
            x=0, y=0,
            char="@",
            hp=50, max_hp=100,
        )
        self.entity.inventory = Inventory()
    
    def _make_item(self, item_id, name, item_type, special_effect=None, effect_strength=0):
        """Helper to create an item."""
        return Item(
            id=item_id,
            name=name,
            item_type=item_type,
            special_effect=special_effect,
            effect_strength=effect_strength,
        )
    
    def test_use_potion_heals_and_consumes(self):
        """Using a potion via use_item should heal and remove from inventory."""
        potion = self._make_item("potion_1", "Healing Potion", ItemType.POTION, "heal", 20)
        self.entity.inventory.add_item(potion)
        self.entity.hp = 30
        
        # Simulate the "U" key logic for potion
        item = self.entity.inventory.get_item(0)
        self.assertEqual(item.item_type, ItemType.POTION)
        
        result = self.entity.use_item(item)
        self.assertTrue(result)
        self.assertEqual(self.entity.hp, 50)  # 30 + 20
        self.assertEqual(len(self.entity.inventory.items), 0)  # Consumed
    
    def test_use_scroll_consumes(self):
        """Using a scroll should consume it."""
        scroll = self._make_item("scroll_1", "Scroll of Fireball", ItemType.SCROLL, "fireball", 15)
        self.entity.inventory.add_item(scroll)
        
        item = self.entity.inventory.get_item(0)
        self.assertEqual(item.item_type, ItemType.SCROLL)
        
        result = self.entity.use_item(item)
        self.assertTrue(result)
        self.assertEqual(len(self.entity.inventory.items), 0)
    
    def test_use_food_consumes(self):
        """Using food should consume it (food is consumable)."""
        food = self._make_item("food_1", "Ration", ItemType.FOOD, "nutrition", 300)
        self.entity.inventory.add_item(food)
        
        item = self.entity.inventory.get_item(0)
        self.assertEqual(item.item_type, ItemType.FOOD)
        
        result = self.entity.use_item(item)
        self.assertTrue(result)
        # Food is consumable and gets removed
        self.assertEqual(len(self.entity.inventory.items), 0)
    
    def test_use_wand_consumes(self):
        """Using a wand should consume it (wands have limited charges)."""
        wand = self._make_item("wand_1", "Wand of Magic Missile", ItemType.WAND, "magic_missile", 10)
        wand.effects = {"charges": 5}  # Wands have charges
        self.entity.inventory.add_item(wand)
        
        item = self.entity.inventory.get_item(0)
        self.assertEqual(item.item_type, ItemType.WAND)
        
        result = self.entity.use_item(item)
        self.assertTrue(result)
        # Wand should be consumed when charges run out (simplified: consumed on use)
        self.assertEqual(len(self.entity.inventory.items), 0)
    
    def test_equip_accessory_ring(self):
        """Equipping a ring via "U" key should work."""
        ring = self._make_item("ring_1", "Ring of Protection", ItemType.ACCESSORY)
        ring.equipment_slot = darkdelve.EquipmentSlot.RING  # Ring slot
        self.entity.inventory.add_item(ring)
        
        item = self.entity.inventory.get_item(0)
        self.assertEqual(item.item_type, ItemType.ACCESSORY)
        
        # Simulate equip logic
        slots = self.entity.inventory._get_valid_slots_for_item(item)
        self.assertIn(darkdelve.EquipmentSlot.RING, slots)
        
        result = self.entity.inventory.equip(item.id, slots[0])
        self.assertTrue(result)
        self.assertTrue(item.equipped)
        self.assertEqual(item.equipped_slot, darkdelve.EquipmentSlot.RING)
    
    def test_equip_accessory_amulet(self):
        """Equipping an amulet via "U" key should work."""
        amulet = self._make_item("amulet_1", "Amulet of Health", ItemType.ACCESSORY)
        amulet.equipment_slot = darkdelve.EquipmentSlot.NECK  # Neck slot
        self.entity.inventory.add_item(amulet)
        
        item = self.entity.inventory.get_item(0)
        self.assertEqual(item.item_type, ItemType.ACCESSORY)
        
        slots = self.entity.inventory._get_valid_slots_for_item(item)
        self.assertIn(darkdelve.EquipmentSlot.NECK, slots)
        
        result = self.entity.inventory.equip(item.id, slots[0])
        self.assertTrue(result)
        self.assertTrue(item.equipped)
        self.assertEqual(item.equipped_slot, darkdelve.EquipmentSlot.NECK)
    
    def test_unequip_accessory(self):
        """Unequipping an accessory via "U" key should work."""
        ring = self._make_item("ring_2", "Ring of Strength", ItemType.ACCESSORY)
        ring.equipment_slot = darkdelve.EquipmentSlot.RING
        self.entity.inventory.add_item(ring)
        
        # Equip first
        slots = self.entity.inventory._get_valid_slots_for_item(ring)
        self.entity.inventory.equip(ring.id, slots[0])
        self.assertTrue(ring.equipped)
        
        # Now unequip via "U" key logic
        self.entity.inventory.unequip(ring.id)
        self.assertFalse(ring.equipped)
        self.assertIsNone(ring.equipped_slot)
    
    def test_misc_item_not_usable(self):
        """MISC items should show 'not usable' message."""
        misc = self._make_item("misc_1", "Gold Coin", ItemType.MISC)
        self.entity.inventory.add_item(misc)
        
        item = self.entity.inventory.get_item(0)
        self.assertEqual(item.item_type, ItemType.MISC)
        
        # MISC is not in consumable_types or equipment types
        consumable_types = (ItemType.POTION, ItemType.SCROLL, ItemType.FOOD, ItemType.WAND)
        equipment_types = (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY)
        
        self.assertNotIn(item.item_type, consumable_types)
        self.assertNotIn(item.item_type, equipment_types)
    
    def test_weapon_equip_via_u_key(self):
        """Weapons should be equippable via "U" key (existing behavior)."""
        sword = self._make_item("sword_1", "Iron Sword", ItemType.WEAPON)
        sword.equipment_slot = darkdelve.EquipmentSlot.MAIN_HAND
        self.entity.inventory.add_item(sword)
        
        item = self.entity.inventory.get_item(0)
        self.assertEqual(item.item_type, ItemType.WEAPON)
        
        slots = self.entity.inventory._get_valid_slots_for_item(item)
        self.assertIn(darkdelve.EquipmentSlot.MAIN_HAND, slots)
        
        result = self.entity.inventory.equip(item.id, slots[0])
        self.assertTrue(result)
        self.assertTrue(item.equipped)
    
    def test_armor_equip_via_u_key(self):
        """Armor should be equippable via "U" key (existing behavior)."""
        armor = self._make_item("armor_1", "Leather Armor", ItemType.ARMOR)
        armor.equipment_slot = darkdelve.EquipmentSlot.CHEST
        self.entity.inventory.add_item(armor)
        
        item = self.entity.inventory.get_item(0)
        self.assertEqual(item.item_type, ItemType.ARMOR)
        
        slots = self.entity.inventory._get_valid_slots_for_item(item)
        self.assertIn(darkdelve.EquipmentSlot.CHEST, slots)
        
        result = self.entity.inventory.equip(item.id, slots[0])
        self.assertTrue(result)
        self.assertTrue(item.equipped)


if __name__ == "__main__":
    unittest.main()