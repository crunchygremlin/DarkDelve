"""Tests for the in-process MCP playtester integration."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from ollama_playtester import PlaytestConfig
from player_agent import PlayerDecision

from src.infrastructure.services.mcp_integration import MCPPlaytester


class FakeInstructionBus:
    """Instruction bus test double."""

    def get_prompt_text(self, target: str) -> str:
        return f"instructions for {target}"


class FakePlayerAgent:
    """Player agent test double that returns deterministic actions."""

    def __init__(self, actions: list[str] | None = None) -> None:
        self.actions = actions or ["d", "e"]
        self.history: list[dict] = []
        self.decisions: list[PlayerDecision] = []

    def decide(
        self,
        map_text: str,
        stats: dict,
        history: list[dict] | None = None,
        instruction_text: str = "",
    ) -> PlayerDecision:
        action = self.actions[len(self.decisions) % len(self.actions)]
        decision = PlayerDecision(
            macro_goal="test exploration",
            reasoning="deterministic test action",
            action=action,
            telemetry_notes="test",
        )
        self.decisions.append(decision)
        self.history.append(decision.to_history_entry())
        return decision


class FakeGame:
    """Minimal game object for testing the playtester loop contract."""

    def __init__(self) -> None:
        self.running = True
        self.player = SimpleNamespace(is_alive=True)
        self.initialize_calls = 0
        self.actions: list[tuple[str, bool, str | None]] = []
        self.frames: list[str] = []

    def initialize(self) -> None:
        self.initialize_calls += 1

    def render_frame_text(self) -> str:
        frame = "frame"
        self.frames.append(frame)
        return frame

    def main_loop(
        self,
        action: str,
        render_to_stdout: bool = True,
        frame_text: str | None = None,
    ) -> None:
        self.actions.append((action, render_to_stdout, frame_text))


def _config(tmp_path: Path) -> PlaytestConfig:
    return PlaytestConfig(
        max_turns=2,
        telemetry_path=tmp_path / "playtest_telemetry.json",
        instruction_path=tmp_path / "instructions.json",
    )


def test_mcp_playtester_drives_fake_game_without_human_input(tmp_path: Path):
    game = FakeGame()
    agent = FakePlayerAgent(actions=["d", "e"])
    config = _config(tmp_path)

    result = MCPPlaytester(
        config=config,
        game=game,
        agent=agent,
        instruction_bus=FakeInstructionBus(),
        auto_initialize=False,
    ).run()

    assert result.status == "max_turns"
    assert result.turns == 2
    assert result.final_frame.frame == "frame"
    assert game.initialize_calls == 0
    assert game.actions == [("d", False, "frame"), ("e", False, "frame")]
    assert [decision.action for decision in agent.decisions] == ["d", "e"]
    assert len(result.telemetry_entries) == 2
    assert result.telemetry_entries[0]["event_type"] == "turn"
    assert result.telemetry_entries[0]["active_instructions"] == "instructions for player"
    assert result.telemetry_entries[1]["action"] == "e"

    telemetry_path = config.telemetry_path
    assert telemetry_path.exists()
    # Telemetry is line-delimited JSON (one object per line)
    with telemetry_path.open("r", encoding="utf-8") as handle:
        telemetry_entries = [json.loads(line) for line in handle if line.strip()]
    assert len(telemetry_entries) == 2
    assert telemetry_entries[0]["action"] == "d"


def test_mcp_playtester_can_initialize_game(tmp_path: Path):
    game = FakeGame()
    agent = FakePlayerAgent(actions=["e"])
    config = _config(tmp_path)

    result = MCPPlaytester(
        config=config,
        game=game,
        agent=agent,
        instruction_bus=FakeInstructionBus(),
        auto_initialize=True,
    ).run()

    assert result.status == "max_turns"
    assert game.initialize_calls == 1
