# Game Systems Cheat Sheet

Quick reference for all major game systems. Update this when systems change.

---

## Core Architecture

| System | Location | Key Class/Function | Purpose |
|--------|----------|-------------------|---------|
| Game Loop | `darkdelve.py:2112` | `Game.main_loop()` | Drives the entire game; processes player + monster turns |
| Energy/Turn Scheduler | `darkdelve.py:829` | `EnergySystem` | Determines who acts and when |
| Entity System | `darkdelve.py:637` | `Entity` | Base class for all game objects (player, mobs, items) |
| Map/Dungeon | `darkdelve.py` | `dungeon_map` (np.ndarray) | 2D grid; `True`=wall, `False`=floor |
| FOV | `darkdelve.py:993` | `FOVSystem` | Computes visible tiles from player position |
| Content Generation | `darkdelve.py:1029` | `ContentGenerator` | LLM-powered theme/monster/item generation |

## Combat

| Component | Location | Purpose |
|-----------|----------|---------|
| Combat Resolver | `darkdelve.py:756` | `CombatResolver.resolve_attack()` | d20-based attack resolution |
| Combat Event | `darkdelve.py` | `CombatEvent` | Result object for attacks |
| Hit Results | `darkdelve.py` | `HitResult` enum | HIT, MISS, CRITICAL, CRITICAL_FAIL |
| Combat Log | `darkdelve.py` | `CombatLog` | Records all combat events |

### Combat Formula
```
to_hit = d20 + power//2 + dex_mod + to_hit_bonus
damage = weapon_dice + power//2 + damage_bonus
AC = 10 + defense + equipment_bonus
Range: melee only (distance ≤ 1)
```

## Movement

| Function | Location | Behavior |
|----------|----------|----------|
| `Entity.move_to()` | `darkdelve.py:703` | Absolute position move with collision check |
| `Entity.move()` | `darkdelve.py:713` | Delta move (legacy) |
| `Entity.move_towards()` | `darkdelve.py:731` | One step toward target (Chebyshev) |
| `Entity.can_move_to()` | collision check | Bounds + wall + blocker check |

## Agent AI System

| Component | Location | Purpose |
|-----------|----------|---------|
| Agent Base | `src/domain/agents/base.py` | `Agent`, `PerceptionResult` |
| RandomAgent | `src/domain/agents/llm_agent.py:258` | `RandomAgent` — default monster AI |
| LLMAgent | `src/domain/agents/llm_agent.py:41` | LLM-powered decisions (optional) |
| CommanderAgent | `src/domain/agents/commander_agent.py:38` | Boss AI with tactical orders |
| Agent Manager | `src/domain/agents/commander_agent.py:160` | `AgentManager` — tracks all agents |
| Turn Processor | `src/domain/agents/integration.py:36` | `AgentTurnProcessor` — executes agent actions |
| Actions | `src/domain/agents/actions.py` | `AgentAction`, `ActionType`, `ActionResult` |
| State | `src/domain/agents/state.py` | `AgentGameState`, `EntityState`, `ItemState` |

### Agent Decision Flow
```
AgentGameState → agent.perceive() → PerceptionResult → agent.decide() → AgentAction → processor.execute()
```

### Action Types
| Type | Effect |
|------|--------|
| `MOVE_NORTH/SOUTH/EAST/WEST` | Delta movement |
| `MOVE_TO` | Path toward target position |
| `ATTACK` | Melee attack on target at new position |
| `ATTACK_TARGET` | Attack specific entity by ID |
| `PICKUP` | Pick up item at feet |
| `WAIT` | Do nothing |
| `HOLD_POSITION` | Commander order |

## Perception

| Component | Location | Purpose |
|-----------|----------|---------|
| Perception Service | `src/domain/services/perception_service.py` | `PerceptionService` — computes what an entity perceives |
| Perception Status | `src/domain/value_objects/perception.py` | `PerceptionStatus`, `PerceptionModifiers` |
| Perception Component | `src/domain/components/perception_component.py` | `PerceptionComponent` — attached to entities |
| FOV Query | `src/application/game_queries/fov_query.py` | FOV query interface |

### Perception Modifiers (per mob type)
| Mob Type | Sight | Hearing | Special |
|----------|-------|---------|---------|
| Undead | 8 | 4 | magic_sense=8 |
| Goblin | 6 | 14 | noise_sensitivity=1.3 |
| Wolf | 8 | 18 | smell=12 |
| Bat | 2 | - | echolocation=14 |
| Default | 8 | 8 | - |

## Behavior Trees

| Component | Location | Purpose |
|-----------|----------|---------|
| Behavior Script Service | `src/domain/services/behavior_script_service.py` | Evaluates behavior trees |
| Behavior Script | `src/domain/value_objects/behavior_script.py` | `BehaviorScript`, `BehaviorNode`, `BehaviorAction` |
| Behavior Component | `src/domain/components/behavior_component.py` | Attached to entities with scripts |

### Node Types
- `ACTION` — performs an action if conditions pass
- `CONDITION` — checks a condition (no action)
- `SELECTOR` — tries children until one succeeds
- `SEQUENCE` — runs all children; fails if any fails
- `PARALLEL` — runs all; returns first action

## Dungeon Generation

| Component | Location | Purpose |
|-----------|----------|---------|
| Dungeon Generator | `darkdelve.py` | `DungeonGenerator` — procedural rooms + corridors |
| Level Design Service | `src/domain/services/level_design_service.py` | Higher-level level theming |
| Content DB | `cache/content.db` | Cached LLM-generated content |

## Player Systems

| System | Location | Purpose |
|--------|----------|---------|
| Inventory | `src/domain/components/inventory.py` | Item storage, weight limits |
| Equipment | `src/domain/components/equipment.py` | Equipped items (weapon/armor) |
| Survival | `src/domain/services/survival_service.py` | Hunger, effects |
| Player Agent | `player_agent.py` | LLM-based player controller (playtests) |

## Map Conventions

```
dungeon_map[x, y]  — indexed as [x, y] not [row, col]
True  = wall (blocked)
False = floor (walkable)

Entity.x = column position
Entity.y = row position

Distance: Chebyshev (max of abs dx, abs dy) for movement
          Manhattan (abs dx + abs dy) for perception
```

## Turn Processing Order

```
1. tick_energy() — all entities gain speed energy
2. next_actor() loop:
   a. Pick highest-energy actor (random tie-break)
   b. If player: process input, then BREAK (player acts once per frame)
   c. If monster: process AI action, continue loop
3. When no actor has ≥ 100 energy → frame ends
4. Wait for next player input
```

## Key Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| Energy threshold | 100 | Energy needed to act |
| Default speed | 100 | Energy gained per tick |
| FOV radius | 8 | Player vision range |
| Melee range | 1 | Attack only at adjacent tiles |
| Base AC | 10 | Armor class without defense |
| Max nutrition | 2000 | Full hunger bar |
| XP to level 1→2 | 100 | Level up threshold |

---

## Recent Changes (map-rebuild branch)

- **Energy system fix**: `main_loop` now processes ALL actors with energy ≥ 100 per frame (was: only one)
- **Random tie-breaking**: `next_actor()` picks randomly among highest-energy actors (was: always first in list)
- **Player position in perception**: `PerceptionResult` now includes `player_position` so monsters can navigate toward the player even when outside FOV
- **Alternative step finding**: `_execute_movement()` tries perpendicular directions when blocked by non-enemies
- **Agent system setup**: Tests now properly initialize `AgentTurnProcessor` and register `RandomAgent` instances
