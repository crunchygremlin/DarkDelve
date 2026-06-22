# Entity AI System Architecture

**Location:** `architecture/entity_ai_system.md`

## Overview
The Entity AI System introduces a layered architecture that replaces the previous monolithic AI component with a set of **modular, data‑driven subsystems**.  All subsystems interact through well‑defined data contracts and the existing **event bus** (`src/application/event_system/event_bus.py`).  The high‑level flow is:

1. **Perception** – `PerceptionStatus` is populated each tick from the FOV query (`src/application/game_queries/fov_query.py`).
2. **Decision Engine** – The LLM (`src/domain/agents/llm_agent.py`) receives the `PerceptionStatus` and optional `PlayerProfile` and returns a **BehaviorScript** (JSON tree).
3. **Behavior Execution** – `BehaviorEngine` (new) walks the tree, invoking actions defined in `src/domain/components/ai.py` and other services.
4. **Social & Loyalty** – Social structures influence which script is selected and modify action parameters.
5. **Power & Skill Layers** – Extend the existing `Stats` value object (`src/domain/value_objects/stats.py`) with power‑level and skill modifiers that are consulted during combat and decision making.
6. **LLM Performance Logging** – Every LLM call is recorded to `playtest/telemetry/llm_performance.json` for analysis.

---

## New Files to Create
| Path | Purpose |
|------|---------|
| `src/domain/value_objects/perception_status.py` | `PerceptionStatus` dataclass and modifiers |
| `src/domain/value_objects/behavior_script.py` | Data model for behavior trees |
| `src/domain/value_objects/social.py` | `SocialRelationship`, `SocialStructure`, `Loyalty` dataclasses |
| `src/domain/value_objects/power_levels.py` | Power‑level categories (offensive/defensive) |
| `src/domain/value_objects/skill_set.py` | Skill enumeration and modifiers |
| `src/domain/value_objects/player_profile.py` | `PlayerProfile` for LLM level design |
| `src/domain/value_objects/llm_logging.py` | `LLMCallLog` & `LLMPerformanceMetrics` |
| `src/domain/services/perception_service.py` | Populate `PerceptionStatus` from FOV query |
| `src/domain/services/behavior_engine.py` | Execute `BehaviorScript` trees |
| `src/domain/services/social_service.py` | Manage relationships & loyalty |
| `src/domain/services/power_service.py` | Compute offensive/defensive power values |
| `src/domain/services/skill_service.py` | Resolve skill effects on actions |
| `src/domain/services/llm_performance_service.py` | Write logs to telemetry path |
| `architecture/entity_ai_system.md` | This document |

## Existing Files to Modify
| File | Change |
|------|--------|
| `src/domain/components/ai.py` | Replace direct map access with a call to `PerceptionService.get_status(entity_id)` and expose a `process_behavior(script: BehaviorScript)` method that delegates to `BehaviorEngine`.
| `src/domain/agents/llm_agent.py` | Update `generate_prompt` to accept a `PerceptionStatus` and optional `PlayerProfile`; change return type to `BehaviorScript`.
| `src/application/game_queries/fov_query.py` | Export a helper `compute_fov(entity_id) -> Set[Position]` used by `PerceptionService`.
| `src/application/event_system/event_bus.py` | Add new event types `PerceptionUpdated`, `BehaviorScriptSelected`, `LoyaltyChanged`.
| `src/domain/value_objects/stats.py` | Extend with `PowerLevels` field (reference new dataclass).

---

## Data Structures

### PerceptionStatus (`src/domain/value_objects/perception_status.py`)
```python
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class PerceptionStatus:
    can_see_player: bool
    can_hear_player: bool
    player_last_known_position: Optional[Tuple[int, int]]
    visible_threats: List[str]          # entity IDs
    audible_threats: List[str]
    distance_to_player: Optional[float]
    modifiers: List[str]                # e.g. ["good_hearing", "echolocation"]
```

### PerceptionModifiers (`src/domain/value_objects/perception_status.py`)
```python
PERCEPTION_MODIFIERS = {
    "goblin": ["good_hearing"],
    "bat": ["echolocation"],
    "spider": ["vibration"]
}
```

### BehaviorScript (`src/domain/value_objects/behavior_script.py`)
```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class BehaviorNode:
    type: str                     # "condition" | "action" | "selector" | "sequence"
    params: Dict[str, Any]
    children: Optional[List["BehaviorNode"]] = None

@dataclass
class BehaviorScript:
    root: BehaviorNode
    version: str = "1.0"
```

### SocialRelationship & SocialStructure (`src/domain/value_objects/social.py`)
```python
@dataclass
class SocialRelationship:
    source_id: str
    target_id: str
    relation: str                # "ally", "enemy", "neutral"
    affinity: float              # 0.0‑1.0

@dataclass
class SocialStructure:
    entity_id: str
    hierarchy_level: int         # 0 = leader, higher = lower rank
    loyalty: float               # 0.0‑1.0
    group_id: str                # e.g. "goblin_kingdom"
```

### PowerLevels (`src/domain/value_objects/power_levels.py`)
```python
@dataclass
class PowerLevels:
    # Offensive
    melee_strength: int = 0
    melee_precision: int = 0
    piercing: int = 0
    slashing: int = 0
    bludgeoning: int = 0
    fire_magic: int = 0
    ice_magic: int = 0
    lightning_magic: int = 0
    poison_magic: int = 0
    arcane_magic: int = 0
    divine_magic: int = 0
    shadow_magic: int = 0
    # Defensive
    physical_armor: int = 0
    piercing_resist: int = 0
    slashing_resist: int = 0
    bludgeoning_resist: int = 0
    fire_resist: int = 0
    ice_resist: int = 0
    lightning_resist: int = 0
    poison_resist: int = 0
    arcane_resist: int = 0
    divine_resist: int = 0
    shadow_resist: int = 0
    evasion: int = 0
```

### SkillSet (`src/domain/value_objects/skill_set.py`)
```python
from enum import Enum

class Skill(Enum):
    SNEAKINESS = "sneakiness"
    STEALTH = "stealth"
    ACROBATICS = "acrobatics"
    PERCEPTION = "perception"
    INVESTIGATION = "investigation"
    INTIMIDATION = "intimidation"
    PERSUASION = "persuasion"
    DECEPTION = "deception"
    LANGUAGE = "language"
    ARCANE_KNOWLEDGE = "arcane_knowledge"
    SURVIVAL = "survival"
    MEDICINE = "medicine"
    WEAPON_MASTERY = "weapon_mastery"
    ARMOR_MASTERY = "armor_mastery"
    TACTICAL_AWARENESS = "tactical_awareness"
```

### PlayerProfile (`src/domain/value_objects/player_profile.py`)
```python
@dataclass
class PlayerProfile:
    level: int
    skills: List[Skill]
    power_levels: PowerLevels
    recent_actions: List[Dict[str, Any]]
```

### LLM Logging (`src/domain/value_objects/llm_logging.py`)
```python
@dataclass
class LLMCallLog:
    timestamp: str
    prompt_summary: str
    response_summary: str
    latency_ms: int
    tokens_used: int
    success: bool

@dataclass
class LLMPerformanceMetrics:
    total_calls: int = 0
    avg_latency_ms: float = 0.0
    error_rate: float = 0.0
```

---

## System Details

### 1. Modular Perception Status
```
+-------------------+        +-------------------+        +-------------------+
| src/application/ |        | src/domain/value_ |        | src/domain/servi |
| game_queries/    |  FOV   | objects/percepti |  API   | ce/perception_se |
| fov_query.py     |------->| on_status.py     |------->| rvice.py         |
| (returns set of   |        | (dataclass)       |        | (creates Percept |
| visible tiles)   |        +-------------------+        +-------------------+
```
* The **FOV query** computes visible tiles for an entity.
* `PerceptionService` translates those tiles into boolean flags, distance metrics, and fills `modifiers` based on the entity type (using `PERCEPTION_MODIFIERS`).
* The resulting `PerceptionStatus` is attached to the entity component `AI.perception` and sent via `PerceptionUpdated` event.

### 2. Behavioral Scripts
```
+-------------------+        +-------------------+        +-------------------+
| src/domain/agents|  Prompt| src/domain/value_ |  JSON   | src/domain/servi |
| /llm_agent.py    |------->| objects/behavio  |------->| ce/behavior_engine|
| (LLM call)       |        | r_script.py       |        | .py               |
|                  |        +-------------------+        +-------------------+
|                  |        | BehaviorScript    |        | walk_tree()       |
|                  |        | (root node)       |        | invoke_action()   |
+-------------------+        +-------------------+        +-------------------+
```
* The LLM receives a **prompt** containing the `PerceptionStatus` (and optionally `PlayerProfile`).
* It returns a JSON tree that conforms to the `BehaviorScript` schema.
* `BehaviorEngine` validates the tree, then each tick walks the tree, evaluating `BehaviorCondition` nodes against the entity’s current state (including **social** and **skill** data) and executing `BehaviorAction` nodes.

#### Catalog of Conditions & Actions (excerpt)
| Condition | Parameters | Meaning |
|-----------|------------|---------|
| `player_visible` | – | `perception.can_see_player`
| `health_below` | `threshold: float` | Entity health < threshold
| `loyalty_above` | `value: float` | `SocialStructure.loyalty >= value`
| `has_skill` | `skill: Skill` | Entity skill level > 0

| Action | Parameters | Effect |
|--------|------------|--------|
| `move_to` | `position: (x, y)` | Calls `AI.move_towards`
| `attack` | `target_id: str` | Calls combat service
| `give_item` | `item_id: str, recipient_id: str` | Inventory transfer
| `increase_loyalty` | `amount: float` | Adjusts `SocialStructure.loyalty`

### 3. Social Structures & Loyalty
```
+-------------------+        +-------------------+        +-------------------+
| src/domain/servi |  Query | src/domain/value_ |  Update | src/domain/servi |
| ce/social_service |------->| objects/social.py|------->| ce/behavior_engine|
| .py               |        | (dataclasses)    |        | .py               |
+-------------------+        +-------------------+        +-------------------+
```
* `SocialService` maintains a graph of `SocialRelationship` objects.
* Loyalty is a float that is **modified** by:
  * Item gifts (`increase_loyalty` action)
  * Combat outcomes (damage dealt/received)
  * Proximity events (being near a leader adds a small boost)
* Loyalty influences **script selection**: each mob type defines a mapping of loyalty thresholds to alternative behavior scripts (e.g., a minion with loyalty > 0.8 follows a *guard* script).

### 4. Power Level Categories
The new `PowerLevels` dataclass **extends** the existing `Stats` value object (`src/domain/value_objects/stats.py`).  `Stats` now contains a field `power_levels: PowerLevels`.  All combat calculations reference the appropriate offensive/defensive entries instead of the generic `strength`/`defense` values.

### 5. Skill Categories
Skills are stored in a `Set[Skill]` on the entity component `SkillComponent` (new).  During condition evaluation, `has_skill` checks this set.  During combat, `SkillService` provides modifiers (e.g., `STEALTH` reduces detection chance, `WEAPON_MASTERY` adds to melee damage).

### 6. LLM Level Design & Item Seeding
* `PlayerProfile` is built from the player’s `Stats`, `PowerLevels`, and learned `Skill`s.
* When the game needs **new content** (e.g., a new dungeon room), the `CommanderAgent` sends a `MapAccessRequest` containing the profile and a request type (`"level_creation"`, `"clairvoyance"`).
* The LLM returns a description and optional item list, which the `LevelGenerator` consumes.

### 7. Social Structure Scenarios
Each scenario is defined in `config/social_structures.yaml` (see *Configuration Schema*).  The table below summarises hierarchy, loyalty mechanics, and typical behavior patterns.

| Scenario | Hierarchy | Loyalty Triggers | Typical Script |
|----------|-----------|------------------|----------------|
| Goblin Kingdom | King → Guard → Minion | Gifts from King, shared loot, combat aid | Guard patrols, minion scavenges, king issues commands |
| Wolf Pack | Alpha → Beta → Omega | Successful hunts, pack cohesion, injury | Alpha leads chase, betas flank, omegas guard den |
| Spider Hive | Queen → Worker → Drone | Egg laying, web maintenance, feeding | Workers expand web, drones gather prey, queen directs |
| Mercenary Band | Captain → Soldier → Scout | Payment, successful contracts, shared victories | Captain issues orders, soldiers hold line, scouts recon |
| Undead Court | Lich → Knight → Skeleton | Dark rituals, bone offerings, necromancy | Lich summons, knights guard, skeletons swarm |
| Merchant Guild | Guildmaster → Merchant → Guard | Trade profit, tax payment, protection | Guildmaster sets prices, merchants sell, guards enforce |

### 8. LLM Performance Logging
* Every call to `LLMAgent.generate_behavior` creates a `LLMCallLog` entry.
* `LLMPerformanceService` aggregates metrics and writes them to `playtest/telemetry/llm_performance.json`.
* The JSON schema includes: `timestamp`, `prompt_summary`, `response_summary`, `latency_ms`, `tokens_used`, `success`.

---

## Integration Points
| Point | Existing Component | New Hook |
|-------|--------------------|----------|
| Perception | `src/application/game_queries/fov_query.py` | `PerceptionService.update(entity_id)` emits `PerceptionUpdated` |
| LLM Prompt | `src/domain/agents/llm_agent.py` | Accepts `PerceptionStatus` + `PlayerProfile` |
| Behavior Execution | `src/domain/components/ai.py` | Calls `BehaviorEngine.process(script)` |
| Social Updates | `src/domain/services/social_service.py` | Listens to `CombatHandler` events to adjust loyalty |
| Power Levels | `src/domain/value_objects/stats.py` | New field `power_levels` referenced by `CombatService` |
| Skill Effects | `src/domain/services/skill_service.py` | Provides modifiers to `BehaviorEngine` and `CombatService` |

---

## Configuration Schema (YAML)
```yaml
mob_types:
  goblin:
    perception_modifiers: [good_hearing]
    default_behavior_script: goblin_idle.json
    power_levels:
      melee_strength: 5
      fire_resist: 2
    skills: [stealth, perception]
    social_structure:
      group_id: goblin_kingdom
      hierarchy_level: 2
      loyalty: 0.5
  bat:
    perception_modifiers: [echolocation]
    default_behavior_script: bat_patrol.json
    power_levels:
      evasion: 8
    skills: [perception]
    social_structure:
      group_id: bat_swarm
      hierarchy_level: 1
      loyalty: 0.7
```

---

## LLM Prompt Templates
### Perception → Behavior Prompt
```
You are an AI controlling a {entity_type} in a roguelike dungeon.
Current perception:
{perception_status}
Player profile:
{player_profile}
Based on this information, output a **BehaviorScript** JSON that directs the entity for the next tick. Use the catalog of conditions and actions defined in the system.
```

### Level Design Prompt (Commander Agent)
```
Player profile:
{player_profile}
Requested level type: {level_type}
Generate a concise description of the new area, list of notable entities, and any special items to seed. Return JSON with keys `description`, `entities`, `items`.
```

---

## Event Flow
```mermaid
stateDiagram-v2
    [*] --> PerceptionUpdate : tick
    PerceptionUpdate --> LLMPrompt : generate
    LLMPrompt --> BehaviorSelected : receive script
    BehaviorSelected --> BehaviorExecution : walk tree
    BehaviorExecution --> Combat / Movement / Social : actions
    Combat --> LoyaltyChange : outcome
    LoyaltyChange --> BehaviorSelection : may trigger new script
    LLMPrompt --> LLMLogging : log call
```

---

## Testing Strategy
* **Unit Tests** – New modules have dedicated tests in `tests/`:
  * `test_perception_service.py` – verifies modifiers and flag generation.
  * `test_behavior_engine.py` – validates tree walking, condition evaluation, and action dispatch.
  * `test_social_service.py` – loyalty adjustments on combat events.
  * `test_power_service.py` – correct mapping from `Stats` to `PowerLevels`.
  * `test_llm_performance_service.py` – log file creation and aggregation.
* **Integration Tests** – Extend existing `test_agent_system.py` to assert that an entity receives a script based on perception and that loyalty changes affect script selection.
* **Playtest Telemetry** – Run automated playtests that record `llm_performance.json`; add assertions that latency stays below a configurable threshold.
* **Regression** – Ensure existing AI behavior remains unchanged when `PerceptionStatus` is empty (fallback to legacy AI).

---

*Document generated by the Architect mode. Developers can now implement the outlined files and modify the referenced components.*

