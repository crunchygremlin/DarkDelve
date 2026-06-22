"""Tests for the file-based playtest instruction bus."""

import json

from playtest.instruction_bus import (
    InstructionBus,
    PlaytestInstructions,
    format_instruction_prompt,
    target_matches,
)


def write_instructions(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_instruction_bus_loads_setup_and_push(tmp_path):
    path = tmp_path / "instructions.json"
    write_instructions(
        path,
        {
            "enabled": True,
            "target": "player",
            "setup": "Explore carefully.",
            "push": "Try stairs next.",
        },
    )

    instructions = InstructionBus(path).load()

    assert instructions.enabled is True
    assert instructions.target == "player"
    assert instructions.setup == "Explore carefully."
    assert instructions.push == "Try stairs next."


def test_instruction_bus_target_scoping(tmp_path):
    path = tmp_path / "instructions.json"
    write_instructions(path, {"enabled": True, "target": "player", "setup": "player only", "push": ""})
    bus = InstructionBus(path)

    assert bus.is_enabled_for("player") is True
    assert bus.is_enabled_for("dungeon_master") is False
    assert bus.get_prompt_text("player") == "Setup instructions:\nplayer only"
    assert bus.get_prompt_text("dungeon_master") == ""


def test_instruction_bus_all_target_matches_game_and_player(tmp_path):
    path = tmp_path / "instructions.json"
    write_instructions(path, {"enabled": True, "target": "all", "setup": "global", "push": "now"})
    bus = InstructionBus(path)

    assert bus.get_prompt_text("player") == "Setup instructions:\nglobal\n\nPush instructions:\nnow"
    assert bus.get_prompt_text("dungeon_master") == "Setup instructions:\nglobal\n\nPush instructions:\nnow"
    assert target_matches("dm", "dungeon_master") is True
    assert target_matches("commander", "player") is False


def test_instruction_bus_disabled_payload_returns_empty_prompt(tmp_path):
    path = tmp_path / "instructions.json"
    write_instructions(path, {"enabled": False, "target": "all", "setup": "ignored", "push": "ignored"})

    assert InstructionBus(path).get_prompt_text("player") == ""


def test_instruction_bus_clear_push_preserves_setup(tmp_path):
    path = tmp_path / "instructions.json"
    write_instructions(path, {"enabled": True, "target": "all", "setup": "persist", "push": "temporary"})

    bus = InstructionBus(path)
    bus.clear_push()

    assert bus.load().setup == "persist"
    assert bus.load().push == ""


def test_format_instruction_prompt_skips_empty_sections():
    assert format_instruction_prompt("setup", "") == "Setup instructions:\nsetup"
    assert format_instruction_prompt("", "push") == "Push instructions:\npush"
    assert format_instruction_prompt("", "") == ""
