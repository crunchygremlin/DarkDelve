Task ID: INV-U-KEY-001
Title: Investigate and fix 'U' key functionality in inventory screen
Description: 
User reports that pressing 'U' in the inventory screen does nothing. However, unit tests show the underlying functionality works correctly. Need to investigate:
1. Whether the inventory screen is properly displaying and receiving input
2. If the 'U' key event is being processed correctly in the show_inventory() method
3. Whether there are any blocking issues in the event loop that prevent key handling
4. Verify that the player.use_item() and inventory.equip()/unequip() methods work as expected when called from the inventory screen

Current evidence:
- All unit tests pass (test_inventory_use_key_fix.py: 10/10)
- MCP playtest passes (test_inventory_use_key_mcp.py: 8/8)
- The show_inventory() method in darkdelve.py lines 3246-3275 contains 'U' key handling logic
- The underlying player.use_item() and inventory methods are tested and working

Expected outcome: Identify why 'U' key appears to do nothing in actual gameplay and fix the issue.
Complexity: MULTI_FILE (may involve darkdelve.py and potentially input handling files)
Files to examine:
- darkdelve.py (show_inventory method, input handling)
- Tests to understand expected behavior

Deliverables:
1. Design document explaining the root cause and solution
2. Updated task description for Coder
3. Updated architecture documentation if needed

Workflow: Orchestrator -> Architect -> Orchestrator -> Coder -> Orchestrator -> Play Tester -> Orchestrator
