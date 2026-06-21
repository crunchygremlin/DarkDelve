# DarkDelve Ollama Player AI Playtest

This directory contains the local Ollama-driven playtesting subsystem. The
playtester launches [`darkdelve.py`](../darkdelve.py:1) as a subprocess, scrapes
the ANSI-cleared console frames from stdout, asks Ollama for one JSON action, and
injects that action back into the game stdin.

## Usage

Start Ollama and ensure the configured model is available:

```bash
ollama serve
ollama pull qwen2.5-coder:7b-instruct
```

Run the playtester from the project root:

```bash
python ollama_playtester.py
```

Useful overrides:

```bash
python ollama_playtester.py --persona "Aggressive Stress-Tester" --max-turns 50
python ollama_playtester.py --model qwen2.5-coder:7b-instruct --endpoint http://127.0.0.1:11434
python ollama_playtester.py --game-command python darkdelve.py
```

Configuration lives in [`playtest_config.yaml`](playtest_config.yaml). Telemetry
is appended to [`playtest_telemetry.json`](playtest_telemetry.json) when it is
created by a run.

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
  "stderr_tail": ""
}
```

Crash or non-zero-exit records use `event_type: "crash"` and include:

- `status`
- `returncode`
- `final_map`
- `stderr_tail`
- `error_message` when an exception interrupted the loop

## Built-in personas

- `Default`: cautious survival and exploration.
- `Aggressive Stress-Tester`: seeks combat, risky exploration, and balance edge
  cases while avoiding obviously suicidal actions.
- `Boundary Pushing Explorer`: probes map edges, unusual items, stairs, inventory
  interactions, and repeated action patterns that may reveal state bugs.
