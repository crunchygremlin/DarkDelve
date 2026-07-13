# Inventory Defense Bonus Fix Design

## Goal
Fix the TypeError in Inventory.get_defense_bonus, get_damage_bonus, and get_to_hit_bonus methods when equipped items have None for defense_bonus, damage_bonus, or to_hit_bonus attributes.

## Files to Modify
- darkdelve.py (lines 635-644): Modify the three methods in the Inventory class

## Pseudocode for Changes

### get_defense_bonus method (lines 635-636)
```python
def get_defense_bonus(self) -> int:
    return sum((item.defense_bonus or 0) for item in self.equipment.values() if item and item.equipped)
```

### get_damage_bonus method (lines 638-640)
```python
def get_damage_bonus(self) -> int:
    weapon = self.equipment[EquipmentSlot.MAIN_HAND]
    return (weapon.damage_bonus or 0) if weapon and weapon.equipped else 0
```

### get_to_hit_bonus method (lines 642-644)
```python
def get_to_hit_bonus(self) -> int:
    weapon = self.equipment[EquipmentSlot.MAIN_HAND]
    return (weapon.to_hit_bonus or 0) if weapon and weapon.equipped else 0
```

## Import Statements
No new imports required. We are only modifying existing lines.

## Test Plan
Create a test file: `tests/test_inventory_bonus_fix.py` with the following content:

```python
import pytest
from src.domain.entities.item import Item, ItemType, EquipmentSlot
from darkdelve import Inventory, Player

def test_inventory_bonus_with_none_values():
    """Test that inventory bonus methods handle None values correctly."""
    # Create a player and inventory
    player = Player()
    inventory = Inventory()
    
    # Create an item with None bonuses
    item = Item(
        name="Test Item",
        item_type=ItemType.ARMOR,
        defense_bonus=None,  # This should be treated as 0
        damage_bonus=None,   # This should be treated as 0
        to_hit_bonus=None,   # This should be treated as 0
        weight=5.0,
        value=10
    )
    
    # Equip the item in chest slot
    inventory.equip(item, player, EquipmentSlot.CHEST)
    
    # Test defense bonus - should be 0 (None treated as 0)
    assert inventory.get_defense_bonus() == 0
    
    # Test damage bonus with no weapon equipped - should be 0
    assert inventory.get_damage_bonus() == 0
    
    # Test to_hit bonus with no weapon equipped - should be 0
    assert inventory.get_to_hit_bonus() == 0
    
    # Now equip a weapon with None bonuses
    weapon = Item(
        name="Test Weapon",
        item_type=ItemType.WEAPON,
        defense_bonus=None,
        damage_bonus=None,   # This should be treated as 0
        to_hit_bonus=None,   # This should be treated as 0
        weight=3.0,
        value=15
    )
    
    inventory.equip(weapon, player, EquipmentSlot.MAIN_HAND)
    
    # Defense bonus should still be 0 (from armor)
    assert inventory.get_defense_bonus() == 0
    
    # Damage bonus should be 0 (None treated as 0)
    assert inventory.get_damage_bonus() == 0
    
    # To-hit bonus should be 0 (None treated as 0)
    assert inventory.get_to_hit_bonus() == 0
    
    # Now test with actual values to ensure we didn't break existing functionality
    item2 = Item(
        name="Better Armor",
        item_type=ItemType.ARMOR,
        defense_bonus=5,
        damage_bonus=0,
        to_hit_bonus=0,
        weight=8.0,
        value=50
    )
    
    # Replace the armor
    inventory.equip(item2, player, EquipmentSlot.CHEST)
    
    # Defense bonus should now be 5
    assert inventory.get_defense_bonus() == 5
    
    # Weapon bonuses still None -> 0
    assert inventory.get_damage_bonus() == 0
    assert inventory.get_to_hit_bonus() == 0
    
    # Now upgrade weapon to have real values
    weapon2 = Item(
        name="Better Weapon",
        item_type=ItemType.WEAPON,
        defense_bonus=0,
        damage_bonus=3,   # Actual value
        to_hit_bonus=1,   # Actual value
        weight=4.0,
        value=75
    )
    
    inventory.equip(weapon2, player, EquipmentSlot.MAIN_HAND)
    
    # Defense bonus from armor
    assert inventory.get_defense_bonus() == 5
    
    # Damage bonus from weapon
    assert inventory.get_damage_bonus() == 3
    
    # To-hit bonus from weapon
    assert inventory.get_to_hit_bonus() == 1

def test_inventory_bonus_with_mixed_none_and_values():
    """Test mixing None and actual values."""
    player = Player()
    inventory = Inventory()
    
    # Armor with None defense (should be 0)
    armor = Item(
        name="Mystic Robe",
        item_type=ItemType.ARMOR,
        defense_bonus=None,   # None -> 0
        damage_bonus=0,
        to_hit_bonus=0,
        weight=2.0,
        value=20
    )
    
    # Weapon with actual damage but None to_hit
    weapon = Item(
        name="Blunt Club",
        item_type=ItemType.WEAPON,
        defense_bonus=0,
        damage_bonus=2,     # Actual value
        to_hit_bonus=None,  # None -> 0
        weight=3.0,
        value=15
    )
    
    inventory.equip(armor, player, EquipmentSlot.CHEST)
    inventory.equip(weapon, player, EquipmentSlot.MAIN_HAND)
    
    # Defense: 0 (from armor) + 0 (from weapon) = 0
    assert inventory.get_defense_bonus() == 0
    
    # Damage: 2 (from weapon)
    assert inventory.get_damage_bonus() == 2
    
    # To-hit: 0 (from weapon, None treated as 0)
    assert inventory.get_to_hit_bonus() == 0
```

## Integration Notes
- The changes are isolated to the Inventory class in darkdelve.py (lines 635-644).
- No other files need to be modified as these methods are only used internally within the Inventory class.
- The fix uses the "or 0" pattern to safely handle None values by treating them as zero.
- This maintains backward compatibility with existing items that have numeric bonus values.

## Risks and Mitigations
- **Risk**: If an item's bonus attribute is not None and not a number (e.g., a string), the existing code would have thrown a TypeError during arithmetic operations, and our fix would not prevent that.
  - **Mitigation**: This is an existing issue unrelated to the None handling fix. The game's item system should ensure bonus attributes are either numbers or None. We could add type checking in the future, but for now we're only fixing the specific None-related TypeError.
  
- **Risk**: The change could potentially affect performance if called frequently in tight loops.
  - **Mitigation**: The performance impact is negligible as we're just adding a simple None check. The methods are called infrequently (typically during combat calculations or equipment changes).

