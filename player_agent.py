"""Local Ollama player agent for DarkDelve playtesting.

The module owns the prompt contract between the console playtester and Ollama.
Every request to ``/api/generate`` includes ``format: "json"`` and the response is
validated against the playtester action schema before anything is injected into
the game process.
"""

from __future__ import annotations

import ast
import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Sequence

import requests


VALID_ACTIONS = ("w", "a", "s", "d", "e", "i")
RESPONSE_FIELDS = ("macro_goal", "reasoning", "action", "telemetry_notes")
DEFAULT_ENDPOINT = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5-coder:7b-instruct"
SAFE_FALLBACK_ACTION = "e"


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp for telemetry records."""

    return datetime.now(timezone.utc).isoformat()


SURVIVE_EXPLORE_BASELINE = """
DarkDelve Ollama Player AI: Survive & Explore.

You are controlling a traditional roguelike character through the console. Your
primary goals are to survive, explore unknown areas, gather useful information,
and keep the playtest moving. Prefer actions that preserve health when danger is
unclear. Use the visible ASCII frame and stats to decide the next single action.

Allowed actions:
- w = move up or attack upward
- a = move left or attack left
- s = move down or attack down
- d = move right or attack right
- e = wait one turn
- i = open or close inventory

Never output multiple actions. Never output control characters. Do not ask for
clarification; choose the safest useful action from the current frame.
""".strip()


RESPONSE_SCHEMA_INSTRUCTIONS = """
Return one JSON object and nothing else. The object must match this schema:

{
  "macro_goal": "string",
  "reasoning": "string",
  "action": "w|a|s|d|e|i",
  "telemetry_notes": "string"
}

If you are unsure, set ``action`` to ``e`` for a safe wait action and explain the
uncertainty in ``telemetry_notes``.
""".strip()


@dataclass(slots=True)
class OllamaConfig:
    """Configuration for Ollama ``/api/generate`` calls."""

    endpoint: str = DEFAULT_ENDPOINT
    model: str = DEFAULT_MODEL
    temperature: float = 0.7
    top_p: float = 0.9
    num_predict: int = 512
    timeout: float = 30.0
    retries: int = 2
    safe_action: str = SAFE_FALLBACK_ACTION

    def __post_init__(self) -> None:
        self.endpoint = self.endpoint.rstrip("/")
        self.temperature = float(self.temperature)
        self.top_p = float(self.top_p)
        self.num_predict = int(self.num_predict)
        self.timeout = float(self.timeout)
        self.retries = int(self.retries)
        if self.safe_action not in VALID_ACTIONS:
            self.safe_action = SAFE_FALLBACK_ACTION

    @classmethod
    def from_dict(cls, data: Optional[Mapping[str, Any]]) -> "OllamaConfig":
        """Build config from a mapping, ignoring unrelated keys."""

        if not data:
            return cls()
        allowed = {
            "endpoint",
            "model",
            "temperature",
            "top_p",
            "num_predict",
            "timeout",
            "retries",
            "safe_action",
        }
        return cls(**{key: value for key, value in data.items() if key in allowed})

    def generate_url(self) -> str:
        """Return the Ollama generate endpoint."""

        if self.endpoint.endswith("/api/generate"):
            return self.endpoint
        return f"{self.endpoint}/api/generate"


@dataclass(slots=True)
class PlayerDecision:
    """Validated decision returned by the player agent."""

    macro_goal: str
    reasoning: str
    action: str
    telemetry_notes: str
    raw_response: str = ""
    issues: List[str] = field(default_factory=list)
    fallback_used: bool = False
    timestamp: str = field(default_factory=utc_now)

    def to_history_entry(self) -> Dict[str, Any]:
        """Convert the decision to a compact five-turn history entry."""

        return {
            "timestamp": self.timestamp,
            "macro_goal": self.macro_goal,
            "action": self.action,
            "telemetry_notes": self.telemetry_notes,
            "fallback_used": self.fallback_used,
        }


class PlayerAgent:
    """Build prompts, call Ollama, and validate player decisions."""

    personas: Dict[str, str] = {
        "Default": (
            "You are a cautious survival-focused playtester. Prioritize staying "
            "alive, learning the map, and avoiding unnecessary risk."
        ),
        "Aggressive Stress-Tester": (
            "You are an aggressive stress-tester. Seek combat, risky exploration, "
            "and edge cases that may expose balance or crash bugs. Still avoid "
            "obviously suicidal actions when the frame gives no useful target."
        ),
        "Boundary Pushing Explorer": (
            "You are a boundary pushing explorer. Probe map edges, unusual item "
            "placements, stairs, inventory interactions, and repeated action "
            "patterns that could reveal boundary or state bugs."
        ),
    }

    def __init__(
        self,
        config: Optional[OllamaConfig | Mapping[str, Any]] = None,
        testing_persona: Optional[str] = None,
        persona_name: str = "Default",
    ) -> None:
        if isinstance(config, Mapping):
            config = OllamaConfig.from_dict(config)
        self.config = config or OllamaConfig()
        self.testing_persona = testing_persona or ""
        self.persona_name = persona_name or "Default"
        self.history: List[Dict[str, Any]] = []

    def build_system_prompt(self) -> str:
        """Construct the system prompt with baseline, persona, and schema rules."""

        persona = self.personas.get(self.persona_name, self.persona_name)
        sections = [
            SURVIVE_EXPLORE_BASELINE,
            "Testing persona:",
            f"{self.persona_name}: {persona}",
        ]
        if self.testing_persona and self.testing_persona not in persona:
            sections.extend(
                [
                    "Additional testing persona modifier:",
                    self.testing_persona,
                ]
            )
        sections.append(RESPONSE_SCHEMA_INSTRUCTIONS)
        return "\n\n".join(section.strip() for section in sections if section.strip())

    def build_user_prompt(
        self,
        map_text: str,
        stats: Optional[Mapping[str, Any]] = None,
        history: Optional[Sequence[Mapping[str, Any]]] = None,
    ) -> str:
        """Construct the per-turn user prompt from the current frame."""

        stats = stats or {}
        history = list(history or self.history)[-5:]
        return "\n\n".join(
            [
                "Current DarkDelve console frame:",
                map_text or "<empty frame>",
                "Current stats:",
                self._format_stats(stats),
                "Recent 5-turn history:",
                self._format_history(history),
                "Choose exactly one action from w, a, s, d, e, or i.",
            ]
        )

    def build_payload(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Build the exact Ollama ``/api/generate`` payload."""

        return {
            "model": self.config.model,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "format": "json",
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "num_predict": self.config.num_predict,
        }

    def request_ollama(self, system_prompt: str, user_prompt: str) -> str:
        """Call Ollama and return the raw model response text."""

        payload = self.build_payload(system_prompt, user_prompt)
        last_error: Optional[Exception] = None
        attempts = max(1, self.config.retries + 1)
        for attempt in range(attempts):
            try:
                response = requests.post(
                    self.config.generate_url(),
                    json=payload,
                    timeout=self.config.timeout,
                )
                response.raise_for_status()
                return str(response.json().get("response", "")).strip()
            except Exception as exc:  # pragma: no cover - exercised by integration runs
                last_error = exc
                if attempt >= attempts - 1:
                    break
                time.sleep(min(2.0, 0.5 * (attempt + 1)))
        raise RuntimeError(f"Ollama generate request failed: {last_error}")

    def decide(
        self,
        map_text: str,
        stats: Optional[Mapping[str, Any]] = None,
        history: Optional[Sequence[Mapping[str, Any]]] = None,
    ) -> PlayerDecision:
        """Request, parse, validate, and record one player decision."""

        active_history = list(history if history is not None else self.history)[-5:]
        system_prompt = self.build_system_prompt()
        user_prompt = self.build_user_prompt(map_text, stats, active_history)
        raw_response = self.request_ollama(system_prompt, user_prompt)
        decision = self.parse_response(raw_response, active_history)
        self.record_turn(decision)
        return decision

    def parse_response(
        self,
        raw_response: str,
        history: Optional[Sequence[Mapping[str, Any]]] = None,
    ) -> PlayerDecision:
        """Sanitize, validate, and normalize a model response."""

        del history  # Kept for API symmetry with decide().
        data, issues = self.sanitize_json_response(raw_response)
        normalized, validation_issues = self.validate_response(data)
        issues.extend(validation_issues)
        fallback_used = any(
            "fallback" in issue.lower() or "falling back" in issue.lower()
            for issue in issues
        )
        telemetry_notes = normalized["telemetry_notes"]
        if issues:
            telemetry_notes = append_note(telemetry_notes, "; ".join(issues))
        return PlayerDecision(
            macro_goal=normalized["macro_goal"],
            reasoning=normalized["reasoning"],
            action=normalized["action"],
            telemetry_notes=telemetry_notes,
            raw_response=raw_response,
            issues=issues,
            fallback_used=fallback_used,
        )

    def sanitize_json_response(self, raw_response: str) -> tuple[Dict[str, Any], List[str]]:
        """Extract a JSON object where possible and report sanitization issues."""

        issues: List[str] = []
        text = (raw_response or "").strip()
        if not text:
            return {}, ["empty Ollama response"]

        fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
        if fenced:
            text = fenced.group(1).strip()
            issues.append("stripped markdown JSON fence")

        try:
            parsed: Any = json.loads(text)
        except json.JSONDecodeError as exc:
            issues.append(f"json parse failed: {exc.msg}")
            extracted = self._extract_json_object(text)
            parsed = None
            if extracted:
                try:
                    parsed = json.loads(extracted)
                except json.JSONDecodeError:
                    parsed = None
            if parsed is None:
                try:
                    parsed = ast.literal_eval(text)
                except (SyntaxError, ValueError):
                    parsed = None
            if isinstance(parsed, str):
                try:
                    parsed = json.loads(parsed)
                except json.JSONDecodeError:
                    parsed = None

        if not isinstance(parsed, dict):
            issues.append("response was not a JSON object; using empty object")
            return {}, issues
        return parsed, issues

    def validate_response(self, data: Mapping[str, Any]) -> tuple[Dict[str, str], List[str]]:
        """Validate the expected response schema and fallback on invalid actions."""

        issues: List[str] = []
        normalized: Dict[str, str] = {}
        if not isinstance(data, Mapping):
            issues.append("response payload was not an object; using empty object")
            data = {}

        for field_name in RESPONSE_FIELDS:
            value = data.get(field_name)
            if value is None:
                issues.append(f"missing response field: {field_name}")
                value = ""
            if not isinstance(value, str):
                issues.append(
                    f"response field {field_name} was {type(value).__name__}; converted to string"
                )
                value = str(value)
            normalized[field_name] = value.strip()

        action = normalized["action"].lower()
        if action not in VALID_ACTIONS:
            issues.append(
                f"invalid action {normalized['action']!r}; falling back to "
                f"{self.config.safe_action}"
            )
            action = self.config.safe_action
        normalized["action"] = action
        return normalized, issues

    def record_turn(self, decision: PlayerDecision) -> None:
        """Append a decision to the five-turn history buffer."""

        self.history.append(decision.to_history_entry())
        self.history = self.history[-5:]

    def _format_stats(self, stats: Mapping[str, Any]) -> str:
        if not stats:
            return "<no stats extracted>"
        return "\n".join(f"- {key}: {value}" for key, value in sorted(stats.items()))

    def _format_history(self, history: Sequence[Mapping[str, Any]]) -> str:
        if not history:
            return "None"
        lines = []
        for index, entry in enumerate(history[-5:], start=1):
            action = entry.get("action", "?")
            goal = entry.get("macro_goal", "")
            notes = entry.get("telemetry_notes", "")
            fallback = " fallback" if entry.get("fallback_used") else ""
            lines.append(f"{index}. action={action}, macro_goal={goal}, notes={notes}{fallback}")
        return "\n".join(lines)

    def _extract_json_object(self, text: str) -> Optional[str]:
        start = text.find("{")
        if start == -1:
            return None
        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(text)):
            char = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start : index + 1]
        return None


def append_note(base: str, note: str) -> str:
    """Append a telemetry note without duplicating identical text."""

    if not note:
        return base
    if not base:
        return note
    if note in base:
        return base
    return f"{base}; {note}"
