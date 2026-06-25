# ATTENTION.md — Code Location Cheat Sheet

> This file helps AI assistants and developers quickly find where things live.
> When you need to change a system, look here first.

---

## Core Systems

| What | File | Line/Class | Notes |
|------|------|-----------|-------|
| **Game Loop** | `darkdelve.py` | `Game.main_loop()` ~L2112 | Processes player + all monsters per frame |
| **Energy System** | `darkdelve.py` | `EnergySystem` ~L829 | `tick_energy()`, `next_actor()` — speed determines turn frequency |
| **Entity (base)** | `darkdelve.py` | `Entity` ~L637 | All game objects. Key fields: `speed`, `power`, `defense`, `hp` |
| **Player creation** | `darkdelve.py` | `Game.create_player()` ~L1926 | Player speed=100 (hardcoded) |
| **Monster spawning** | `darkdelve.py` | `Game.generate_level()` ~L2026 | Speed scaled by tier: Minion=50%, Soldier=60%, Elite=70%, Boss=80% |
| **Monster templates** | `darkdelve.py` | `MobTemplate` ~L536 | Default speed=100 before scaling |
| **Dungeon map** | `darkdelve.py` | `Game.dungeon_map` | `np.ndarray`, `True`=wall, `False`=floor, indexed `[x, y]` |

## Movement & Collision

| What | File | Function | Notes |
|------|------|----------|-------|
| Move with collision | `darkdelve.py` | `Entity.move_to()` ~L703 | Bounds + wall + blocker check |
| Delta move | `darkdelve.py` | `Entity.move()` ~L713 | Legacy helper |
| Move toward target | `darkdelve.py` | `Entity.move_towards()` ~L731 | One step closer (Chebyshev) |
| Alternative step | `src/domain/agents/integration.py` | `_find_alternative_step()` ~L298 | Tries perpendicular when blocked |

## FOV & Perception

| What | File | Class/Function | Notes |
|------|------|---------------|-------|
| FOV computation | `darkdelve.py` | `FOVSystem.compute()` ~L998 | tcod FOV_BASIC, radius=8 |
| Explored tiles | `darkdelve.py` | `FOVSystem.explored` | Once seen, always dimmed |
| Perception service | `src/domain/services/perception_service.py` | `PerceptionService` | What an entity perceives |
| Perception modifiers | `src/domain/value_objects/perception.py` | `PerceptionModifiers` | Per mob type (sight, hearing, etc.) |
| Perception component | `src/domain/components/perception_component.py` | `PerceptionComponent` | Attached to entities |

## Combat

| What | File | Function | Notes |
|------|------|----------|-------|
| Attack resolution | `darkdelve.py` | `CombatResolver.resolve_attack()` ~L758 | d20 + power//2 + dex_mod vs AC |
| Damage calc | `darkdelve.py` | `CombatResolver` ~L797 | weapon_dice + power//2 + bonus |
| AC calculation | `darkdelve.py` | `Entity.armor_class` ~L684 | 10 + defense + equipment |
| To-hit bonus | `darkdelve.py` | `Entity.to_hit_bonus` ~L692 | Equipment bonus |
| Combat log | `darkdelve.py` | `CombatLog` | Records all combat events |

## Agent AI System

| What | File | Class | Notes |
|------|------|-------|-------|
| Agent base | `src/domain/agents/base.py` | `Agent` | Abstract base with `perceive()`, `decide()`, `execute()` |
| RandomAgent | `src/domain/agents/llm_agent.py` | `RandomAgent` ~L258 | Default monster AI |
| LLMAgent | `src/domain/agents/llm_agent.py` | `LLMAgent` ~L41 | Optional LLM-powered AI |
| CommanderAgent | `src/domain/agents/commander_agent.py` | `CommanderAgent` ~L38 | Boss tactical AI |
| Agent manager | `src/domain/agents/commander_agent.py` | `AgentManager` ~L160 | Tracks all agents |
| Turn processor | `src/domain/agents/integration.py` | `AgentTurnProcessor` ~L36 | Executes agent actions |
| Action execution | `src/domain/agents/integration.py` | `_execute_movement()` ~L229 | MOVE_TO logic with collision |
| Combat execution | `src/domain/agents/integration.py` | `_execute_combat()` ~L280 | ATTACK logic |
| Perception result | `src/domain/agents/base.py` | `PerceptionResult` | Now includes `player_position` |
| Actions | `src/domain/agents/actions.py` | `AgentAction`, `ActionType` | MOVE_TO, ATTACK, WAIT, etc. |
| Game state for agents | `src/domain/agents/state.py` | `AgentGameState` | Snapshot passed to agents |

## Behavior Trees (advanced AI)

| What | File | Class | Notes |
|------|------|-------|-------|
| Behavior service | `src/domain/services/behavior_script_service.py` | `BehaviorScriptService` | Evaluates behavior trees |
| Behavior script | `src/domain/value_objects/behavior_script.py` | `BehaviorScript` | Node types: ACTION, CONDITION, SELECTOR, SEQUENCE |
| Behavior component | `src/domain/components/behavior_component.py` | `BehaviorComponent` | Attached to entities with scripts |

## Map Conventions

```
dungeon_map[x, y]  — indexed as [x, y] (not [row, col])
True  = wall (blocked)
False = floor (walkable)

Entity.x = column position (0 to width-1)
Entity.y = row position (0 to height-1)

Distance types:
  Chebyshev: max(abs(dx), abs(dy)) — used for movement
  Manhattan: abs(dx) + abs(dy) — used for perception ranges
```

## Turn Processing Order

```
1. tick_energy() — all entities gain speed energy
2. next_actor() loop:
   a. Pick highest-energy actor (random tie-break among equals)
   b. If player: process input, continue loop (monsters also act this frame)
   c. If monster: process AI action, continue loop
3. When no actor has >= 100 energy → frame ends
4. Wait for next player input
```

## Key Constants

| Constant | Value | Location | Purpose |
|----------|-------|----------|---------|
| Energy threshold | 100 | `EnergySystem.next_actor()` | Energy needed to act |
| Player speed | 100 | `Game.create_player()` | Acts every tick |
| Minion speed | 50 | `Game.generate_level()` | Acts every 2 ticks |
| Soldier speed | 60 | `Game.generate_level()` | Acts every ~1.7 ticks |
| Elite speed | 70 | `Game.generate_level()` | Acts every ~1.4 ticks |
| Boss speed | 80 | `Game.generate_level()` | Acts every ~1.25 ticks |
| FOV radius | 8 | `Game.__init__()` | Player vision range |
| Melee range | 1 | `CombatResolver.resolve_attack()` | Attack only at adjacent tiles |
| Base AC | 10 | `Entity.armor_class` | Without defense/equipment |

## Monster Speed Scaling (2026-06-25)

```python
tier_speed_scale = {
    MobTier.MINION: 0.50,   # speed 50
    MobTier.SOLDIER: 0.60,  # speed 60
    MobTier.ELITE: 0.70,    # speed 70
    MobTier.BOSS: 0.80,     # speed 80
}
```

## Recent Changes

- **2026-06-25**: Energy system fix — process all ready actors per frame
- **2026-06-25**: Random tie-breaking in `next_actor()`
- **2026-06-25**: Player position in `PerceptionResult` for out-of-FOV navigation
- **2026-06-25**: Monster speed scaling by tier (player advantage)
- **2026-06-25**: Alternative step finding for collision avoidance
