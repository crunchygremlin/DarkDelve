# How DarkDelve Works — A Human's Guide

This document explains the core systems that make DarkDelve tick. It's written for humans who want to understand the game's architecture without reading thousands of lines of code.

---

## Table of Contents

1. [The Game Loop](#1-the-game-loop)
2. [The Energy System (Turn Scheduler)](#2-the-energy-system-turn-scheduler)
3. [Entities & Stats](#3-entities--stats)
4. [Movement & Collision](#4-movement--collision)
5. [Field of View (FOV)](#5-field-of-view-fov)
6. [Combat](#6-combat)
7. [The Agent AI System](#7-the-agent-ai-system)
8. [Putting It All Together](#8-putting-it-all-together)

---

## 1. The Game Loop

DarkDelve uses a **turn-based game loop** driven by player input. Here's the basic flow:

```
┌─────────────────────────────────────────────┐
│              MAIN LOOP                       │
│                                              │
│  1. Tick energy for all entities             │
│  2. Find the highest-energy actor            │
│  3. If it's the PLAYER:                      │
│     - Wait for keyboard input                │
│     - Process the action (move/attack/wait)  │
│  4. If it's a MONSTER:                       │
│     - Run monster AI (decide action)         │
│     - Execute action (move/attack)           │
│  5. Repeat from step 2 until no actor has    │
│     enough energy, then go back to step 1    │
│                                              │
└─────────────────────────────────────────────┘
```

The key insight: **the game doesn't run on real-time**. Nothing happens until the player presses a key. When they do, the game processes their action AND all monster actions that have accumulated, then waits for the next input.

---

## 2. The Energy System (Turn Scheduler)

### What It Simulates

The energy system is an **initiative scheduler**. It determines who gets to act and how often. Think of it like D&D's initiative system, but continuous:

- Every entity has a **speed** stat (typically 100)
- Each frame, every entity gains energy equal to their speed
- When an entity reaches **100 energy**, it can take a turn
- After acting, it loses 100 energy

### Why This Approach?

**It models "readiness" over time.** A faster creature (speed=200) gains energy twice as fast as a normal one (speed=100), so it gets twice as many turns. This is a classic roguelike mechanic used in games like DCSS and Angband.

### How It Works Step-by-Step

```
Frame 0:
  tick_energy: P +100, G0 +100, G1 +100, G2 +100
  next_actor: P=100, G0=100, G1=100, G2=100
  → Random pick from highest-energy actors
  → Say G1 is picked (energy 100→0)
  → G1 acts (moves toward player)

Frame 1:
  tick_energy: P +100, G0 +100, G1 +100, G2 +100
  next_actor: P=200, G0=200, G1=100, G2=200
  → Random pick from [P, G0, G2] (all at 200)
  → Say P is picked (energy 200→100)
  → Player acts (waits/moves)

Frame 2:
  tick_energy: P +100, G0 +100, G1 +100, G2 +100
  next_actor: P=200, G0=300, G1=200, G2=300
  → Random pick from [G0, G2] (both at 300)
  → Say G0 acts (energy 300→200)

...and so on. All actors with energy ≥ 100 act every frame.
```

### Why Not Other Approaches?

| Approach | How It Works | Pros | Cons |
|----------|-------------|------|------|
| **Energy System** (current) | Entities accumulate energy, act when full | Natural speed differences, proven in roguelikes | Slightly complex |
| **Round-Robin** | Each entity acts once per round in order | Simple, fair | Can't represent speed differences |
| **Priority Queue** | Entities scheduled at future timestamps | Very flexible, efficient | More complex to implement |
| **Tick Counter** | Each entity has a countdown timer | Similar to energy | Inverted mental model |

The energy system was chosen because it's a well-understood pattern in roguelike development and naturally supports creatures with different speeds.

---

## 3. Entities & Stats

Everything in the game is an **Entity** — the player, monsters, items, even dungeon features.

### Core Stats

| Stat | What It Does | Used By |
|------|-------------|---------|
| `hp` / `max_hp` | Health points; entity dies at 0 | All entities |
| `power` | Attack strength; affects damage | All entities |
| `defense` | Reduces incoming damage | All entities |
| `speed` | How fast energy regenerates; determines turn frequency | All entities |
| `armor_class` | Difficulty to hit; = 10 + defense + equipment | Player mainly |
| `to_hit_bonus` | Added to attack rolls | Player mainly |
| `intel_tier` | Intelligence level (affects AI complexity) | Monsters |
| `level` / `xp` | Character progression | Player |
| `nutrition` | Hunger meter; decreases over time | Player |

### Entity Types

- **Player**: Has inventory, stats, XP, nutrition. Controlled by human input.
- **Mob (Monster)**: Has `mob_type`, `home_position`, AI agent. Controlled by AI.
- **Item Entity**: An item on the ground. Has `item` field. Can be picked up.

### Monster Tiers

Monsters come in four tiers that affect their stats and behavior:

| Tier | Typical HP | Behavior |
|------|-----------|----------|
| Minion | Low | Basic aggressive AI |
| Soldier | Medium | Standard aggressive AI |
| Elite | High | Stronger stats |
| Boss | Very High | Uses Commander AI (tactical, can issue orders) |

---

## 4. Movement & Collision

### How Movement Works

Movement is grid-based, one tile at a time. When an entity tries to move:

```
1. Calculate target position (current + direction)
2. Check if target is within map bounds
3. Check if target is a floor tile (not a wall)
4. Check if any blocking entity occupies the target tile
5. If all checks pass → move to target
6. If blocked → don't move (or attack if hostile entity is there)
```

### The `move_to()` Function

```python
def move_to(self, x, y, dungeon_map, entities):
    # 1. Check bounds
    if 0 <= x < dungeon_map.shape[0] and 0 <= y < dungeon_map.shape[1]:
        # 2. Check if floor (False = floor, True = wall)
        if not dungeon_map[x, y]:
            # 3. Check no blocking entity at target
            if not any(e.blocks for e in entities 
                       if e.x == x and e.y == y and e is not self):
                self.x = x
                self.y = y
                return True
    return False
```

### Movement Toward a Target

When a monster wants to move toward the player, it uses `move_towards()`:

```python
def move_towards(self, target_x, target_y, dungeon_map, entities):
    dx = target_x - self.x
    dy = target_y - self.y
    distance = max(abs(dx), abs(dy))  # Chebyshev distance
    if distance > 0:
        step_x = int(round(dx / distance))  # Normalize to -1, 0, or 1
        step_y = int(round(dy / distance))
        self.move_to(self.x + step_x, self.y + step_y, dungeon_map, entities)
```

This moves the entity one step closer to the target, using diagonal movement when appropriate.

---

## 5. Field of View (FOV)

### What It Represents

FOV determines **what the player can see** on the map. It's computed using tcod's FOV algorithm (FOV_BASIC) with a configurable radius (default: 8 tiles).

### How It Works

```
1. Start with the dungeon map (True = wall, False = floor)
2. Invert it to a transparency array (walls block vision)
3. Compute FOV from the player's position with radius=8
4. Result: a boolean array where True = visible, False = not visible
5. Track "explored" tiles separately (once seen, always shown as dimmed)
```

### Key Concepts

- **Visible**: Currently in FOV — shown in full brightness
- **Explored**: Previously in FOV but not currently — shown dimmed
- **Unexplored**: Never seen — not shown at all (black)

### Why FOV Matters for AI

The FOV array is also used by the agent system to determine what monsters can "see." Currently, monsters use the **player's FOV** (not their own), which means a monster "knows" about any entity that the player can see. This is a design simplification — in a more realistic system, each monster would compute its own FOV from its own position.

---

## 6. Combat

### Attack Resolution

Combat uses a D&D-style d20 system:

```
1. Check range: melee attacks only work at adjacent distance (distance ≤ 1)
2. Roll d20
3. Calculate total: d20 + power//2 + dex_mod + to_hit_bonus
4. Compare against target's armor_class (AC)
5. Determine result:
   - Natural 20 → CRITICAL HIT (double damage)
   - Natural 1 → CRITICAL FAIL (automatic miss)
   - total ≥ AC → HIT
   - total < AC → MISS
6. If HIT: roll weapon dice + power//2 + damage_bonus
7. If CRITICAL: double the damage
```

### Damage Formula

```
damage = roll(weapon_dice) + power//2 + damage_bonus
critical_damage = damage * 2
```

### Armor Class

```
AC = 10 + defense + equipment_bonus
```

### Range Guard

Melee attacks only work at distance 1 (adjacent tiles). If the target is further away, the attack automatically misses with `out_of_range=True`. This prevents monsters from attacking across the map.

---

## 7. The Agent AI System

### Overview

Monsters are controlled by an **agent system** that separates perception from decision-making:

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────────┐
│  Perceive   │ →   │    Decide    │ →   │   Execute    │ →   │   Result   │
│ (see world) │     │ (pick action)│     │ (do action)  │     │ (outcome)  │
└─────────────┘     └──────────────┘     └──────────────┘     └────────────┘
```

### Agent Types

| Agent | Used By | Behavior |
|-------|---------|----------|
| `RandomAgent` | Most monsters | Moves toward player when visible, wanders otherwise |
| `LLMAgent` | Optional (Ollama-powered) | Uses a local LLM to make decisions |
| `CommanderAgent` | Boss monsters | Tactical AI that can issue orders to subordinates |

### RandomAgent Decision Logic

```
1. If player is visible (in FOV):
   → MOVE_TO player's position
2. Else if player's last known position is known:
   → MOVE_TO player_position
3. Else if visible entities and random < 0.3:
   → ATTACK a random visible entity
4. Else if visible items and random < 0.3:
   → MOVE_TO a random visible item
5. Else:
   → Random movement (N/S/E/W) or WAIT
```

### Perception Pipeline

The agent's perception is built from the game state:

1. **AgentGameState** is constructed from the current game state
2. It includes all entities, visible entities (in player's FOV), items, and player position
3. The agent's `perceive()` method creates a **PerceptionResult** from this
4. The `decide()` method uses the PerceptionResult to choose an action

### Action Execution

Once the agent decides on an action, `AgentTurnProcessor` executes it:

- **MOVE_TO**: Calculate direction, normalize to single step, check for obstacles/entities, move or attack
- **ATTACK**: Find target by ID, resolve combat
- **WAIT**: Do nothing (costs a turn)
- **PICKUP**: Pick up item at current position

---

## 8. Putting It All Together

### A Complete Turn Example

```
Player presses 'e' (wait):

1. tick_energy()
   P: 100→200, G0: 100→200, G1: 100→200

2. next_actor() → P picked (random among tied at 200)
   P energy: 200→100

3. Player acts: action='e' → wait, no movement

4. next_actor() → G1 picked (random among tied at 200)
   G1 energy: 200→100

5. G1 acts:
   - perceive: player at (40,20), G1 at (35,20)
   - decide: MOVE_TO (40,20)
   - execute: dx=5, dy=0 → step=(1,0) → move to (36,20)

6. next_actor() → G0 picked (random among tied at 200)
   G0 energy: 200→100

7. G0 acts:
   - perceive: player at (40,20), G0 at (20,20)
   - decide: MOVE_TO (40,20)
   - execute: dx=20, dy=0 → step=(1,0) → move to (21,20)

...all monsters with energy ≥ 100 act...

8. No more actors with energy ≥ 100 → frame ends

9. Game waits for next player input
```

### Key Design Decisions

1. **Turn-based, not real-time**: The game only advances when the player acts. This gives the player time to think and makes the game fair.

2. **Energy-based initiative**: Allows creatures with different speeds to act at different frequencies, adding tactical depth.

3. **Batch actor processing**: All actors with sufficient energy act in a single frame, preventing energy accumulation and ensuring fairness.

4. **FOV-based perception**: Monsters "see" what the player sees, which is a simplification that could be extended to per-monster FOV for more realistic behavior.

5. **Agent-based AI**: Separating perception, decision, and execution makes the AI system modular and extensible (e.g., swapping in LLM-based decisions).

---

## File Map

For those who want to dive into the code:

| System | Key File(s) | Key Classes |
|--------|------------|-------------|
| Game Loop | `darkdelve.py` | `Game.main_loop()` |
| Energy System | `darkdelve.py` | `EnergySystem` |
| Entities | `darkdelve.py` | `Entity`, `MobTemplate` |
| Movement | `darkdelve.py` | `Entity.move_to()`, `Entity.move_towards()` |
| FOV | `darkdelve.py` | `FOVSystem` |
| Combat | `darkdelve.py` | `CombatResolver` |
| Agent System | `src/domain/agents/` | `Agent`, `RandomAgent`, `AgentTurnProcessor` |
| Agent State | `src/domain/agents/state.py` | `AgentGameState`, `EntityState` |
| Agent Actions | `src/domain/agents/actions.py` | `AgentAction`, `ActionType` |
| Perception | `src/domain/agents/base.py` | `PerceptionResult` |
| Behavior Trees | `src/domain/services/behavior_script_service.py` | `BehaviorScriptService` |
