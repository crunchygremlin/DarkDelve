"""Tests for LLM logging value objects."""

import pytest
import json
import os
import tempfile
from src.domain.value_objects.llm_logging import (
    LLMCallLog,
    LLMPerformanceMetrics,
    LLMLogger,
)


class TestLLMCallLog:
    """Tests for LLMCallLog dataclass."""

    def test_default_values(self):
        log = LLMCallLog(
            call_id="call_001",
            timestamp=1000.0,
            context="behavior_generation",
            entity_id="entity_001",
            prompt_summary="test prompt",
            response_summary="test response",
            latency_ms=150.5,
            tokens_used=100,
            success=True
        )
        assert log.call_id == "call_001"
        assert log.context == "behavior_generation"
        assert log.success is True
        assert log.error is None

    def test_with_error(self):
        log = LLMCallLog(
            call_id="call_002",
            timestamp=1001.0,
            context="level_design",
            entity_id=None,
            prompt_summary="test",
            response_summary="test",
            latency_ms=50.0,
            tokens_used=0,
            success=False,
            error="API timeout"
        )
        assert log.success is False
        assert log.error == "API timeout"

    def test_to_dict(self):
        log = LLMCallLog(
            call_id="call_003",
            timestamp=1002.0,
            context="item_seeding",
            entity_id="entity_002",
            prompt_summary="short prompt",
            response_summary="short response",
            latency_ms=200.0,
            tokens_used=50,
            success=True,
            behavior_script_id="script_001"
        )
        d = log.to_dict()
        assert isinstance(d, dict)
        assert d["call_id"] == "call_003"
        assert d["context"] == "item_seeding"
        assert d["behavior_script_id"] == "script_001"


class TestLLMPerformanceMetrics:
    """Tests for LLMPerformanceMetrics dataclass."""

    def test_default_values(self):
        metrics = LLMPerformanceMetrics()
        assert metrics.total_calls == 0
        assert metrics.total_latency_ms == 0.0
        assert metrics.error_count == 0
        assert metrics.total_tokens == 0

    def test_record_call(self):
        metrics = LLMPerformanceMetrics()
        log = LLMCallLog(
            call_id="call_001",
            timestamp=1000.0,
            context="behavior_generation",
            entity_id="entity_001",
            prompt_summary="test",
            response_summary="test",
            latency_ms=100.0,
            tokens_used=50,
            success=True
        )
        metrics.record_call(log)
        assert metrics.total_calls == 1
        assert metrics.total_latency_ms == 100.0
        assert metrics.total_tokens == 50
        assert metrics.calls_by_context["behavior_generation"] == 1

    def test_error_recording(self):
        metrics = LLMPerformanceMetrics()
        log = LLMCallLog(
            call_id="call_002",
            timestamp=1001.0,
            context="level_design",
            entity_id=None,
            prompt_summary="test",
            response_summary="test",
            latency_ms=50.0,
            tokens_used=0,
            success=False,
            error="failed"
        )
        metrics.record_call(log)
        assert metrics.error_count == 1
        assert len(metrics.recent_failures) == 1

    def test_avg_latency_ms(self):
        metrics = LLMPerformanceMetrics()
        for i in range(3):
            log = LLMCallLog(
                call_id=f"call_{i}",
                timestamp=float(i),
                context="test",
                entity_id="e",
                prompt_summary="t",
                response_summary="t",
                latency_ms=100.0 * (i + 1),
                tokens_used=10,
                success=True
            )
            metrics.record_call(log)
        assert metrics.avg_latency_ms == 200.0  # (100 + 200 + 300) / 3

    def test_error_rate(self):
        metrics = LLMPerformanceMetrics()
        for i in range(4):
            log = LLMCallLog(
                call_id=f"call_{i}",
                timestamp=float(i),
                context="test",
                entity_id="e",
                prompt_summary="t",
                response_summary="t",
                latency_ms=100.0,
                tokens_used=10,
                success=(i < 3)  # 3 success, 1 failure
            )
            metrics.record_call(log)
        assert metrics.error_rate == 0.25

    def test_avg_tokens(self):
        metrics = LLMPerformanceMetrics()
        for i in range(2):
            log = LLMCallLog(
                call_id=f"call_{i}",
                timestamp=float(i),
                context="test",
                entity_id="e",
                prompt_summary="t",
                response_summary="t",
                latency_ms=100.0,
                tokens_used=100 * (i + 1),
                success=True
            )
            metrics.record_call(log)
        assert metrics.avg_tokens == 150.0  # (100 + 200) / 2

    def test_p95_latency_empty(self):
        metrics = LLMPerformanceMetrics()
        assert metrics.p95_latency() == 0.0

    def test_p95_latency_with_data(self):
        metrics = LLMPerformanceMetrics()
        latencies = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for i, lat in enumerate(latencies):
            log = LLMCallLog(
                call_id=f"call_{i}",
                timestamp=float(i),
                context="test",
                entity_id="e",
                prompt_summary="t",
                response_summary="t",
                latency_ms=float(lat),
                tokens_used=10,
                success=True
            )
            metrics.record_call(log)
        # p95 of 10 items: index 9 (0-indexed), which is 100
        assert metrics.p95_latency() == 100.0


class TestLLMLogger:
    """Tests for LLMLogger class."""

    def test_init_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = os.path.join(tmpdir, "test_logs")
            logger = LLMLogger(log_dir=log_dir)
            assert os.path.exists(log_dir)

    def test_log_call_writes_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = LLMLogger(log_dir=tmpdir)
            log = LLMCallLog(
                call_id="call_001",
                timestamp=1000.0,
                context="behavior_generation",
                entity_id="entity_001",
                prompt_summary="test prompt",
                response_summary="test response",
                latency_ms=150.0,
                tokens_used=100,
                success=True
            )
            logger.log_call(log)
            log_path = os.path.join(tmpdir, "llm_performance.json")
            assert os.path.exists(log_path)

    def test_log_call_updates_metrics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = LLMLogger(log_dir=tmpdir)
            log = LLMCallLog(
                call_id="call_001",
                timestamp=1000.0,
                context="behavior_generation",
                entity_id="entity_001",
                prompt_summary="test",
                response_summary="test",
                latency_ms=100.0,
                tokens_used=50,
                success=True
            )
            logger.log_call(log)
            assert logger.metrics.total_calls == 1

    def test_get_metrics_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = LLMLogger(log_dir=tmpdir)
            log = LLMCallLog(
                call_id="call_001",
                timestamp=1000.0,
                context="test",
                entity_id="e",
                prompt_summary="t",
                response_summary="t",
                latency_ms=100.0,
                tokens_used=50,
                success=True
            )
            logger.log_call(log)
            summary = logger.get_metrics_summary()
            assert "LLM Metrics:" in summary
            assert "1 calls" in summary

    def test_json_file_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = LLMLogger(log_dir=tmpdir)
            log = LLMCallLog(
                call_id="call_001",
                timestamp=1000.0,
                context="test",
                entity_id="e",
                prompt_summary="test prompt",
                response_summary="test response",
                latency_ms=100.0,
                tokens_used=50,
                success=True
            )
            logger.log_call(log)
            log_path = os.path.join(tmpdir, "llm_performance.json")
            with open(log_path, 'r') as f:
                data = json.load(f)
            assert "metrics" in data
            assert "recent_calls" in data
            assert "recent_failures" in data
            assert data["metrics"]["total_calls"] == 1