# T-2026-0629-005 — No way to drop or use inventory items

**Verdict: CONFIRMED (with nuance)** — reproduced 2026-06-29.

## Summary

The task description is **partially inaccurate**. The `I` key binding and the `show_inventory()` screen **do exist** in [`darkdelve.py`](darkdelve.py:2073) and [`darkdelve.py:3707-3735`](darkdelve.py:3707). The real, narrower bug is:

> The inventory overlay is an **equip-only** screen. `UseCommand` and `DropCommand` exist as backend classes but are **dead code from the player's perspective** — no key binding, no overlay action, and no `process_action` verb ever invokes them. The player can open inventory, navigate, and equip/unequip, but **cannot use a potion/scroll or drop any item**.

The backend plumbing is ready (`UseCommand.execute()` → `player.use_item()`, `DropCommand.execute()` → `player.drop_item()`, and [`Entity.drop_item(item, x, y)`](darkdelve.py:3679) already spawns a floor entity). Only the input/overlay wiring is missing.

## Evidence

| Check | Result | Location |
|-------|--------|----------|
| `UseCommand` / `DropCommand` reachable from input handlers | **NEVER** instantiated from any input handler, overlay, or game-loop code path | [`use_command.py:10`](src/application/game_commands/use_command.py:10), [`drop_command.py:11`](src/application/game_commands/drop_command.py:11). Grep shows they are only referenced in their own files and in [`playtest/test_equip_use_combat.py`](playtest/test_equip_use_combat.py:30) (a unit test that constructs them directly). |
| `InputController` inventory bindings | `InputController` is a generic key-bind store with only `bind_key`/`handle_input`/`reset`/`get_last_action`. It has **no** inventory bindings and is **not** wired into the live game loop ([`darkdelve.py`](darkdelve.py:2040) uses its own `handle_event`, not `InputController`). | [`input_controller.py:6-30`](src/presentation/controllers/input_controller.py:6) |
| `darkdelve.py` inventory interaction mode | `show_inventory()` exists and is bound to `I`. ENTER only toggles equip/unequip. **No `U` key for Use, no `D` key for Drop, no sub-menu.** `render_inventory` shows no hint about Use/Drop keys. | [`darkdelve.py:2073`](darkdelve.py:2073), [`darkdelve.py:3707-3735`](darkdelve.py:3707), [`darkdelve.py:3812`](darkdelve.py:3812) |
| `process_action('i')` path | Intentionally a no-op returning `False` without opening the blocking inventory screen (correct for automated playtests, but means the library agent cannot Use/Drop either). | [`darkdelve.py:3171-3177`](darkdelve.py:3171), [`tests/test_game_logic.py:179-184`](tests/test_game_logic.py:179) |
| Existing tests for player-facing use/drop | **No test** exercises Use or Drop from player input. Closest: [`test_equip_use_combat.py:95-114`](playtest/test_equip_use_combat.py:95) constructs `UseCommand` directly; [`test_console_input.py:111-133`](tests/test_console_input.py:111) only checks that `show_inventory()` waits for events; [`test_entity_system.py`](tests/test_entity_system.py) covers inventory CRUD but not Use/Drop from input. | see left |

## Root Cause

The inventory overlay ([`show_inventory()`](darkdelve.py:3707)) is an equip-only screen. `UseCommand` and `DropCommand` exist as backend classes but are dead code from the player's perspective: no key binding, no overlay action, and no `process_action` verb ever invokes them.

**Backend is ready:**
- [`UseCommand.execute()`](src/application/game_commands/use_command.py:31) → `player.use_item(item)`
- [`DropCommand.execute()`](src/application/game_commands/drop_command.py:32) → `player.drop_item(item)`
- [`Entity.drop_item(item, x, y)`](darkdelve.py:3679) already spawns a floor entity at the target position.

Only the input/overlay wiring is missing.

## Fix Scope for the Debugger

1. **Overlay input** — In [`show_inventory()`](darkdelve.py:3707-3735), add key handlers:
   - `U` → Use selected item via `UseCommand(player, item).execute()`
   - `D` → Drop selected item via `DropCommand(player, item).execute()`, then place the item entity on the floor using the existing [`drop_item(item, x, y)`](darkdelve.py:3679) pattern.
2. **Render hint** — Update [`render_inventory()`](darkdelve.py:3812) footer to show: `ENTER=equip  U=use  D=drop  ESC/I=close`.
3. **`process_action` verbs (optional)** — Add `process_action('u')`/`<index>` and `'d'`/`<index>` verbs so the library agent can drive use/drop without the blocking overlay (mirrors the existing no-op guard at [`darkdelve.py:3174`](darkdelve.py:3174)).
4. **Tests to add:**
   - Pressing `U` on a usable consumable in `show_inventory` applies its effect and decrements the stack.
   - Pressing `D` on a droppable item removes it from inventory and spawns a floor entity at the player's position.
   - `UseCommand`/`DropCommand` are reachable end-to-end from a simulated `KeyDown` event through `handle_event` → `show_inventory`.

## Telemetry

Evidence appended to [`playtest/playtest_telemetry.json`](playtest/playtest_telemetry.json) under task `T-2026-0629-005`.
