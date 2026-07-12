# DarkDelve DM Improvement Plan (Consolidated)

## Complexity: SYSTEM
Touches the DM agent, LLM worker, config, behavior library, memory, cache-miss
tracker, and the playtester interface. Requires Architect -> Coder -> Play Tester.

## Goal
Evolve the local-LLM Dungeon Master from a stateless per-call script generator into
a cohesive, context-aware, efficiently-throttled "single mind": one shared poetic
memory, behavior templates for swarms, one model config, prompt truncation with
logging, a cache-miss tracker, and an MCP-driven (not LLM-driven) playtester.

## Item 1 - One DM Mind
Fold LLMWorker.evaluate_player_stats difficulty logic into DungeonMasterAgent.
Single agent owns: behavior, level design, map generation, content, difficulty, memory.
Files: dungeon_master_agent.py, llm_worker.py

## Item 2 - Global Throttled DM Memory
One global DM memory store (NOT per-monster) holding a condensed poetic-prose summary
of dungeon state. Size-bounded to available context headroom via check_headroom.
Updated at level boundaries / major events. Fed into every DM prompt.
Call frequency note: LLM fires only when current_script is None (scripts persist as
multi-step plans). Per level ~= 1 design_level + 1 map_generation + occasional content
batches + monster behavior calls only when plans exhaust. Capped at 5 calls/turn.
Files: dungeon_master_agent.py, llm_logging.py, behavior_component.py

## Item 3 - Swarm / Formation Behaviors + Leader Commands
Behavior TEMPLATES ("surround player", "flee to pack", "flee to stronger mob") selected
by monster intelligence tier. Leader mobs (high intelligence) bark commands to
subordinates via event bus / social service. AI controls templates, not per-monster micro.
Files: plan_generator.py (catalog), behavior_script_service.py, social service, event_bus

## Item 4 - Single Model Config
qwen2.5-coder:7b-instruct everywhere. model + temperature loaded from game.yaml (one
source). Remove hardcoded "gpt-oss" default.
Files: dungeon_master_agent.py, game.yaml, llm_worker.py

## Item 5 - Truncation + Truncation Logging
Apply configurable (default 8k) prompt truncation to ALL DM prompt builds (behavior,
level, map, content, difficulty, memory). Log truncated bytes / dropped sections to
LLMLogger so context size can be tuned vs player fun.
Files: dungeon_master_agent.py, llm_logging.py

## Item 6 - Behavior Library + Fallback
DM maintains a BehaviorLibrary (catalog of reusable scripts). LLM picks from library by
default; creates new entries as needed; library persisted (content repository / live
config). On LLM failure, fallback = basic behavior from library (monsters never freeze).
Files: plan_generator.py, dungeon_master_agent.py, content_repository.py

## Item 7 - Cache-Miss Tracker (prerequisite to caching)
Before any caching, add a tracker comparing current prompt to previous prompt; if
>=75% similar, flag cache hit/miss; emit metric to telemetry. Informs later caching.
Files: llm_logging.py, llm_worker.py

## Item 8 - Playtester Uses MCP, Not Local LLM
Refactor ollama_playtester.py / player_agent.py so the automated player drives the game
through the SAME MCP toolkit interface the DM uses, not a second Ollama instance.
Files: ollama_playtester.py, player_agent.py, mcp_toolkit.py

## Files Likely Touched
- src/domain/agents/dungeon_master_agent.py
- src/application/services/llm_worker.py
- src/domain/services/llm_map_generator.py
- src/domain/services/behavior_script_service.py
- src/domain/services/plan_generator.py
- src/domain/value_objects/llm_logging.py
- src/domain/components/behavior_component.py
- config/game.yaml
- src/infrastructure/services/mcp_toolkit.py
- ollama_playtester.py, player_agent.py
- architecture/agent_system.md, system_overview.md, gotchas.md

## Acceptance
All existing 86+ tests pass. New tests for: memory throttle, truncation logging,
cache-miss tracker, behavior library fallback, MCP playtester.
