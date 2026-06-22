"""LLM logging value objects for the Entity AI system."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
import time
import json
import os

__all__ = [
    "LLMCallLog",
    "LLMPerformanceMetrics",
    "LLMLogger",
]


@dataclass
class LLMCallLog:
    """Log entry for a single LLM call."""
    call_id: str
    timestamp: float
    context: str  # "behavior_generation", "level_design", "item_seeding"
    entity_id: Optional[str]
    prompt_summary: str  # first 200 chars
    response_summary: str  # first 200 chars
    latency_ms: float
    tokens_used: int
    success: bool
    error: Optional[str] = None
    behavior_script_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "call_id": self.call_id,
            "timestamp": self.timestamp,
            "context": self.context,
            "entity_id": self.entity_id,
            "prompt_summary": self.prompt_summary,
            "response_summary": self.response_summary,
            "latency_ms": self.latency_ms,
            "tokens_used": self.tokens_used,
            "success": self.success,
            "error": self.error,
            "behavior_script_id": self.behavior_script_id,
        }


@dataclass
class LLMPerformanceMetrics:
    """Aggregated metrics for LLM performance."""
    total_calls: int = 0
    total_latency_ms: float = 0.0
    latencies: List[float] = field(default_factory=list)
    error_count: int = 0
    total_tokens: int = 0
    calls_by_context: Dict[str, int] = field(default_factory=dict)
    recent_failures: List[LLMCallLog] = field(default_factory=list)

    def record_call(self, log: LLMCallLog):
        """Record a call in the metrics."""
        self.total_calls += 1
        self.total_latency_ms += log.latency_ms
        self.latencies.append(log.latency_ms)
        self.total_tokens += log.tokens_used
        self.calls_by_context[log.context] = self.calls_by_context.get(log.context, 0) + 1
        if not log.success:
            self.error_count += 1
            self.recent_failures.append(log)
            if len(self.recent_failures) > 50:
                self.recent_failures = self.recent_failures[-50:]

    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency in milliseconds."""
        return self.total_latency_ms / max(1, self.total_calls)

    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        return self.error_count / max(1, self.total_calls)

    @property
    def avg_tokens(self) -> float:
        """Calculate average tokens per call."""
        return self.total_tokens / max(1, self.total_calls)

    def p95_latency(self) -> float:
        """Calculate 95th percentile latency."""
        if not self.latencies:
            return 0.0
        sorted_l = sorted(self.latencies)
        idx = int(len(sorted_l) * 0.95)
        return sorted_l[min(idx, len(sorted_l) - 1)]


class LLMLogger:
    """Logs LLM calls to playtest/telemetry/llm_performance.json"""

    def __init__(self, log_dir: str = "playtest/telemetry"):
        self.log_dir = log_dir
        self.metrics = LLMPerformanceMetrics()
        self.call_log: List[LLMCallLog] = []
        os.makedirs(log_dir, exist_ok=True)

    def log_call(self, log: LLMCallLog):
        """Log a call and update metrics."""
        self.call_log.append(log)
        self.metrics.record_call(log)
        self._flush()

    def _flush(self):
        """Write metrics to file."""
        path = os.path.join(self.log_dir, "llm_performance.json")
        data = {
            "metrics": {
                "total_calls": self.metrics.total_calls,
                "avg_latency_ms": self.metrics.avg_latency_ms,
                "p95_latency_ms": self.metrics.p95_latency(),
                "error_rate": self.metrics.error_rate,
                "avg_tokens": self.metrics.avg_tokens,
                "calls_by_context": self.metrics.calls_by_context,
            },
            "recent_calls": [c.to_dict() for c in self.call_log[-100:]],
            "recent_failures": [f.to_dict() for f in self.metrics.recent_failures[-20:]],
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def get_metrics_summary(self) -> str:
        """Get a text summary of metrics."""
        m = self.metrics
        return (
            f"LLM Metrics: {m.total_calls} calls, "
            f"avg={m.avg_latency_ms:.0f}ms, p95={m.p95_latency():.0f}ms, "
            f"errors={m.error_rate:.1%}, avg_tokens={m.avg_tokens:.0f}"
        )