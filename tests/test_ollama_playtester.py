"""Tests for console frame parsing and telemetry behavior."""

import json
from argparse import Namespace
from types import SimpleNamespace

from ollama_playtester import (
    ConsoleFrameParser,
    OllamaPlaytester,
    PlaytestConfig,
    TelemetryStore,
    apply_cli_overrides,
    extract_stats,
    load_config,
    strip_ansi,
)


def test_strip_ansi_removes_console_escape_sequences():
    text = "\033[H\033[2JHP 10/10\033[0m\n"

    assert strip_ansi(text) == "HP 10/10\n"


def test_console_frame_parser_extracts_frames_stats_and_remaining_buffer():
    parser = ConsoleFrameParser()
    frame_one = "\033[H\033[2J#####\n#@...\nHP 10/10  AC 2  Level 1  Depth 1  Turn 0\033[0m\n"
    frame_two_partial = "\033[H\033[2J#####\n#@..."

    frames, remaining = parser.parse_frames(frame_one + frame_two_partial)

    assert len(frames) == 1
    assert frames[0].rows == ("#####", "#@...", "HP 10/10  AC 2  Level 1  Depth 1  Turn 0")
    assert frames[0].stats["hp"] == 10
    assert frames[0].stats["max_hp"] == 10
    assert frames[0].stats["ac"] == 2
    assert frames[0].stats["level"] == 1
    assert frames[0].stats["depth"] == 1
    assert frames[0].stats["turn"] == 0
    assert remaining == frame_two_partial


def test_console_frame_parser_handles_multiple_complete_frames():
    parser = ConsoleFrameParser()
    first = "\033[H\033[2Jfirst\033[0m\n"
    second = "\033[H\033[2Jsecond\033[0m\n"

    frames, remaining = parser.parse_frames(first + second)

    assert [frame.frame for frame in frames] == ["first", "second"]
    assert remaining == ""


def test_extract_stats_returns_none_for_unknown_values():
    stats = extract_stats("HP ?/?  AC ?  Level ?  Depth ?  Turn ?  Gold ?  Nutrition ?/?")

    assert stats["hp"] is None
    assert stats["max_hp"] is None
    assert stats["ac"] is None
    assert stats["level"] is None
    assert stats["depth"] is None
    assert stats["turn"] is None
    assert stats["gold"] is None
    assert stats["nutrition"] is None
    assert stats["max_nutrition"] is None


def test_telemetry_store_appends_json_list(tmp_path):
    """TelemetryStore uses line-delimited JSON format, not a JSON list."""
    path = tmp_path / "playtest_telemetry.json"

    TelemetryStore.append(path, {"event_type": "turn", "turn_number": 1})
    TelemetryStore.append(path, {"event_type": "turn", "turn_number": 2})

    # Read as line-delimited JSON
    with path.open("r", encoding="utf-8") as handle:
        lines = handle.read().strip().splitlines()

    assert len(lines) == 2
    entry1 = json.loads(lines[0])
    entry2 = json.loads(lines[1])
    assert entry1 == {"event_type": "turn", "turn_number": 1}
    assert entry2 == {"event_type": "turn", "turn_number": 2}


def test_telemetry_store_appends_to_existing_file(tmp_path):
    """TelemetryStore appends line-delimited JSON to existing file."""
    path = tmp_path / "playtest_telemetry.json"
    # Write a single JSON object (not a list) - this is allowed
    path.write_text('{"event_type": "bad"}\n', encoding="utf-8")

    TelemetryStore.append(path, {"event_type": "turn"})

    # Read as line-delimited JSON
    with path.open("r", encoding="utf-8") as handle:
        lines = handle.read().strip().splitlines()

    assert len(lines) == 2
    entry1 = json.loads(lines[0])
    entry2 = json.loads(lines[1])
    assert entry1 == {"event_type": "bad"}
    assert entry2 == {"event_type": "turn"}


def test_playtest_config_loads_yaml_defaults_and_paths(tmp_path):
    config_path = tmp_path / "playtest_config.yaml"
    config_path.write_text(
        "endpoint: https://openrouter.ai/api/v1\n"
        "model: nvidia/nemotron-3-super-120b-a12b:free\n"
        "persona: Boundary Pushing Explorer\n"
        "testing_persona: probe edges\n"
        "max_turns: 7\n"
        "telemetry_path: playtest/custom_telemetry.json\n"
        "instruction_path: playtest/custom_instructions.json\n"
        "game_command:\n"
        "  - python\n"
        "  - darkdelve.py\n",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.endpoint == "https://openrouter.ai/api/v1"
    assert config.model == "nvidia/nemotron-3-super-120b-a12b:free"
    assert config.persona == "Boundary Pushing Explorer"
    assert config.testing_persona == "probe edges"
    assert config.max_turns == 7
    assert config.telemetry_path.name == "custom_telemetry.json"
    assert config.instruction_path.name == "custom_instructions.json"
    assert config.game_command == ["python", "darkdelve.py"]


def test_playtest_config_from_dict_ignores_unrelated_keys():
    config = PlaytestConfig.from_dict({"model": "test-model", "ignored": True})

    assert config.model == "test-model"
    assert not hasattr(config, "ignored")


def test_apply_cli_overrides_instruction_path(tmp_path):
    config = PlaytestConfig()
    args = Namespace(
        endpoint="",
        model="",
        persona="",
        testing_persona="",
        max_turns=None,
        telemetry="",
        instructions=str(tmp_path / "live_instructions.json"),
        game_command=None,
    )

    apply_cli_overrides(config, args)

    assert config.instruction_path == tmp_path / "live_instructions.json"


def test_apply_cli_overrides_keeps_existing_instruction_path_without_override(tmp_path):
    config = PlaytestConfig(instruction_path=tmp_path / "existing.json")
    args = SimpleNamespace(
        endpoint="",
        model="",
        persona="",
        testing_persona="",
        max_turns=None,
        telemetry="",
        instructions="",
        game_command=None,
    )

    apply_cli_overrides(config, args)

    assert config.instruction_path == tmp_path / "existing.json"


def test_apply_cli_overrides_instruction_path_with_relative_path():
    config = PlaytestConfig()
    args = SimpleNamespace(
        endpoint="",
        model="",
        persona="",
        testing_persona="",
        max_turns=None,
        telemetry="",
        instructions="playtest/custom_instructions.json",
        game_command=None,
    )

    apply_cli_overrides(config, args)

    assert config.instruction_path.name == "custom_instructions.json"
    assert config.instruction_path.parent.name == "playtest"


def test_ollama_playtester_accepts_custom_instruction_bus(tmp_path):
    from playtest.instruction_bus import InstructionBus

    bus = InstructionBus(tmp_path / "custom.json")
    playtester = OllamaPlaytester(instruction_bus=bus)

    assert playtester.instruction_bus is bus


def test_turn_entry_records_active_instructions():
    from ollama_playtester import ConsoleFrame
    from player_agent import PlayerDecision

    playtester = OllamaPlaytester()
    frame = ConsoleFrame(frame="frame", rows=("frame",), stats={"hp": 10})
    decision = PlayerDecision("Explore", "safe", "e", "notes", [], False)

    entry = playtester._turn_entry(1, frame, decision, "", "Setup instructions:\nExplore carefully.")

    assert entry["active_instructions"] == "Setup instructions:\nExplore carefully."


def test_load_config_uses_default_instruction_path_when_missing(tmp_path):
    config_path = tmp_path / "empty.yaml"
    config_path.write_text("", encoding="utf-8")

    config = load_config(config_path)

    assert config.instruction_path.name == "instructions.json"
    assert config.instruction_path.parent.name == "playtest"
