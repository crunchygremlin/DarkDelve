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