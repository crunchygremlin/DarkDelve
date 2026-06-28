# T-2026-0628-001: Wire DM LLM into Live Game with Observability

## Goal
Connect the existing DungeonMasterAgent and LevelDesignService to the live game loop (`darkdelve.py`) so the LLM actively participates in gameplay, and build a comprehensive observability system that logs every LLM interaction.

## Background
The DM LLM infrastructure exists but is completely disconnected from the live game:
- `DungeonMasterAgent` (`src/domain/agents/dungeon_master_agent.py`) — can generate behavior scripts and design levels via LLM
- `LevelDesignService` (`src/domain/services/level_design_service.py`) — can generate level layouts and item seeding
- `BehaviorScriptService` (`src/domain/services/behavior_script_service.py`) — can evaluate behavior trees
- `LLMLogger` (`src/domain/value_objects/llm_logging.py`) — already has logging infrastructure
- `PlayerAgent` (`player_agent.py`) — already wired in via MCP playtester

**None of these are imported or called from `darkdelve.py`.** The live game uses hardcoded Python logic for monster AI (flee thresholds, basic pathfinding) and procedural generation for levels.

## Requirements

### Part 1: Wire DM Agent into Live Game Loop

**Files to modify:** `darkdelve.py`

1. **Initialize DM Agent on game start** — In `Game.initialize()` or `Game.__init__()`, instantiate:
   - `DungeonMasterAgent` with a configured Ollama service
   - The agent should use the same Ollama endpoint configured in `config/game.yaml`

2. **Behavior script generation on entity spawn** — When entities are spawned (in `generate_level()` or `spawn_entities()`), call `dm_agent.generate_behavior_script()` for each non-player entity. Pass:
   - `entity_id` = entity's unique ID
   - `mob_type` = entity name or type
   - `perception` = current PerceptionStatus for that entity
   - `social_context` = empty string for now
   - `valid_conditions` and `valid_actions` from MOB_BEHAVIOR_CATALOG

3. **Behavior script evaluation in entity update** — In the entity update/AI loop (where `entity.update()` or similar is called), evaluate the entity's behavior script using `BehaviorScriptService.evaluate_script()`. Use the returned action to drive entity behavior instead of hardcoded flee logic.

4. **Level design on level generation** — When `generate_level()` is called for depth > 1, use `LevelDesignService.generate_level_layout()` to augment or override the procedural generation. Fall back to procedural if LLM is unavailable.

### Part 2: LLM Observability Log

**New file:** `logs/llm_activity.json` (append-only JSONL)

For every LLM call, log:
```json
{
  "timestamp": "ISO-8601",
  "turn_number": int,
  "call_type": "behavior_generation" | "level_design",
  "entity_id": str or null,
  "level_number": int or null,
  "prompt_summary": str (first 200 chars),
  "response_summary": str (first 200 chars),
  "latency_ms": float,
  "tokens_used": int,
  "success": bool,
  "error": str or null,
  "model": str
}
```

**Also add to UI:** In `render_ui()`, display a recent LLM activity feed (last 3-5 calls) showing:
- Turn #, call type, latency, success/failure
- This helps the player understand what the DM is doing

### Part 3: Configuration

**File:** `config/game.yaml`

Add section:
```yaml
dungeon_master:
  enabled: true
  model: "gpt-oss"
  temperature: 0.7
  ollama_endpoint: "http://localhost:11434"
  log_path: "logs/llm_activity.json"
  # Throttle: max LLM calls per turn to avoid lag
  max_calls_per_turn: 5
  # Which features to enable
  enable_behavior_generation: true
  enable_level_design: false  # Start with behavior only
```

## Constraints
- LLM calls must not block the game loop — use async or threading with a timeout
- If LLM is unavailable, fall back to existing hardcoded behavior (zero regression)
- Respect `max_calls_per_turn` to prevent lag spirals
- All LLM activity must be logged to `logs/llm_activity.json`
- Changes must not break existing tests (929 currently pass)

## Success Criteria
1. Game runs with DM agent active, generating behavior scripts for spawned entities
2. Entity AI uses LLM-generated behavior trees when available
3. `logs/llm_activity.json` captures every LLM call with full metadata
4. UI shows recent DM activity
5. All 929 existing tests still pass
6. Fallback to hardcoded behavior works when LLM is down
