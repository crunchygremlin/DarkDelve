# Floor 1 Fixes Implementation Plan

## Context

Floor 1 dungeon entrance was implemented with specialized generator and spawner. Review found:
1. Monsters don't approach the player (missing AI agent registration)
2. Roaming creatures too sparse (distance constraint too strict)
3. Monster templates hardcoded instead of loaded from YAML
4. No floor1-specific DM playtest scenarios
5. No floor1 telemetry assertions
6. No floor1 to floor2 transition test

## Implementation Instructions

Work through these tasks IN ORDER. After each task, run the validation tests before proceeding. If any test fails, STOP and fix the issue before moving on.

---

### Task 1: Register AI Agents for Floor 1 Monsters (Critical)

**File:** `darkdelve.py`
**Where:** Inside `_generate_floor1()` method, after the item-placement loop (after the `break` at line 2037), before energy system init (line 2039)

**What to do:** Add a loop that registers AI agents for every non-player entity, mirroring the pattern already used in `_generate_standard_level()` (lines 2146-2151).

**Exact change:** Replace the current lines 2037-2043 with:

```python
                     self.entities.append(entity)
                     break

+        # Register AI agents for floor 1 monsters
+        from src.domain.agents import CommanderAgent, RandomAgent, AgentType
+        for entity in self.entities:
+            if entity is self.player:
+                continue
+            if getattr(entity, 'is_commander', False):
+                agent = CommanderAgent(entity, home_position=(entity.x, entity.y))
+            else:
+                agent = RandomAgent(entity, agent_type=AgentType.MONSTER)
+            self.agent_manager.register_agent(agent)
+
         # Initialize energy system
         self.energy_system = EnergySystem()
         for entity in self.entities:
```

**Search block to find (lines 2035-2043):**
```
                    self.entities.append(entity)
                    break
        
        # Initialize energy system
        self.energy_system = EnergySystem()
        for entity in self.entities:
            initial_energy = 100 if entity is self.player else 0
            self.energy_system.add_entity(entity, initial_energy=initial_energy)
```

**Validation:** `cd /home/danny/Code/DarkDelve && python -m pytest tests/test_manual_playtest.py::TestManualPlaytestMonsterMovement::test_03_monsters_approach_when_player_waits tests/test_manual_playtest.py::TestManualPlaytestMonsterMovement::test_04_monsters_approach_when_player_moves_away -v` — both should PASS.

---

### Task 2: Relax Roaming Creature Placement

**File:** `src/application/services/floor1_generator.py`
**Where:** `_place_roaming_spawns()` method, line 221 and line 229

**What to do:** Two changes:
1. Change the search attempts limit from 100 to 200 (line 221)
2. Change the minimum distance check from `> 5` to `> 3` (line 229)

**Change 1 — search attempts (line 221):**
Search: `while len(spawns) < roaming_count and attempts < 100:`
Replace: `while len(spawns) < roaming_count and attempts < 200:`

**Change 2 — distance threshold (line 229):**
Search: `if min_dist > 5:  # At least 5 tiles from main path`
Replace: `if min_dist > 3:  # At least 3 tiles from main path`

**Validation:** `cd /home/danny/Code/DarkDelve && python -m pytest tests/test_floor1_generator.py -v` — all existing tests should still PASS.

---

### Task 3: Load Monster Templates from YAML

**File:** `src/application/services/floor1_spawner.py`
**Where:** After the hardcoded `MONSTER_TEMPLATES` dict (after line 52), before the `Floor1Spawner` class (line 55)

**What to do:** Add a `load_templates()` function that reads `config/floor1_monsters.yaml` and returns the template dict. Fall back to the hardcoded `MONSTER_TEMPLATES` if YAML loading fails. Then update `Floor1Spawner.__init__` to call `load_templates()` instead of using the hardcoded dict.

**Exact change — insert after line 52 (end of MONSTER_TEMPLATES dict):**

```python


def load_templates(config: dict = None) -> dict:
    """Load monster templates from YAML config, fall back to hardcoded defaults."""
    yaml_path = Path(__file__).parent.parent.parent / "config" / "floor1_monsters.yaml"
    try:
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        raw = data.get('floor1_monsters', {})
        templates = {}
        for key, val in raw.items():
            templates[key] = {
                'name': val['name'],
                'symbol': val['symbol'],
                'color': tuple(val['color']),
                'hp': int(val['hp']),
                'power': int(val['power']),
                'defense': int(val['defense']),
                'speed': int(val.get('speed', 60)),
            }
        return templates
    except Exception:
        return MONSTER_TEMPLATES
```

**Then update `Floor1Spawner.__init__` to use it:**
Search:
```python
class Floor1Spawner:
    """Spawns entities for floor 1."""
    
    def __init__(self, player: Entity, config: dict, dungeon_map: np.ndarray = None):
        self.player = player
        self.config = config
        self.dungeon_map = dungeon_map
        self.occupied_positions: Set[Tuple[int, int]] = set()
```

Replace:
```python
class Floor1Spawner:
    """Spawns entities for floor 1."""
    
    def __init__(self, player: Entity, config: dict, dungeon_map: np.ndarray = None):
        self.player = player
        self.config = config
        self.dungeon_map = dungeon_map
        self.occupied_positions: Set[Tuple[int, int]] = set()
        self.templates = load_templates(config)
```

**Then update all references from `MONSTER_TEMPLATES` to `self.templates` inside Floor1Spawner methods:**
- Line 144: `template = MONSTER_TEMPLATES[template_key]` → `template = self.templates[template_key]`
- Line 177: `template = MONSTER_TEMPLATES[template_key]` → `template = self.templates[template_key]`
- Line 192: `template = MONSTER_TEMPLATES[creature_type]` → `template = self.templates[creature_type]`

**Also add imports at the top of the file (after line 9):**
```python
from pathlib import Path
import yaml
```

**Validation:** `cd /home/danny/Code/DarkDelve && python -m pytest tests/test_floor1_generator.py -v` — all tests should PASS.

---

### Task 4: Add Floor1 Generation DM Playtest Scenario

**Files:** `playtest/dm_test_scenarios.py` and `playtest/dm_playtester.py`

#### 4a. Add scenario to `playtest/dm_test_scenarios.py`

**Where:** After the last scenario in `TEST_SCENARIOS` list (after `difficulty_scaling_test` at line 218), before the closing `]`

**What to do:** Add a new `DMTestScenario` with `test_type="floor1_generation"`:

```python
    DMTestScenario(
        name="floor1_generation_test",
        description="Initialize game, verify floor 1 has guards, sergeants, dens, no overlaps, no wall spawns, monsters weaker than player",
        test_type="floor1_generation",
        setup={},
        expected_outcomes={
            "guards_exist": True,
            "sergeants_exist": True,
            "dens_exist": True,
            "no_overlaps": True,
            "no_wall_spawns": True,
            "monsters_weaker": True,
        }
    ),
```

#### 4b. Add handler to `playtest/dm_playtester.py`

**Where:** In `run_scenario()` method, add a new `elif` branch before the `else` at line 118:

```python
            elif scenario.test_type == "floor1_generation":
                result = self.run_floor1_generation_test(scenario)
```

**Where:** Add the handler method before `run_behavior_generation_test`:

```python
    def run_floor1_generation_test(self, scenario: DMTestScenario) -> dict:
        """Run floor 1 generation test: verify entities, positions, and constraints."""
        try:
            from darkdelve import Game
            game = Game()
            game.initialize()
            
            entities = game.entities
            player = game.player
            
            # Check guards exist
            guards = [e for e in entities if e.name == 'Dungeon Guard']
            sergeants = [e for e in entities if e.name == 'Guard Sergeant']
            
            # Check dens exist (spider queens or rat kings = den leaders)
            den_leaders = [e for e in entities if e.name in ('Spider Queen', 'Rat King')]
            
            # Check no two blocking entities share a position
            blocking = [e for e in entities if e.blocks]
            positions = [(e.x, e.y) for e in blocking]
            no_overlaps = len(positions) == len(set(positions))
            
            # Check all entities on floor tiles
            no_wall_spawns = True
            for e in entities:
                if 0 <= e.x < game.dungeon_map.shape[0] and 0 <= e.y < game.dungeon_map.shape[1]:
                    if game.dungeon_map[e.x, e.y]:  # True = wall
                        no_wall_spawns = False
                        break
            
            # Check monsters weaker than player
            monsters_weaker = True
            for e in entities:
                if e is player:
                    continue
                if e.max_hp > player.max_hp + 5 or e.power > player.power:
                    monsters_weaker = False
                    break
            
            passed = (
                len(guards) > 0 and
                len(sergeants) > 0 and
                len(den_leaders) > 0 and
                no_overlaps and
                no_wall_spawns and
                monsters_weaker
            )
            
            return {
                "passed": passed,
                "guards_count": len(guards),
                "sergeants_count": len(sergeants),
                "den_leaders_count": len(den_leaders),
                "no_overlaps": no_overlaps,
                "no_wall_spawns": no_wall_spawns,
                "monsters_weaker": monsters_weaker,
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
```

**Validation:** `cd /home/danny/Code/DarkDelve && python -m pytest tests/test_dm_playtester.py -v` — all tests should PASS.

---

### Task 5: Create Floor1 Telemetry Test

**File:** `tests/test_floor1_telemetry.py` (NEW FILE)

**What to do:** Create a new test file with integration assertions about floor 1 state.

**Complete file content:**

```python
"""Integration tests for floor 1 telemetry state."""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch


class TestFloor1Telemetry:
    """Verify floor 1 game state meets expectations."""

    @pytest.fixture
    def game(self):
        """Create a game instance and generate floor 1."""
        from darkdelve import Game
        g = Game()
        g.initialize()
        return g

    def test_entity_count_in_range(self, game):
        """Floor 1 should have between 15 and 35 entities (player + monsters + items + corpses)."""
        assert 15 <= len(game.entities) <= 35, f"Expected 15-35 entities, got {len(game.entities)}"

    def test_at_least_two_guard_sergeants(self, game):
        """Floor 1 should have at least 2 guard sergeants."""
        sergeants = [e for e in game.entities if e.name == 'Guard Sergeant']
        assert len(sergeants) >= 2, f"Expected >=2 sergeants, got {len(sergeants)}"

    def test_at_least_one_den_leader(self, game):
        """Floor 1 should have at least 1 den leader (Spider Queen or Rat King)."""
        leaders = [e for e in game.entities if e.name in ('Spider Queen', 'Rat King')]
        assert len(leaders) >= 1, f"Expected >=1 den leader, got {len(leaders)}"

    def test_no_blocking_entity_overlaps(self, game):
        """No two blocking entities should share the same position."""
        blocking = [e for e in game.entities if e.blocks]
        positions = [(e.x, e.y) for e in blocking]
        assert len(positions) == len(set(positions)), "Overlapping blocking entities detected"

    def test_all_entities_on_floor_tiles(self, game):
        """All entities should be on floor tiles (not walls)."""
        for e in game.entities:
            if 0 <= e.x < game.dungeon_map.shape[0] and 0 <= e.y < game.dungeon_map.shape[1]:
                assert not game.dungeon_map[e.x, e.y], f"Entity {e.name} at ({e.x},{e.y}) is on a wall"

    def test_stairs_down_exists(self, game):
        """Stairs down should exist and be on a floor tile."""
        assert game.stair_down_pos is not None, "No stairs down found"
        sx, sy = game.stair_down_pos
        assert not game.dungeon_map[sx, sy], f"Stairs down at ({sx},{sy}) is on a wall"
```

**Validation:** `cd /home/danny/Code/DarkDelve && python -m pytest tests/test_floor1_telemetry.py -v` — all tests should PASS.

---

### Task 6: Test Floor 1 to Floor 2 Transition

**File:** `tests/test_floor1_generator.py`
**Where:** At the end of the file, after `TestMonsterTemplates` class

**What to do:** Add a new test class with a transition test:

```python
class TestFloor1ToFloor2Transition:
    
    def test_floor1_to_floor2_transition(self, config):
        """Verify descending from floor 1 to floor 2 works without crashes."""
        from darkdelve import Game
        
        game = Game()
        game.initialize()
        
        # Verify we are on floor 1
        assert game.state.depth == 1
        
        # Generate floor 2
        game.generate_level(2, "main")
        
        # Verify floor 2 has entities
        assert len(game.entities) > 0, "Floor 2 should have entities"
        
        # Verify floor 2 has a valid map
        assert game.dungeon_map is not None, "Floor 2 should have a dungeon map"
        assert game.dungeon_map.shape[0] > 0, "Floor 2 map should have width"
        assert game.dungeon_map.shape[1] > 0, "Floor 2 map should have height"
        
        # Verify depth updated
        assert game.state.depth == 2, "State depth should be 2 after transition"
        
        # Verify player still exists and is alive
        assert game.player is not None, "Player should exist on floor 2"
        assert game.player.is_alive, "Player should be alive on floor 2"
```

**Validation:** `cd /home/danny/Code/DarkDelve && python -m pytest tests/test_floor1_generator.py::TestFloor1ToFloor2Transition -v` — should PASS.

---

## Execution Order & Dependencies

1. **Task 1** — Critical, unblocks monster movement
2. **Task 2** — Quick fix, independent
3. **Task 3** — Independent (but tests reference `MONSTER_TEMPLATES`, keep it importable)
4. **Task 4** — Independent
5. **Task 5** — Independent
6. **Task 6** — Independent

## Full Test Suite Validation

After ALL tasks pass individually, run the full validation:

```bash
cd /home/danny/Code/DarkDelve && python -m pytest tests/test_floor1_generator.py tests/test_floor1_telemetry.py tests/test_dm_playtester.py tests/test_manual_playtest.py -v
```

All tests should pass. If `test_05_speed_comparison` fails intermittently, it is a known flaky test unrelated to these changes — re-run it to confirm.

## Files Modified Summary

| File | Tasks | Type |
|---|---|---|
| `darkdelve.py` | Task 1 | Edit |
| `src/application/services/floor1_generator.py` | Task 2 | Edit |
| `src/application/services/floor1_spawner.py` | Task 3 | Edit |
| `playtest/dm_test_scenarios.py` | Task 4 | Edit |
| `playtest/dm_playtester.py` | Task 4 | Edit |
| `tests/test_floor1_telemetry.py` | Task 5 | New file |
| `tests/test_floor1_generator.py` | Task 6 | Edit |
