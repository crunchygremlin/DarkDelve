# Playtest Integration Architecture

> Cross-cutting concern: how the playtest subsystem integrates with core game logic.

## Overview

DarkDelve has two playtest modes:

1. **Subprocess mode** — `ollama_playtester.py` launches `darkdelve.py` as a child process, drives it through stdin/stdout, and scrapes ANSI console frames.
2. **In-process library mode** — `MCPPlaytester` drives a `Game` instance directly without subprocess overhead.

Both modes must remain isolated from core game logic so they can be added, modified, or removed without refactoring the game.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Playtest Subsystem                        │
│                                                             │
│  ollama_playtester.py          MCPPlaytester                │
│  (subprocess mode)             (in-process mode)            │
│       │                              │                      │
│       ▼                              ▼                      │
│  ConsoleFrameParser           Game.process_action()         │
│  PlayerAgent                  Game.render_frame_text()      │
│  TelemetryStore               InstructionBus                │
│       │                              │                      │
│       └──────────┬───────────────────┘                      │
│                  │                                          │
│                  ▼                                          │
│         playtest/playtest_config.yaml                        │
│         playtest/instruction_bus.py                         │
│         playtest/playtest_telemetry.json                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ (stdin/stdout or API calls)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Core Game (darkdelve.py)                  │
│                                                             │
│  Game.main_loop()  ◄─── action injection                    │
│  Game.process_action() ◄─── in-process actions              │
│  Game.render_frame_text() ◄─── frame for prompt             │
│  InstructionBus ◄─── operator instructions                  │
└─────────────────────────────────────────────────────────────┘
```

## Subprocess Mode

### Contract

| Component | File | Responsibility |
|-----------|------|----------------|
| `OllamaPlaytester` | `ollama_playtester.py` | Popen loop, frame parsing, action injection |
| `ConsoleFrameParser` | `ollama_playtester.py` | Split `\033[H\033[2J` frames, extract stats |
| `PlayerAgent` | `player_agent.py` | Build prompt, validate response, fallback |
| `PlaytestConfig` | `playtest/playtest_config.yaml` | Endpoint, model, persona, max turns |
| `TelemetryStore` | `ollama_playtester.py` | Atomic JSON append to telemetry file |

### Data Flow

```
OllamaPlaytester
├── Popen launches darkdelve.py with piped stdin/stdout/stderr
├── ConsoleFrameParser scrapes \033[H\033[2J ASCII frames
├── PlayerAgent builds Survive & Explore prompt + persona + 5-turn history
├── Ollama /api/generate payload includes "format": "json"
├── JSON response is validated against macro_goal/reasoning/action/telemetry_notes
├── action is injected as one line into game stdin
└── TelemetryStore.append() writes every turn to playtest/playtest_telemetry.json
```

### Console Input Contract

| Action | Meaning |
|--------|---------|
| `w` | Move up or attack upward |
| `a` | Move left or attack left |
| `s` | Move down or attack down |
| `d` | Move right or attack right |
| `e` | Wait one turn |
| `i` | Open or close inventory (no-op in automation) |

## In-Process Library Mode

### Contract

| Component | File | Responsibility |
|-----------|------|----------------|
| `MCPPlaytester` | `src/infrastructure/services/mcp_integration.py` | Library wrapper around PlayerAgent |
| `Game.process_action()` | `darkdelve.py` | Non-blocking action entry point |
| `Game.render_frame_text()` | `darkdelve.py` | Plain text frame for prompt |
| `InstructionBus` | `playtest/instruction_bus.py` | Operator instruction injection |

### Data Flow

```
MCPPlaytester
├── Game.render_frame_text() → frame text
├── PlayerAgent.decide(frame_text, stats) → PlayerDecision
├── Game.process_action(decision.action) → state change
├── TelemetryStore.append() → telemetry
└── Repeat until max_turns, exit, crash, or player death
```

## Instruction Bus

The instruction bus allows operator instructions to be injected into prompts without modifying game code.

| Target | Injection Point | Purpose |
|--------|-----------------|---------|
| `player` | PlayerAgent prompt | Guide player behavior |
| `game` | Content generation prompts | Guide dungeon generation |
| `all` | Both targets | Global instructions |

### File: `playtest/instruction_bus.py`

```python
class InstructionBus:
    def load_instructions(path: str) -> PlaytestInstructions
    def get_active_instructions(target: str) -> List[str]
    def clear_push(self)  # Remove one-shot push instructions after consumption
```

## Telemetry Schema

### Turn Record

```json
{
  "event_type": "turn",
  "turn_number": 5,
  "timestamp": "2026-06-27T04:00:00Z",
  "stats": { "hp": 23, "ac": 12, "depth": 1, "turn": 5, "gold": 0, "nutrition": 1999 },
  "action": "w",
  "macro_goal": "explore",
  "reasoning": "moving toward unexplored area",
  "telemetry_notes": "",
  "issues": [],
  "fallback_used": false,
  "history": ["turn 1: ...", "turn 2: ..."],
  "frame": "ascii frame text",
  "stderr_tail": ""
}
```

### Crash Record

```json
{
  "event_type": "crash",
  "status": "error",
  "returncode": -9,
  "final_map": "last ascii frame",
  "stderr_tail": "Error: ...",
  "error_message": "Process killed after timeout"
}
```

## Configuration

```yaml
# playtest/playtest_config.yaml
ollama:
  endpoint: "http://127.0.0.1:11434"
  model: "qwen2.5-coder:7b-instruct"
  temperature: 0.7
  num_predict: 512

playtest:
  max_turns: 100
  timeout_seconds: 300
  telemetry_path: "playtest/playtest_telemetry.json"
  config_darkdelve: "config/game.yaml"

persona: "Default"
```

## Gotchas

1. **Console quit contract**: The game does not exit cleanly from stdin in non-TTY mode. Use `process_action()` for in-process automation.
2. **`i` is a no-op in automation**: The real inventory screen blocks for a second input event. Automation should treat `i` as wait.
3. **Frame parsing**: The console renderer clears each frame with `\033[H\033[2J`. Parser must split on this exact sequence.
4. **LLM output validation**: Always include `"format": "json"` in Ollama payloads. Validate response schema and fall back to `e` for invalid actions.
5. **Telemetry atomic writes**: Use append mode with flush to ensure telemetry is written even on crash.
6. **Cache isolation**: Playtest runs may write to `cache/content.db`. Use isolated configs for repeatable tests.
