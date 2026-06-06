# AI Roguelike — Design & Runbook

## Concept
- Retro-style roguelike (NetHack-like) where most game mechanics are deterministic engine code.
- A local LLM (Ollama-hosted 3B model) controls high-level commander decisions only. The LLM must never compute direct paths or low-level movement.

## High-level architecture
- Engine (this repo): map generation, rendering (libtcod), turn loop, combat, deterministic pathfinding, and entity actions.
- LLM service (local Ollama): receives concise JSON prompts about a commander's situation and returns a single high-level JSON command.
- Communication: engine enqueues prompts to a background LLM worker thread and consumes responses asynchronously so the main loop never blocks.

## LLM Contract (must be enforced)
- The model returns a single JSON object with fields:
  - `commander_shout` (string): short battle shout shown in logs
  - `command` (string): one of `ATTACK_PLAYER`, `HOLD_POSITION`, `RETREAT_TO_ROOM`, `DEFEND_COMMANDER`
- The model must not return coordinates, movement steps, or path instructions. The engine performs pathfinding from current position to the command target.
- If the model returns plain text, the engine treats it as `commander_shout` and falls back to `ATTACK_PLAYER`.

## Prompt Template (example)
Use the following JSON prompt body as the `prompt` sent to Ollama (engine already serializes to JSON):

{
  "commander_id": "Goblin Warlord",
  "commander_position": [x, y],
  "player_position": [px, py],
  "player_hp": [hp, max_hp],
  "visible_entities": [{"name":"Orc","type":"o","position":[ox,oy],"hp":8}],
  "instructions": "Return exactly one JSON object with `commander_shout` and `command`. Valid commands: ATTACK_PLAYER, HOLD_POSITION, RETREAT_TO_ROOM, DEFEND_COMMANDER. Do NOT provide paths or steps—engine handles pathfinding.",
  "response_format": {"commander_shout":"string","command":"string"}
}

## Running locally (quick)
1. Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

2. Start your local Ollama API (consult Ollama docs for your version). Commonly this is:

```bash
ollama serve
```

This typically exposes an HTTP API on `http://127.0.0.1:11434` (verify your Ollama config).

3. Run the game:

```bash
python3 main.py
```

## Files of interest
- `main.py` — engine, LLM integration, and pathfinding
- `README.md` — this design doc and runbook
- `requirements.txt` — minimal Python deps

## Troubleshooting
- If the game freezes, ensure Ollama is running; the engine sends prompts asynchronously and has fallbacks, but network timeouts may delay responses.
- If Ollama responses are not valid JSON, the engine will display the raw text as `commander_shout` and default to `ATTACK_PLAYER`.

## Next steps / roadmap
- Improve prompt to include limited tactical context (cover positions, choke points).
- Add unit tests for `find_path()` and LLM response parsing.
- Add configurable Ollama endpoint/port via environment variables or CLI flags.

If you'd like, I can add environment-based configuration and a stricter prompt template file next.
 
## Containerization (optional)
- A `Dockerfile` and `docker-compose.yml` are included to run the game inside a container and (optionally) run an Ollama service as a sidecar.
- The compose file uses `ollama/ollama:latest` as a placeholder image for the Ollama service — replace this with the actual Ollama image or run Ollama on the host and remove the `ollama` service.

To build and run both services with Compose:

```bash
docker compose build
docker compose up
```

Or run only the game container and point it to a host Ollama instance by setting `LOCAL_LLM_ENDPOINT`:

```bash
docker build -t ai-roguelike .
docker run --env LOCAL_LLM_ENDPOINT=http://host.docker.internal:11434/api/generate -it ai-roguelike
```

Note: packaging Ollama inside a container may require a licensed or official image; the compose file supplies a placeholder to make experimenting easier.

CI and pushing
----------------
The repository includes a GitHub Actions workflow at `.github/workflows/ci.yml` that runs tests on push and pull requests. To push these changes and create a PR:

```bash
git add .
git commit -m "Add LLM integration, tests, CI, and metrics UI"
git push origin your-branch-name
# then open a PR on GitHub from that branch into main
```

Ollama image notes
------------------
The `docker-compose.yml` uses `ollama/ollama:latest` as a placeholder. You have three options:

- Run Ollama on the host (recommended for development) and set `LOCAL_LLM_ENDPOINT` to `http://host.docker.internal:11434/api/generate` when running the `game` container.
- Replace the placeholder image with your official or licensed Ollama image in `docker-compose.yml`.
- Do not start the `ollama` service in compose and run Ollama manually on the host.

If you want, I can prepare a `Makefile` or a script to build and run with the correct host networking flags for your platform.