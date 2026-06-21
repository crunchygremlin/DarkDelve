"""Tests for console frame parsing and telemetry behavior."""

import json

from ollama_playtester import (
    ConsoleFrameParser,
    PlaytestConfig,
    TelemetryStore,
    extract_stats,
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
    path = tmp_path / "playtest_telemetry.json"

    TelemetryStore.append(path, {"event_type": "turn", "turn_number": 1})
    TelemetryStore.append(path, {"event_type": "turn", "turn_number": 2})

    with path.open("r", encoding="utf-8") as handle:
        entries = json.load(handle)

    assert entries == [
        {"event_type": "turn", "turn_number": 1},
        {"event_type": "turn", "turn_number": 2},
    ]


def test_telemetry_store_rejects_non_list_existing_file(tmp_path):
    path = tmp_path / "playtest_telemetry.json"
    path.write_text('{"event_type": "bad"}', encoding="utf-8")

    try:
        TelemetryStore.append(path, {"event_type": "turn"})
    except ValueError as exc:
        assert "must contain a JSON list" in str(exc)
    else:  # pragma: no cover - pytest should raise
        raise AssertionError("ValueError was not raised")


def test_playtest_config_loads_yaml_defaults_and_paths(tmp_path):
    config_path = tmp_path / "playtest_config.yaml"
    config_path.write_text(
        "endpoint: http://localhost:11434\n"
        "model: qwen2.5-coder:7b-instruct\n"
        "persona: Boundary Pushing Explorer\n"
        "testing_persona: probe edges\n"
        "max_turns: 7\n"
        "telemetry_path: playtest/custom_telemetry.json\n"
        "game_command:\n"
        "  - python\n"
        "  - darkdelve.py\n",
        encoding="utf-8",
    )

    from ollama_playtester import load_config

    config = load_config(config_path)

    assert config.endpoint == "http://localhost:11434"
    assert config.model == "qwen2.5-coder:7b-instruct"
    assert config.persona == "Boundary Pushing Explorer"
    assert config.testing_persona == "probe edges"
    assert config.max_turns == 7
    assert config.telemetry_path.name == "custom_telemetry.json"
    assert config.game_command == ["python", "darkdelve.py"]


def test_playtest_config_from_dict_ignores_unrelated_keys():
    config = PlaytestConfig.from_dict({"model": "test-model", "ignored": True})

    assert config.model == "test-model"
    assert not hasattr(config, "ignored")
