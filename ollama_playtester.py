"""Subprocess playtester that drives DarkDelve with an Ollama player agent."""

from __future__ import annotations

import argparse
import json
import os
import select
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import yaml

from player_agent import PlayerAgent, PlayerDecision, utc_now


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "playtest" / "playtest_config.yaml"
DEFAULT_TELEMETRY_PATH = PROJECT_ROOT / "playtest" / "playtest_telemetry.json"
FRAME_CLEAR = "\033[H\033[2J"
FRAME_END = "\033[0m"
ANSI_RE = __import__("re").compile(r"\033\[[0-?]*[ -/]*[@-~]")


@dataclass(slots=True)
class PlaytestConfig:
    """Runtime configuration for the Ollama-driven playtester."""

    game_command: List[str] = field(
        default_factory=lambda: [sys.executable, str(PROJECT_ROOT / "darkdelve.py")]
    )
    endpoint: str = "http://127.0.0.1:11434"
    model: str = "qwen2.5-coder:7b-instruct"
    persona: str = "Default"
    testing_persona: str = ""
    temperature: float = 0.7
    top_p: float = 0.9
    num_predict: int = 512
    timeout: float = 30.0
    retries: int = 2
    max_turns: Optional[int] = None
    telemetry_path: Path = DEFAULT_TELEMETRY_PATH

    @classmethod
    def from_dict(cls, data: Optional[Mapping[str, Any]]) -> "PlaytestConfig":
        """Build configuration from YAML data."""

        if not data:
            return cls()
        game_command = data.get("game_command", data.get("gameCommand"))
        telemetry_path = data.get("telemetry_path", data.get("telemetryPath"))
        kwargs: Dict[str, Any] = {}
        if game_command:
            kwargs["game_command"] = [str(part) for part in game_command]
        if telemetry_path:
            kwargs["telemetry_path"] = resolve_path(telemetry_path)
        allowed = {
            "endpoint",
            "model",
            "persona",
            "testing_persona",
            "temperature",
            "top_p",
            "num_predict",
            "timeout",
            "retries",
            "max_turns",
        }
        for key, value in data.items():
            if key in allowed and value is not None:
                kwargs[key] = value
        return cls(**kwargs)

    def to_agent_config(self) -> Dict[str, Any]:
        """Return the subset used by :class:`player_agent.OllamaConfig`."""

        return {
            "endpoint": self.endpoint,
            "model": self.model,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "num_predict": self.num_predict,
            "timeout": self.timeout,
            "retries": self.retries,
        }


@dataclass(slots=True)
class ConsoleFrame:
    """One ANSI-cleared console frame scraped from game stdout."""

    frame: str
    rows: Tuple[str, ...]
    stats: Dict[str, Any]


@dataclass(slots=True)
class PlaytestResult:
    """Summary returned after a playtester run."""

    status: str
    returncode: Optional[int]
    turns: int
    telemetry_entries: List[Dict[str, Any]] = field(default_factory=list)
    final_frame: Optional[ConsoleFrame] = None
    stderr_tail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the result for CLI output."""

        return {
            "status": self.status,
            "returncode": self.returncode,
            "turns": self.turns,
            "stderr_tail": self.stderr_tail,
            "final_frame": self.final_frame.frame if self.final_frame else None,
            "telemetry_entries": self.telemetry_entries,
        }


class ConsoleFrameParser:
    """Parse DarkDelve console frames and extract visible stats."""

    def parse_frames(self, buffer: str) -> tuple[List[ConsoleFrame], str]:
        """Return complete frames and the remaining partial stdout buffer."""

        if FRAME_CLEAR not in buffer:
            return [], buffer
        parts = buffer.split(FRAME_CLEAR)
        frames: List[ConsoleFrame] = []
        remaining = parts[0]
        for part in parts[1:]:
            if FRAME_END not in part:
                remaining = FRAME_CLEAR + part
                break
            frame_text, after = part.split(FRAME_END, 1)
            frame_text = strip_ansi(frame_text).rstrip("\n")
            rows = tuple(strip_ansi(line).rstrip() for line in frame_text.splitlines())
            frames.append(
                ConsoleFrame(
                    frame="\n".join(rows),
                    rows=rows,
                    stats=extract_stats(frame_text),
                )
            )
            remaining = after.lstrip("\n")
        return frames, remaining

    def parse_latest(self, buffer: str) -> tuple[Optional[ConsoleFrame], str]:
        """Parse all available frames and return only the latest complete frame."""

        frames, remaining = self.parse_frames(buffer)
        return (frames[-1] if frames else None), remaining


class TelemetryStore:
    """Append JSON telemetry entries to ``playtest/playtest_telemetry.json``."""

    @staticmethod
    def append(path: Path, entry: Mapping[str, Any]) -> None:
        """Atomically append one entry to the JSON telemetry list."""

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        entries: List[Dict[str, Any]] = []
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                content = handle.read().strip()
                if content:
                    loaded = json.loads(content)
                    if not isinstance(loaded, list):
                        raise ValueError(f"Telemetry file {path} must contain a JSON list")
                    entries = loaded
        entries.append(dict(entry))
        tmp_path = path.with_name(f".{path.name}.tmp")
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(entries, handle, indent=2, sort_keys=True)
            handle.write("\n")
        tmp_path.replace(path)


class OllamaPlaytester:
    """Launch DarkDelve, scrape console frames, and inject Ollama actions."""

    def __init__(
        self,
        config: Optional[PlaytestConfig] = None,
        agent: Optional[PlayerAgent] = None,
        frame_parser: Optional[ConsoleFrameParser] = None,
        telemetry_store: Optional[TelemetryStore] = None,
    ) -> None:
        self.config = config or PlaytestConfig()
        self.agent = agent or PlayerAgent(
            config=self.config.to_agent_config(),
            testing_persona=self.config.testing_persona,
            persona_name=self.config.persona,
        )
        self.frame_parser = frame_parser or ConsoleFrameParser()
        self.telemetry_store = telemetry_store or TelemetryStore()

    def launch(self) -> subprocess.Popen[str]:
        """Start the game process with piped stdin, stdout, and stderr."""

        command = self.config.game_command or [sys.executable, str(PROJECT_ROOT / "darkdelve.py")]
        return subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=str(PROJECT_ROOT),
        )

    def run(self) -> PlaytestResult:
        """Run the playtest loop until exit, crash, error, or max turns."""

        process = self.launch()
        stdout_buffer = ""
        stderr_chunks: List[str] = []
        telemetry_entries: List[Dict[str, Any]] = []
        final_frame: Optional[ConsoleFrame] = None
        turn_number = 0
        status = "running"
        error_message = ""
        returncode: Optional[int] = None

        try:
            while True:
                if self.config.max_turns is not None and turn_number >= self.config.max_turns:
                    status = "max_turns"
                    break
                if process.poll() is not None:
                    returncode = process.returncode
                    status = "exit" if returncode == 0 else "crash"
                    break

                chunk = process.stdout.read(1)
                if chunk:
                    stdout_buffer += chunk
                    frames, stdout_buffer = self.frame_parser.parse_frames(stdout_buffer)
                    if frames:
                        final_frame = frames[-1]
                        decision = self.agent.decide(
                            final_frame.frame,
                            final_frame.stats,
                            history=self.agent.history,
                        )
                        self._write_action(process, decision.action)
                        turn_number += 1
                        entry = self._turn_entry(
                            turn_number,
                            final_frame,
                            decision,
                            self._tail_text(stderr_chunks),
                        )
                        self.telemetry_store.append(self.config.telemetry_path, entry)
                        telemetry_entries.append(entry)
                    continue

                if process.poll() is not None:
                    returncode = process.returncode
                    status = "exit" if returncode == 0 else "crash"
                    break
                stderr_chunk = self._read_available(process.stderr)
                if stderr_chunk:
                    stderr_chunks.append(stderr_chunk)
                time.sleep(0.01)
        except Exception as exc:  # pragma: no cover - defensive path for real runs
            status = "error"
            error_message = str(exc)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:  # pragma: no cover - rare cleanup
                    process.kill()
                    process.wait()

            remaining_stdout = self._drain_available(process.stdout)
            if remaining_stdout:
                stdout_buffer += remaining_stdout
                frames, stdout_buffer = self.frame_parser.parse_frames(stdout_buffer)
                if frames:
                    final_frame = frames[-1]
            remaining_stderr = self._drain_available(process.stderr)
            if remaining_stderr:
                stderr_chunks.append(remaining_stderr)
            stderr_tail = self._tail_text(stderr_chunks)

            if status in {"crash", "error"}:
                crash_entry = self._event_entry(
                    "crash",
                    status,
                    process.returncode if process.poll() is not None else None,
                    final_frame,
                    stderr_tail,
                    error_message,
                )
                self.telemetry_store.append(self.config.telemetry_path, crash_entry)
                telemetry_entries.append(crash_entry)

        return PlaytestResult(
            status=status,
            returncode=returncode if returncode is not None else process.returncode,
            turns=turn_number,
            telemetry_entries=telemetry_entries,
            final_frame=final_frame,
            stderr_tail=stderr_tail if "stderr_tail" in locals() else self._tail_text(stderr_chunks),
        )

    def _write_action(self, process: subprocess.Popen[str], action: str) -> None:
        if process.stdin is None:
            raise RuntimeError("Game stdin is not available")
        process.stdin.write(action + "\n")
        process.stdin.flush()

    def _turn_entry(
        self,
        turn_number: int,
        frame: ConsoleFrame,
        decision: PlayerDecision,
        stderr_tail: str,
    ) -> Dict[str, Any]:
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
            "stderr_tail": stderr_tail,
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
        return {
            "event_type": event_type,
            "timestamp": utc_now(),
            "status": status,
            "returncode": returncode,
            "final_map": frame.frame if frame else "",
            "stderr_tail": stderr_tail,
            "error_message": error_message,
        }

    @staticmethod
    def _read_available(stream: Any) -> str:
        if stream is None or stream.closed:
            return ""
        ready, _, _ = select.select([stream], [], [], 0)
        if not ready:
            return ""
        return stream.read() or ""

    @staticmethod
    def _drain_available(stream: Any) -> str:
        chunks: List[str] = []
        while True:
            chunk = OllamaPlaytester._read_available(stream)
            if not chunk:
                break
            chunks.append(chunk)
        return "".join(chunks)

    @staticmethod
    def _tail_text(chunks: Sequence[str], max_chars: int = 4000) -> str:
        return "".join(chunks)[-max_chars:]


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from console text."""

    return ANSI_RE.sub("", text)


def extract_stats(frame_text: str) -> Dict[str, Any]:
    """Extract DarkDelve status values from a console frame."""

    text = strip_ansi(frame_text)
    stats: Dict[str, Any] = {
        "hp": None,
        "max_hp": None,
        "ac": None,
        "level": None,
        "depth": None,
        "turn": None,
        "gold": None,
        "nutrition": None,
        "max_nutrition": None,
        "raw_status": "",
    }
    status_line = ""
    for line in text.splitlines():
        if " HP " in f" {line} " or line.startswith("HP "):
            status_line = line
            break
    if not status_line:
        return stats

    patterns = {
        "hp": r"HP\s*(\d+|\?)/(\d+|\?)",
        "ac": r"AC\s*(\d+|\?)",
        "level": r"Level\s*(\d+|\?)",
        "depth": r"Depth\s*(\d+|\?)",
        "turn": r"Turn\s*(\d+|\?)",
        "gold": r"Gold\s*(\d+|\?)",
        "nutrition": r"Nutrition\s*(\d+|\?)/(\d+|\?)",
    }
    for key, pattern in patterns.items():
        match = re_search(pattern, status_line)
        if match:
            if key in {"hp", "nutrition"}:
                stats[key] = to_optional_int(match.group(1))
                stats[f"max_{key}"] = to_optional_int(match.group(2))
            else:
                stats[key] = to_optional_int(match.group(1))
    stats["raw_status"] = status_line.strip()
    return stats


def re_search(pattern: str, text: str):
    """Small wrapper so tests can import the module without name conflicts."""

    return __import__("re").search(pattern, text)


def to_optional_int(value: str) -> Optional[int]:
    """Convert ``?`` or invalid text to ``None``."""

    if value in {"", "?", None}:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def resolve_path(value: str | os.PathLike[str]) -> Path:
    """Resolve relative playtest paths against the project root."""

    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_config(path: str | os.PathLike[str] = DEFAULT_CONFIG_PATH) -> PlaytestConfig:
    """Load playtester configuration from YAML."""

    config_path = resolve_path(path) if not Path(path).is_absolute() else Path(path)
    if not config_path.exists():
        return PlaytestConfig()
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return PlaytestConfig.from_dict(data)


def apply_cli_overrides(config: PlaytestConfig, args: argparse.Namespace) -> PlaytestConfig:
    """Apply command-line overrides to a loaded config."""

    if args.endpoint:
        config.endpoint = args.endpoint
    if args.model:
        config.model = args.model
    if args.persona:
        config.persona = args.persona
    if args.testing_persona:
        config.testing_persona = args.testing_persona
    if args.max_turns is not None:
        config.max_turns = args.max_turns
    if args.telemetry:
        config.telemetry_path = resolve_path(args.telemetry)
    if args.game_command:
        config.game_command = args.game_command
    return config


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description="Drive DarkDelve with an Ollama player AI.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="YAML config path")
    parser.add_argument("--endpoint", help="Ollama base endpoint")
    parser.add_argument("--model", help="Ollama model name")
    parser.add_argument("--persona", choices=sorted(PlayerAgent.personas), help="Built-in persona")
    parser.add_argument("--testing-persona", help="Additional persona modifier string")
    parser.add_argument("--max-turns", type=int, help="Stop after this many player turns")
    parser.add_argument("--telemetry", help="Telemetry JSON path")
    parser.add_argument(
        "--game-command",
        nargs="+",
        help="Game command, e.g. python darkdelve.py",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point."""

    args = parse_args(argv)
    config = apply_cli_overrides(load_config(args.config), args)
    playtester = OllamaPlaytester(config)
    result = playtester.run()
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.status in {"exit", "max_turns"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
