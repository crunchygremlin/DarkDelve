"""Tests for DarkDelve's local instruction prompt helper."""

import json
from pathlib import Path

import darkdelve


def test_load_instruction_prompt_loads_dungeon_master_scoped_setup_and_push(tmp_path, monkeypatch):
    instruction_path = tmp_path / "instructions.json"
    instruction_path.write_text(
        json.dumps(
            {
                "enabled": True,
                "target": "dungeon_master",
                "setup": "Make encounters harsher.",
                "push": "Force a boss hint now.",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(darkdelve, "INSTRUCTION_PATH", instruction_path)

    prompt = darkdelve.load_instruction_prompt("dungeon_master")

    assert "Setup instructions:" in prompt
    assert "Make encounters harsher." in prompt
    assert "Push instructions:" in prompt
    assert "Force a boss hint now." in prompt


def test_load_instruction_prompt_respects_target_scope(tmp_path, monkeypatch):
    instruction_path = tmp_path / "instructions.json"
    instruction_path.write_text(
        json.dumps(
            {
                "enabled": True,
                "target": "player",
                "setup": "Player only",
                "push": "",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(darkdelve, "INSTRUCTION_PATH", instruction_path)

    assert darkdelve.load_instruction_prompt("dungeon_master") == ""
    assert darkdelve.load_instruction_prompt("player") == "Setup instructions:\nPlayer only"


def test_load_instruction_prompt_ignores_disabled_payload(tmp_path, monkeypatch):
    instruction_path = tmp_path / "instructions.json"
    instruction_path.write_text(
        json.dumps(
            {
                "enabled": False,
                "target": "all",
                "setup": "Ignored",
                "push": "Ignored",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(darkdelve, "INSTRUCTION_PATH", instruction_path)

    assert darkdelve.load_instruction_prompt("dungeon_master") == ""


def test_load_instruction_prompt_handles_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(darkdelve, "INSTRUCTION_PATH", tmp_path / "missing.json")

    assert darkdelve.load_instruction_prompt("dungeon_master") == ""
