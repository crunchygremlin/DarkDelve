"""File-based instruction bus for DarkDelve playtesting.

The bus lets an external operator inject persistent setup instructions and live
push instructions into LLM prompts without changing core game code. It is used by
both the local Player AI and the Dungeon Master/content LLM prompts.

Expected JSON shape:

```json
{
  "enabled": true,
  "target": "all",
  "setup": "Persistent guidance for the LLM.",
  "push": "Live instruction for the current playtest session."
}
```

`target` may be `all`, `player`, `game`, `dungeon_master`, `dm`, or `commander`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional


DEFAULT_INSTRUCTION_PATH = Path(__file__).resolve().parents[1] / "playtest" / "instructions.json"
TARGET_ALIASES = {
    "all": "all",
    "player": "player",
    "game": "game",
    "dungeon_master": "dungeon_master",
    "dm": "dungeon_master",
    "commander": "commander",
}


@dataclass(slots=True)
class PlaytestInstructions:
    """Decoded instruction payload from the communication file."""

    enabled: bool = True
    target: str = "all"
    setup: str = ""
    push: str = ""

    @classmethod
    def from_mapping(cls, data: Optional[Mapping[str, Any]]) -> "PlaytestInstructions":
        """Build instructions from a mapping, ignoring unknown keys."""

        if not data:
            return cls()
        return cls(
            enabled=bool(data.get("enabled", True)),
            target=str(data.get("target", "all") or "all"),
            setup=str(data.get("setup", "") or ""),
            push=str(data.get("push", "") or ""),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the instruction payload."""

        return {
            "enabled": self.enabled,
            "target": self.target,
            "setup": self.setup,
            "push": self.push,
        }


@dataclass(slots=True)
class InstructionBus:
    """Load and format playtest instructions from a JSON file."""

    path: Path = DEFAULT_INSTRUCTION_PATH
    default_target: str = "all"

    def load(self) -> PlaytestInstructions:
        """Load the current instruction payload from disk."""

        if not self.path.exists():
            return PlaytestInstructions()
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                return PlaytestInstructions.from_mapping(json.load(handle))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return PlaytestInstructions(enabled=False)

    def is_enabled_for(self, target: Optional[str] = None) -> bool:
        """Return whether instructions are enabled for the requested target."""

        instructions = self.load()
        if not instructions.enabled:
            return False
        return target_matches(instructions.target, target or self.default_target)

    def get_setup(self, target: Optional[str] = None) -> str:
        """Return setup instructions for the requested target."""

        instructions = self.load()
        if not self._is_payload_enabled_for(instructions, target):
            return ""
        return instructions.setup.strip()

    def get_push(self, target: Optional[str] = None) -> str:
        """Return live push instructions for the requested target."""

        instructions = self.load()
        if not self._is_payload_enabled_for(instructions, target):
            return ""
        return instructions.push.strip()

    def get_prompt_text(self, target: Optional[str] = None) -> str:
        """Return formatted setup and push text for an LLM prompt."""

        instructions = self.load()
        if not self._is_payload_enabled_for(instructions, target):
            return ""
        return format_instruction_prompt(instructions.setup.strip(), instructions.push.strip())

    def clear_push(self) -> None:
        """Clear the live push section while preserving setup and target."""

        instructions = self.load()
        instructions.push = ""
        self.save(instructions)

    def save(self, instructions: PlaytestInstructions) -> None:
        """Write an instruction payload atomically."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_name(f".{self.path.name}.tmp")
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(instructions.to_dict(), handle, indent=2, sort_keys=True)
            handle.write("\n")
        tmp_path.replace(self.path)

    def _is_payload_enabled_for(
        self,
        instructions: PlaytestInstructions,
        target: Optional[str],
    ) -> bool:
        if not instructions.enabled:
            return False
        return target_matches(instructions.target, target or self.default_target)


def target_matches(source_target: str, requested_target: str) -> bool:
    """Return whether a source target includes the requested target."""

    source = TARGET_ALIASES.get(source_target.lower(), source_target.lower())
    requested = TARGET_ALIASES.get(requested_target.lower(), requested_target.lower())
    return source == "all" or source == requested


def format_instruction_prompt(setup: str = "", push: str = "") -> str:
    """Format setup and push instructions for injection into an LLM prompt."""

    sections = []
    if setup:
        sections.append(f"Setup instructions:\n{setup.strip()}")
    if push:
        sections.append(f"Push instructions:\n{push.strip()}")
    if not sections:
        return ""
    return "\n\n".join(sections)
