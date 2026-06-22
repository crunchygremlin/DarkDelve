"""Tests for the local Ollama player agent prompt and validation contract."""

import json

import pytest

from player_agent import PlayerAgent, PlayerDecision, VALID_ACTIONS


class FakeResponse:
    def __init__(self, response):
        self._response = response

    def raise_for_status(self):
        return None

    def json(self):
        return {"response": self._response}


def test_system_prompt_includes_survive_explore_baseline_and_json_schema():
    agent = PlayerAgent()

    prompt = agent.build_system_prompt()

    assert "Survive & Explore" in prompt
    assert "Return one JSON object and nothing else" in prompt
    assert '"format"' not in prompt


def test_persona_injection_uses_builtin_persona():
    agent = PlayerAgent(persona_name="Aggressive Stress-Tester")

    prompt = agent.build_system_prompt()

    assert "Aggressive Stress-Tester" in prompt
    assert "Seek combat" in prompt


def test_custom_testing_persona_modifier_is_appended():
    agent = PlayerAgent(testing_persona="Always probe stairs and inventory edges.")

    prompt = agent.build_system_prompt()

    assert "Additional testing persona modifier" in prompt
    assert "Always probe stairs and inventory edges" in prompt


def test_user_prompt_includes_frame_stats_and_five_turn_history():
    agent = PlayerAgent()
    history = [
        {"action": "w", "macro_goal": "Explore north", "telemetry_notes": "safe"},
        {"action": "d", "macro_goal": "Explore east", "telemetry_notes": ""},
        {"action": "s", "macro_goal": "Retreat", "telemetry_notes": "low hp"},
        {"action": "e", "macro_goal": "Wait", "telemetry_notes": "unclear"},
        {"action": "a", "macro_goal": "Explore west", "telemetry_notes": ""},
        {"action": "i", "macro_goal": "Inventory", "telemetry_notes": "old"},
    ]

    prompt = agent.build_user_prompt("##\n@.", {"hp": 3, "turn": 4}, history)

    assert "Current DarkDelve console frame" in prompt
    assert "##" in prompt
    assert "- hp: 3" in prompt
    assert "Explore west" in prompt
    assert "Explore north" not in prompt


def test_user_prompt_includes_active_instruction_text():
    agent = PlayerAgent()

    prompt = agent.build_user_prompt(
        "##",
        {"hp": 10},
        [],
        instruction_text="Setup instructions:\nExplore carefully.\n\nPush instructions:\nUse stairs.",
    )

    assert "Active playtest instructions" in prompt
    assert "Explore carefully." in prompt
    assert "Use stairs." in prompt


def test_request_payload_always_includes_json_format(monkeypatch):
    # Use a non-OpenRouter endpoint to test Ollama format
    agent = PlayerAgent(config={"endpoint": "http://localhost:11434"})
    calls = []
    
    def fake_post(url, **kwargs):
        calls.append((url, kwargs["json"], kwargs["timeout"]))
        # Ollama returns {"response": "the actual response text"}
        # FakeResponse.json() returns {"response": self._response}
        # So we pass just the inner response text
        return FakeResponse('{"macro_goal": "Explore", "reasoning": "Safe", "action": "e", "telemetry_notes": ""}')
    
    monkeypatch.setattr("player_agent.requests.post", fake_post)
    
    response = agent.request_ollama("system", "user")
    
    # The response field contains the actual JSON string
    assert response == '{"macro_goal": "Explore", "reasoning": "Safe", "action": "e", "telemetry_notes": ""}'
    assert calls[0][0].endswith("/api/generate")
    assert calls[0][1]["format"] == "json"
    assert calls[0][1]["model"] == agent.config.model


def test_parse_response_accepts_valid_schema():
    agent = PlayerAgent()
    raw = json.dumps(
        {
            "macro_goal": "Explore north",
            "reasoning": "North is clear",
            "action": "w",
            "telemetry_notes": "looking for stairs",
        }
    )

    decision = agent.parse_response(raw)

    assert decision.action == "w"
    assert decision.macro_goal == "Explore north"
    assert decision.issues == []
    assert decision.fallback_used is False


@pytest.mark.parametrize("action", sorted(VALID_ACTIONS))
def test_parse_response_accepts_all_allowed_actions(action):
    agent = PlayerAgent()
    raw = json.dumps(
        {
            "macro_goal": "Test",
            "reasoning": "Action is allowed",
            "action": action,
            "telemetry_notes": "",
        }
    )

    decision = agent.parse_response(raw)

    assert decision.action == action
    assert decision.fallback_used is False


def test_json_sanitization_strips_markdown_fence_and_trailing_text():
    agent = PlayerAgent()
    raw = 'prefix ```json\n{"macro_goal":"Explore","reasoning":"Clear","action":"d","telemetry_notes":"notes"}\n``` trailing'

    decision = agent.parse_response(raw)

    assert decision.action == "d"
    assert "stripped markdown JSON fence" in decision.issues
    assert "json parse failed" not in decision.issues


def test_json_sanitization_accepts_python_dict_literal():
    agent = PlayerAgent()
    raw = "{'macro_goal': 'Explore', 'reasoning': 'Clear', 'action': 's', 'telemetry_notes': 'notes'}"

    decision = agent.parse_response(raw)

    assert decision.action == "s"
    assert any(issue.startswith("json parse failed") for issue in decision.issues)


def test_invalid_action_falls_back_to_safe_action_and_logs_issue():
    agent = PlayerAgent()
    raw = json.dumps(
        {
            "macro_goal": "Bad action",
            "reasoning": "Model chose x",
            "action": "x",
            "telemetry_notes": "model was unsure",
        }
    )

    decision = agent.parse_response(raw)

    assert decision.action == "e"
    assert decision.fallback_used is True
    assert any("invalid action" in issue for issue in decision.issues)
    assert "invalid action" in decision.telemetry_notes


def test_missing_action_falls_back_and_records_missing_field():
    agent = PlayerAgent()
    raw = json.dumps({"macro_goal": "No action", "reasoning": "Missing field", "telemetry_notes": ""})

    decision = agent.parse_response(raw)

    assert decision.action == "e"
    assert decision.fallback_used is True
    assert any("missing response field: action" in issue for issue in decision.issues)


def test_malformed_json_falls_back_to_safe_action():
    agent = PlayerAgent()

    decision = agent.parse_response("not json at all")

    assert decision.action == "e"
    assert decision.fallback_used is True
    assert any("json parse failed" in issue for issue in decision.issues)


def test_record_turn_keeps_only_last_five_turns():
    agent = PlayerAgent()

    for index, action in enumerate(["w", "a", "s", "d", "e", "i", "w"]):
        agent.record_turn(
            PlayerDecision(
                macro_goal=f"goal {index}",
                reasoning="test",
                action=action,
                telemetry_notes="",
            )
        )

    assert [entry["action"] for entry in agent.history] == ["s", "d", "e", "i", "w"]
