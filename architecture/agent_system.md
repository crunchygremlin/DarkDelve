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