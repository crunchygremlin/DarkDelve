# MCP Integration Architecture

> Cross-cutting concern: how the Model Context Protocol integrates with game systems.

## Overview

DarkDelve uses MCP (Model Context Protocol) to enable LLM-driven game manipulation
through a structured tool set. The integration lives in `src/infrastructure/services/`
and provides programmatic access to game state, entity management, and live configuration.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Integration Layer                     │
│                                                             │
│  mcp_integration.py          mcp_toolkit.py                 │
│  (MCPPlaytester)             (MCPToolSet)                   │
│       │                            │                        │
│       ▼                            ▼                        │
│  Game.process_action()       Tool execution                  │
│  Game.render_frame_text()    State manipulation              │
│  PlayerAgent                 Live config                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Core Game (darkdelve.py)                  │
│                                                             │
│  Game.main_loop()                                           │
│  Game.process_action()                                      │
│  EnergySystem                                               │
│  Entity management                                          │
└─────────────────────────────────────────────────────────────┘
```

## Components

### MCPPlaytester

**File:** `src/infrastructure/services/mcp_integration.py`

The in-process playtester that drives a `Game` instance directly. Avoids subprocess
overhead and enables embedded automation.

```python
class MCPPlaytester:
    def __init__(self, game: Game, config: PlaytestConfig, agent: PlayerAgent):
        self.game = game
        self.config = config
        self.agent = agent
        self.telemetry = TelemetryStore()

    def run_turn(self) -> TurnResult:
        frame = self.game.render_frame_text()
        stats = extract_stats(frame)
        decision = self.agent.decide(frame, stats)
        self.game.process_action(decision.action)
        self.telemetry.append(decision)
        return TurnResult(decision=decision, game_state=self.game.state)

    def run(self, max_turns: int = 100) -> PlaytestResult:
        for turn in range(max_turns):
            result = self.run_turn()
            if result.game_state.is_game_over:
                break
        return PlaytestResult(turns=turn, telemetry=self.telemetry.to_list())
```

### MCPToolSet

**File:** `src/infrastructure/services/mcp_toolkit.py`

A set of tools for LLM-driven game manipulation. Each tool is a callable that
operates on the game state.

```python
class MCPToolSet:
    def create_mob(self, mob_type: str, position: Tuple[int, int], name: str) -> str:
        """Spawn a new monster at the given position."""

    def add_item(self, entity_id: str, item_id: str) -> str:
        """Add an item to an entity's inventory."""

    def modify_stat(self, entity_id: str, stat: str, delta: float) -> str:
        """Modify an entity's stat (health, strength, etc.)."""

    def request_map_section(self, x: int, y: int, width: int, height: int) -> str:
        """Request a slice of the dungeon map."""

    def write_live_config(self, key: str, value: Any) -> str:
        """Update persistent llm_state.json."""

    def read_live_config(self, key: str) -> str:
        """Read from live config."""

    def list_entities(self) -> str:
        """List all entities in the game."""

    def send_message(self, message: str, recipient: str = "player") -> str:
        """Send a message to the player or game log."""
```

## Integration Points

| MCP Tool | Game System | File |
|----------|-------------|------|
| `create_mob()` | Entity spawning | `darkdelve.py:Game.generate_level()` |
| `add_item()` | Inventory system | `darkdelve.py:Inventory` |
| `modify_stat()` | Entity stats | `darkdelve.py:Entity` |
| `request_map_section()` | Map system | `darkdelve.py:Game.dungeon_map` |
| `write_live_config()` | LLM state | `src/domain/services/context_manager.py` |
| `list_entities()` | Entity management | `darkdelve.py:Game.entities` |
| `send_message()` | UI messaging | `darkdelve.py:Game.add_message()` |

## Live Config (llm_state.json)

The live config file provides persistent state that survives across game sessions.
It is used by the MCP tools to store operator preferences and game state.

**File:** `cache/llm_state.json`

```json
{
  "difficulty_override": "hard",
  "max_monster_count": 50,
  "player_persona": "aggressive",
  "operator_notes": "Testing floor 3 balance"
}
```

## Communication Modes

The system supports three communication modes for LLM interaction:

| Mode | Mechanism | Use Case |
|------|-----------|----------|
| JSON Command Snippets | `AgentCommunication` | Turn-based actions via stdin |
| MCP Tool Set | `MCPToolSet` | Rich programmatic world manipulation |
| Live Config File | `llm_state.json` | Persistent state and operator preferences |

## PlayerAgent Integration

The `PlayerAgent` (`player_agent.py`) is the validation boundary between the LLM
and the game. It is used by both subprocess and in-process playtesters.

```python
class PlayerAgent:
    def build_system_prompt(self) -> str:
        """Returns Survive & Explore baseline + persona + JSON schema."""

    def build_user_prompt(self, frame: str, stats: Dict, history: List) -> str:
        """Returns prompt with current frame, stats, and recent history."""

    def request_ollama(self, payload: Dict) -> Dict:
        """Posts to Ollama /api/generate with format: json."""

    def validate_response(self, response: Dict) -> PlayerDecision:
        """Validates schema, falls back to 'e' for invalid actions."""

    def record_turn(self, decision: PlayerDecision) -> None:
        """Stores the latest five decisions for history."""
```

## Gotchas

1. **auto_initialize=False**: When the caller has already called `Game.initialize()`,
   construct `MCPPlaytester` with `auto_initialize=False` to avoid double-init.
2. **render_to_stdout=False**: Pass this to `main_loop()` for in-process runs to
   prevent console output during automation.
3. **Treat `i` as no-op**: The real inventory screen blocks for a second input event.
   Automation should avoid entering that blocking state.
4. **Frame text only**: Use `Game.render_frame_text()` for the prompt, not the raw
   console buffer which includes ANSI escape sequences.
5. **Tool validation**: All MCP tool inputs are untrusted. Validate entity IDs and
   positions before applying changes.
