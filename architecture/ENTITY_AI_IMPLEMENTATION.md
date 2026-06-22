# Entity AI Implementation Summary

## Files Created

| File | Purpose |
|------|---------|
| `config/entity_ai.yaml` | YAML configuration defining mob types, perception modifiers, social structures, and behavior catalogs |
| `src/infrastructure/configuration/entity_ai_config_loader.py` | Python class for loading and accessing entity AI configuration |
| `tests/test_entity_ai_config.py` | 22 unit tests for the config loader |

## Test Results

- **Total tests:** 518 passed, 17 failed (pre-existing failures unrelated to Entity AI)
- **New tests:** 22 passed (all Entity AI config tests)
- **Test count increase:** +22 tests

## Architecture Diagram

```
+-------------------+     +------------------------+     +----------------------+
| config/entity_ai. |     | entity_ai_config_load  |     | Domain Services      |
| yaml              | --> | er.py                  | --> | (PerceptionService,  |
| (YAML data)       |     | (ConfigLoader)         |     |  BehaviorEngine,     |
+-------------------+     +------------------------+     |  SocialService)      |
                                                         +----------------------+
                                                                |
                                                                v
                                                    +------------------------+
                                                    | Entity Components      |
                                                    | - AI Component         |
                                                    | - PerceptionComponent  |
                                                    | - SocialComponent      |
                                                    +------------------------+
```

## How to Use the System

### Loading Configuration

```python
from src.infrastructure.configuration.entity_ai_config_loader import EntityAIConfigLoader

# Load with default path
loader = EntityAIConfigLoader()

# Or specify custom path
loader = EntityAIConfigLoader("config/entity_ai.yaml")
```

### Accessing Mob Type Data

```python
# Get all mob types
mob_types = loader.get_mob_types()

# Get specific mob type
goblin = loader.get_mob_type("goblin")

# Get perception modifiers for a mob
perception = loader.get_perception_modifiers("goblin")
# Returns: {"sight_range": 6.0, "hearing_range": 14.0, ...}

# Get power offsets
power = loader.get_power_offsets("goblin")
# Returns: {"melee_strength": 2.0, "melee_precision": 1.0}

# Get skill offsets
skills = loader.get_skill_offsets("goblin")
# Returns: {"sneakiness": 2.0, "intimidation": 1.0}
```

### Accessing Social Structures

```python
# Get all social structure types
structures = loader.get_all_structure_types()

# Get specific structure
kingdom = loader.get_social_structure("goblin_kingdom")
```

### Checking Leadership Status

```python
if loader.is_leader("goblin_king"):
    # This mob type is a leader
    pass
```

## Integration Points with Existing Code

1. **Perception System** (`src/domain/services/perception_service.py`)
   - Uses `get_perception_modifiers()` to apply mob-specific perception bonuses
   - Integrates with existing `PerceptionSense` enum

2. **Social System** (`src/domain/services/social_service.py`)
   - Uses `get_base_loyalty()` for initial loyalty values
   - Uses `get_social_structure()` for group behavior patterns

3. **Power/Skill System** (`src/domain/value_objects/power_levels.py`)
   - Uses `get_power_offsets()` and `get_skill_offsets()` for stat calculations

4. **Behavior Engine** (`src/domain/services/behavior_script_service.py`)
   - Uses `get_behavior_catalog_name()` to select behavior scripts

## What the LLM Receives vs Previous System

### Before (Hardcoded Values)
- Perception modifiers were hardcoded in `src/domain/value_objects/perception.py`
- Power levels were hardcoded in `src/domain/value_objects/power_levels.py`
- Social structures were not configurable

### After (Data-Driven Configuration)
- **Perception:** Configurable sight/hearing/smell ranges, darkvision, echolocation, vibration sense, noise/light sensitivity
- **Power Offsets:** Configurable melee strength, precision, piercing, slashing, magic abilities
- **Skill Offsets:** Configurable sneakiness, stealth, acrobatics, intimidation, tactical awareness, etc.
- **Social Structures:** Configurable group hierarchies, loyalty mechanics, promotion systems
- **Behavior Catalogs:** Each mob type maps to a behavior catalog for LLM prompting

## Configuration Schema Overview

```yaml
mob_types:
  <type>:
    display_name: string
    health: int
    speed: float
    perception:
      sight_range: float
      hearing_range: float
      smell_range: float
      vibration_range: float
      echolocation_range: float
      magic_sense_range: float
      darkvision: bool
      see_invisible: bool
      ignore_walls_hearing: bool
      ignore_walls_vibration: bool
      noise_sensitivity: float
      light_sensitivity: float
      darkness_penalty: float
    power_offsets:
      melee_strength: float
      melee_precision: float
      piercing: float
      slashing: float
      arcane_magic: float
      # ... etc
    skill_offsets:
      sneakiness: float
      stealth: float
      # ... etc
    behavior_catalog: string
    default_role: string
    base_loyalty: float
    is_leader: bool

social_structures:
  <structure_type>:
    display_name: string
    description: string
    leader_type: string
    member_types: [string]
    guard_type: string
    min_members: int
    max_members: int
    loyalty_sensitive: bool
    wealth_driven: bool
    hive_mind: bool
    # ... etc

loyalty:
  min_value: float
  max_value: float
  desertion_threshold: float
  betrayal_threshold: float
  fanatic_threshold: float
  # ... etc

perception:
  default_sight_range: float
  default_hearing_range: float
  memory_duration_ticks: int
  recalc_interval_ticks: int

behavior:
  default_evaluation_interval: int
  max_script_depth: int
  max_children_per_node: int
  default_timeout_ms: int