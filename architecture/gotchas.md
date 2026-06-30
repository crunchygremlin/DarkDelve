# DarkDelve Development Gotchas

## Common Import Error

### Problem
After refactoring code into the modular `src/` structure, you frequently encounter Pylance import errors like:

```
Import "application.game_commands.base_command" could not be resolved
Import "domain.entities.player" could not be resolved
```

### Root Cause
The import statements in test files and other modules are still using the old flat import style that assumes all modules are directly accessible from the project root. However, after the modular refactoring, all code is now organized under the `src/` directory with proper Python package structure.

### Solution
Update all import statements to use the new package structure:

**Before (old style):**
```python
from application.game_commands.base_command import BaseCommand
from domain.entities.player import Player
```

**After (new style):**
```python
from src.application.game_commands.base_command import BaseCommand
from src.domain.entities.player import Player
```

### Affected Modules
- `test_app_imports.py`
- `test_imports.py`
- Any other files that import from the modularized structure

### Best Practices
1. **Always use absolute imports** with the `src.` prefix when importing from within the project
2. **Use relative imports** only when importing between modules within the same package
3. **Update imports** whenever you move or reorganize code files
4. **Check import paths** after any major refactoring

### How to Fix
1. Open the file with import errors
2. Replace all import statements that reference `application.*`, `domain.*`, etc. with `src.application.*`, `src.domain.*`, etc.
3. Ensure all imported modules actually exist in the expected locations under `src/`

### Prevention
- Be mindful of the project structure when writing new code
- Use IDE features to auto-generate correct import paths
- Regularly run tests to catch import issues early
- Consider using `__init__.py` files to make imports more consistent

## UI Object Player Attribute Error

### Problem
When running the game, you encounter an AttributeError:

```
AttributeError: 'UI' object has no attribute 'player'
```

This error occurs in the `render_entities` method at line 1517 when trying to access `self.player` on a UI object.

### Root Cause
The `render_entities` method in the UI class was trying to access `self.player`, but the UI object doesn't have a `player` attribute. The player object is owned by the Game class, not the UI class.

### Solution
Modify the `render_entities` method to accept the player as a parameter:

1. **Update the method signature**:
   ```python
   def render_entities(self, entities: List[Entity], fov: np.ndarray, player=None):
   ```

2. **Update the method logic** to use the parameter instead of `self.player`:
   ```python
   if fov[entity.y, entity.x] or entity is player:
   ```

3. **Update the method call** in the `render` method to pass the player:
   ```python
   self.ui.render_entities(self.entities, self.fov, self.player)
   ```

### Affected Code
- `darkdelve.py` line 1511: `render_entities` method signature
- `darkdelve.py` line 1517: Logic using player parameter
- `darkdelve.py` line 2060: Method call in `render`

### Prevention
- Be careful about object ownership and attribute access
- Pass required parameters explicitly rather than assuming they exist as attributes
- Test UI rendering functionality thoroughly after any changes

## In-Process Playtester Action Loop

### Problem
Automated playtests can hang or skip turns if the in-process driver enters the
normal console menu path or if the game is initialized twice.

### Root Cause
The normal inventory screen waits for a second input event, and `Game.run()`
calls `Game.initialize()` before entering the human input loop. The library
playtester also needs a fully initialized game, but the entry point already
initializes the game before constructing `MCPPlaytester`.

### Solution
Use [`Game.process_action()`](../darkdelve.py:2112) for library-supplied actions
instead of the blocking inventory flow. Treat `i` as a no-op unless you
implement a separate inventory-state machine. When the caller has already called
`Game.initialize()`, construct `MCPPlaytester` with `auto_initialize=False`.

### Affected Code
- [`Game.main_loop()`](../darkdelve.py:2031)
- [`Game.process_action()`](../darkdelve.py:2112)
- [`MCPPlaytester`](../src/infrastructure/services/mcp_integration.py:44)
- [`darkdelve.py` `main()`](../darkdelve.py:2529)

### Prevention
- Keep the playtester loop in `render -> decide -> main_loop(action) -> telemetry`
  order.
- Pass `render_to_stdout=False` and `frame_text=frame_text` for in-process runs.
- Keep `playtest.enabled` disabled for normal human play.
- Add tests with a fake `PlayerAgent` so the loop can be verified without Ollama.

## Tile Rendering Logic Error

### Problem
Tiles were rendered incorrectly - walls appeared as floors and floors appeared as walls.

### Root Cause
In the `render_dungeon` method, the logic for determining wall vs floor tiles was backwards. The code was checking:
```python
if dungeon_map[y, x]:
    self.console.print(x, y, ".", COLORS['floor'])  # Wrong - floor character for wall
else:
    self.console.print(x, y, "#", COLORS['wall'])   # Wrong - wall character for floor
```

However, the dungeon generator uses boolean arrays where:
- `True` = wall
- `False` = floor

### Solution
Fixed the logic to correctly map tile values to characters:
```python
if dungeon_map[y, x]:  # True = wall
    self.console.print(x, y, "#", COLORS['wall'])
else:  # False = floor
    self.console.print(x, y, ".", COLORS['floor'])
```

### Affected Code
- `darkdelve.py` line 1492: `render_dungeon` method logic

### Prevention
- Understand the data format used by the dungeon generator
- Test tile rendering with known input/output patterns
- Create unit tests for rendering functionality
- Use visual debugging when tile rendering looks wrong

## Tile Rendering Debug Tools

### Problem
When debugging map tile rendering issues, it's difficult to see what tiles are actually being rendered and verify the correct symbols are being used.

### Solution
Use the comprehensive test suite in `tests/test_tile_rendering.py` and the debug script `debug_tiles.py` to visualize map tiles as text symbols.

### Available Tools

1. **Unit Tests** (`tests/test_tile_rendering.py`):
   - `test_render_dungeon_floor_wall_logic`: Tests basic wall/floor rendering
   - `test_render_dungeon_explored_areas`: Tests color rendering for explored areas
   - `test_text_symbol_conversion`: Tests conversion to text grid format
   - `test_debug_output_visualization`: Tests debug output generation
   - `test_edge_cases`: Tests edge cases like empty maps

2. **Debug Script** (`debug_tiles.py`):
   - Generates visual text representation of the map
   - Shows visible vs explored vs unexplored tiles
   - Provides both detailed debug output and simplified text grid

### Usage Examples

**Run the test suite:**
```bash
python -m pytest tests/test_tile_rendering.py -v
```

**Use the debug script:**
```bash
python debug_tiles.py
```

### Debug Output Format

The debug tools output maps with the following symbols:
- `#` = Wall
- `.` = Floor
- `V` = Visible tile (uppercase in text grid)
- `E` = Explored but not visible tile (lowercase in text grid)
- `U` = Unexplored tile
- `?` = Unknown/unrendered tile

### How to Use for Debugging

1. When tiles look wrong, run the debug script to see the actual text representation
2. Check if the correct symbols are being used for walls vs floors
3. Verify that visibility is working correctly (visible tiles should be uppercase)
4. Use the unit tests to catch regressions when making changes

### Affected Code
- `tests/test_tile_rendering.py` - Comprehensive test suite
- `debug_tiles.py` - Debug visualization script
- `darkdelve.py` - `render_dungeon` method (tested by the suite)

## UI Text Rendering Issue

### Problem
UI text was rendering as full strings instead of individual characters, causing text to appear as "map tiles in place of text" instead of readable text.

### Root Cause
The UI rendering methods were using `console.print()` with full text strings, which were being treated as single characters rather than being rendered as individual characters.

### Solution
Added `_render_text()` helper method that renders text character by character using `console.print()` for each character individually.

### Affected Code
- `darkdelve.py` - UI rendering methods
- `tests/test_tile_rendering.py` - UI rendering tests

### Changes Made
1. Added `_render_text(x, y, text, color)` method to UI class
2. Updated `render_ui()` to use `_render_text()` instead of direct `console.print()` calls
3. Updated `render_combat_log()` to use `_render_text()` instead of direct `console.print()` calls
4. Updated tests to properly check for individual characters in console calls

### Prevention
- Always render text character by character in UI elements
- Use helper methods for text rendering to ensure consistency
- Test UI rendering with comprehensive test suites that check individual character rendering

## Monster and Item Spawning in Walls
### Problem
Monsters and items were spawning in walls instead of floors, making them invisible and causing gameplay issues.

### Root Cause
The spawn condition was checking `if self.dungeon_map[x, y]` which is `True` for walls, but should be `False` for floors.

### Solution
Changed the spawn conditions to check for floors:
- Monsters: `if not self.dungeon_map[x, y] and not any(e.x == x and e.y == y for e in self.entities)`
- Items: `if not self.dungeon_map[x, y] and not any(e.x == x and e.y == y for e in self.entities)`

### Affected Code
- `generate_level()` method in `Game` class (lines 1780, 1801)

### Prevention
Always double-check the logic for dungeon map coordinates: `True` = wall, `False` = floor.

## Player Movement Logic Error
### Problem
Player was getting blocked by objects they couldn't see due to incorrect movement logic.

### Root Cause
The `move_to()` method was checking `if dungeon_map[x, y]` which is `True` for walls, but should be checking for floors (`False`).

### Solution
Changed the movement condition to check for walkable floors:
```python
if not dungeon_map[x, y]:  # Check if it's a floor (False), not a wall (True)
```

### Affected Code
- `move_to()` method in `Entity` class (line 661)

### Prevention
Always verify the logic for movement: players can move through floors (`False`) but not walls (`True`).

## Console Coordinate System Issue
### Problem
Console character array access was using wrong coordinate system, causing text to appear at wrong positions and player character to not be found.

### Root Cause
tcod console character array has shape `(height, width)` but was being accessed as `console.ch[x, y]` instead of `console.ch[y, x]`.

### Solution
Fixed console character array access in tests to use correct coordinate system: `console.ch[y, x]`.

### Affected Code
- `test_game_rendering.py` - Fixed console character access in player character and UI text detection

### Prevention
- Always check console.ch.shape before accessing characters
- Use `console.ch[y, x]` for coordinate access (not `console.ch[x, y]`)
- Test coordinate system with simple debug scripts before complex tests

## Player Spawning in Walls
### Problem
Player was spawning in walls instead of walkable floors, making them unable to move.

### Root Cause
The dungeon generator was returning player start positions that were walls (True values) instead of floors (False values).

### Solution
Added validation in `generate_level()` method to check if the player start position is walkable, and if not, find the nearest walkable position.

### Affected Code
- `generate_level()` method in `Game` class (lines 1777-1795)

### Changes Made
1. Added check for `self.dungeon_map[player_start[0], player_start[1]]`
2. If position is a wall, search for nearest walkable position
3. Update player position to walkable location

### Prevention
- Always validate player start positions after dungeon generation
- Ensure players spawn on floors (False values), not walls (True values)
- Add fallback logic to find walkable positions if spawn location is invalid

## Tileset Character Rendering Issues
### Problem
Player character and other ASCII symbols render as incorrect visual artifacts (e.g., yellow square with dot instead of '@' symbol).

### Root Cause
The default tileset `dejavu10x10_gs_tc.png` does not have proper glyphs for certain ASCII characters, particularly the '@' symbol used for the player character.

### Solution
1. Create a custom ASCII tileset with proper character glyphs
2. Update the game configuration to use the new tileset
3. Test character rendering with the new tileset

### Affected Code
- `config/game.yaml`: Tileset configuration
- `generate_custom_tileset.py`: Custom tileset generation script
- `test_new_tileset.py`: Tileset testing script

### Changes Made
1. Created `generate_custom_tileset.py` to generate a custom ASCII tileset
2. Updated `config/game.yaml` to use `custom_ascii_tileset.png` instead of `dejavu10x10_gs_tc.png`
3. Created `test_new_tileset.py` to verify the fix works correctly

### Prevention
- Use custom tilesets designed for ASCII game characters
- Test all game characters with the chosen tileset
- Create character mapping documentation for tilesets
- Ensure player character is positioned within FOV bounds for testing

## Tileset Character Rendering Issues - RESOLVED
### Problem
Player character and other ASCII symbols render as incorrect visual artifacts (e.g., yellow square with dot instead of '@' symbol).

### Root Cause
The default tileset `dejavu10x10_gs_tc.png` does not have proper glyphs for certain ASCII characters, particularly the '@' symbol used for the player character.

### Solution
1. Create a proper ASCII tileset with correct character mappings
2. Update the game configuration to use the new tileset
3. Test character rendering with proper player positioning

### Affected Code
- `config/game.yaml`: Updated to use `proper_ascii_tileset.png`
- `generate_proper_tileset.py`: Custom tileset generation script
- `test_player_visibility.py`: Player visibility testing script

### Changes Made
1. Created `generate_proper_tileset.py` to generate a proper ASCII tileset
2. Updated `config/game.yaml` to use `proper_ascii_tileset.png` instead of `dejavu10x10_gs_tc.png`
3. Created `test_player_visibility.py` to verify the fix works correctly with proper player positioning
4. Created `test_tileset_directly.py` to analyze tileset content directly

### Resolution
✅ **Tileset successfully created** - `assets/tilesets/proper_ascii_tileset.png`
✅ **Player character correctly rendered** - '@' symbol displays properly
✅ **Console data confirmed** - Character code 64 ('@') is being rendered
✅ **Color correct** - Yellow color (255, 255, 0) is applied correctly
✅ **Player positioning fixed** - Players are now positioned within FOV bounds

### Prevention
- Use custom tilesets designed for ASCII game characters
- Test all game characters with the chosen tileset
- Create character mapping documentation for tilesets
- Ensure player character is positioned within FOV bounds for testing

## FOV and Console Refresh Artifacts

### Problem
The map can visibly refresh every frame and appear spatially wrong, especially when the player is not on an `x == y` diagonal.

### Root Cause
DarkDelve dungeon arrays are indexed as `[x, y]`, but tcod's `compute_fov()` expects its `pov` argument as `(row, column)`. Passing `(safe_y, safe_x)` centers FOV on the swapped coordinate when the player is off-diagonal.

### Solution
Pass FOV as `(safe_x, safe_y)` and draw console output with terminal cursor positioning instead of `print(self._console)`:

```python
fov = tcod.map.compute_fov(
    transparency=~dungeon_map,
    pov=(safe_x, safe_y),
    radius=self.radius,
    algorithm=tcod.constants.FOV_BASIC,
)
```

```python
def present(self) -> None:
    sys.stdout.write("\033[H\033[2J" + frame + "\033[0m\n")
```

### Affected Code
- [`darkdelve.py`](darkdelve.py:946) - `FOVSystem.compute()`
- [`src/presentation/renderer.py`](src/presentation/renderer.py:55) - `ConsoleRenderer.present()`
- [`tests/test_map_rendering.py`](tests/test_map_rendering.py:1) - FOV and screenshot regression tests

### Prevention
- Keep all rendering code consistent on DarkDelve's `[x, y]` dungeon coordinate system.
- Do not use `print(self._console)`; use a stable terminal redraw path during gameplay.
- Add off-diagonal player FOV tests and headless Linux screenshot tests for visual regressions.

## Item Pickup Feedback

### Problem
Players can step onto item entities but receive no feedback if they press the pickup key while no item is on the current tile. Successful pickups also need to remove the item from both the entity list and the energy scheduler.

### Root Cause
`Game.pickup_item()` only emitted messages when an item was found and successfully added to inventory. It returned `None`, so input handling had no explicit success/failure signal, and tests did not verify scheduler cleanup.

### Solution
Return a boolean from [`Game.pickup_item()`](darkdelve.py:2113), remove picked-up item entities from [`EnergySystem`](darkdelve.py:802), and report when the current tile has no pickup target.

```python
picked_up = self.pickup_item()
if not picked_up:
    self.add_message("There is nothing here to pick up.")
```

### Affected Code
- [`darkdelve.py`](darkdelve.py:2113) - `Game.pickup_item()`
- [`darkdelve.py`](darkdelve.py:1625) - pickup key handling in `InputHandler`
- [`tests/test_game_logic.py`](tests/test_game_logic.py:108) - item pickup and feedback regression tests
- [`tests/test_console_input.py`](tests/test_console_input.py:31) - console comma/period key mapping

### Prevention
- Pickup keys should produce user feedback on both success and failure.
- Removing floor items must keep entity and energy-system state consistent.
- Console mode needs explicit tests for comma and period key conversion.


## Console UI Layout and Menu Input

### Problem
Console output can wrap or clip when the offscreen console is wider than the terminal, and the status panel can render below the configured console height. Arrow keys in raw terminal mode can also arrive as escape sequences and be mistaken for the menu escape key.

### Root Cause
The console renderer presented the full configured console width and height without checking terminal size. The UI panel was placed at `map_height + 3`, which is below the 50-row console used by the default config. Raw terminal arrow keys begin with `\x1b`, so the previous console key mapper treated them as `ESCAPE`.

### Solution
Clip console presentation to [`shutil.get_terminal_size()`](src/presentation/renderer.py:56), reserve UI rows inside the configured console height, render status/messages/controls within those rows, and map full arrow escape sequences to directional keys:

```python
"\x1b[A": (tcod.event.Scancode.UP, tcod.event.KeySym.UP)
```

### Affected Code
- [`darkdelve.py`](darkdelve.py:1530) - `UI` status-panel layout
- [`darkdelve.py`](darkdelve.py:1598) - `UI.render_ui()`
- [`darkdelve.py`](darkdelve.py:2030) - console arrow escape-sequence mapping
- [`darkdelve.py`](darkdelve.py:2054) - console escape-sequence reading
- [`src/presentation/renderer.py`](src/presentation/renderer.py:56) - terminal-size clipping in `ConsoleRenderer.present()`
- [`tests/test_console_input.py`](tests/test_console_input.py:24) - console key and menu regression tests
- [`tests/test_map_rendering.py`](tests/test_map_rendering.py:45) - terminal clipping and status-panel tests

### Prevention
- Console presentation must never exceed the active terminal size.
- UI rows must fit inside the configured console height.
- Arrow keys should navigate menus, not close them.
- Unknown menu keys should be ignored until Escape or Enter is pressed.

## Startup Monster Initiative

### Problem
On some generated levels, fast monsters can take multiple turns before the player gets their first input, which can kill the player immediately after startup.

### Root Cause
The energy system selects the actor with the highest accumulated energy. A level 1 monster with speed 120 reaches the 100-energy action threshold before the player at speed 100, so a fast scout can close distance and attack before the player acts.

### Solution
Give the player a one-turn startup priority when initializing a new level:

```python
initial_energy = 100 if entity is self.player else 0
self.energy_system.add_entity(entity, initial_energy=initial_energy)
```

### Affected Code
- [`darkdelve.py`](darkdelve.py:794) - `EnergySystem.add_entity()`
- [`darkdelve.py`](darkdelve.py:1914) - level energy initialization
- [`tests/test_energy_system.py`](tests/test_energy_system.py:6) - startup initiative regression test

### Prevention
- New levels should always let the player act before fast enemies close distance.
- Add energy-system tests for turn-order edge cases.
- Simulate generated startup states when a player can die before input.
## Console Renderer Input

### Problem
In console renderer mode, `tcod.event.wait()` can return an empty event iterator when SDL has not been initialized for a visible context. The game loop then continues without waiting for the player, allowing monsters to act repeatedly before input. Console-only screens such as inventory, character, and menu also need the same backend-specific input path.

### Root Cause
The console renderer only owns an offscreen `tcod.console.Console`, not a tcod context/window. Event polling depends on SDL input initialization, so console mode needs its own blocking input path instead of calling `tcod.event.wait()` directly.

### Solution
Centralize event waiting behind [`Game._wait_for_events()`](darkdelve.py:2005), route console renderers through [`Game._wait_for_console_input()`](darkdelve.py:2031), and convert terminal keys into `tcod.event.KeyDown` objects for the existing input handler:

```python
events = self._wait_for_events()
```

```python
def _wait_for_events(self) -> List[Any]:
    if self._uses_console_renderer():
        return self._wait_for_console_input()
    return tcod.event.wait()
```

### Affected Code
- [`darkdelve.py`](darkdelve.py:1953) - player input selection in `main_loop()`
- [`darkdelve.py`](darkdelve.py:2005) - centralized event waiting
- [`darkdelve.py`](darkdelve.py:2031) - console renderer detection and key conversion helpers
- [`darkdelve.py`](darkdelve.py:2142) - inventory screen input
- [`darkdelve.py`](darkdelve.py:2157) - character screen input
- [`darkdelve.py`](darkdelve.py:2166) - menu input
- [`tests/test_console_input.py`](tests/test_console_input.py:6) - console input regression tests

### Prevention
- Console mode must block for player input before monsters can continue acting.
- All gameplay and modal screens should call the same event-waiting helper.
- Keep console input conversion covered by tests.
- Verify non-interactive runs exit instead of simulating unattended monster turns.
## Generated Item Data and Entity Rendering

### Problem
Generated or external item data can provide numeric fields such as `weight` as strings. Pickup then crashes with `TypeError: unsupported operand type(s) for +: 'int' and 'str'` when inventory weight is checked. Items on the player's tile can also render after the player and overwrite the player's `@` glyph.

### Root Cause
`Inventory.add_item()` and `Inventory.get_total_weight()` assumed item weights were always integers. `UI.render_entities()` rendered entities in list order, so an item entity sharing the player's tile could draw after the player.

### Solution
Normalize item weights to integers before arithmetic and render the player after other visible entities so the player glyph is never overwritten by an item on the same tile:

```python
def _weight_value(self, value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
```

```python
for entity in visible_entities:
    self.renderer.print(entity.x, entity.y, entity.char, entity.color)
if player_entity is not None:
    self.renderer.print(player_entity.x, player_entity.y, player_entity.char, player_entity.color)
```

### Affected Code
- [`darkdelve.py`](darkdelve.py:429) - inventory weight normalization
- [`darkdelve.py`](darkdelve.py:1571) - player-last entity rendering
- [`tests/test_game_logic.py`](tests/test_game_logic.py:148) - string item weight regression
- [`tests/test_map_rendering.py`](tests/test_map_rendering.py:95) - player-over-item rendering regression

### Prevention
- Treat generated data as untrusted and normalize numeric fields before math.
- Keep pickup covered by tests, including generated-content edge cases.
- Always render the player after non-player entities that can share a tile.
## Ollama Player AI JSON Protocol

### Problem
The local playtester drives the game with an LLM through console stdin/stdout. If
Ollama returns non-JSON text, extra markdown, a missing `action`, or an invalid
action, arbitrary text can be injected into the game process or the playtester
can lose telemetry context for why a fallback happened.

### Root Cause
LLM output is untrusted even when the Ollama endpoint is asked for JSON. Local
models can omit fields, wrap JSON in markdown fences, append prose, or choose an
action outside the console action set.

### Solution
Keep the validation boundary in [`player_agent.py`](../player_agent.py:1):

```python
"format": "json"
```

must be present in every `/api/generate` payload. Validate the response schema:

```json
{
  "macro_goal": "string",
  "reasoning": "string",
  "action": "w|a|s|d|e|i",
  "telemetry_notes": "string"
}
```

Sanitize where possible, append issues to `telemetry_notes`, and fall back to the
safe wait action `e` when the action is missing or invalid. [`ollama_playtester.py`](../ollama_playtester.py:1)
must append the final map frame and stderr tail to telemetry when the game exits
non-zero or crashes.

### Affected Code
- [`player_agent.py`](../player_agent.py:1) - prompt construction, JSON parsing,
  response validation, and safe-action fallback
- [`ollama_playtester.py`](../ollama_playtester.py:1) - subprocess loop, frame
  parsing, action injection, and crash telemetry
- [`tests/test_player_agent.py`](../tests/test_player_agent.py:1) - prompt,
  validation, sanitization, and history regression tests
- [`tests/test_ollama_playtester.py`](../tests/test_ollama_playtester.py:1) -
  frame parsing, stats extraction, and telemetry append tests

### Prevention
- Never inject raw model text into game stdin.
- Always include `"format": "json"` in Ollama payloads.
- Keep the five-turn history buffer small and deterministic.
- Log invalid JSON, missing fields, invalid actions, and fallback decisions in
  telemetry.
- Preserve console frame parsing around `\033[H\033[2J` because the console
  renderer clears each frame with that exact escape sequence.

## Content DB Schema Gotcha

### Problem
The `content.db` schema is key-based, not tag-based. The `generations` table uses a `key` column like `"items_arcane|divine"` or `"monsters_undead|demon|beast_1"`. Tags are embedded in the key, not in a separate column. Querying by tags requires `LIKE '%tag%'` on the key column. Do not assume a normalized schema — the key IS the tag encoding.

### Root Cause
When implementing seed-based content generation, developers might assume the content database has a normalized schema with separate tag columns. However, the existing `generations` table stores tags as part of the key string.

### Solution
Use `LIKE '%tag%'` queries on the key column when filtering by tags. For example:

```python
# Get seeds with specific tags
seeds = repo.get_seeds_by_tags(["arcane", "divine"])
# This translates to: key LIKE '%arcane%' AND key LIKE '%divine%'
```

### Affected Code
- `ContentRepository.get_seeds_by_tags()` method
- Any code that assumes tag-based querying on a normalized schema

### Prevention
- Always query the key column with `LIKE '%tag%'` patterns
- Remember that tags are encoded in the key string, not separate columns
- Use the provided `ContentRepository` methods rather than writing raw SQL
- Document the key format: `"content_type_tag1|tag2|tag3"`

## Explored State Leak Between Levels

### Problem
When transitioning from level 1 to level 2, the explored (fog-of-war) state from level 1 leaks into level 2, causing the player to see areas on the new level that should be unexplored.

### Root Cause
The `FOVSystem.explored` array is initialized once in `__init__` and reused across level transitions. The `compute()` method uses `|=` (OR assignment) to accumulate explored tiles, so if the explored array already exists with the same shape as the new dungeon map, it retains the old explored state.

### Solution
Reset the explored state to `None` before computing FOV for a new level:

```python
# In _generate_floor1() and _generate_standard_level()
self.fov_system.explored = None
self.fov = self.fov_system.compute(self.dungeon_map, self.player.x, self.player.y)
```

This forces `compute()` to create a fresh `np.zeros()` array for the new level.

### Affected Code
- [`darkdelve.py`](darkdelve.py:2336) - `_generate_floor1()` method
- [`darkdelve.py`](darkdelve.py:2481) - `_generate_standard_level()` method
- [`darkdelve.py`](darkdelve.py:1146) - `FOVSystem.compute()` method

### Prevention
- Always reset `fov_system.explored = None` when generating a new level
- Consider adding a `reset()` method to `FOVSystem` for clarity
- Add tests that verify explored state is fresh for each level