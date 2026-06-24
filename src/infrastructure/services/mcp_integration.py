"""Direct library integration for DarkDelve's local AI playtester."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import traceback

from ollama_playtester import (
    ConsoleFrame,
    PlaytestConfig,
    TelemetryStore,
    extract_stats,
    load_config,
)
from player_agent import PlayerAgent, PlayerDecision, utc_now
from playtest.instruction_bus import InstructionBus


@dataclass(slots=True)
class MCPPlaytestResult:
    """Summary returned after an in-process playtest run."""

    status: str
    turns: int
    telemetry_entries: List[Dict[str, Any]] = field(default_factory=list)
    final_frame: Optional[ConsoleFrame] = None
    stderr_tail: str = ""
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the result for CLI output."""

        return {
            "status": self.status,
            "turns": self.turns,
            "stderr_tail": self.stderr_tail,
            "error_message": self.error_message,
            "final_frame": self.final_frame.frame if self.final_frame else None,
            "telemetry_entries": self.telemetry_entries,
        }


class MCPPlaytester:
    """Drive an in-process [`Game`](darkdelve.py:1774) with an Ollama player agent."""

    def __init__(
        self,
        config: Optional[PlaytestConfig] = None,
        config_path: Optional[str | Path] = None,
        game: Any = None,
        agent: Optional[PlayerAgent] = None,
        telemetry_store: Optional[TelemetryStore] = None,
        instruction_bus: Optional[InstructionBus] = None,
        auto_initialize: bool = True,
        render_to_stdout: bool = True,
    ) -> None:
        """Create a library playtester.

        Args:
            config: Preloaded playtest configuration.
            config_path: YAML path used when ``config`` is not provided.
            game: Optional prebuilt game instance. The caller owns initialization
                when ``auto_initialize`` is false.
            agent: Optional prebuilt player agent.
            telemetry_store: Optional telemetry writer.
            instruction_bus: Optional instruction bus.
            auto_initialize: Whether ``run()`` should call ``game.initialize()``.
            render_to_stdout: Whether to render the game to stdout (default True, use --hideui to disable).
        """

        self.config = config or (load_config(str(config_path)) if config_path else load_config())
        if game is None:
            from darkdelve import Game
            self.game = Game()
        else:
            self.game = game
        self.agent = agent or PlayerAgent(
            config=self.config.to_agent_config(),
            testing_persona=self.config.testing_persona,
            persona_name=self.config.persona,
        )
        self.telemetry_store = telemetry_store or TelemetryStore()
        self.instruction_bus = instruction_bus or InstructionBus(self.config.instruction_path)
        self.auto_initialize = auto_initialize
        self.render_to_stdout = render_to_stdout

    def run(self) -> MCPPlaytestResult:
        """Run the playtest loop until exit, crash, error, or max turns."""

        if self.auto_initialize:
            self.game.initialize()

        telemetry_entries: List[Dict[str, Any]] = []
        final_frame: Optional[ConsoleFrame] = None
        turn_number = 0
        status = "running"
        error_message = ""
        stderr_tail = ""

        try:
            while self._should_continue(turn_number):
                frame_text = self.game.render_frame_text()
                stats = extract_stats(frame_text)
                final_frame = ConsoleFrame(
                    frame=frame_text,
                    rows=tuple(frame_text.splitlines()),
                    stats=stats,
                )

                active_instructions = self.instruction_bus.get_prompt_text("player")
                decision = self.agent.decide(
                    frame_text,
                    stats,
                    history=self.agent.history,
                    instruction_text=active_instructions,
                )
                self.game.main_loop(
                    action=decision.action,
                    render_to_stdout=self.render_to_stdout,
                    frame_text=frame_text,
                )

                turn_number += 1
                entry = self._turn_entry(turn_number, final_frame, decision, active_instructions)
                self.telemetry_store.append(self.config.telemetry_path, entry)
                telemetry_entries.append(entry)

            status = self._final_status(turn_number)

        except Exception as exc:  # pragma: no cover - exercised by integration runs
            status = "error"
            # Include full traceback with line numbers for debugging
            error_message = f"{str(exc)}\n\nTraceback:\n{traceback.format_exc()}"

        finally:
            if status in {"crash", "error"}:
                crash_entry = self._event_entry(
                    "crash" if status == "crash" else "error",
                    status,
                    None,
                    final_frame,
                    stderr_tail,
                    error_message,
                )
                self.telemetry_store.append(self.config.telemetry_path, crash_entry)
                telemetry_entries.append(crash_entry)

        return MCPPlaytestResult(
            status=status,
            turns=turn_number,
            telemetry_entries=telemetry_entries,
            final_frame=final_frame,
            stderr_tail=stderr_tail,
            error_message=error_message,
        )

    def _should_continue(self, turn_number: int) -> bool:
        """Return whether another player turn should be processed."""

        if self.config.max_turns is not None and turn_number >= self.config.max_turns:
            return False
        if not getattr(self.game, "running", False):
            return False
        player = getattr(self.game, "player", None)
        return player is not None and getattr(player, "is_alive", False)

    def _final_status(self, turn_number: int) -> str:
        """Classify the final run status after the loop exits."""

        if self.config.max_turns is not None and turn_number >= self.config.max_turns:
            return "max_turns"
        if not getattr(self.game, "running", False):
            player = getattr(self.game, "player", None)
            if player is None or not getattr(player, "is_alive", False):
                return "crash"
            return "exit"
        return "exit"

    def _turn_entry(
        self,
        turn_number: int,
        frame: ConsoleFrame,
        decision: PlayerDecision,
        active_instructions: str,
    ) -> Dict[str, Any]:
        """Build one telemetry entry for a player turn."""

        return {
            "event_type": "turn",
            "timestamp": utc_now(),
            "turn_number": turn_number,
            "stats": frame.stats,
            "action": decision.action,
            "macro_goal": decision.macro_goal,
            "reasoning": decision.reasoning,
            "telemetry_notes": decision.telemetry_notes,
            "issues": decision.issues,
            "fallback_used": decision.fallback_used,
            "history": list(self.agent.history),
            "frame": frame.frame,
            "active_instructions": active_instructions,
        }

    def _event_entry(
        self,
        event_type: str,
        status: str,
        returncode: Optional[int],
        frame: Optional[ConsoleFrame],
        stderr_tail: str,
        error_message: str = "",
    ) -> Dict[str, Any]:
        """Build a crash or error telemetry entry."""

        return {
            "event_type": event_type,
            "timestamp": utc_now(),
            "status": status,
            "returncode": returncode,
            "final_map": frame.frame if frame else "",
            "stderr_tail": stderr_tail,
            "error_message": error_message,
        }
