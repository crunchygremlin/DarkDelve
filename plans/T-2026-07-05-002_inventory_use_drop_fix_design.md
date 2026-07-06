# Design Document: Fix Inventory Use/Drop Key Handling

## 1. Goal
Fix the inventory use and drop functionality by correcting:
1. The indentation bug that makes `KeySym.D` and `KeySym.U` handlers unreachable
2. The `is_droppable` property that incorrectly prevents dropping unequipped items

## 2. Files to Create
None - this is a fix to existing code only.

## 3. Files to Modify

### File 1: `darkdelve.py` (lines 3218-3275)
**Problem**: The `elif event.sym == tcod.event.KeySym.D:` and `elif event.sym == tcod.event.KeySym.U:` blocks are incorrectly nested inside the `KeySym.RETURN` handler block due to wrong indentation.

**Current (broken) structure**:
```python
elif event.sym in (tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER):
    if self.player and self.player.inventory:
        item = self.player.inventory.get_item(self.inventory_selection)
        if item:
            # ... equip/unequip logic ...
        
        elif event.sym == tcod.event.KeySym.D:  # WRONG: nested inside if item
            # Drop logic - NEVER REACHED
        
        elif event.sym == tcod.event.KeySym.U:  # WRONG: nested inside if item
            # Use logic - NEVER REACHED
```

**Fixed structure**:
```python
elif event.sym in (tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER):
    if self.player and self.player.inventory:
        item = self.player.inventory.get_item(self.inventory_selection)
        if item:
            if item.equipped:
                self.player.inventory.unequip(item.id)
            else:
                slots = self.player.inventory._get_valid_slots_for_item(item)
                if slots:
                    self.player.inventory.equip(item.id, slots[0])

elif event.sym == tcod.event.KeySym.D:  # CORRECT: at same level as RETURN
    # Drop selected item
    if self.player and self.player.inventory:
        item = self.player.inventory.get_item(self.inventory_selection)
        if item:
            if item.equipped:
                self.add_message("Unequip the item before dropping it.")
            else:
                self.player.inventory.remove_item(item.id)
                self.drop_item(item, self.player.x, self.player.y)
                self.add_message(f"Dropped {item.name}.")
                item_count = len(self.player.inventory.items)
                if item_count > 0 and self.inventory_selection >= item_count:
                    self.inventory_selection = item_count - 1

elif event.sym == tcod.event.KeySym.U:  # CORRECT: at same level as RETURN
    # Use/Equip selected item
    if self.player and self.player.inventory:
        item = self.player.inventory.get_item(self.inventory_selection)
        if item:
            if item.item_type in (ItemType.POTION, ItemType.SCROLL, ItemType.FOOD, ItemType.WAND):
                result = self.player.use_item(item)
                if result:
                    self.add_message(f"Used {item.name}.")
                    item_count = len(self.player.inventory.items)
                    if item_count > 0 and self.inventory_selection >= item_count:
                        self.inventory_selection = item_count - 1
                else:
                    self.add_message(f"Cannot use {item.name}.")
            elif item.item_type in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY):
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
            else:
                self.add_message(f"{item.name} is not usable.")
```

### File 2: `src/domain/entities/item.py` (line 37-39)
**Problem**: `is_droppable` returns `False` for any equippable item with an equipment_slot, but should only return `False` for items that are actually equipped.

**Current (broken)**:
```python
@property
def is_droppable(self) -> bool:
    """Check if item can be dropped (all items are droppable unless equipped)"""
    return not (getattr(self, 'equippable', False) and getattr(self, 'equipment_slot', None))
```

**Fixed**:
```python
@property
def is_droppable(self) -> bool:
    """Check if item can be dropped (all items are droppable unless equipped)"""
    return not getattr(self, 'equipped', False)
```

## 4. Test Plan

### Test File: `tests/test_inventory_use_drop_fix.py`

```python
"""
Tests for the inventory use/drop key fix.
Verifies that:
- KeySym.D and KeySym.U handlers are at correct indentation level
- is_droppable returns True for unequipped items
- is_droppable returns False for equipped items
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

Item = darkdelve.Item
ItemType = darkdelve.ItemType


class TestItemIsDroppable(unittest.TestCase):
    """Test the is_droppable property fix."""
    
    def test_unequipped_item_is_droppable(self):
        """Unequipped items should be droppable."""
        item = Item(item_id="sword_1", name="Iron Sword", item_type="weapon")
        item.equippable = True
        item.equipment_slot = "main_hand"
        item.equipped = False
        self.assertTrue(item.is_droppable)
    
    def test_equipped_item_is_not_droppable(self):
        """Equipped items should not be droppable."""
        item = Item(item_id="sword_2", name="Iron Sword", item_type="weapon")
        item.equippable = True
        item.equipment_slot = "main_hand"
        item.equipped = True
        self.assertFalse(item.is_droppable)
    
    def test_potion_is_droppable(self):
        """Potions should be droppable."""
        item = Item(item_id="potion_1", name="Healing Potion", item_type="potion")
        self.assertTrue(item.is_droppable)


class TestInventoryKeyHandlers(unittest.TestCase):
    """Test that use/drop key handlers are correctly structured."""
    
    def test_drop_key_handler_exists_at_correct_level(self):
        """Verify show_inventory has drop key handling at correct indentation."""
        import inspect
        mod = darkdelve
        source = inspect.getsource(mod.Game.show_inventory)
        # The D handler should be at the same level as RETURN handler
        # Check that "KeySym.D" appears after the RETURN block ends
        lines = source.split('\n')
        return_line_idx = None
        d_line_idx = None
        for i, line in enumerate(lines):
            if 'KeySym.RETURN' in line or 'KeySym.KP_ENTER' in line:
                return_line_idx = i
            if 'KeySym.D' in line and 'KeySym.DOWN' not in line:
                d_line_idx = i
        self.assertIsNotNone(d_line_idx, "KeySym.D handler not found")
        self.assertGreater(d_line_idx, return_line_idx, "KeySym.D should be after RETURN handler")
    
    def test_use_key_handler_exists_at_correct_level(self):
        """Verify show_inventory has use key handling at correct indentation."""
        import inspect
        mod = darkdelve
        source = inspect.getsource(mod.Game.show_inventory)
        lines = source.split('\n')
        return_line_idx = None
        u_line_idx = None
        for i, line in enumerate(lines):
            if 'KeySym.RETURN' in line or 'KeySym.KP_ENTER' in line:
                return_line_idx = i
            if 'KeySym.U' in line:
                u_line_idx = i
        self.assertIsNotNone(u_line_idx, "KeySym.U handler not found")
        self.assertGreater(u_line_idx, return_line_idx, "KeySym.U should be after RETURN handler")


if __name__ == "__main__":
    unittest.main()
```

## 5. Integration Notes

- The `show_inventory()` method in `darkdelve.py` is a blocking event loop
- The `KeySym.D` and `KeySym.U` handlers were incorrectly nested inside the `KeySym.RETURN` block
- The `is_droppable` property in `Item` class was checking the wrong condition
- No new imports needed

## 6. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| The indentation fix may break existing tests | Run all tests after fix to verify |
| The is_droppable fix may affect DropCommand | The DropCommand uses `is_droppable` property, which will now work correctly |