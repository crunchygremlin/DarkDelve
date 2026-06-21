# DarkDelve Implementation Guide

## Step-by-Step Refactoring Process

This guide provides a clear, step-by-step process for refactoring the monolithic DarkDelve codebase into a modular structure. The process is designed to be followed by an LLM assistant (Qwen 7b Coder).

## Phase 1: Setup and Preparation

### Step 1: Create Project Structure
```bash
mkdir -p src/{config,core,systems,content,data,ui,persistence,utils}
touch src/__init__.py
touch src/config/__init__.py
touch src/core/__init__.py
touch src/systems/__init__.py
touch src/content/__init__.py
touch src/data/__init__.py
touch src/ui/__init__.py
touch src/persistence/__init__.py
touch src/utils/__init__.py
```

### Step 2: Extract Configuration
1. Copy the `CONFIG_PATH` and `load_config()` function to `src/config/config.py`
2. Move all configuration-related constants to this module
3. Update imports in main file to use `from src.config import config`

### Step 3: Extract Utilities
1. Move utility functions (`clamp`, `heuristic`) to `src/utils/math.py`
2. Create logging system in `src/utils/logger.py`
3. Update imports throughout the codebase

## Phase 2: Core Module Implementation

### Step 4: Extract Game State
1. Create `src/core/game_state.py` with `GameState` dataclass
2. Move all game state data structures from main file
3. Implement serialization/deserialization methods
4. Update main file to import and use `GameState`

### Step 5: Extract Game Loop
1. Create `src/core/game_loop.py` with `GameLoop` class
2. Extract timing and update logic from main game loop
3. Implement delta time calculations
4. Update main file to use `GameLoop`

### Step 6: Extract Main Game Controller
1. Create `src/core/game.py` with `Game` class
2. Move main game logic from `main()` function
3. Implement system initialization and management
4. Update `main()` to create and run `Game` instance

## Phase 3: Systems Module Implementation

### Step 7: Extract Dungeon System
1. Create `src/systems/dungeon.py` with `DungeonGenerator` class
2. Move all dungeon generation logic
3. Extract level themes and generation algorithms
4. Update main file to use `DungeonGenerator`

### Step 8: Extract FOV System
1. Create `src/systems/fov.py` with `FOVSystem` class
2. Move field of view calculation logic
3. Implement raycasting algorithm
4. Update main file to use `FOVSystem`

### Step 9: Extract Combat System
1. Create `src/systems/combat.py` with `CombatResolver` class
2. Move all combat resolution logic
3. Extract damage calculations and combat events
4. Update main file to use `CombatResolver`

### Step 10: Extract Energy System
1. Create `src/systems/energy.py` with `EnergySystem` class
2. Move action point system logic
3. Implement energy regeneration
4. Update main file to use `EnergySystem`

### Step 11: Extract Survival System
1. Create `src/systems/survival.py` with `SurvivalSystem` class
2. Move hunger and survival mechanics
3. Implement health and status effects
4. Update main file to use `SurvivalSystem`

### Step 12: Extract Identification System
1. Create `src/systems/identification.py` with `IdentificationSystem` class
2. Move item identification logic
3. Implement identification chances and mechanics
4. Update main file to use `IdentificationSystem`

## Phase 4: Content Module Implementation

### Step 13: Extract Ollama Management
1. Create `src/content/ollama.py` with `EmbeddedOllama` class
2. Move Ollama instance management logic
3. Implement process control and API calls
4. Update main file to use `EmbeddedOllama`

### Step 14: Extract Content Cache
1. Create `src/content/cache.py` with `ContentCache` class
2. Move SQLite caching logic
3. Implement cache management and retrieval
4. Update main file to use `ContentCache`

### Step 15: Extract Content Generator
1. Create `src/content/generator.py` with `ContentGenerator` class
2. Move LLM-based content generation logic
3. Implement prompt templates and generation methods
4. Update main file to use `ContentGenerator`

### Step 16: Extract Mob System
1. Create `src/content/mobs.py` with `MobRoster` class
2. Move monster template and generation logic
3. Implement mob generation algorithms
4. Update main file to use `MobRoster`

## Phase 5: Data Structures Implementation

### Step 17: Extract Entity System
1. Create `src/data/entity.py` with `Entity` dataclass
2. Move entity-related data structures
3. Implement entity methods and behaviors
4. Update main file to use `Entity`

### Step 18: Extract Item System
1. Create `src/data/item.py` with `Item` dataclass
2. Move item-related data structures
3. Implement item effects and properties
4. Update main file to use `Item`

### Step 19: Extract Inventory System
1. Create `src/data/inventory.py` with `Inventory` dataclass
2. Move inventory management logic
3. Implement inventory operations
4. Update main file to use `Inventory`

### Step 20: Extract Event System
1. Create `src/data/events.py` with `CombatEvent` and `CombatLog` classes
2. Move event-related data structures
3. Implement event management and logging
4. Update main file to use event classes

## Phase 6: UI Module Implementation

### Step 21: Extract UI System
1. Create `src/ui/ui.py` with `UI` class
2. Move UI management logic
3. Implement UI initialization and management
4. Update main file to use `UI`

### Step 22: Extract Renderer
1. Create `src/ui/renderer.py` with `Renderer` class
2. Move rendering logic from UI class
3. Implement separate rendering methods
4. Update UI class to use `Renderer`

### Step 23: Extract Input Handler
1. Create `src/ui/input.py` with `InputHandler` class
2. Move input processing logic
3. Implement input mapping and handling
4. Update main file to use `InputHandler`

## Phase 7: Persistence Module Implementation

### Step 24: Extract Save System
1. Create `src/persistence/save.py` with `SaveSystem` class
2. Move save/load logic
3. Implement save file management
4. Update main file to use `SaveSystem`

### Step 25: Extract High Scores
1. Create `src/persistence/highscores.py` with `HighScores` class
2. Move high score management logic
3. Implement score tracking and persistence
4. Update main file to use `HighScores`

## Phase 8: Integration and Testing

### Step 26: Update Main Entry Point
1. Create `src/main.py` with clean entry point
2. Import all necessary modules
3. Initialize game systems
4. Start main game loop

### Step 27: Update Dependencies
1. Review all imports and update to use new module structure
2. Remove circular dependencies
3. Ensure all modules are properly imported
4. Test basic functionality

### Step 28: Add Configuration Support
1. Ensure all modules can accept configuration
2. Implement configuration validation
3. Add configuration documentation
4. Test configuration loading

### Step 29: Add Error Handling
1. Add proper error handling throughout modules
2. Implement logging for debugging
3. Add exception handling for edge cases
4. Test error scenarios

### Step 30: Performance Optimization
1. Profile performance bottlenecks
2. Optimize LLM calls with caching
3. Improve rendering performance
4. Optimize memory usage

## Testing Strategy

### Unit Testing
1. Create test files for each module
2. Test individual system functionality
3. Mock external dependencies (Ollama, TCOD)
4. Run comprehensive unit tests

### Integration Testing
1. Test module interactions
2. Test game flow and state management
3. Test content generation integration
4. Test UI and input handling

### System Testing
1. Test complete game functionality
2. Test save/load functionality
3. Test performance with LLM calls
4. Test edge cases and error conditions

## Local Ollama Player AI Playtest Implementation Notes

DarkDelve supports two playtester modes:

- Subprocess mode: [`ollama_playtester.py`](../ollama_playtester.py:1) launches
  [`darkdelve.py`](../darkdelve.py:1), scrapes ANSI-cleared console frames, and
  injects actions through stdin.
- In-process library mode: [`MCPPlaytester`](../src/infrastructure/services/mcp_integration.py:44)
  drives a [`Game`](../darkdelve.py:1774) instance directly. This is the preferred
  integration path for local AI playtesting because it avoids process boundaries,
  preserves telemetry, and can be embedded by tools without starting a separate
  server.

### Subprocess playtester contract

1. Create `player_agent.py` with `OllamaConfig`, `PlayerDecision`, and
   `PlayerAgent`.
2. Build a `Survive & Explore` system prompt, add an optional persona modifier,
   and include the three built-in personas: `Default`, `Aggressive Stress-Tester`,
   and `Boundary Pushing Explorer`.
3. Keep a five-turn history buffer and include it in each user prompt.
4. Every `/api/generate` request must include `"format": "json"`.
5. Validate the model response schema:
   `macro_goal`, `reasoning`, `action`, and `telemetry_notes`.
6. Accept only `w`, `a`, `s`, `d`, `e`, or `i` as the action. Malformed JSON,
   missing fields, or invalid actions must be logged in telemetry and fall back
   to the safe wait action `e`.
7. Create `ollama_playtester.py` with `Popen`, stdout frame parsing, action
   injection, telemetry append, and crash/non-zero-exit logging.
8. Add focused tests for prompt generation, persona injection, response
   validation, JSON sanitization, five-turn history, frame parsing, stats
   extraction, and telemetry append behavior.
9. Document usage and telemetry format in `playtest/README.md` and defaults in
   `playtest/playtest_config.yaml`.

### In-process library playtester contract

1. Expose a non-blocking action entry point on [`Game`](../darkdelve.py:1774),
   such as [`Game.process_action()`](../darkdelve.py:2112), so automation can
   apply `w`, `a`, `s`, `d`, `e`, pickup, stairs, and quit actions without
   entering blocking console menus.
2. Extract the current view into plain text with [`Game.render_frame_text()`](../darkdelve.py:2205).
   The text frame should be suitable for the Player AI prompt and should not
   present to stdout during automated runs.
3. Implement [`MCPPlaytester`](../src/infrastructure/services/mcp_integration.py:44)
   as a library wrapper around the existing `PlayerAgent`, `PlaytestConfig`,
   `TelemetryStore`, `extract_stats`, and `InstructionBus`.
4. For each turn, render the frame, extract stats, ask `PlayerAgent.decide(...)`,
   call `Game.main_loop(action=decision.action, render_to_stdout=False,
   frame_text=frame_text)`, append telemetry, and repeat until `max_turns`,
   exit, crash, or player death.
5. Treat `i` as a no-op in automated action processing. The real inventory screen
   waits for a second input event, so in-process automation should avoid entering
   that blocking state unless a separate menu driver is implemented.
6. Add integration tests with a fake `PlayerAgent` and fake `Game` to prove the
   playtester loop writes telemetry and passes actions without human input.

## Common Pitfalls to Avoid

1. **Circular Dependencies**: Ensure proper module ordering and imports
2. **Configuration Issues**: Test configuration loading and validation
3. **LLM Integration**: Handle LLM failures gracefully
4. **Memory Management**: Proper cleanup of resources
5. **Performance**: Profile and optimize critical paths
6. **Error Handling**: Comprehensive error handling throughout
7. **Testing**: Thorough testing at each phase

## Success Criteria

1. All modules are properly separated and documented
2. The game runs without errors
3. Content generation works correctly
4. Save/load functionality is preserved
5. Performance is acceptable
6. Code is maintainable and extensible

## Next Steps

1. Start with Phase 1: Setup and Preparation
2. Follow each step in order
3. Test after each major phase
4. Document any issues or challenges
5. Review and refactor as needed
