# Task Description: Fix Inventory Drop and Combat Hit Chance Bugs

## Problem Statement
Two critical bugs have been reported:
1. Inventory drop is not working - players cannot drop items from inventory
2. On level 2, players cannot hit monsters even on a roll of 20+ (they keep missing)

## Root Cause Analysis

### Inventory Drop Bug
- **Location**: `src/domain/entities/item.py` line 37-39 and `src/application/game_commands/drop_command.py` line 156
- **Issue**: The `Item.is_droppable` property incorrectly prevents dropping equipable items. It returns `False` for any item that is equippable OR has an equipment slot, meaning equipped items cannot be dropped (which is correct) but also unequipped equipable items cannot be dropped (which is incorrect).
- **Additional Issue**: The `DropCommand.can_execute()` method checks `self.player.get_item_count(self.item) <= 0` but the runtime `Entity` class (used in actual gameplay) doesn't have the `get_item_count` method that the domain `Player` class has.

### Combat Hit Chance Bug
- **Location**: `darkdelve.py` lines 988-1001 in `CombatResolver.resolve_attack`
- **Issue**: The combat resolver expects `attacker.stats` to be a dictionary (as seen in test entities) but the actual `Player` entity has a `stats` attribute that is a `Stats` object (from `domain/components/stats.py`). When the code tries to access `attacker.stats.get('dex', 10)`, it fails because `Stats` objects don't have a `.get()` method, causing the dexterity modifier to default to 0, making hit chances much lower than intended.

## Required Fixes

### Fix 1: Inventory Drop
1. Fix `Item.is_droppable` property to only check if item is NOT equipped (equipped items cannot be dropped, but unequipped equipable items can be)
2. Update `DropCommand.can_execute()` to handle both domain Player and runtime Entity objects by checking for the existence of `get_item_count` method or falling back to inventory check

### Fix 2: Combat Hit Chance
1. Modify `CombatResolver.resolve_attack` to properly handle both dictionary-style stats (for tests) and Stats objects (for actual gameplay)
2. Extract dexterity modifier correctly from Stats object using appropriate method

## Test Verification
After fixes, the following tests should pass:
- `tests/test_inventory_use_drop.py` (specifically drop-related tests)
- `tests/test_combat_system.py` (hit/miss/critical hit tests)
- Manual playtesting should confirm items can be dropped and combat works correctly on level 2+

## Implementation Plan
1. Fix Item.is_droppable property in src/domain/entities/item.py
2. Fix DropCommand.can_execute method in src/application/game_commands/drop_command.py
3. Fix CombatResolver.resolve_attack stat handling in darkdelve.py
4. Run relevant tests to verify fixes
5. Optionally run manual playtesting to confirm level 2 combat works

