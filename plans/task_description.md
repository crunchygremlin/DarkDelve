# Task Description: DarkDelve DM Improvement (SYSTEM)

## Complexity: SYSTEM
Core DM engine, LLM worker, config, behavior library, memory, cache-miss tracker,
playtester interface. Pipeline: Orchestrator -> Architect -> Orchestrator -> Coder
-> Orchestrator -> Play Tester -> Orchestrator.

## Primary Goal
Evolve the local-LLM Dungeon Master into one cohesive, context-aware, efficiently
throttled "single mind" with shared poetic memory, swarm behavior templates, one
model config, prompt truncation with logging, a cache-miss tracker, and an MCP-driven
playtester. Full design in plans/dm_improvements_plan.md.

## Scope (8 items)
1. One DM mind: fold LLMWorker.evaluate_player_stats difficulty logic into
   DungeonMasterAgent.
2. Global throttled poetic DM memory bounded by LLMLogger.check_headroom; refreshed at
   level boundaries; NOT per-monster.
3. Swarm/formation behavior TEMPLATES by intelligence tier + leader barked commands via
   event bus; AI controls templates not per-monster micro.
4. Single model config qwen2.5-coder:7b-instruct from game.yaml; remove hardcoded
   "gpt-oss".
5. Truncation (default 8k) + truncation logging on all DM prompts.
6. BehaviorLibrary: LLM selects/authors entries; fallback so monsters never freeze.
7. Cache-miss tracker (>=75% prompt similarity) emitting telemetry, BEFORE caching.
8. Playtester drives via mcp_toolkit.py, not a second Ollama instance.

## Constraints
- All 86+ existing tests must remain green.
- New tests required for: memory throttle, truncation logging, cache-miss tracker,
  library fallback, MCP playtester.
- Do NOT implement — Architect produces design only, then returns to Orchestrator.

## Key Files (read before designing)
- plans/dm_improvements_plan.md
- src/domain/agents/dungeon_master_agent.py
- src/application/services/llm_worker.py
- src/domain/services/llm_map_generator.py
- src/domain/services/behavior_script_service.py
- src/domain/services/plan_generator.py
- src/domain/value_objects/llm_logging.py
- src/domain/components/behavior_component.py
- src/domain/services/entity_ai_orchestrator.py
- config/game.yaml
- src/infrastructure/services/mcp_toolkit.py
- ollama_playtester.py, player_agent.py
- architecture/agent_system.md, system_overview.md, gotchas.md
