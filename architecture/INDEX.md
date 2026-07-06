# Architecture Documentation Index

> Routing table for the Orchestrator. When a task matches a keyword, read the
> listed file(s) before routing to the Architect or Coder.

## Usage

1. Receive task description from user
2. Match keywords against the tables below
3. Read the listed file(s) to gather context
4. Route to Architect with the context injected

---

## Routing by Task Type

### Core Game Systems

| Keywords | File(s) | Purpose |
|----------|---------|---------|
| game loop, main loop, turn processing | `ATTENTION.md`, `system_overview.md` | Locate game loop, energy system, turn order |
| dungeon, map, tile, room, corridor | `map_system.md`, `ATTENTION.md`, `gotchas.md` | Map generation, rendering, coordinate system |
| fov, visibility, perception, sight | `ATTENTION.md`, `entity_ai_system.md`, `gotchas.md` | FOV computation, perception modifiers |
| combat, attack, damage, ac, to-hit | `ATTENTION.md`, `gotchas.md`, `dungeon_item_systems.md` | Combat resolution, damage model |
| energy, speed, turn order, tick | `ATTENTION.md`, `gotchas.md` | Energy system, monster speed scaling |
| inventory, item, equip, pickup | `ATTENTION.md`, `gotchas.md`, `dungeon_item_systems.md` | Item system, inventory management |
| entity, mob, monster, player, npc | `ATTENTION.md`, `module_design.md` | Entity types, component system |

### AI & Agent Systems

| Keywords | File(s) | Purpose |
|----------|---------|---------|
| agent, ai, behavior, decision, llm agent | `agent_system.md`, `entity_ai_system.md`, `ATTENTION.md` | Agent base classes, LLM integration |
| behavior tree, behavior script, behavior engine | `entity_ai_system.md`, `dungeon_item_systems.md` | Behavior tree execution, script format |
| perception status, perception modifiers | `entity_ai_system.md` (canonical) | Perception data structures |
| social, loyalty, relationship, faction | `entity_ai_system.md` (canonical) | Social structures and loyalty mechanics |
| power level, skill, stat | `entity_ai_system.md`, `stat_system_overhaul_proposal.md` | Power/skill/stat systems |
| commander, dungeon master, dm agent | `agent_system.md`, `ENTITY_AI_IMPLEMENTATION.md` | Commander and DM agent implementations |
| action dispatcher, flee, patrol | `agent_system.md`, `ENTITY_AI_IMPLEMENTATION.md` | Action handlers and dispatch |

### Playtesting & Automation

| Keywords | File(s) | Purpose |
|----------|---------|---------|
| playtest, ollama playtester, telemetry | `playtest_problem_exploration_plan.md`, `api_interfaces.md`, `README.md` | Playtest harness, telemetry format |
| player agent, prompt builder, validation | `api_interfaces.md`, `gotchas.md` | Player AI prompt/response contract |
| instruction bus, operator instruction | `playtest_problem_exploration_plan.md` | Instruction injection system |
| console, renderer, display, frame | `gotchas.md`, `map_system.md` | Console/graphical rendering |
| quit, exit, save, death, victory | `playtest_problem_exploration_plan.md`, `gotchas.md` | Game exit and persistence paths |

### Architecture & Refactoring

| Keywords | File(s) | Purpose |
|----------|---------|---------|
| solid, layer, module, refactoring | `system_overview.md`, `module_design.md`, `solid_design.md` | SOLID architecture, layer responsibilities |
| implementation, migrate, phase | `implementation_plan.md`, `implementation_guide.md` | Step-by-step refactoring plans |
| interface, contract, api | `api_interfaces.md`, `module_design.md` | Module interfaces and integration points |
| gotcha, bug, pitfall, known issue | `gotchas.md` | Historical bugs and prevention |

### Proposals (DO NOT IMPLEMENT WITHOUT SIGN-OFF)

| Keywords | File(s) | Purpose |
|----------|---------|---------|
| stat overhaul, stat container, base stats | `plans/proposals/stat_system_overhaul_proposal.md` | Proposed unified stat system (GATED) |

> **Note:** `stat_system_overhaul_proposal.md` was moved from `architecture/` to
> `plans/proposals/` to prevent accidental implementation. The architecture/
> directory now only contains active design docs and cross-cutting references. |

---

## File Inventory

| File | Lines | Last Updated | Status |
|------|-------|--------------|--------|
| `ATTENTION.md` | ~130 | 2026-06-25 | Active |
| `README.md` | ~60 | 2026-06-25 | Active |
| `system_overview.md` | ~170 | 2026-06-25 | Needs update: stale phase markers |
| `module_design.md` | ~350 | 2026-06-25 | Active |
| `implementation_plan.md` | ~475 | 2026-06-25 | Active |
| `implementation_guide.md` | ~310 | 2026-06-27 | Deprecated — see module_design.md |
| `api_interfaces.md` | ~130 | 2026-06-25 | Active |
| `gotchas.md` | ~630 | 2026-06-25 | Active |
| `solid_design.md` | ~740 | 2026-06-25 | Active |
| `map_system.md` | ~170 | 2026-06-25 | Active |
| `agent_system.md` | ~220 | 2026-06-25 | Active |
| `entity_ai_system.md` | ~510 | 2026-06-25 | Active |
| `dungeon_item_systems.md` | ~710 | 2026-06-25 | Active |
| `ENTITY_AI_IMPLEMENTATION.md` | ~290 | 2026-06-25 | Active |
| `playtest_problem_exploration_plan.md` | ~230 | 2026-06-25 | Active |
| `event_bus_routing.md` | ~100 | 2026-06-27 | New — cross-cutting event flow |
| `playtest_integration.md` | ~140 | 2026-06-27 | New — playtest ↔ core integration |
| `mcp_integration_architecture.md` | ~120 | 2026-06-27 | New — MCP tool set architecture |
| `src/infrastructure/repositories/content_repository.py` | ~137 | 2026-06-30 | New — ContentRepository for seed-based content generation |
| `src/application/services/content_seeder.py` | ~137 | 2026-06-30 | New — ContentSeeder for building seed-aware prompts |
| `src/domain/services/content_generation_service.py` | ~137 | 2026-06-30 | New — ContentGenerationService for orchestrating content generation |
| `tests/test_content_repository.py` | ~91 | 2026-06-30 | New — Tests for ContentRepository |
| `tests/test_content_seeder.py` | ~91 | 2026-06-30 | New — Tests for ContentSeeder |
| `tests/test_content_generation_service.py` | ~91 | 2026-06-30 | New — Tests for ContentGenerationService |

---

## Deduplication Map

The following data structures are defined in multiple files. When referencing
them, prefer the **canonical** source to avoid contradictions.

| Structure | Canonical Source | Also In |
|-----------|-----------------|---------|
| `PerceptionStatus` | `entity_ai_system.md` | `dungeon_item_systems.md` |
| `PerceptionModifiers` | `entity_ai_system.md` | `dungeon_item_systems.md` |
| `BehaviorScript` | `entity_ai_system.md` | `dungeon_item_systems.md` |
| `BehaviorNode` | `entity_ai_system.md` | `dungeon_item_systems.md` |
| `SocialRelationship` | `entity_ai_system.md` | `dungeon_item_systems.md` |
| `SocialStructure` | `entity_ai_system.md` | `dungeon_item_systems.md` |
| `LoyaltyState` | `entity_ai_system.md` | `dungeon_item_systems.md` |
| `PowerLevels` | `entity_ai_system.md` | `dungeon_item_systems.md` |
| `PlayerProfile` | `entity_ai_system.md` | `dungeon_item_systems.md` |
| `LLMCallLog` | `entity_ai_system.md` | `dungeon_item_systems.md` |
| `DifficultyMode` | `dungeon_item_systems.md` | `ENTITY_AI_IMPLEMENTATION.md` |
| `ItemStats` | `dungeon_item_systems.md` | `entity_ai_system.md` (partial) |
| `DamageCalculator` | `dungeon_item_systems.md` | `entity_ai_system.md` (reference only) |

---

## Cross-Cutting Concerns

For tasks spanning multiple systems, read these files in order:

1. **Any task** → `ATTENTION.md` (locate code) + `gotchas.md` (avoid pitfalls)
2. **Multi-layer task** → `system_overview.md` (understand layers) + `module_design.md` (module details)
3. **AI task** → `agent_system.md` (agent framework) + `entity_ai_system.md` (AI specifics)
4. **Playtest task** → `playtest_problem_exploration_plan.md` + `api_interfaces.md`
5. **Refactoring task** → `implementation_plan.md` + `solid_design.md`
| `src/domain/value_objects/damage_caps.py` | ~60 | 2026-06-30 | New — Damage cap/floor formulas for balance clamping |
| `src/presentation/item_emoji.py` | ~60 | 2026-06-30 | New — Item emoji lookup table |
| `src/presentation/monster_emoji.py` | ~80 | 2026-06-30 | New — Monster emoji lookup table |
| `tests/test_damage_caps.py` | ~100 | 2026-06-30 | New — Tests for damage cap/floor formulas |
| `tests/test_item_emoji.py` | ~50 | 2026-06-30 | New — Tests for item emoji lookup |
| `tests/test_monster_emoji.py` | ~50 | 2026-06-30 | New — Tests for monster emoji lookup |
| `tests/test_inventory_description_panel.py` | ~80 | 2026-06-30 | New — Tests for inventory description panel |
| `playtest/test_inventory_use_key_mcp.py` | ~200 | 2026-07-04 | New — MCP playtest for inventory U key functionality |
| `tests/test_inventory_use_drop_fix.py` | ~80 | 2026-07-05 | New — Tests for inventory use/drop key fix |
