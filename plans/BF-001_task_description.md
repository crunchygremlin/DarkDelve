Task ID: BF-001
Task: Fix TypeError in Inventory.get_defense_bonus and related methods
Objective: Fix the TypeError that occurs when equipped items have None values for defense_bonus, damage_bonus, or to_hit_bonus attributes in the Inventory class.

Steps:
1. Analyze the error traceback from darkdelve.py lines 636, 640, and 644
2. Identify the problematic methods: get_defense_bonus, get_damage_bonus, get_to_hit_bonus
3. Fix the methods to handle None values by treating them as 0 using the "or 0" pattern
4. Implement the fix in darkdelve.py
5. Create tests to verify the fix works correctly
6. Verify the fix resolves the crash when using healing staff and leaving inventory

Deliverables:
- Fixed darkdelve.py file with the three methods corrected
- Test file tests/test_inventory_bonus_fix.py verifying the fix
- Confirmation that the original error no longer occurs

Context:
The error occurs in the Inventory class methods when summing bonus values or returning bonus values where equipped items have None for defense_bonus, damage_bonus, or to_hit_bonus. The fix involves using (item.defense_bonus or 0) instead of item.defense_bonus in the sum, and similar patterns for the other methods.
