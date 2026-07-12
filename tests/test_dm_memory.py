"""Tests for DM Global Memory value object."""

import pytest
from src.domain.value_objects.dm_memory import DMGlobalMemory, estimate_tokens


class TestDMGlobalMemory:
    """Tests for DMGlobalMemory."""

    def test_memory_bounded_by_headroom(self):
        """Test that memory is bounded by headroom tokens."""
        mem = DMGlobalMemory(max_tokens=100)
        mem.refresh("A" * 1000, headroom_tokens=20)  # 20 tokens ~ 80 chars
        assert estimate_tokens(mem.summary) <= 20

    def test_refresh_at_level_boundary(self):
        """Test memory refresh at level boundary."""
        from unittest.mock import Mock
        from types import SimpleNamespace
        logger = Mock()
        logger.check_headroom.return_value = SimpleNamespace(headroom_tokens=500)
        agent = Mock()
        agent.logger = logger
        agent._memory = DMGlobalMemory(max_tokens=8192)
        
        # Simulate refresh_memory call
        agent._memory.refresh("The crypt deepens.", 500)
        agent._memory.last_updated_level = 2
        
        assert "crypt" in agent._memory.summary

    def test_context_string_returns_summary(self):
        """Test that context_string returns the summary."""
        mem = DMGlobalMemory(summary="Test memory")
        assert mem.context_string() == "Test memory"

    def test_truncate_to_headroom_returns_full_when_under(self):
        """Test truncate_to_headroom returns full summary when under headroom."""
        mem = DMGlobalMemory(summary="Short summary")
        result = mem.truncate_to_headroom(100)
        assert result == "Short summary"

    def test_truncate_to_headroom_truncates_when_over(self):
        """Test truncate_to_headroom truncates when over headroom."""
        mem = DMGlobalMemory(summary="A" * 200)
        result = mem.truncate_to_headroom(10)  # 10 tokens = 40 chars
        assert len(result) <= 40

    def test_estimate_tokens_returns_positive(self):
        """Test estimate_tokens returns positive value."""
        assert estimate_tokens("hello world") >= 1
        assert estimate_tokens("") >= 1  # Minimum 1 token