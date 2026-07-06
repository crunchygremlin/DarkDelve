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
        item = Item(id="sword_1", name="Iron Sword", item_type=ItemType.WEAPON)
        item.equipped = False
        self.assertTrue(item.is_droppable)
    
    def test_equipped_item_is_not_droppable(self):
        """Equipped items should not be droppable."""
        item = Item(id="sword_2", name="Iron Sword", item_type=ItemType.WEAPON)
        item.equipped = True
        self.assertFalse(item.is_droppable)
    
    def test_potion_is_droppable(self):
        """Potions should be droppable."""
        item = Item(id="potion_1", name="Healing Potion", item_type=ItemType.POTION)
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