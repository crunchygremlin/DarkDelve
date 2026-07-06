# Design Document: Fix 'U' Key Functionality in Inventory Screen

## Task Information
- Task ID: INV-U-KEY-001
- Title: Investigate and fix 'U' key functionality in inventory screen
- Complexity: MULTI_FILE (actually SINGLE_FILE fix)

## Root Cause Analysis

After examining the `show_inventory()` method in `darkdelve.py` (lines 3198-3275), I found that the 'U' key handling logic is correctly implemented (lines 3246-3275). The method properly handles `tcod.event.KeySym.U` for both consumable items and equipment.

However, examining the event handling system revealed the issue: the `_console_key_to_event()` method (lines 2870-2908) maps keyboard inputs to tcod events, but it's missing a mapping for the lowercase 'u' key. 

The inventory screen correctly handles `tcod.event.KeySym.U` (uppercase U), but when running in console mode (which appears to be the default based on the `_uses_console_renderer()` check), keyboard input goes through `_console_key_to_event()`. Since there's no mapping for the "u" key in the keymap dictionary, pressing 'u' returns `None` instead of a proper `tcod.event.KeyDown` event, causing the key press to be ignored in the inventory screen's event loop.

## Solution

Add a mapping for the lowercase 'u' key in the `_console_key_to_event()` method's keymap dictionary, mapping it to the same tcod event as the uppercase 'U' key.

## Design Document

**Goal:** Fix the 'U' key functionality in the inventory screen by adding the missing key mapping in the console input handler.

**Files to Modify:**
- `darkdelve.py` - Add missing 'u' key mapping in `_console_key_to_event()` method

**Pseudocode for Changes:**
```python
def _console_key_to_event(self, key: str) -> Optional[tcod.event.KeyDown]:
    keymap = {
        # ... existing mappings ...
        "u": (tcod.event.Scancode.U, tcod.event.KeySym.U),  # ADD THIS LINE
        # ... existing mappings ...
    }
    # ... rest of method unchanged ...
```

**Integration Notes:**
- The fix is minimal and localized - only adding one line to the existing keymap dictionary
- This maps the lowercase 'u' key to the same tcod event as uppercase 'U', which the inventory screen already handles correctly
- No changes needed to the inventory screen logic itself since it already properly handles `tcod.event.KeySym.U`
- This follows the existing pattern in the keymap where lowercase letters map to their uppercase tcod equivalents (e.g., "w" maps to KeySym.W)

**Risks and Mitigations:**
- Risk: Minimal - this is a simple addition to an existing dictionary
- Mitigation: The fix follows the existing pattern in the codebase where lowercase letters map to uppercase tcod symbols
- Testing: Unit tests already pass, confirming the underlying functionality works. Manual testing of the 'U' key in inventory screen should now work.

**Test Plan:**
The existing unit tests (`test_inventory_use_key_fix.py`) and MCP playtests (`test_inventory_use_key_mcp.py`) should continue to pass, confirming the underlying functionality works. Manual verification should confirm that pressing 'u' (lowercase) in the inventory screen now properly uses/equips items.

**Architecture Updates Needed:**
None required - this is a simple bug fix that doesn't change system architecture.

## Implementation Steps for Coder
1. Open `darkdelve.py`
2. Locate the `_console_key_to_event()` method (around line 2870)
3. In the `keymap` dictionary, add: `"u": (tcod.event.Scancode.U, tcod.event.KeySym.U),`
4. Save the file
5. Run unit tests to verify no regressions
6. Manual test: Start game, open inventory ('i'), select an item, press 'u' to use/equip

## Expected Results
- Pressing 'u' (lowercase) in inventory screen should now work identically to pressing 'U' (uppercase)
- Consumable items (potions, scrolls, food, wands) should be used
- Equipment (weapons, armor, accessories) should be equipped/unequipped
- MISC items should show "not usable" message
- All existing unit tests should continue to pass
