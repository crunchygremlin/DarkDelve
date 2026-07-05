"""Tests for inventory description panel rendering."""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestInventoryDescriptionPanel(unittest.TestCase):
    """Test that the description panel renders selected item info."""

    def _import_runtime(self):
        import importlib.util as _ilu
        _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _DARKDELVE_PATH = os.path.join(_REPO_ROOT, "darkdelve.py")
        _spec = _ilu.spec_from_file_location("darkdelve_rt", _DARKDELVE_PATH)
        _mod = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        return _mod

    def test_accessory_slot_enum_has_ring_and_neck(self):
        mod = self._import_runtime()
        self.assertTrue(hasattr(mod.EquipmentSlot, 'RING'))
        self.assertTrue(hasattr(mod.EquipmentSlot, 'NECK'))
        self.assertEqual(mod.EquipmentSlot.RING.value, "ring")
        self.assertEqual(mod.EquipmentSlot.NECK.value, "neck")

    def test_inventory_has_ring_and_neck_slots(self):
        mod = self._import_runtime()
        inv = mod.Inventory()
        self.assertIn(mod.EquipmentSlot.RING, inv.equipment)
        self.assertIn(mod.EquipmentSlot.NECK, inv.equipment)
        self.assertIsNone(inv.equipment[mod.EquipmentSlot.RING])
        self.assertIsNone(inv.equipment[mod.EquipmentSlot.NECK])

    def test_ring_item_maps_to_ring_slot(self):
        mod = self._import_runtime()
        ring = mod.Item(
            id="test_ring",
            name="Ring of Protection",
            item_type=mod.ItemType.ACCESSORY,
            defense_bonus=2,
        )
        inv = mod.Inventory()
        valid_slots = inv._get_valid_slots_for_item(ring)
        self.assertIn(mod.EquipmentSlot.RING, valid_slots)

    def test_amulet_item_maps_to_neck_slot(self):
        mod = self._import_runtime()
        amulet = mod.Item(
            id="test_amulet",
            name="Amulet of Wisdom",
            item_type=mod.ItemType.ACCESSORY,
        )
        inv = mod.Inventory()
        valid_slots = inv._get_valid_slots_for_item(amulet)
        self.assertIn(mod.EquipmentSlot.NECK, valid_slots)

    def test_item_type_has_accessory(self):
        mod = self._import_runtime()
        self.assertTrue(hasattr(mod.ItemType, 'ACCESSORY'))
        self.assertEqual(mod.ItemType.ACCESSORY.value, "accessory")

    def test_drop_key_handler_exists(self):
        """Verify show_inventory has drop key handling (source inspection)."""
        import inspect
        mod = self._import_runtime()
        source = inspect.getsource(mod.Game.show_inventory)
        self.assertIn("KeySym.D", source)

    def test_use_key_handler_exists(self):
        """Verify show_inventory has use key handling (source inspection)."""
        import inspect
        mod = self._import_runtime()
        source = inspect.getsource(mod.Game.show_inventory)
        self.assertIn("KeySym.U", source)

    def test_render_item_description_method_exists(self):
        """Verify _render_item_description method exists on Game class."""
        import inspect
        mod = self._import_runtime()
        self.assertTrue(hasattr(mod.Game, '_render_item_description'))
        sig = inspect.signature(mod.Game._render_item_description)
        params = list(sig.parameters.keys())
        # Should have: self, x, y, width, item
        self.assertEqual(params, ['self', 'x', 'y', 'width', 'item'])
        # Check type hints
        self.assertEqual(sig.parameters['x'].annotation, int)
        self.assertEqual(sig.parameters['y'].annotation, int)
        self.assertEqual(sig.parameters['width'].annotation, int)

    def test_render_inventory_calls_description_panel(self):
        """Verify render_inventory calls _render_item_description for selected item."""
        import inspect
        mod = self._import_runtime()
        source = inspect.getsource(mod.Game.render_inventory)
        self.assertIn('_render_item_description', source)
        self.assertIn('desc_x', source)
        self.assertIn('panel_width', source)


if __name__ == "__main__":
    unittest.main()