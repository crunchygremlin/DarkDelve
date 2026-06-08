#!/usr/bin/env python3
"""
Test suite for DarkDelve entity system
"""

import unittest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path to import darkdelve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from darkdelve import Entity, Item, Inventory, ItemType, EquipmentSlot, COLORS


class TestEntitySystem(unittest.TestCase):
    """Test cases for Entity system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.player = Entity(
            x=5, y=5,
            char="@",
            color=COLORS['player'],
            name="Test Player",
            blocks=True
        )
        
        self.enemy = Entity(
            x=10, y=10,
            char="g",
            color=COLORS['enemy_normal'],
            name="Goblin",
            blocks=True
        )
        
        self.item = Item(
            id="test_sword",
            name="Iron Sword",
            description="A sharp iron sword",
            glyph="/",
            color=COLORS['item'],
            item_type=ItemType.WEAPON,
            equipment_slot=EquipmentSlot.MAIN_HAND
        )
        
    def test_entity_creation(self):
        """Test basic entity creation"""
        self.assertEqual(self.player.x, 5)
        self.assertEqual(self.player.y, 5)
        self.assertEqual(self.player.char, "@")
        self.assertEqual(self.player.name, "Test Player")
        self.assertTrue(self.player.blocks)
        
    def test_entity_movement(self):
        """Test entity movement"""
        # Test valid movement
        new_x, new_y = 7, 7
        dungeon_map = np.zeros((20, 20), dtype=int)  # Empty map
        
        # Create a simple path
        dungeon_map[5:8, 5:8] = 0  # Clear path
        
        result = self.player.move(new_x - self.player.x, new_y - self.player.y, dungeon_map)
        self.assertTrue(result)
        self.assertEqual(self.player.x, new_x)
        self.assertEqual(self.player.y, new_y)
        
    def test_entity_collision(self):
        """Test entity collision detection"""
        # Create a map with walls
        dungeon_map = np.ones((20, 20), dtype=int)  # All walls
        dungeon_map[5:8, 5:8] = 0  # Clear path
        
        # Try to move into a wall
        result = self.player.move(10, 0, dungeon_map)
        self.assertFalse(result)
        self.assertEqual(self.player.x, 5)  # Position should not change
        
    def test_entity_distance_calculation(self):
        """Test distance calculation between entities"""
        distance = self.player.distance_to(self.enemy)
        expected_distance = abs(5 - 10) + abs(5 - 10)  # Manhattan distance
        self.assertEqual(distance, expected_distance)
        
    def test_item_creation(self):
        """Test item creation"""
        self.assertEqual(self.item.id, "test_sword")
        self.assertEqual(self.item.name, "Iron Sword")
        self.assertEqual(self.item.item_type, ItemType.WEAPON)
        self.assertEqual(self.item.equipment_slot, EquipmentSlot.MAIN_HAND)
        self.assertFalse(self.item.identified)
        
    def test_inventory_creation(self):
        """Test inventory creation"""
        inventory = Inventory()
        self.assertEqual(len(inventory.items), 0)
        self.assertEqual(inventory.capacity, 26)
        
    def test_inventory_add_item(self):
        """Test adding items to inventory"""
        inventory = Inventory()
        result = inventory.add_item(self.item)
        self.assertTrue(result)
        self.assertEqual(len(inventory.items), 1)
        self.assertEqual(inventory.items[0], self.item)
        
    def test_inventory_remove_item(self):
        """Test removing items from inventory"""
        inventory = Inventory()
        inventory.add_item(self.item)
        
        result = inventory.remove_item(self.item)
        self.assertTrue(result)
        self.assertEqual(len(inventory.items), 0)
        
    def test_inventory_capacity(self):
        """Test inventory capacity limits"""
        inventory = Inventory(capacity=3)
        
        # Add items up to capacity
        for i in range(3):
            item = Item(
                id=f"item_{i}",
                name=f"Item {i}",
                description=f"Test item {i}",
                glyph="*",
                color=COLORS['item'],
                item_type=ItemType.MISC
            )
            inventory.add_item(item)
            
        # Try to add one more item
        extra_item = Item(
            id="extra_item",
            name="Extra Item",
            description="This should not fit",
            glyph="*",
            color=COLORS['item'],
            item_type=ItemType.MISC
        )
        
        result = inventory.add_item(extra_item)
        self.assertFalse(result)
        self.assertEqual(len(inventory.items), 3)
        
    def test_item_equipment_slots(self):
        """Test equipment slot functionality"""
        # Test weapon slot
        weapon = Item(
            id="sword",
            name="Sword",
            description="A sharp sword",
            glyph="/",
            color=COLORS['item'],
            item_type=ItemType.WEAPON,
            equipment_slot=EquipmentSlot.MAIN_HAND
        )
        
        # Test armor slot
        armor = Item(
            id="armor",
            name="Leather Armor",
            description="Protective leather armor",
            glyph="[",
            color=COLORS['equipment'],
            item_type=ItemType.ARMOR,
            equipment_slot=EquipmentSlot.BODY
        )
        
        self.assertEqual(weapon.equipment_slot, EquipmentSlot.MAIN_HAND)
        self.assertEqual(armor.equipment_slot, EquipmentSlot.BODY)
        
    def test_entity_component_system(self):
        """Test entity component system"""
        # Test adding components to entity
        combat_component = MagicMock()
        movement_component = MagicMock()
        
        self.player.add_component(combat_component, "combat")
        self.player.add_component(movement_component, "movement")
        
        # Test retrieving components
        retrieved_combat = self.player.get_component("combat")
        self.assertEqual(retrieved_combat, combat_component)
        
        retrieved_movement = self.player.get_component("movement")
        self.assertEqual(retrieved_movement, movement_component)
        
        # Test removing components
        self.player.remove_component("combat")
        self.assertIsNone(self.player.get_component("combat"))
        self.assertIsNotNone(self.player.get_component("movement"))


class TestGameLogic(unittest.TestCase):
    """Test cases for game logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.player = Entity(
            x=5, y=5,
            char="@",
            color=COLORS['player'],
            name="Test Player",
            blocks=True
        )
        
    def test_player_movement_on_empty_map(self):
        """Test player movement on an empty map"""
        dungeon_map = np.zeros((20, 20), dtype=int)  # Empty map
        
        # Move player
        self.player.move(2, 1, dungeon_map)
        self.assertEqual(self.player.x, 7)
        self.assertEqual(self.player.y, 6)
        
    def test_player_collision_with_walls(self):
        """Test player collision with walls"""
        dungeon_map = np.ones((20, 20), dtype=int)  # All walls
        dungeon_map[5:8, 5:8] = 0  # Clear path around player
        
        # Try to move into a wall
        self.player.move(5, 0, dungeon_map)  # Move right into wall
        self.assertEqual(self.player.x, 5)  # Position should not change
        
    def test_player_movement_bounds(self):
        """Test player movement within bounds"""
        dungeon_map = np.zeros((20, 20), dtype=int)
        
        # Try to move beyond map bounds
        self.player.move(-10, 0, dungeon_map)  # Move left beyond bounds
        self.assertEqual(self.player.x, 0)  # Should be clamped to map bounds
        
        self.player.move(0, -10, dungeon_map)  # Move up beyond bounds
        self.assertEqual(self.player.y, 0)  # Should be clamped to map bounds
        
        self.player.move(25, 0, dungeon_map)  # Move right beyond bounds
        self.assertEqual(self.player.x, 19)  # Should be clamped to map bounds
        
        self.player.move(0, 25, dungeon_map)  # Move down beyond bounds
        self.assertEqual(self.player.y, 19)  # Should be clamped to map bounds


class TestItemSystem(unittest.TestCase):
    """Test cases for item system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.inventory = Inventory()
        
        # Create test items
        self.sword = Item(
            id="iron_sword",
            name="Iron Sword",
            description="A sharp iron sword",
            glyph="/",
            color=COLORS['item'],
            item_type=ItemType.WEAPON,
            equipment_slot=EquipmentSlot.MAIN_HAND
        )
        
        self.potion = Item(
            id="health_potion",
            name="Health Potion",
            description="A red potion that restores health",
            glyph="!",
            color=COLORS['item'],
            item_type=ItemType.CONSUMABLE,
            equipment_slot=None
        )
        
    def test_add_multiple_items(self):
        """Test adding multiple items to inventory"""
        self.inventory.add_item(self.sword)
        self.inventory.add_item(self.potion)
        
        self.assertEqual(len(self.inventory.items), 2)
        self.assertIn(self.sword, self.inventory.items)
        self.assertIn(self.potion, self.inventory.items)
        
    def test_remove_item_not_in_inventory(self):
        """Test removing an item that's not in inventory"""
        result = self.inventory.remove_item(self.sword)
        self.assertFalse(result)
        self.assertEqual(len(self.inventory.items), 0)
        
    def test_get_item_by_index(self):
        """Test getting items by index"""
        self.inventory.add_item(self.sword)
        self.inventory.add_item(self.potion)
        
        first_item = self.inventory.get_item(0)
        second_item = self.inventory.get_item(1)
        
        self.assertEqual(first_item, self.sword)
        self.assertEqual(second_item, self.potion)
        
        # Test out of bounds
        nonexistent_item = self.inventory.get_item(5)
        self.assertIsNone(nonexistent_item)
        
    def test_inventory_weight(self):
        """Test inventory weight calculation"""
        # Add items with weight
        self.sword.effects['weight'] = 5
        self.potion.effects['weight'] = 1
        
        self.inventory.add_item(self.sword)
        self.inventory.add_item(self.potion)
        
        total_weight = self.inventory.get_total_weight()
        self.assertEqual(total_weight, 6)
        
    def test_equipment_slots(self):
        """Test equipment slot functionality"""
        # Test that equipment items can be equipped
        self.inventory.add_item(self.sword)
        
        # Get valid slots for the item
        valid_slots = self.inventory._get_valid_slots_for_item(self.sword)
        self.assertIn(EquipmentSlot.MAIN_HAND, valid_slots)
        
        # Test equipping
        result = self.inventory.equip(self.sword.id, EquipmentSlot.MAIN_HAND)
        self.assertTrue(result)
        self.assertTrue(self.sword.equipped)


if __name__ == '__main__':
    unittest.main()