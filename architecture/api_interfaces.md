# DarkDelve Module Interfaces

## Local Ollama Player AI Interfaces

### `player_agent.PlayerAgent`

`PlayerAgent` is the prompt and validation boundary between the playtester and
Ollama. It does not know about subprocesses or game process management.

#### Public methods

- [`build_system_prompt()`](../player_agent.py:1): returns the `Survive & Explore`
  baseline, selected persona, optional persona modifier, and JSON-only response
  instructions.
- [`build_user_prompt()`](../player_agent.py:1): returns a prompt containing the
  current console frame, extracted stats, and up to five recent turns.
- [`build_payload()`](../player_agent.py:1): returns the exact `/api/generate`
  payload. This payload must always include `"format": "json"`.
- [`request_ollama()`](../player_agent.py:1): posts the payload to the configured
  Ollama endpoint.
- [`parse_response()`](../player_agent.py:1): sanitizes, validates, and returns a
  `PlayerDecision`.
- [`record_turn()`](../player_agent.py:1): stores the latest five decisions.

#### Ollama request contract

Every request to `/api/generate` must include:

```json
{
  "model": "qwen2.5-coder:7b-instruct",
  "prompt": "...",
  "system": "...",
  "stream": false,
  "format": "json",
  "temperature": 0.7,
  "top_p": 0.9,
  "num_predict": 512
}
```

#### Ollama response contract

Expected schema:

```json
{
  "macro_goal": "string",
  "reasoning": "string",
  "action": "w|a|s|d|e|i",
  "telemetry_notes": "string"
}
```

Validation rules:

- Missing string fields are converted to empty strings and logged in telemetry.
- Non-string fields are converted to strings and logged in telemetry.
- `action` must be one of `w`, `a`, `s`, `d`, `e`, or `i`.
- Malformed JSON is sanitized where possible using markdown fence stripping,
  object extraction, and Python literal fallback.
- Invalid or missing actions fall back to `e` and set `fallback_used: true`.

### `ollama_playtester.OllamaPlaytester`

`OllamaPlaytester` owns the subprocess loop and must not refactor core game
logic.

#### Public methods

- [`launch()`](../ollama_playtester.py:1): starts `darkdelve.py` with piped
  stdin, stdout, and stderr.
- [`run()`](../ollama_playtester.py:1): drives the game until exit, crash,
  error, or max turns.
- [`TelemetryStore.append()`](../ollama_playtester.py:1): atomically appends a
  JSON object to `playtest/playtest_telemetry.json`.

#### Console frame contract

The renderer emits frames using:

```text
\033[H\033[2J<ascii frame>\033[0m\n
```

`ConsoleFrameParser.parse_frames()` splits on `\033[H\033[2J`, removes ANSI
sequences, extracts rows, and parses the status line for `HP`, `AC`, `Level`,
`Depth`, `Turn`, `Gold`, and `Nutrition`.

#### Telemetry append contract

Every player turn appends an object with:

- `event_type: "turn"`
- `turn_number`
- `timestamp`
- `stats`
- `action`
- `macro_goal`
- `reasoning`
- `telemetry_notes`
- `issues`
- `fallback_used`
- `history`
- `frame`
- `stderr_tail`

Crash and non-zero-exit records append an object with:

- `event_type: "crash"`
- `status`
- `returncode`
- `final_map`
- `stderr_tail`
- `error_message`

## Console Input Contract

Console-mode playtesting relies on one-line stdin actions. The supported player
action set is:

| Action | Meaning |
| --- | --- |
| `w` | Move up or attack upward |
| `a` | Move left or attack left |
| `s` | Move down or attack down |
| `d` | Move right or attack right |
| `e` | Wait one turn |
| `i` | Open or close inventory |

The console renderer must block for input before monsters continue acting, so
the playtester can safely scrape one frame, call Ollama, and inject one action.
