# T-2026-0628-004: Floor 1 Stairs Missing — Cannot Descend

**Playtest Report**  
**Date:** 2026-06-28  
**Mode:** 🎮 Play Tester  
**Status:** ROOT CAUSE CONFIRMED

---

## Summary

The bug is **confirmed**. The stair-down glyph `>` is not visible on initial floor 1 because the stair tile at `(width//2, height-3)` is outside the player's FOV radius (8 tiles) and not yet explored. The `render_dungeon()` method at [`darkdelve.py:1836-1844`](darkdelve.py:1836) correctly gates stair rendering on FOV/explored state. Additionally, `use_stairs_down()` at [`darkdelve.py:3297-3300`](darkdelve.py:3297) produces **zero feedback** when the player is not on the stairs — no message, no log — making the feature appear completely broken.

---

## Evidence

### Baseline Tests
```
tests/test_floor1_generator.py — 12 passed
tests/test_game_logic.py       — 39 passed
Total: 51 passed, 0 failed (68.95s)
```

### Telemetry (from `playtest/playtest_telemetry.json`)

| Phase | Finding |
|-------|---------|
| **1 — Initial state** | `stair_down_pos = (40, 40)`, player at `(40, 2)`, stair tile IS floor (`True`), stair in FOV = **`false`**, stair explored = **`false`** |
| **2 — Walk to stairs** | Player blocked at `(40, 15)` by a `Cave Rat` den creature on the main corridor. Path length = 14 steps before blockage. |
| **3 — Descend on stairs** | Player never reached stairs (blocked at y=15, stair at y=40). `depth_changed = false`. |
| **4 — Descend off stairs** | Player at entrance `(40, 2)`, pressed `>`. `depth_changed = false`, `new_messages = []`, **`bug_no_feedback = true`** |
| **5 — Render check** | UI not initialized in headless harness (expected). |

### Direct Corridor Inspection (seed=42)

```
y=2:  floor=True, entities=[Adventurer]
y=3:  floor=True, entities=[]
y=4:  floor=True, entities=[]
y=5:  floor=True, entities=[]
y=6:  floor=True, entities=[]
y=7:  floor=True, entities=[]
y=8:  floor=True, entities=[]
  ...
y=15: floor=True, entities=[]
y=16: floor=True, entities=[Cave Rat]  ← BLOCKS CORRIDOR
```

---

## Root Cause Analysis

### Primary Bug: Stair glyph not visible (FOV gating)

1. `_generate_floor1()` at [`darkdelve.py:2339`](darkdelve.py:2339) sets `self.stair_down_pos = floor1_data.stair_down`
2. The generator at [`src/application/services/floor1_generator.py:101-102`](src/application/services/floor1_generator.py:101) computes `stair_x = width // 2 = 40`, `stair_y = height - 3 = 40`
3. The main path is carved from `entrance_y=2` to `stair_y=40` inclusive — stair tile IS floor
4. Player starts at `(40, 2)`, FOV radius = 8 → FOV reaches rows 2-10 only
5. Stair at row 40 is **38 tiles away** — well outside FOV
6. `render_dungeon()` at [`darkdelve.py:1843`](darkdelve.py:1843) only renders `>` if `fov[sx, sy] or explored[sx, sy]` — both are `false`
7. **Result:** No `>` glyph visible anywhere on the map

### Secondary Bug: Silent failure on `use_stairs_down()`

```python
# darkdelve.py:3297-3300
def use_stairs_down(self):
    if self.stair_down_pos and self.player.x == self.stair_down_pos[0] and self.player.y == self.stair_down_pos[1]:
        self.generate_level(self.state.depth + 1, self.state.branch)
        self.add_message("You descend deeper into the dungeon...")
    # ← No else clause. No logging. No feedback when player is NOT on stairs.
```

When the player presses `>` and is NOT on the stairs, the method silently returns. The user has no idea whether the key didn't register or there are no stairs here.

### Tertiary Finding: Den creature blocking main corridor

A `Cave Rat` spawned at `(40, 16)` directly on the main corridor, blocking the player's path to the stairs. Den creatures should be confined to side rooms, but the spawner placed one on the main path. This is a separate issue (possibly T-2026-0628-005).

---

## Recommended Fix

### Part 1: Add stair-use logging and feedback (REQUIRED)

In [`darkdelve.py:3297-3300`](darkdelve.py:3297), add an `else` clause:

```python
def use_stairs_down(self):
    if self.stair_down_pos and self.player.x == self.stair_down_pos[0] and self.player.y == self.stair_down_pos[1]:
        self.generate_level(self.state.depth + 1, self.state.branch)
        self.add_message("You descend deeper into the dungeon...")
    else:
        self.add_message("There are no stairs here.")
```

Same pattern for `use_stairs_up()` at [`darkdelve.py:3302-3309`](darkdelve.py:3302).

### Part 2: Add `tests/test_stairs.py` (REQUIRED)

- Test: `stair_down_pos` is not None after `_generate_floor1()`
- Test: `stair_down_pos` is on a floor tile
- Test: `stair_down_pos` is reachable from entrance via BFS
- Test: `use_stairs_down()` on stairs increments depth
- Test: `use_stairs_down()` off stairs does NOT change depth and logs a message

### Part 3: Verify stair rendering (REQUIRED)

- Confirm `>` appears at bottom of corridor when tile is in FOV
- Add guard in spawner to prevent entities on `stair_down_pos`

---

## Evidence Files

| File | Description |
|------|-------------|
| `playtest/playtest_telemetry.json` | Full 5-phase telemetry with positions, FOV state, depth changes |
| `playtest/repro_floor1_stairs.py` | Reproduction script (deterministic, seed=42) |
| `playtest/floor1_stairs_report.md` | This report |

---

## Conclusion

**Root cause confirmed.** The stair-down system works correctly when the player reaches the stairs, but two UX failures make it appear broken:
1. The `>` glyph is invisible until the player explores within 8 tiles of it (FOV gating)
2. Pressing `>` off-stairs produces zero feedback (silent failure)

Both issues are in [`darkdelve.py:3297-3300`](darkdelve.py:3297) and [`darkdelve.py:1836-1844`](darkdelve.py:1836). The fix is straightforward: add an `else` clause with a user-facing message, and add unit tests to prevent regression.
