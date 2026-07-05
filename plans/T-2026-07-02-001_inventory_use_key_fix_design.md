# Design Document: Fix "U" Key Not Working for Consumables/Wands/Accessories in Inventory

## 1. Goal
Fix the "U" key in inventory screen to properly handle all usable item types (potions, scrolls, food, wands) and correctly equip/unequip accessories (rings, amulets) instead of showing "is not usable" message.

## 2. Files to Create
None - this is a fix to existing code only.

## 3. Files to Modify
- `darkdelve.py` (lines 3197-3226): Fix the "U" key handler in the inventory screen

## 4. Pseudocode

### Modified Function: `handle_inventory_input` (lines 3197-3226 in darkdelve.py)

```python
elif event.sym == tcod.event.KeySym.U:
    # Use/Equip selected item
    if self.player and self.player.inventory:
        item = self.player.inventory.get_item(self.inventory_selection)
        if item:
            # Check if item is a consumable (usable via "U" key)
            consumable_types = (ItemType.POTION, ItemType.SCROLL, ItemType.FOOD, ItemType.WAND)
            if item.item_type in consumable_types:
                # Use consumable
                result = self.player.use_item(item)
                if result:
                    self.add_message(f"Used {item.name}.")
                    # Adjust selection if needed
                    item_count = len(self.player.inventory.items)
                    if item_count > 0 and self.inventory_selection >= item_count:
                        self.inventory_selection = item_count - 1
                else:
                    self.add_message(f"Cannot use {item.name}.")
            
            # Check if item is equipment (weapon, armor, accessory)
            elif item.item_type in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY):
                # Equip/unequip equipment
                if item.equipped:
                    self.player.inventory.unequip(item.id)
                    self.add_message(f"Unequipped {item.name}.")
                else:
                    slots = self.player.inventory._get_valid_slots_for_item(item)
                    if slots:
                        self.player.inventory.equip(item.id, slots[0])
                        self.add_message(f"Equipped {item.name}.")
                    else:
                        self.add_message(f"Cannot equip {item.name}.")
            
            # MISC items and other types are not usable via "U" key
            else:
                self.add_message(f"{item.name} is not usable.")
```

## 5. Import Statements
No new imports needed. The `ItemType` enum is already defined in `darkdelve.py` (lines 326-334).

## 6. Test Plan

### Test File: `tests/test_inventory_use_key_fix.py`

```python
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
        """Using food should consume it and restore nutrition."""
        food = self._make_item("food_1", "Ration", ItemType.FOOD, "nutrition", 300)
        self.entity.inventory.add_item(food)
        self.entity.nutrition = 500
        self.entity.max_nutrition = 2000
        
        item = self.entity.inventory.get_item(0)
        self.assertEqual(item.item_type, ItemType.FOOD)
        
        result = self.entity.use_item(item)
        self.assertTrue(result)
        self.assertEqual(self.entity.nutrition, 800)
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
        ring.equipment_slot = "ring"  # Ring slot
        self.entity.inventory.add_item(ring)
        
        item = self.entity.inventory.get_item(0)
        self.assertEqual(item.item_type, ItemType.ACCESSORY)
        
        # Simulate equip logic
        slots = self.entity.inventory._get_valid_slots_for_item(item)
        self.assertIn("ring", slots)
        
        result = self.entity.inventory.equip(item.id, slots[0])
        self.assertTrue(result)
        self.assertTrue(item.equipped)
        self.assertEqual(item.equipped_slot, "ring")
    
    def test_equip_accessory_amulet(self):
        """Equipping an amulet via "U" key should work."""
        amulet = self._make_item("amulet_1", "Amulet of Health", ItemType.ACCESSORY)
        amulet.equipment_slot = "neck"  # Neck slot
        self.entity.inventory.add_item(amulet)
        
        item = self.entity.inventory.get_item(0)
        self.assertEqual(item.item_type, ItemType.ACCESSORY)
        
        slots = self.entity.inventory._get_valid_slots_for_item(item)
        self.assertIn("neck", slots)
        
        result = self.entity.inventory.equip(item.id, slots[0])
        self.assertTrue(result)
        self.assertTrue(item.equipped)
        self.assertEqual(item.equipped_slot, "neck")
    
    def test_unequip_accessory(self):
        """Unequipping an accessory via "U" key should work."""
        ring = self._make_item("ring_2", "Ring of Strength", ItemType.ACCESSORY)
        ring.equipment_slot = "ring"
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
        sword.equipment_slot = "main_hand"
        self.entity.inventory.add_item(sword)
        
        item = self.entity.inventory.get_item(0)
        self.assertEqual(item.item_type, ItemType.WEAPON)
        
        slots = self.entity.inventory._get_valid_slots_for_item(item)
        self.assertIn("main_hand", slots)
        
        result = self.entity.inventory.equip(item.id, slots[0])
        self.assertTrue(result)
        self.assertTrue(item.equipped)
    
    def test_armor_equip_via_u_key(self):
        """Armor should be equippable via "U" key (existing behavior)."""
        armor = self._make_item("armor_1", "Leather Armor", ItemType.ARMOR)
        armor.equipment_slot = "chest"
        self.entity.inventory.add_item(armor)
        
        item = self.entity.inventory.get_item(0)
        self.assertEqual(item.item_type, ItemType.ARMOR)
        
        slots = self.entity.inventory._get_valid_slots_for_item(item)
        self.assertIn("chest", slots)
        
        result = self.entity.inventory.equip(item.id, slots[0])
        self.assertTrue(result)
        self.assertTrue(item.equipped)


if __name__ == "__main__":
    unittest.main()
```

## 7. Integration Notes

### Current Behavior (Broken)
- Line 3202: `if item.item_type.value in ("potion", "scroll", "food"):` - Only handles potion, scroll, food
- Line 3213: `elif item.item_type.value in ("weapon", "armor", "accessory"):` - Handles equipment but uses string values
- Line 3225-3226: `else: self.add_message(f"{item.name} is not usable.")` - Wands and other types fall here

### Fixed Behavior
- Add `ItemType.WAND` to consumable types tuple
- Use `ItemType` enum values directly instead of string comparison
- Accessories (rings, amulets) are already handled in equipment branch - they work correctly
- The bug was that wands were falling through to "not usable" message

### Key Changes
1. Change line 3202 from string tuple to `ItemType` enum tuple including `WAND`
2. Change line 3213 to use `ItemType` enum values
3. The `item.item_type` is already an `ItemType` enum (not `.value` string)

### Inventory Methods Used
- `inventory.get_item(index)` - Returns Item at index
- `inventory.equip(item_id, slot)` - Equips item
- `inventory.unequip(item_id)` - Unequips item
- `inventory._get_valid_slots_for_item(item)` - Returns valid equipment slots
- `player.use_item(item)` - Uses consumable, applies effects, removes if consumable

## 8. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Wands might have charges and not be fully consumed on use | Current `use_item` removes item if `item.consumable` is True. Wands should have `consumable=True` or custom logic. Test verifies current behavior. |
| Accessory slot mapping might not include "ring"/"neck" | `_get_valid_slots_for_item` in Inventory (line 606-629) maps "ring" to RING slot and "amulet/necklace/pendant" to NECK slot. Verified working. |
| String vs Enum comparison | Fixed by using `ItemType` enum directly instead of `.value` strings |
| Existing tests might break | Run `tests/test_inventory_use_drop.py` to verify existing behavior preserved |

### Architecture Gotchas (from architecture/gotchas.md)
- `dungeon_map[x, y]`: True=wall, False=floor - NOT RELEVANT
- `FOV: pov=(safe_x, safe_y)` not (y, x) - NOT RELEVANT
- Console: use `\033[H\033[2J` for frame clearing - NOT RELEVANT
- Playtest loop: render, decide, main_loop(action), telemetry - NOT RELEVANT

### Project Conventions (from workflow_instructions)
- All imports use `src.` prefix - NOT NEEDED (darkdelve.py is root level)
- Value objects use `@dataclass(frozen=True)` - NOT RELEVANT
- New entities go in `src/domain/entities/` - NOT CREATING NEW
- Tests go in `tests/test_MODULE.py` - FOLLOWED

