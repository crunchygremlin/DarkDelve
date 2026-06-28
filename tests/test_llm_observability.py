"""Tests for LLM observability value objects."""

import pytest
import tempfile
import os

from src.domain.value_objects.llm_logging import LLMLogger, LLMCallLog
from src.domain.value_objects.llm_observability import LLMUIEntry, recent_ui_entries


class TestLLMUIEntry:
    """Tests for LLMUIEntry dataclass."""

    def test_create_entry(self):
        entry = LLMUIEntry(turn=1, call_type="behavior_generation", latency_ms=150.5, success=True)
        assert entry.turn == 1
        assert entry.call_type == "behavior_generation"
        assert entry.latency_ms == 150.5
        assert entry.success is True

    def test_entry_with_failure(self):
        entry = LLMUIEntry(turn=2, call_type="level_design", latency_ms=50.0, success=False)
        assert entry.success is False


class TestRecentUIEntries:
    """Tests for recent_ui_entries function."""

    def test_empty_logger(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = LLMLogger(log_path=os.path.join(tmpdir, "test.json"))
            entries = recent_ui_entries(logger, limit=5)
            assert entries == []

    def test_single_entry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = LLMLogger(log_path=os.path.join(tmpdir, "test.json"))
            log = LLMCallLog(
                call_id="test_1",
                timestamp=1000.0,
                context="behavior_generation",
                entity_id="entity_1",
                prompt_summary="test",
                response_summary="test",
                latency_ms=100.0,
                tokens_used=50,
                success=True,
                turn_number=1,
                call_type="behavior_generation",
            )
            logger.log_call(log)
            
            entries = recent_ui_entries(logger, limit=5)
            assert len(entries) == 1
            assert entries[0].turn == 1
            assert entries[0].call_type == "behavior_generation"
            assert entries[0].latency_ms == 100.0
            assert entries[0].success is True

    def test_multiple_entries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = LLMLogger(log_path=os.path.join(tmpdir, "test.json"))
            
            for i in range(3):
                log = LLMCallLog(
                    call_id=f"test_{i}",
                    timestamp=1000.0 + i,
                    context="behavior_generation",
                    entity_id=f"entity_{i}",
                    prompt_summary="test",
                    response_summary="test",
                    latency_ms=100.0 * (i + 1),
                    tokens_used=50,
                    success=True,
                    turn_number=i + 1,
                    call_type="behavior_generation",
                )
                logger.log_call(log)
            
            entries = recent_ui_entries(logger, limit=5)
            assert len(entries) == 3
            assert entries[0].turn == 1
            assert entries[1].turn == 2
            assert entries[2].turn == 3

    def test_limit_respected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = LLMLogger(log_path=os.path.join(tmpdir, "test.json"))
            
            for i in range(10):
                log = LLMCallLog(
                    call_id=f"test_{i}",
                    timestamp=1000.0 + i,
                    context="behavior_generation",
                    entity_id=f"entity_{i}",
                    prompt_summary="test",
                    response_summary="test",
                    latency_ms=100.0,
                    tokens_used=50,
                    success=True,
                    turn_number=i + 1,
                    call_type="behavior_generation",
                )
                logger.log_call(log)
            
            entries = recent_ui_entries(logger, limit=3)
            assert len(entries) == 3
            # Should get the last 3 entries
            assert entries[0].turn == 8
            assert entries[1].turn == 9
            assert entries[2].turn == 10

    def test_fallback_to_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = LLMLogger(log_path=os.path.join(tmpdir, "test.json"))
            log = LLMCallLog(
                call_id="test_1",
                timestamp=1000.0,
                context="behavior_generation",
                entity_id="entity_1",
                prompt_summary="test",
                response_summary="test",
                latency_ms=100.0,
                tokens_used=50,
                success=True,
                call_type="",  # Empty call_type
            )
            logger.log_call(log)
            
            entries = recent_ui_entries(logger, limit=5)
            # Should fall back to context when call_type is empty
            assert entries[0].call_type == "behavior_generation"