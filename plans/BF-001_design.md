# Goal: Fix TypeError in Inventory.get_defense_bonus and related methods

## Files to Create
(None - no new files needed)

## Files to Modify
- darkdelve.py (lines 635-644): Fix the three methods in the Inventory class

## Pseudocode for Each New Function/Method
(None - we are modifying existing methods)

## Exact Import Statements Needed
(None - no new imports needed)

## Test Plan
(None - this is a bug fix; existing tests should cover it. If not, we rely on existing test suite.)

## Integration Notes
The fix is localized to the Inventory class methods. These methods are called by the CombatResolver during combat resolution. The fix ensures that None values are treated as 0, preventing TypeError when summing bonuses.

## Risks and Mitigations
- Risk: If an item's bonus is intentionally set to None to mean "no bonus", treating it as 0 changes behavior. However, looking at the Item class, bonuses are initialized as integers (default 0) and only set to integers via magic items. None values likely indicate uninitialized or missing data, so treating as 0 is safe.
- Mitigation: The fix aligns with existing patterns in the codebase (see Item.get_stat_string lines 493-498 where `or 0` is already used for bonuses).

## Detailed Changes

### File: darkdelve.py
#### Lines 635-636: get_defense_bonus
**Before:**
```python
    def get_defense_bonus(self) -> int:
        return sum(item.defense_bonus for item in self.equipment.values() if item and item.equipped)
```

**After:**
```python
    def get_defense_bonus(self) -> int:
        return sum((item.defense_bonus or 0) for item in self.equipment.values() if item and item.equipped)
```

#### Lines 638-640: get_damage_bonus
**Before:**
```python
    def get_damage_bonus(self) -> int:
        weapon = self.equipment[EquipmentSlot.MAIN_HAND]
        return weapon.damage_bonus if weapon and weapon.equipped else 0
```

**After:**
```python
    def get_damage_bonus(self) -> int:
        weapon = self.equipment[EquipmentSlot.MAIN_HAND]
        return (weapon.damage_bonus or 0) if weapon and weapon.equipped else 0
```

#### Lines 642-644: get_to_hit_bonus
**Before:**
```python
    def get_to_hit_bonus(self) -> int:
        weapon = self.equipment[EquipmentSlot.MAIN_HAND]
        return weapon.to_hit_bonus if weapon and weapon.equipped else 0
```

**After:**
```python
    def get_to_hit_bonus(self) -> int:
        weapon = self.equipment[EquipmentSlot.MAIN_HAND]
        return (weapon.to_hit_bonus or 0) if weapon and weapon.equipped else 0
```

## Alignment with Architecture
This fix follows the existing pattern in the codebase where `or 0` is used to handle potentially None numeric values (see Item.get_stat_string lines 493-498). It maintains the Single Responsibility Principle by keeping the bonus calculation logic within the Inventory class. The fix is minimal and localized, reducing risk of introducing new bugs.

