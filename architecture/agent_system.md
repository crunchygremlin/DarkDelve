# Agent System Architecture

## Overview

The Agent System provides a generic framework for AI agents to perceive game state, make decisions, and execute actions in DarkDelve. It integrates with the existing EnergySystem for turn-based execution and works with the existing LLM infrastructure.

## Directory Structure

```
src/domain/agents/
├── __init__.py           # Module exports
├── base.py               # Abstract Agent base class and types
├── actions.py            # AgentAction and ActionResult classes
├── state.py              # Game state representation for agents
├── llm_agent.py          # LLM-based and Random agent implementations
├── commander_agent.py    # Commander agent for tactical decisions
└── integration.py        # Integration with EnergySystem and Game
```

## Core Components

### 1. Agent Base Class (`base.py`)

The abstract `Agent` class defines the interface that all agents must implement:

```python
class Agent(ABC):
    @abstractmethod
    def perceive(self, game_state: AgentGameState) -> PerceptionResult:
        """Perceive the current game state."""
        pass
    
    @abstractmethod
    def decide(self, perception: PerceptionResult) -> AgentAction:
        """Make a decision based on perceived state."""
        pass
    
    def execute(self, action: AgentAction, game_context: Dict) -> ActionResult:
        """Execute an action in the game context."""
        pass
```

### 2. Agent Types (`AgentType` enum)

- `PLAYER` - Human player agent
- `NPC` - Non-player character
- `COMMANDER` - Tactical commander for groups
- `MONSTER` - Monster/AI entity

### 3. Perception System (`state.py`)

`AgentGameState` provides a read-only snapshot of the game state:

- `EntityState` - Individual entity information
- `ItemState` - Item information
- `CombatState` - Combat event data
- `AgentGameState` - Complete game state for agent perception

### 4. Action System (`actions.py`)

`AgentAction` represents an action an agent wants to perform:

- Movement actions (MOVE_NORTH, MOVE_SOUTH, MOVE_EAST, MOVE_WEST, MOVE_TO)
- Combat actions (ATTACK, ATTACK_TARGET)
- Interaction actions (PICKUP, USE, EQUIP, DROP)
- Special actions (WAIT, CAST_SPELL, HOLD_POSITION)

`ActionResult` contains the result of action execution.

### 5. Agent Implementations

#### LLMAgent (`llm_agent.py`)
- Uses local LLM (Ollama) for decision making
- Configurable model, temperature, and prompts
- Includes fallback to RandomAgent behavior on LLM failure

#### RandomAgent (`llm_agent.py`)
- Simple random decision making
- Useful for testing and as a baseline

#### CommanderAgent (`commander_agent.py`)
- Specialized for tactical command
- Issues orders to subordinates
- Manages pending orders queue

### 6. Integration (`integration.py`)

`AgentManager` coordinates all agents:
- Register/unregister agents
- Get agent for entity
- Process turns

`AgentTurnProcessor` bridges EnergySystem and agents:
- Builds game state snapshots
- Executes agent actions
- Handles movement and combat

## Integration with Existing Systems

### EnergySystem Integration

The agent system integrates with the existing `EnergySystem` (lines 795-825 in darkdelve.py):

```python
# In Game.main_loop()
actor = self.energy_system.next_actor()
if actor is self.player:
    # Player turn - handled by input
else:
    # Agent turn - use AgentManager
    result = agent_manager.process_turn(actor, game_state, context)
```

### LLM Infrastructure Integration

The agent system works with the existing LLM queues (lines 1409-1529 in darkdelve.py):

```python
# LLMAgent can use the existing LLM infrastructure
llm_request_queue.put({
    "prompt": prompt,
    "commander_id": entity_id
})
```

## Usage Example

```python
from src.domain.agents import (
    LLMAgent, LLMAgentConfig, AgentManager,
    create_agent_game_state_snapshot
)

# Create agent manager
agent_manager = AgentManager()

# Create an LLM agent for an entity
config = LLMAgentConfig(model="qwen2.5-coder:7b-instruct")
agent = LLMAgent(entity, agent_type=AgentType.NPC, config=config)
agent_manager.register_agent(agent)

# During game loop
game_state = create_agent_game_state_snapshot(game)
result = agent_manager.process_turn(actor, game_state, game_context)
```

## Design Principles

1. **Separation of Concerns**: Perception, decision, and execution are separate
2. **Extensibility**: New agent types can be added by subclassing `Agent`
3. **Testability**: Each component can be tested independently
4. **Integration**: Works with existing EnergySystem and LLM infrastructure
5. **Fallback**: Graceful degradation when LLM is unavailable

## Future Enhancements

- Behavior trees for complex AI
- Goal-oriented action planning
- Memory system for agents
- Learning from player behavior
- Multi-agent communication protocols

## Implemented Features (as of this update)

### 1. MCP Toolkit (`src/infrastructure/services/mcp_toolkit.py`)
A new module providing tools for LLM-driven game manipulation:
- `create_mob(mob_type, position, name)` - Spawn new monsters
- `add_item(entity_id, item_id)` - Add items to entity inventories
- `modify_stat(entity_id, stat, delta)` - Modify entity stats (health, strength, etc.)
- `request_map_section(x, y, width, height)` - Request map data slices
- `write_live_config(key, value)` - Update persistent `llm_state.json`
- `read_live_config(key)` - Read from live config
- `list_entities()` - List all entities in the game
- `send_message(message, recipient)` - Send messages to player or log

### 2. LLM Agent Enhancements (`src/domain/agents/llm_agent.py`)
- **Context-size protection**: Automatic prompt truncation when token count exceeds 8k limit
- **Map-request API**: `request_map_section()` method for on-demand map data
- **Token budget management**: Configurable `max_context_tokens` in `LLMAgentConfig`

### 3. Behavior Script Validation (`src/domain/services/plan_generator.py`)
- Scripts are validated against `MOB_BEHAVIOR_CATALOG` for each mob type
- Invalid conditions/actions are logged and ignored
- Catalog defines valid conditions/actions per mob type (goblin, goblin_king, wolf, spider, mercenary, undead, default)

### 4. Plan Memory Updates (`src/domain/services/behavior_script_service.py`)
- Multi-step plans now track:
  - `current_step` - Current position in the behavior tree
  - `last_search_pos` - Last known player position
  - `attack_count` - Number of attacks in current plan
  - `current_health` - Current health percentage
  - `visible_threats` - Count of visible threats
  - `player_seen` / `player_heard` - Player detection status
  - `last_known_player_pos` - Last recorded player position

### 5. Condition Evaluation Logging (`src/domain/services/behavior_script_service.py`)
- Failed condition evaluations are logged with details:
  - Condition type, actual value, operator, expected value
  - Helps debug why a behavior branch was not taken

### 6. EventBus Integration (`src/domain/services/agent_communication.py`)
- All message types now publish events:
  - `order_issued` - When an order is sent
  - `orders_requested` - When a subordinate requests orders
  - `status_reported` - When a subordinate reports status
  - `alert_sent` - When an alert is broadcast

### 7. Action Dispatcher (`src/domain/services/action_dispatcher.py`)
All action handlers are now implemented:
- `ATTACK`, `FLEE`, `PATROL`, `MOVE_TO`, `CALL_ALLIES`
- `FOLLOW_LEADER`, `GUARD_POSITION`, `PICKUP_ITEM`
- `GIFT_ITEM`, `GIVE_ORDERS`, `WAIT`, `SEARCH`
- `HIDE`, `USE_ITEM`, `TRADE`, `PROMOTE_MINION`

### 8. Hybrid Communication Architecture
The system now supports three communication modes:
1. **JSON Command Snippets** - Turn-based actions via `AgentCommunication`
2. **MCP Tool Set** - Rich programmatic access for world manipulation
3. **Live Config File** - Persistent state in `llm_state.json`

This enables:
- Real-time player-like actions
- World editing (spawn mobs, modify stats, add items)
- Map queries for context-limited LLM prompts
- IDE debugging and playtesting
## Unified DungeonMasterAgent (DM Improvements)

The DungeonMasterAgent has been enhanced to become a single cohesive "mind" owning:
- Behavior script generation
- Level design
- Map generation (via LLMMapGenerator)
- Content batches
- Difficulty evaluation (moved from LLMWorker)
- Global throttled poetic memory (DMGlobalMemory)
- Behavior library (BehaviorLibrary)
- Swarm templates (SwarmTemplateService)
- Cache-miss tracking (CacheMissTracker)

### Key Changes

1. **Constructor** now accepts:
   - `model_name: str = "qwen2.5-coder:7b-instruct"` - Single model config
   - `temperature: float = 0.7`
   - `max_prompt_chars: int = 8000` - Truncation threshold

2. **Memory System** (`DMGlobalMemory`):
   - Global poetic memory bounded by headroom tokens
   - Refreshed at level boundaries via `refresh_memory()`
   - Injected into all DM prompts via `_prepare_prompt()`

3. **Behavior Library** (`BehaviorLibrary`):
   - Caches behavior scripts by mob type
   - Falls back to `create_default_script()` on LLM failure
   - Persists to `cache/behavior_library.json`

4. **Swarm Templates** (`SwarmTemplateService`):
   - Templates by intelligence tier (1-5)
   - Leader commands via event bus
   - Default templates for surround, flee, ambush behaviors

5. **Cache-Miss Tracker** (`CacheMissTracker`):
   - Telemetry-only tracking of prompt similarity
   - Uses difflib for >=75% similarity detection
   - Logs to `playtest/telemetry/cache_miss.jsonl`

### LLMWorker Changes

- Removed `evaluate_player_stats` methods (moved to DungeonMasterAgent)
- Added `map_generation` branch in `llm_worker_func`
- Delegates map generation to `dm_agent.generate_map()`
