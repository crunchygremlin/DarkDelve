"""Tests for LLM logging value objects."""

import pytest
import json
import os
import tempfile
from src.domain.value_objects.llm_logging import (
    LLMCallLog,
    LLMPerformanceMetrics,
    LLMLogger,
    ContextWindowDiagnostics,
    TokenBudget,
    estimate_tokens,
)


class TestEstimateTokens:
    """Tests for token estimation function."""

    def test_estimate_tokens_basic(self):
        assert estimate_tokens("hello world") == 2  # 11 chars // 4 = 2

    def test_estimate_tokens_empty(self):
        assert estimate_tokens("") == 1  # minimum is 1

    def test_estimate_tokens_long_text(self):
        text = "a" * 100
        assert estimate_tokens(text) == 25  # 100 // 4 = 25


class TestContextWindowDiagnostics:
    """Tests for ContextWindowDiagnostics dataclass."""

    def test_default_values(self):
        diag = ContextWindowDiagnostics()
        assert diag.max_context_tokens == 8192
        assert diag.headroom_tokens == 8192
        assert diag.headroom_pct == 100.0

    def test_calculate_headroom(self):
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
        assert diag.can_expand_context is False  # 14.55% is not > 20%
        assert diag.should_shrink_context is False  # 14.55% is not < 10%

    def test_calculate_headroom_with_large_headroom(self):
        diag = ContextWindowDiagnostics(
            max_context_tokens=8192,
            system_prompt_tokens=500,
            conversation_history_tokens=500,
            current_prompt_tokens=500,
            response_tokens=500
        )
        diag.calculate_headroom()
        assert diag.total_used_tokens == 2000
        assert diag.headroom_tokens == 6192
        assert diag.headroom_pct == pytest.approx(76.1, rel=0.1)
        assert diag.can_expand_context is True
        assert diag.should_shrink_context is False


class TestTokenBudget:
    """Tests for TokenBudget dataclass."""

    def test_default_values(self):
        budget = TokenBudget()
        assert budget.system_prompt == 1000
        assert budget.perception_status == 500
        assert budget.available_for_response == 2000

    def test_total_allocated(self):
        budget = TokenBudget()
        assert budget.total_allocated() == 4100  # 1000+500+300+200+2000+100

    def test_fits_in_context(self):
        budget = TokenBudget()
        assert budget.fits_in_context(8192) is True
        assert budget.fits_in_context(4000) is False

    def test_utilization_pct(self):
        budget = TokenBudget()
        assert budget.utilization_pct(8192) == pytest.approx(50.0, rel=0.1)


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
        # New fields
        assert log.prompt_tokens == 0
        assert log.response_tokens == 0
        assert log.context_headroom == 8192
        assert log.model == ""
        assert log.temperature == 0.0
        assert log.cached is False

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

    def test_to_dict_with_new_fields(self):
        log = LLMCallLog(
            call_id="call_004",
            timestamp=1003.0,
            context="test",
            entity_id="e1",
            prompt_summary="p",
            response_summary="r",
            latency_ms=100.0,
            tokens_used=50,
            success=True,
            prompt_tokens=25,
            response_tokens=25,
            context_headroom=4000,
            model="gpt-4",
            temperature=0.8,
            cached=True
        )
        d = log.to_dict()
        assert d["prompt_tokens"] == 25
        assert d["response_tokens"] == 25
        assert d["context_headroom"] == 4000
        assert d["model"] == "gpt-4"
        assert d["temperature"] == 0.8
        assert d["cached"] is True


class TestLLMPerformanceMetrics:
    """Tests for LLMPerformanceMetrics dataclass."""

    def test_default_values(self):
        metrics = LLMPerformanceMetrics()
        assert metrics.total_calls == 0
        assert metrics.total_latency_ms == 0.0
        assert metrics.error_count == 0
        assert metrics.total_tokens == 0
        assert metrics.max_context_tokens == 8192
        assert metrics.context_pressure_events == 0

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

    def test_avg_prompt_tokens(self):
        metrics = LLMPerformanceMetrics()
        log1 = LLMCallLog(
            call_id="call_1",
            timestamp=1000.0,
            context="test",
            entity_id="e",
            prompt_summary="t",
            response_summary="t",
            latency_ms=100.0,
            tokens_used=10,
            success=True,
            prompt_tokens=100
        )
        log2 = LLMCallLog(
            call_id="call_2",
            timestamp=1001.0,
            context="test",
            entity_id="e",
            prompt_summary="t",
            response_summary="t",
            latency_ms=100.0,
            tokens_used=10,
            success=True,
            prompt_tokens=200
        )
        metrics.record_call(log1)
        metrics.record_call(log2)
        assert metrics.avg_prompt_tokens == 150.0

    def test_avg_response_tokens(self):
        metrics = LLMPerformanceMetrics()
        log1 = LLMCallLog(
            call_id="call_1",
            timestamp=1000.0,
            context="test",
            entity_id="e",
            prompt_summary="t",
            response_summary="t",
            latency_ms=100.0,
            tokens_used=10,
            success=True,
            response_tokens=50
        )
        log2 = LLMCallLog(
            call_id="call_2",
            timestamp=1001.0,
            context="test",
            entity_id="e",
            prompt_summary="t",
            response_summary="t",
            latency_ms=100.0,
            tokens_used=10,
            success=True,
            response_tokens=150
        )
        metrics.record_call(log1)
        metrics.record_call(log2)
        assert metrics.avg_response_tokens == 100.0

    def test_max_prompt_tokens_seen(self):
        metrics = LLMPerformanceMetrics()
        assert metrics.max_prompt_tokens_seen == 0
        log = LLMCallLog(
            call_id="call_1",
            timestamp=1000.0,
            context="test",
            entity_id="e",
            prompt_summary="t",
            response_summary="t",
            latency_ms=100.0,
            tokens_used=10,
            success=True,
            prompt_tokens=500
        )
        metrics.record_call(log)
        assert metrics.max_prompt_tokens_seen == 500

    def test_context_pressure_rate(self):
        metrics = LLMPerformanceMetrics(max_context_tokens=8192)
        # No pressure events
        assert metrics.context_pressure_rate == 0.0
        # Add a call with low headroom (pressure event)
        log = LLMCallLog(
            call_id="call_1",
            timestamp=1000.0,
            context="test",
            entity_id="e",
            prompt_summary="t",
            response_summary="t",
            latency_ms=100.0,
            tokens_used=10,
            success=True,
            context_headroom=100  # < 10% of 8192
        )
        metrics.record_call(log)
        assert metrics.context_pressure_rate == 1.0

    def test_get_context_advice_high_pressure(self):
        metrics = LLMPerformanceMetrics(max_context_tokens=8192)
        metrics.context_pressure_events = 4
        metrics.total_calls = 10
        assert "HIGH PRESSURE" in metrics.get_context_advice()

    def test_get_context_advice_low_usage(self):
        metrics = LLMPerformanceMetrics(max_context_tokens=8192)
        metrics.prompt_token_samples = [100, 200, 150]  # avg 150, < 30% of 8192
        assert "LOW USAGE" in metrics.get_context_advice()

    def test_get_context_advice_balanced(self):
        metrics = LLMPerformanceMetrics(max_context_tokens=8192)
        metrics.prompt_token_samples = [2000, 2500, 3000]  # avg 2500, ~30% of 8192
        assert "BALANCED" in metrics.get_context_advice()

    def test_model_usage_tracking(self):
        metrics = LLMPerformanceMetrics()
        log1 = LLMCallLog(
            call_id="call_1",
            timestamp=1000.0,
            context="test",
            entity_id="e",
            prompt_summary="t",
            response_summary="t",
            latency_ms=100.0,
            tokens_used=10,
            success=True,
            model="gpt-4"
        )
        log2 = LLMCallLog(
            call_id="call_2",
            timestamp=1001.0,
            context="test",
            entity_id="e",
            prompt_summary="t",
            response_summary="t",
            latency_ms=100.0,
            tokens_used=10,
            success=True,
            model="gpt-4"
        )
        log3 = LLMCallLog(
            call_id="call_3",
            timestamp=1002.0,
            context="test",
            entity_id="e",
            prompt_summary="t",
            response_summary="t",
            latency_ms=100.0,
            tokens_used=10,
            success=True,
            model="gpt-oss"
        )
        metrics.record_call(log1)
        metrics.record_call(log2)
        metrics.record_call(log3)
        assert metrics.model_usage["gpt-4"] == 2
        assert metrics.model_usage["gpt-oss"] == 1


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

    def test_estimate_prompt_tokens(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = LLMLogger(log_dir=tmpdir)
            assert logger.estimate_prompt_tokens("hello world") == 2

    def test_check_headroom(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = LLMLogger(log_dir=tmpdir)
            diag = logger.check_headroom("test prompt", "system prompt", "history")
            assert diag.system_prompt_tokens > 0
            assert diag.current_prompt_tokens > 0
            diag.calculate_headroom()
            assert diag.headroom_tokens > 0

    def test_get_performance_report(self):
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
                success=True,
                prompt_tokens=25,
                response_tokens=25
            )
            logger.log_call(log)
            report = logger.get_performance_report()
            assert "LLM PERFORMANCE REPORT" in report
            assert "Total calls: 1" in report
            assert "Avg prompt tokens: 25" in report