# DarkDelve Playtest Problem Exploration Plan

Prepared for the architect after a bounded playtest pass. This plan focuses on the highest-value exploration paths discovered from the current architecture, existing playtester harness, and observed smoke-test behavior.

## Evidence from this pass

- Unit/integration subset passed:
  - `python -m pytest -q tests/test_ollama_playtester.py tests/test_player_agent.py tests/test_game_logic.py tests/test_energy_system.py tests/test_combat_system.py`
  - Result: `86 passed in 4.47s`
- Presentation/input subset passed:
  - `python -m pytest -q tests/test_console_input.py tests/test_input_handler.py tests/test_tile_rendering.py tests/test_map_rendering.py tests/test_player_rendering_comprehensive.py`
  - Result: `51 passed in 1.10s`
- Existing harness contract reviewed:
  - [`ollama_playtester.py`](ollama_playtester.py:226) drives [`darkdelve.py`](darkdelve.py:1) through stdin/stdout.
  - [`player_agent.py`](player_agent.py:257) validates one JSON action per turn.
  - [`playtest/playtest_config.yaml`](playtest/playtest_config.yaml:13) currently launches `python darkdelve.py`.
- Smoke test found a likely automation/quit gap:
  - Direct stdin sequence `w d s a i i ESC` rendered frames but did not exit; process ended `-9` after timeout.
  - Menu sequence `ESC ENTER ENTER` rendered the menu but did not exit; process ended `-9` after timeout.
  - Relevant code: [`darkdelve.py`](darkdelve.py:2248) reads line-buffered stdin when non-TTY, [`darkdelve.py`](darkdelve.py:2271) maps stdin to key events, and [`darkdelve.py`](darkdelve.py:2390) only exits the menu via Escape or Return on the selected option.
- Fake-Ollama harness smoke run succeeded:
  - Command used a temporary YAML config pointing `ollama_playtester.py` at a fake HTTP endpoint returning JSON action `e`.
  - Result: `status=max_turns`, `turns=2`, two telemetry entries, final frame showed `HP 23/23`, `Depth 1`, `Turn 2`, `Nutrition 1999/2000`.
  - Important caveat: max-turn termination terminates the game process with SIGTERM, so telemetry records `returncode=-15`.

## Priority P1: Console subprocess automation cannot quit cleanly

### Problem hypothesis

The game can render and accept stdin actions in non-TTY mode, but the current input contract does not provide a reliable way for a subprocess playtester to end the game cleanly. The observed direct smoke tests were killed after timeout, and the fake-Ollama harness can only stop by max-turn SIGTERM.

### Why this matters

- Long automated playtests will leave child processes unless externally killed.
- Telemetry cannot reliably capture graceful quit/save/death/victory exits.
- Human console users may also have ambiguous quit behavior if `q` is not mapped.

### Explore

1. Confirm whether `q` should be a direct quit shortcut or only a menu command.
2. Confirm whether `ESC` should exit the menu or only return to game.
3. Confirm whether Return should activate the selected menu item or merely resume.
4. Inspect whether `tcod.event.Quit` is used anywhere outside [`darkdelve.py`](darkdelve.py:2274).

### Reproduce

```bash
python - <<'PY'
import subprocess, time, select, sys
proc = subprocess.Popen([sys.executable, 'darkdelve.py'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
for ch in ['\x1b\n', '\n', '\n']:
    time.sleep(0.2)
    proc.stdin.write(ch)
    proc.stdin.flush()
time.sleep(2)
try:
    proc.wait(timeout=3)
except subprocess.TimeoutExpired:
    proc.kill()
    proc.wait()
print(proc.returncode)
PY
```

Expected failure: process remains alive and must be killed.

### Architect questions

- Should console mode support `q` as a direct quit shortcut?
- Should menu selection use arrow keys plus Return consistently?
- Should the playtester inject `QUIT` through a dedicated command channel rather than keyboard emulation?

## Priority P2: Ollama startup and model availability can block or alter playtests

### Problem hypothesis

[`Game.initialize()`](darkdelve.py:1819) starts embedded Ollama, optionally pulls the model, initializes the content cache, and starts an LLM worker before renderer initialization and new game creation. If Ollama is missing, slow, or the model is absent, the game falls back to generated content but may still spend startup time in `start()` and `ensure_model()`.

### Why this matters

- Playtests can become slow or non-deterministic depending on local Ollama state.
- The fake-Ollama harness bypasses game-side content generation, so it does not prove real LLM startup behavior.
- Cache writes can mutate [`cache/content.db`](cache/content.db:1), complicating repeatable test runs.

### Explore

1. Run a short game session with real Ollama disabled via config and verify fallback content still initializes quickly.
2. Run with a fake Ollama endpoint for content generation and assert cache writes are bounded.
3. Run with the real configured model and record startup latency, cache hit rate, and first-level generation latency.
4. Compare first-run vs cached-run telemetry.

### Reproduce baseline

```bash
python -m pytest -q tests/test_ollama_playtester.py tests/test_player_agent.py
```

Then run a bounded fake-Ollama playtester as above and inspect:

```bash
python - <<'PY'
import json
from pathlib import Path
entries = json.loads(Path('playtest/playtest_telemetry.json').read_text())
print([(e.get('turn_number'), e.get('issues'), e.get('fallback_used')) for e in entries])
PY
```

### Architect questions

- Should Ollama startup be decoupled from renderer/game initialization?
- Should playtest mode disable `auto_pull_model` by default?
- Should cache path be configurable per playtest run to avoid shared state?

## Priority P3: Console renderer and graphical renderer paths are both risky

### Problem hypothesis

The current default config sets `display.renderer: console` at [`config/game.yaml`](config/game.yaml:82), but [`create_renderer()`](src/presentation/renderer.py:101) also supports `graphical`. The smoke output used console rendering, so graphical renderer behavior remains unexercised.

### Why this matters

- A renderer-specific crash can block non-console users.
- Graphical input uses `tcod.event.wait()` while console input uses custom stdin parsing; bugs may only appear in one backend.
- Inventory, character, and menu presentation call `renderer.present()` even in console mode, which may be acceptable but should be verified.

### Explore

1. Run renderer factory tests for both `console` and `graphical` with a tiny synthetic tileset.
2. Run a headless graphical smoke with `display.width=20`, `display.height=10`, and a known tileset.
3. Exercise inventory, character, and menu rendering in both backends.
4. Verify that console mode does not depend on SDL event polling.

### Relevant files

- [`src/presentation/renderer.py`](src/presentation/renderer.py:38)
- [`src/presentation/renderer.py`](src/presentation/renderer.py:76)
- [`tests/test_tile_rendering.py`](tests/test_tile_rendering.py:1)
- [`tests/test_map_rendering.py`](tests/test_map_rendering.py:1)
- [`tests/test_player_rendering_comprehensive.py`](tests/test_player_rendering_comprehensive.py:1)

### Architect questions

- Is graphical renderer still a required target?
- Should console mode be the primary automated playtest backend?
- Should renderer creation be split from Ollama/content initialization?

## Priority P4: Instruction bus target matching needs end-to-end validation

### Problem hypothesis

The instruction bus exists in both [`playtest/instruction_bus.py`](playtest/instruction_bus.py:73) and embedded logic in [`darkdelve.py`](darkdelve.py:58). The playtester injects instructions into the player prompt, while the game injects dungeon-master/commander instructions into content generation. The two implementations should be tested together.

### Why this matters

- Incorrect target matching can leak instructions to the wrong LLM.
- Invalid JSON should disable instructions safely.
- The instruction bus can change player behavior without changing code, so it is a high-leverage exploration surface.

### Explore

1. Test `target=all`, `target=player`, `target=game`, and invalid target JSON.
2. Run fake-Ollama playtester with a player-specific push instruction and assert it appears in `active_instructions`.
3. Run content generation with a dungeon-master instruction and assert it appears in the prompt or cache key.
4. Add a negative test that commander instructions do not appear in player telemetry.

### Relevant files

- [`playtest/instruction_bus.py`](playtest/instruction_bus.py:150)
- [`tests/test_instruction_bus.py`](tests/test_instruction_bus.py:1)
- [`tests/test_darkdelve_instruction_bus.py`](tests/test_darkdelve_instruction_bus.py:1)
- [`tests/test_ollama_playtester.py`](tests/test_ollama_playtester.py:185)

### Architect questions

- Should the instruction bus be a single shared module instead of duplicated in `darkdelve.py`?
- Should target aliases be centralized?
- Should active instructions be included in crash telemetry?

## Priority P5: Save, quit, death, victory, and high-score side effects need bounded playtest coverage

### Problem hypothesis

The game mutates [`saves/`](saves:1) and [`highscores.json`](highscores.json:1) on save, death, victory, and quit. Permadeath and score-on-quit are enabled in [`config/game.yaml`](config/game.yaml:121), so accidental automated runs can alter persistent state.

### Why this matters

- Playtests should be repeatable and safe.
- Telemetry should capture whether a run ended through quit, death, victory, crash, or forced max-turn termination.
- Existing fake-Ollama max-turn runs do not cover endgame transitions.

### Explore

1. Add a temporary playtest config with `score_on_quit: false` and isolated save/highscore paths.
2. Exercise menu save-and-quit once the quit path is clarified.
3. Force death in a deterministic small map and assert save deletion/high-score behavior.
4. Force victory if stairs/victory path is reachable in a small map.
5. Add telemetry event types for `quit`, `save`, `death`, and `victory`.

### Relevant files

- [`darkdelve.py`](darkdelve.py:1327)
- [`darkdelve.py`](darkdelve.py:2413)
- [`darkdelve.py`](darkdelve.py:2421)
- [`darkdelve.py`](darkdelve.py:2425)
- [`darkdelve.py`](darkdelve.py:2434)

### Architect questions

- Should playtest mode use isolated save/highscore directories by default?
- Should `score_on_quit` be disabled for automated runs?
- Should high-score writes be injectable/mocked in tests?

## Recommended next exploration sequence

1. Fix or explicitly design the console quit contract, then rerun direct stdin smoke tests.
2. Add a deterministic subprocess test that starts the game, sends actions, opens inventory/menu, and exits cleanly.
3. Add a fake-Ollama content-generation harness with isolated cache and instruction bus paths.
4. Add renderer backend smoke tests for both console and graphical modes.
5. Add save/death/victory telemetry coverage with isolated persistent paths.

## Commands to preserve evidence

```bash
python -m pytest -q tests/test_ollama_playtester.py tests/test_player_agent.py tests/test_game_logic.py tests/test_energy_system.py tests/test_combat_system.py
python -m pytest -q tests/test_console_input.py tests/test_input_handler.py tests/test_tile_rendering.py tests/test_map_rendering.py tests/test_player_rendering_comprehensive.py
```

For future bounded playtester runs, prefer temporary telemetry paths under `playtest/telemetry/` and remove them after copying the relevant evidence into the architect report.
