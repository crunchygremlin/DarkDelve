"""Context manager for LLM calls to maximize effectiveness."""

from typing import List, Dict
from src.domain.value_objects.llm_logging import (
    ContextWindowDiagnostics,
    estimate_tokens,
)

__all__ = ["ContextManager"]


class ContextManager:
    """Manages context window for LLM calls to maximize effectiveness."""

    def __init__(self, max_tokens: int = 8192, system_prompt: str = ""):
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.conversation_history: List[Dict[str, str]] = []
        self._system_tokens = estimate_tokens(system_prompt)

    def set_system_prompt(self, prompt: str):
        """Set or update the system prompt."""
        self.system_prompt = prompt
        self._system_tokens = estimate_tokens(prompt)

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.conversation_history.append({"role": role, "content": content})

    def get_context_usage(self) -> ContextWindowDiagnostics:
        """Get current context usage."""
        diag = ContextWindowDiagnostics(max_context_tokens=self.max_tokens)
        diag.system_prompt_tokens = self._system_tokens
        history_text = " ".join(m["content"] for m in self.conversation_history)
        diag.conversation_history_tokens = estimate_tokens(history_text)
        diag.calculate_headroom()
        return diag

    def trim_history(self, target_tokens: int = None):
        """Trim conversation history to fit within target tokens."""
        if target_tokens is None:
            target_tokens = int(self.max_tokens * 0.5)
        while self.conversation_history:
            history_text = " ".join(m["content"] for m in self.conversation_history)
            if estimate_tokens(history_text) <= target_tokens:
                break
            self.conversation_history.pop(0)

    def build_prompt(self, user_message: str) -> str:
        """Build a full prompt with system + history + user message."""
        parts = [self.system_prompt]
        for msg in self.conversation_history[-10:]:  # last 10 messages
            parts.append(f"{msg['role']}: {msg['content']}")
        parts.append(f"user: {user_message}")
        return "\n\n".join(parts)

    def can_fit(self, user_message: str, expected_response_tokens: int = 500) -> bool:
        """Check if we can fit the user message and expected response."""
        prompt = self.build_prompt(user_message)
        total = estimate_tokens(prompt) + expected_response_tokens
        return total <= self.max_tokens

    def get_optimal_history_length(self) -> int:
        """Find how many history messages we can keep without exceeding context."""
        for length in range(len(self.conversation_history), 0, -1):
            test = self.conversation_history[-length:]
            text = " ".join(m["content"] for m in test)
            total = self._system_tokens + estimate_tokens(text) + 500  # 500 for response
            if total <= self.max_tokens:
                return length
        return 0