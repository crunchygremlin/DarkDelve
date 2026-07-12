"""Tests for truncation logging."""

import tempfile
from pathlib import Path
from src.domain.value_objects.llm_logging import LLMLogger, TruncationInfo


class TestTruncationLogging:
    """Tests for truncation logging."""

    def test_truncate_logs_when_over_limit(self, tmp_path):
        """Test that truncation logs when prompt exceeds limit."""
        logger = LLMLogger(log_dir=tmp_path)
        big = "x" * 9000
        out, info = logger.truncate_prompt(big, max_chars=8000)
        assert info.was_truncated and info.original_chars == 9000
        logger.log_truncation("c1", "behavior", info)
        assert (tmp_path / "truncation.jsonl").exists()

    def test_no_truncation_under_limit(self, tmp_path):
        """Test that no truncation occurs under limit."""
        logger = LLMLogger(log_dir=tmp_path)
        out, info = logger.truncate_prompt("small", 8000)
        assert not info.was_truncated

    def test_truncation_preserves_head_and_tail(self, tmp_path):
        """Test that truncation preserves head (70%) and tail (30%)."""
        logger = LLMLogger(log_dir=tmp_path)
        big = "A" * 9000
        out, info = logger.truncate_prompt(big, max_chars=8000)
        # Head should be 70% of 8000 = 5600 chars
        # Tail should be 30% of 8000 = 2400 chars
        assert len(out) == 5600 + len("\n...[truncated]...\n") + 2400

    def test_log_memory_refresh(self, tmp_path):
        """Test memory refresh logging."""
        logger = LLMLogger(log_dir=tmp_path)
        logger.log_memory_refresh(2, 100, 500)
        assert (tmp_path / "dm_memory.jsonl").exists()