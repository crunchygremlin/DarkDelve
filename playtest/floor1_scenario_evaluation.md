# Floor 1 Playtest Scenario Evaluation

## Current State Summary

The floor 1 dungeon entrance implementation is **functional and tested**. This document evaluates the existing playtest infrastructure and provides actionable scenarios for an LLM to modify, extend, and validate floor 1 behavior.

---

## Existing Playtest Infrastructure

### 1. Unit Tests (`tests/test_floor1_generator.py`)
- **13 tests** covering generator, spawner, and monster templates
- All pass consistently
- Tests are **deterministic** (no mocking of random, but results are stable across runs)

### 2. Entity Spawning Tests (`tests/test_entity_spawning.py`)
- **5 tests** verifying entities spawn inside map, on floor tiles, not on walls, no overlaps
- All pass after the Cave Rat overlap fix

### 3. Manual Playtest (`tests/test_manual_playtest.py`)
- **6 tests** controlling the game via WASD keypresses
- 3 pre-existing failures (monster movement/approach tests) — **unrelated to floor1**
- These failures indicate monsters on floor 1 don't approach the player during wait

### 4. DM Playtester (`playtest/dm_playtester.py` + `playtest/dm_test_scenarios.py`)
- **10 scenarios** testing DM systems (behavior, level design, items, narrative, loyalty, durability, damage, context, pipeline, difficulty)
- **No floor1-specific scenarios exist yet**
- The DM test scenarios use a `test_type` dispatch pattern — new types need a handler in `dm_playtester.py`

### 5. In-Process Playtester (`src/infrastructure/services/mcp_integration.py`)
- `MCPPlaytester` drives the full game loop with an LLM agent
- Produces telemetry entries per turn
- No floor1-specific assertions

### 6. Verification Script (`playtest/verify_floor1_generation.py`)
- Standalone script that initializes the game and checks floor 1 properties
- Covers: map shape, player position, entity overlaps, wall spawns, monster types, guard counts, den creatures, roaming creatures, corpse loot, stat bounds, stair validity

---

## Gaps & Issues Found

### Critical
1. **Monster AI doesn't approach player on floor 1** — The `test_manual_playtest.py` failures (test_03, test_04, test_05) show monsters don't move toward the player during wait. This is likely because floor 1 entities are created with `intel_tier=1` but lack proper AI agent assignment (the `_generate_floor1()` method doesn't register agents via `agent_manager` like `_generate_standard_level()` does).

### Moderate
2. **No floor1 scenarios in DM playtester** — The `dm_test_scenarios.py` has no `floor1_generation` test type
3. **No telemetry validation for floor 1** — The MCP playtester doesn't assert floor1-specific properties
4. **Roaming creature count is low** — Only 1 roaming creature spawned in the test run (expected 3-5). The `_place_roaming_spawns()` method requires floor tiles >5 tiles from main path, which is hard to satisfy given the map layout.

### Minor
5. **`config/floor1_monsters.yaml` is not loaded by code** — The YAML file exists but `floor1_spawner.py` uses hardcoded `MONSTER_TEMPLATES` dict instead of loading from YAML
6. **No test for descending to floor 2** — Verifying the transition from floor 1 (custom generator) to floor 2 (standard generator) works correctly

---

## Scenarios for LLM to Implement

### Scenario A: Fix Monster AI on Floor 1
**File:** `darkdelve.py` → `_generate_floor1()` method  
**Problem:** Floor 1 entities lack AI agent registration  
**Action:** After spawning entities, register agents for non-player entities:
```python
# In _generate_floor1(), after spawning entities:
for entity in self.entities:
    if entity is self.player:
        continue
    if getattr(entity, 'is_commander', False):
        agent = CommanderAgent(entity, home_position=(entity.x, entity.y))
    else:
        agent = RandomAgent(entity, agent_type=AgentType.MONSTER)
    self.agent_manager.register_agent(agent)
```

### Scenario B: Add Floor1 Generation Scenario to DM Playtester
**File:** `playtest/dm_test_scenarios.py`  
**Action:** Add a new `DMTestScenario` with `test_type="floor1_generation"`:
```python
DMTestScenario(
    name="floor1_generation_test",
    description="Verify floor 1 generates with guards, dens, roamers, corpses, no overlaps",
    test_type="floor1_generation",
    setup={"config": {...}},
    expected_outcomes={
        "has_guards": True,
        "has_sergeants": True,
        "has_spider_den": True,
        "has_rat_den": True,
        "has_corpses": True,
        "no_overlaps": True,
        "no_wall_spawns": True,
        "monsters_weaker_than_player": True,
    }
)
```
**Also add handler in `dm_playtester.py`:** `run_floor1_generation_test()` method

### Scenario C: Add Floor1 Telemetry Assertions
**File:** `src/infrastructure/services/mcp_integration.py` or new test file  
**Action:** After floor 1 initialization, assert:
- Entity count is within expected range (15-30)
- At least 2 guard sergeants exist
- At least 1 spider queen or rat king exists
- No two blocking entities share a position
- All entities are on floor tiles

### Scenario D: Fix Roaming Creature Placement
**File:** `src/application/services/floor1_generator.py` → `_place_roaming_spawns()`  
**Problem:** The `min_dist > 5` constraint is too strict for the current map layout  
**Action:** Reduce to `min_dist > 3` or increase search attempts to 200

### Scenario E: Load Monster Templates from YAML
**File:** `src/application/services/floor1_spawner.py`  
**Problem:** `MONSTER_TEMPLATES` is hardcoded instead of loading from `config/floor1_monsters.yaml`  
**Action:** Add a `load_templates()` function that reads YAML and returns the template dict

### Scenario F: Test Floor 1 → Floor 2 Transition
**File:** New test in `tests/test_floor1_generator.py`  
**Action:** Generate floor 1, simulate descending stairs, verify floor 2 generates with standard generator without errors

### Scenario G: Fix Manual Playtest Monster Movement
**File:** `tests/test_manual_playtest.py`  
**Problem:** Tests 03-05 fail because monsters don't approach player  
**Action:** Once Scenario A is fixed, re-run these tests. If they still fail, investigate whether `RandomAgent` decision-making works correctly on floor 1 entities.

---

## Priority Order

1. **Scenario A** (Critical — monsters don't move/approach)
2. **Scenario D** (Moderate — too few roaming creatures)
3. **Scenario B** (Moderate — no DM playtest coverage for floor1)
4. **Scenario C** (Moderate — no telemetry validation)
5. **Scenario G** (Moderate — fix pre-existing test failures)
6. **Scenario E** (Minor — YAML loading)
7. **Scenario F** (Minor — transition test)

---

## Evidence Files
- `playtest/verify_floor1_generation.py` — Automated floor 1 verification script
- `playtest/floor1_scenario_evaluation.md` — This document
- `tests/test_floor1_generator.py` — 13 unit tests (all pass)
- `tests/test_entity_spawning.py` — 5 entity tests (all pass)
- `tests/test_manual_playtest.py` — 6 movement tests (3 fail, pre-existing)
