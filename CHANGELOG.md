# Changelog

All notable changes to this project are documented in this file.

## Unreleased

### Added

- Added direct in-process local AI playtester integration through [`src/infrastructure/services/mcp_integration.py`](src/infrastructure/services/mcp_integration.py).
- Added `Game.process_action()` and action-aware `Game.main_loop()` support for non-blocking playtester-driven turns.
- Added textual frame extraction via `Game.render_frame_text()` for local Ollama player-agent prompts.
- Added `playtest.enabled` and `playtest.config_path` configuration in [`config/game.yaml`](config/game.yaml).
- Added playtester integration tests and action-level regression tests.
- Documented in-process playtester usage, contracts, and gotchas in the architecture and playtest documentation.
