# DarkDelve Ollama Player AI Playtest

This directory contains the local Ollama-driven playtesting subsystem. The
original playtester launches [`darkdelve.py`](../darkdelve.py:1) as a subprocess,
scrapes the ANSI-cleared console frames from stdout, asks Ollama for one JSON
action, and injects that action back into the game stdin.

DarkDelve also supports an in-process library mode. With
`playtest.enabled: true` in [`config/game.yaml`](../config/game.yaml:138),
`darkdelve.py` initializes a [`Game`](../darkdelve.py:1774) instance and drives
it through [`MCPPlaytester`](../src/infrastructure/services/mcp_integration.py:44).
That path renders plain-text frames from the game console buffer, passes them to
the existing `PlayerAgent`, applies the returned action with
[`Game.main_loop()`](../darkdelve.py:2031), and writes the same telemetry format
used by the subprocess playtester.

## Usage

Start Ollama and ensure the configured model is available:

```bash
ollama serve
ollama pull qwen2.5-coder:7b-instruct
```

Run the subprocess playtester from the project root:

```bash
python ollama_playtester.py
```

Run the game in in-process playtester mode:

```bash
python darkdelve.py
```

Enable it in [`config/game.yaml`](../config/game.yaml:138):

```yaml
playtest:
  enabled: true
  config_path: playtest/playtest_config.yaml
```

The in-process mode uses the same `playtest/playtest_config.yaml` settings for
Ollama endpoint, model, persona, max turns, telemetry path, and instruction path.
It does not require a separate MCP server, FastAPI service, or subprocess game
window.

Useful subprocess overrides:

```bash
python ollama_playtester.py --persona "Aggressive Stress-Tester" --max-turns 50
python ollama_playtester.py --model qwen2.5-coder:7b-instruct --endpoint http://127.0.0.1:11434
python ollama_playtester.py --game-command python darkdelve.py
```

Configuration lives in [`playtest_config.yaml`](playtest_config.yaml). Telemetry
is appended to [`playtest_telemetry.json`](playtest_telemetry.json) when it is
created by a run.

For quick local validation you can temporarily set
`playtest.playtest_config.max_turns` to a small number in
`playtest/playtest_config.yaml`, run `python darkdelve.py`, then restore the
normal value. The game config flag `playtest.enabled` should remain `false` for
normal human play.

## Operator instruction bus

The playtester can read live operator instructions from
[`playtest/instructions.json`](instructions.json). This keeps the game window and
operator instruction channel separate: the game continues to render normally, while
you update the communication file and the next prompt sent to Ollama includes the
active instructions.

The JSON payload shape is:

```json
{
  "enabled": true,
  "target": "player",
  "setup": "Persistent guidance for this session.",
  "push": "One-shot instruction for the next prompt."
}
```

- `setup`: persistent instructions that remain active until you edit the file.
- `push`: one-shot/live instruction for the current session. Clear it by setting
  `"push": ""` or by calling `InstructionBus.clear_push()`.
- `enabled`: when `false`, the payload is ignored.
- `target`: controls which LLM prompt receives the instructions:
  - `player`: the Ollama Player AI prompt.
  - `dungeon_master` or `dm`: DarkDelve content/Dungeon Master prompts.
  - `commander`: commander-side local LLM prompt.
  - `game`: the game process prompt target, currently reserved for future use.
  - `all`: inject into every supported target.

Use `--instructions` to point the playtester at a different communication file:

```bash
python ollama_playtester.py --instructions playtest/instructions.json
```

Example live workflow:

1. Start the game window normally, or start the playtester.
2. Edit `playtest/instructions.json` with `setup` and/or `push`.
3. Ask the operator assistant to read the file and summarize the active
   instructions.
4. The playtester injects `target: "player"` instructions into the Player AI
   prompt before asking Ollama for the next action.
5. Clear `push` after the one-shot instruction has been used.

The in-process playtester also reads `target: "player"` instructions through the
same `InstructionBus`, so live operator guidance works in both subprocess and
library modes.

## Ollama protocol

Every call to `/api/generate` includes:

```json
{
  "format": "json"
}
```

The expected model response schema is:

```json
{
  "macro_goal": "string",
  "reasoning": "string",
  "action": "w|a|s|d|e|i",
  "telemetry_notes": "string"
}
```

If Ollama returns malformed JSON, missing fields, or an invalid action, the agent
sanitizes where possible, logs the issue in telemetry, and falls back to a safe
action (`e`, wait one turn).

## Telemetry format

`playtest_telemetry.json` is a JSON array. Each player turn appends one object:

```json
{
  "event_type": "turn",
  "timestamp": "2026-06-21T00:00:00+00:00",
  "turn_number": 1,
  "stats": {
    "hp": 34,
    "max_hp": 34,
    "ac": 2,
    "level": 1,
    "depth": 1,
    "turn": 0,
    "gold": 0,
    "nutrition": 100,
    "max_nutrition": 100,
    "raw_status": "HP 34/34  AC 2  Level 1  Depth 1  Turn 0"
  },
  "action": "w",
  "macro_goal": "Explore north while preserving health",
  "reasoning": "The north tile is visible floor with no adjacent enemy.",
  "telemetry_notes": "",
  "issues": [],
  "fallback_used": false,
  "history": [],
  "frame": "...",
  "stderr_tail": "",
  "active_instructions": "Setup instructions:\nExplore carefully."
}
```

Crash or non-zero-exit records use `event_type: "crash"` and include:

- `status`
- `returncode`
- `final_map`
- `stderr_tail`
- `error_message` when an exception interrupted the loop

In-process runs return a JSON summary with `status`, `turns`, `stderr_tail`,
`error_message`, `final_frame`, and `telemetry_entries`. Normal successful
endpoints are `exit` and `max_turns`; `error` means the in-process loop raised an
exception.

## Built-in personas

- `Default`: cautious survival and exploration.
- `Aggressive Stress-Tester`: seeks combat, risky exploration, and balance edge
  cases while avoiding obviously suicidal actions.
- `Boundary Pushing Explorer`: probes map edges, unusual items, stairs, inventory
  interactions, and repeated action patterns that may reveal state bugs.
