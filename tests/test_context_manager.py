"""Tests for ContextManager service."""

import pytest
from src.domain.services.context_manager import ContextManager
from src.domain.value_objects.llm_logging import (
    ContextWindowDiagnostics,
    TokenBudget,
    estimate_tokens,
)


class TestContextManager:
    """Tests for ContextManager class."""

    def test_context_manager_creation(self):
        cm = ContextManager()
        assert cm.max_tokens == 8192
        assert cm.system_prompt == ""
        assert cm.conversation_history == []

    def test_context_manager_with_custom_max_tokens(self):
        cm = ContextManager(max_tokens=4096)
        assert cm.max_tokens == 4096

    def test_context_manager_with_system_prompt(self):
        cm = ContextManager(system_prompt="You are a helpful assistant.")
        assert cm.system_prompt == "You are a helpful assistant."
        assert cm._system_tokens > 0

    def test_set_system_prompt(self):
        cm = ContextManager()
        cm.set_system_prompt("New system prompt")
        assert cm.system_prompt == "New system prompt"
        assert cm._system_tokens == estimate_tokens("New system prompt")

    def test_add_message(self):
        cm = ContextManager()
        cm.add_message("user", "Hello")
        assert len(cm.conversation_history) == 1
        assert cm.conversation_history[0] == {"role": "user", "content": "Hello"}

    def test_add_multiple_messages(self):
        cm = ContextManager()
        cm.add_message("user", "Hello")
        cm.add_message("assistant", "Hi there")
        assert len(cm.conversation_history) == 2

    def test_get_context_usage(self):
        cm = ContextManager(system_prompt="System prompt here")
        cm.add_message("user", "Hello")
        diag = cm.get_context_usage()
        assert isinstance(diag, ContextWindowDiagnostics)
        assert diag.system_prompt_tokens > 0
        assert diag.conversation_history_tokens > 0

    def test_trim_history(self):
        cm = ContextManager(max_tokens=100)
        # Add many messages
        for i in range(20):
            cm.add_message("user", f"Message {i} " * 10)
        original_len = len(cm.conversation_history)
        cm.trim_history(target_tokens=50)
        assert len(cm.conversation_history) < original_len

    def test_trim_history_empty_target(self):
        cm = ContextManager()
        cm.add_message("user", "Hello")
        cm.trim_history(target_tokens=0)
        assert len(cm.conversation_history) == 0

    def test_build_prompt(self):
        cm = ContextManager(system_prompt="You are a bot.")
        cm.add_message("user", "Hello")
        cm.add_message("assistant", "Hi")
        prompt = cm.build_prompt("How are you?")
        assert "You are a bot." in prompt
        assert "user: Hello" in prompt
        assert "assistant: Hi" in prompt
        assert "How are you?" in prompt

    def test_build_prompt_with_last_10_messages(self):
        cm = ContextManager()
        for i in range(15):
            cm.add_message("user", f"Message {i}")
        prompt = cm.build_prompt("Last message")
        # Should only include last 10 messages
        assert "Message 5" in prompt
        assert "Message 14" in prompt

    def test_can_fit_true(self):
        cm = ContextManager(max_tokens=1000)
        cm.set_system_prompt("System")
        assert cm.can_fit("Short message") is True

    def test_can_fit_false(self):
        cm = ContextManager(max_tokens=100)
        cm.set_system_prompt("A" * 50)
        # Very long message that won't fit
        assert cm.can_fit("A" * 200) is False

    def test_get_optimal_history_length(self):
        cm = ContextManager(max_tokens=1000)
        for i in range(10):
            cm.add_message("user", f"Message {i}")
        length = cm.get_optimal_history_length()
        assert length >= 0
        assert length <= 10

    def test_get_optimal_history_length_empty(self):
        cm = ContextManager()
        assert cm.get_optimal_history_length() == 0


class TestContextWindowDiagnosticsCalculations:
    """Tests for ContextWindowDiagnostics calculations."""

    def test_calculate_headroom_basic(self):
        diag = ContextWindowDiagnostics(
            max_context_tokens=8192,
            system_prompt_tokens=1000,
            conversation_history_tokens=2000,
            current_prompt_tokens=3000,
            response_tokens=1000
        )
        diag.calculate_headroom()
        assert diag.total_used_tokens == 7000
        assert diag.headroom_tokens == 1192
        assert diag.headroom_pct == pytest.approx(14.55, rel=0.1)

    def test_calculate_headroom_zero_headroom(self):
        diag = ContextWindowDiagnostics(
            max_context_tokens=8192,
            system_prompt_tokens=8192,
            conversation_history_tokens=0,
            current_prompt_tokens=0,
            response_tokens=0
        )
        diag.calculate_headroom()
        assert diag.headroom_tokens == 0
        assert diag.headroom_pct == 0.0
        assert diag.should_shrink_context is True

    def test_calculate_headroom_full_headroom(self):
        diag = ContextWindowDiagnostics(
            max_context_tokens=8192,
            system_prompt_tokens=0,
            conversation_history_tokens=0,
            current_prompt_tokens=0,
            response_tokens=0
        )
        diag.calculate_headroom()
        assert diag.headroom_tokens == 8192
        assert diag.headroom_pct == 100.0
        assert diag.can_expand_context is True
        assert diag.should_shrink_context is False


class TestTokenBudgetCalculations:
    """Tests for TokenBudget calculations."""

    def test_total_allocated(self):
        budget = TokenBudget()
        assert budget.total_allocated() == 4100  # 1000+500+300+200+2000+100

    def test_total_allocated_custom(self):
        budget = TokenBudget(
            system_prompt=500,
            perception_status=250,
            social_context=150,
            behavior_history=100,
            available_for_response=1000,
            overhead=50
        )
        assert budget.total_allocated() == 2050

    def test_fits_in_context_true(self):
        budget = TokenBudget()
        assert budget.fits_in_context(8192) is True
        assert budget.fits_in_context(10000) is True

    def test_fits_in_context_false(self):
        budget = TokenBudget()
        assert budget.fits_in_context(4000) is False

    def test_utilization_pct(self):
        budget = TokenBudget()
        assert budget.utilization_pct(8192) == pytest.approx(50.0, rel=0.1)
        assert budget.utilization_pct(10000) == pytest.approx(41.0, rel=0.1)


class TestEstimateTokens:
    """Tests for estimate_tokens function."""

    def test_estimate_tokens_basic(self):
        assert estimate_tokens("hello world") == 2  # 11 chars // 4 = 2

    def test_estimate_tokens_empty(self):
        assert estimate_tokens("") == 1  # minimum is 1

    def test_estimate_tokens_long_text(self):
        text = "a" * 100
        assert estimate_tokens(text) == 25  # 100 // 4 = 25

    def test_estimate_tokens_single_char(self):
        assert estimate_tokens("a") == 1  # minimum is 1

    def test_estimate_tokens_multiple_of_four(self):
        assert estimate_tokens("a" * 4) == 1
        assert estimate_tokens("a" * 8) == 2