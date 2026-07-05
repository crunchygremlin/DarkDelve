# Task T-2026-0630-006: Critical Multi-System Bug Fixes

## Task ID
T-2026-0630-006

## Complexity Classification
**CRITICAL** - Multiple core systems broken (inventory, stairs/visibility, DM/LLM)

## Primary Objective
Fix three critical game-breaking bugs:
1. **Inventory Use/Drop Crash** - Using items from inventory crashes the game
2. **Stairs Visibility Bug** - Stairs visible from anywhere on floor 1 (should only be visible in FOV)
3. **DM/LLM Integration Broken** - Dungeon Master / LLM agent integration broken

## Specific Bugs to Fix

### Bug 1: Inventory Use/Drop Crash
- **Location**: `src/application/game_commands/use_command.py`, `src/application/game_commands/drop_command.py`, `src/application/game_commands/equip_command.py`
- **Symptom**: Using items from inventory crashes the game
- **Related files**: `src/application/game_commands/use_command.py`, `src/application/game_commands/drop_command.py`, `src/application/game_commands/equip_command.py`, `src/application/game_queries/inventory_query.py`, `src/domain/services/inventory_service.py`, `tests/test_inventory_use_drop.py`

### Bug 2: Stairs Visibility Bug (Floor 1)
- **Location**: `src/domain/services/floor1_generator.py`, `src/domain/services/perception_service.py`, `src/presentation/renderers/tile_renderer.py`
- **Symptom**: Stairs visible from anywhere on floor 1 (should only be visible in FOV)
- **Related files**: `src/domain/services/floor1_generator.py`, `src/domain/services/perception_service.py`, `src/presentation/renderers/tile_renderer.py`, `src/domain/services/perception_service.py`, `tests/test_stairs.py`, `playtest/repro_floor1_stairs.py`

### Bug 3: DM/LLM Integration Broken
- **Location**: `src/domain/agents/dungeon_master_agent.py`, `src/domain/agents/commander_agent.py`, `src/domain/agents/integration.py`, `src/domain/services/dungeon_master_service.py`, `src/domain/agents/llm_agent.py`
- **Symptom**: DM/LLM agent integration broken - DM not responding, LLM not being called properly
- **Related files**: `src/domain/agents/dungeon_master_agent.py`, `src/domain/agents/commander_agent.py`, `src/domain/agents/integration.py`, `src/domain/services/dungeon_master_service.py`, `src/domain/agents/llm_agent.py`, `src/infrastructure/external/ollama_service.py`, `tests/test_dungeon_master_agent.py`, `tests/test_dungeon_master_service.py`

## Pipeline Stages Required
1. **Architect** - Design fixes for all three systems
2. **Coder** - Implement fixes for all three bugs
3. **Playtester** - Run playtests to verify all three bugs fixed
4. **Debugger** - If any playtest fails, debug and fix

## Success Criteria
1. Inventory use/drop/equip commands work without crashing
2. Stairs on floor 1 only visible within FOV (not visible from across the map)
3. DM/LLM integration working - DM responds to events, LLM calls work
4. All existing tests pass
5. Playtest verification passes for all three issues

## Related Files to Review
- `playtest/reports/T-2026-0630-005_crash_verification.md` - Inventory crash report
- `playtest/repro_floor1_stairs.py` - Stairs visibility repro
- `playtest/reports/T-2026-0630-005_final_verification_v2.md` - Previous verification
- `tests/test_inventory_use_drop.py` - Inventory tests
- `tests/test_stairs.py` - Stairs tests
- `tests/test_dungeon_master_agent.py` - DM tests
- `tests/test_dungeon_master_service.py` - DM service tests
