# AI Roguelike Architecture Review

## Executive Summary

**Status**: ⚠️ **INCOMPLETE - Critical Issues Found**

This project implements a hybrid roguelike where a local LLM (Ollama 3B) provides high-level tactical decisions for enemy commanders while the deterministic game engine handles all mechanics (pathfinding, combat, rendering, map generation). The architecture is sound but the implementation has critical blockers that prevent execution.

---

## Architecture Overview

### Design Pattern
**Layered Architecture with Async LLM Integration**

```
┌─────────────────────────────────────────────────┐
│          Main Game Loop (Tcod Console)          │
│   - Rendering, input handling, turn sequence    │
├─────────────────────────────────────────────────┤
│       Commander AI Layer (LLM Integration)      │
│   - Entity state → prompt → LLM request queue   │
│   - LLM response queue → command interpretation │
├─────────────────────────────────────────────────┤
│     Deterministic Engine Layer (Core Logic)     │
│   - A* pathfinding, collision detection         │
│   - Combat calculation, entity state management │
│   - Dungeon generation (BSP + room tunneling)   │
├─────────────────────────────────────────────────┤
│    Background LLM Worker (Async Threading)      │
│   - Non-blocking Ollama HTTP client             │
│   - Request/response queue decoupling           │
│   - Fallback behavior on timeout/error          │
└─────────────────────────────────────────────────┘
```

### Threading Model
- **Main thread**: Game loop (rendering, input, turn management)
- **Background daemon thread**: LLM HTTP client (non-blocking)
- **Queue-based communication**: Prevents game stalls from slow LLM responses

### Data Flow
1. **Commander Turn**: LLM worker dequeues prompt, sends to Ollama
2. **LLM Response**: Ollama returns tactical command (validated)
3. **Action Interpretation**: Command + board state → target position
4. **Pathfinding**: Engine computes A* path to target (NOT LLM)
5. **Movement/Combat**: Deterministic engine executes action

---

## Core Components

### 1. **Entity System** ⚠️ BROKEN
**File**: `main.py` (lines ~220-280)

**Issue**: Class declaration is missing. Methods exist but are orphaned (no `class Entity:` line).

**Required Attributes**:
```python
- x, y: Position
- char, color: Rendering
- name: Identifier
- hp, max_hp, power, defense: Combat stats
- blocks: Collision flag
- intel_tier, training: AI metadata
- is_commander: NPC type flag
- current_command: Current LLM command (dict or None)
- pending_command: Awaiting LLM response (bool)
- home_position: Commander spawn point (tuple)
```

**Required Methods**:
- `__init__()`: Initialization
- `is_alive` (property): `hp > 0`
- `move_to()`: Atomic position update
- `move_towards()`: Single step toward target

---

### 2. **LLM Integration** ✅ MOSTLY WORKING
**File**: `main.py` (lines 1-100)

**Components**:
- `local_llm_worker()`: Background daemon thread
- `start_llm_worker()`: Thread initialization
- `llm_request_queue`, `llm_response_queue`: Async communication
- `llm_metrics`: Global request/response tracking

**Strengths**:
- ✅ Async design (game loop never blocks)
- ✅ Streaming NDJSON parsing for Ollama compatibility
- ✅ Timeout handling (10s default)
- ✅ Command validation (4 allowed commands enforced)

**Issues**:
- ❌ `get_llm_metrics()` function not implemented (called in UI rendering)

---

### 3. **Command Interpretation** ❌ MISSING
**Function**: `interpret_commander_action()` (undefined)

**Purpose**: Convert LLM high-level command → (action, target_position)

**Expected Signature**:
```python
def interpret_commander_action(
    commander: Entity,
    player: Entity,
    dungeon_map: np.ndarray,
    entities: List[Entity]
) -> Tuple[str, Optional[Tuple[int, int]]]:
    """
    Interpret a commander's LLM decision into an engine action and target.
    
    Returns:
        (action, target_position)
        where action ∈ {"WAIT", "ATTACK", "RETREAT", "DEFEND"}
        and target_position is (x, y) or None for WAIT
    """
```

**Mapping**:
- `ATTACK_PLAYER` → `("ATTACK", player_position)`
- `HOLD_POSITION` → `("WAIT", None)`
- `RETREAT_TO_ROOM` → `("RETREAT", home_position)`
- `DEFEND_COMMANDER` → `("DEFEND", home_position)`

---

### 4. **Pathfinding** ✅ WORKING
**File**: `main.py` (lines 134-162)

**Algorithm**: A* with 8-directional movement

**Features**:
- ✅ Collision-aware (respects `entity.blocks`)
- ✅ Goal-biased heuristic (Manhattan distance)
- ✅ Returns full path including start position
- ✅ Empty path on unreachable goal

---

### 5. **Dungeon Generation** ✅ WORKING
**File**: `main.py` (lines 287-352)

**Algorithm**: Binary Space Partitioning (BSP) + random rooms

**Features**:
- ✅ Room-based generation (prevents long corridors)
- ✅ Tunnel connections between adjacent rooms
- ✅ Random entity spawning per room
- ✅ Special first-room setup (commander + zombies)

**Entities Spawned**:
- Room 0: Player (30 HP, 5 ATK, 2 DEF)
- Room 1: Goblin Warlord commander (25 HP) + 8 Zombies
- Rooms 2+: Random Orcs (8 HP) or Trolls (16 HP)

---

### 6. **Game Loop & Rendering** ✅ MOSTLY WORKING
**File**: `main.py` (lines 354-500)

**Structure**:
1. Compute player FOV (tcod built-in)
2. Render dungeon + explored areas
3. Render living entities in FOV
4. Render UI (HP bar, message log, LLM metrics)
5. Handle player input (arrow keys, Esc to quit)
6. Process monster turns (if player acted)
7. Handle combat + pathfinding

**Issues**:
- ❌ `get_llm_metrics()` call will crash (undefined function)
- ⚠️ Prompt template incomplete (only `{visible_entities}` placeholder)

---

### 7. **Prompt Template** ❌ INCOMPLETE
**File**: `prompt/commander_prompt.txt`

**Current State**: `JSONONLY {visible_entities}` (useless)

**Should Be**: Full LLM-readable prompt with context

**Recommended Template**:
```
You are a goblin commander in a dungeon battle. Analyze the situation and respond with a JSON object.

**Your Status:**
- Position: {commander_position}
- HP: {hp} / {max_hp}
- Training: {training}

**Player Location:** {player_position} (HP: {player_hp[0]}/{player_hp[1]})

**Visible Allies & Enemies:**
{visible_entities}

**Your Tactical Options:**
1. ATTACK_PLAYER - Move aggressively toward the player to strike
2. HOLD_POSITION - Stay put and defend your ground
3. RETREAT_TO_ROOM - Fall back to your home position
4. DEFEND_COMMANDER - Hold the center position

**Response Format (JSON only):**
{
  "commander_shout": "Your battle cry here",
  "command": "ATTACK_PLAYER|HOLD_POSITION|RETREAT_TO_ROOM|DEFEND_COMMANDER"
}

Respond with ONLY valid JSON. No explanations.
```

---

## Critical Issues & Fixes Required

### ❌ Issue #1: Entity Class Malformed
**Severity**: 🔴 BLOCKER
**Lines**: ~220-280
**Fix**: Wrap methods in proper `class Entity:` declaration with proper indentation

### ❌ Issue #2: Missing `interpret_commander_action()`
**Severity**: 🔴 BLOCKER
**Called**: Line 446
**Fix**: Implement function to map LLM commands → (action, target)

### ❌ Issue #3: Missing `get_llm_metrics()`
**Severity**: 🔴 BLOCKER
**Called**: Line 389
**Fix**: Return dict with `{"requests": int, "responses": int, "avg_latency_ms": float}`

### ❌ Issue #4: Incomplete Prompt Template
**Severity**: 🟡 HIGH
**File**: `prompt/commander_prompt.txt`
**Fix**: Replace placeholder with tactical context for LLM

### ⚠️ Issue #5: Missing Entity Attributes
**Severity**: 🟡 HIGH
**Missing**: `home_position`, `current_command`, `pending_command`, `max_hp`
**Fix**: Add to `__init__()` with sensible defaults

### ⚠️ Issue #6: Test Suite Non-Functional
**Severity**: 🟡 HIGH
**Reason**: Entity class + missing functions not importable
**Impact**: All 9 tests fail immediately on import

---

## Dependency Analysis

### Required Packages
```
tcod          - Terminal rendering (libtcod wrapper)
numpy         - Map arrays + FOV computation  
pytest        - Unit testing (not needed at runtime)
```

### External Services
- **Ollama API**: Local LLM service (localhost:11434)
- **Default Model**: `llama3.2:3b` (configurable via `LOCAL_LLM_MODEL`)

### Environment Variables
- `LOCAL_LLM_ENDPOINT` (default: `http://127.0.0.1:11434/api/generate`)
- `LOCAL_LLM_MODEL` (default: `llama3.2:3b`)
- `LLM_TIMEOUT_SECONDS` (default: `10`)

---

## Deployment Architecture

### Docker Setup (Incomplete)
- **Dockerfile**: Provided but references non-existent base image
- **docker-compose.yml**: Defines app + ollama services
- **Status**: Not tested; requires valid Python base + Ollama image

### Local Development
- `scripts/dev_run.sh`: Run game locally
- `scripts/dev_docker_run.sh`: Run in Docker
- `Makefile`: Build/test targets

---

## Performance Characteristics

### Latency Budget (per turn)
- **Game loop iteration**: ~16ms (60 FPS target)
- **LLM request enqueue**: <1ms
- **LLM response processing**: <5ms
- **Pathfinding (A*)**: ~10-50ms (depends on distance)
- **Rendering**: ~5-10ms

### Async Benefit
- LLM requests (10s timeout) do NOT block game loop
- Game continues with stale or fallback commands
- Metrics tracked in background without UI lag

---

## Code Quality Issues

### Architectural Strengths ✅
1. Clean separation: Engine logic ≠ AI decisions
2. Async design prevents LLM from stalling gameplay
3. Comprehensive validation (command whitelist)
4. Good use of Python type hints
5. Reasonable logging for debugging

### Architectural Gaps ❌
1. **No configuration system**: Hardcoded parameters (map size, HP, etc.)
2. **No entity factory**: Entity creation duplicated in dungeon generation
3. **No event system**: Turn sequence is implicit in main loop
4. **No abstraction for AI**: Only commanders; monsters use hardcoded behavior
5. **No save/load**: Game state not serializable
6. **Limited metrics**: Only LLM latency tracked; no gameplay metrics

---

## Recommended Improvements (Post-MVP)

### Short Term (1-2 days)
1. ✅ Fix Entity class + missing functions
2. ✅ Improve prompt template with tactical context
3. ✅ Add metrics dashboard (requests/responses/latency)
4. Improve error handling (graceful degradation on Ollama failure)
5. Add debug mode (log all LLM exchanges)

### Medium Term (1-2 weeks)
1. Refactor: Separate `Entity` from rendering (Entity base + Renderer)
2. Add configuration YAML (difficulty levels, entity stats, map generation)
3. Implement save/load (pickle or JSON serialization)
4. Add more commander types (different intel tiers, training effects)
5. Expand test coverage (integration tests for LLM loop)

### Long Term (1+ months)
1. Add UI improvements (sidebar with metrics, command history)
2. Implement persistent LLM cache (replay past decisions)
3. Add procedural difficulty scaling
4. Multi-level dungeons with progression
5. Web frontend (WebSocket for remote LLM, browser rendering)

---

## Conclusion

The architecture is **sound and innovative** (async LLM + deterministic engine). The implementation is **incomplete**: critical classes and functions are missing, preventing execution. 

**Time to Fix**: ~1-2 hours (fix Entity class + 3 missing functions + prompt template)
**Time to MVP**: ~4-6 hours (fixes + testing + Docker)
**Time to Production**: ~2-4 weeks (full refactoring + comprehensive testing)

**Next Steps**: Implement fixes in priority order (blockers first).
