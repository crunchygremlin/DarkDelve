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