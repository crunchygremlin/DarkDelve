"""LLM logging value objects for the Entity AI system."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
import time
import json
import os
import threading

__all__ = [
    "ContextWindowDiagnostics",
    "TokenBudget",
    "LLMCallLog",
    "LLMPerformanceMetrics",
    "LLMLogger",
    "estimate_tokens",
]


def estimate_tokens(text: str) -> int:
    """Rough token estimation. ~4 chars per token for English text."""
    return max(1, len(text) // 4)


@dataclass
class ContextWindowDiagnostics:
    """Tracks context window usage and headroom."""
    max_context_tokens: int = 8192       # 8K default
    system_prompt_tokens: int = 0
    conversation_history_tokens: int = 0
    current_prompt_tokens: int = 0
    response_tokens: int = 0
    total_used_tokens: int = 0
    headroom_tokens: int = 8192
    headroom_pct: float = 100.0
    can_expand_context: bool = True
    should_shrink_context: bool = False
    
    def calculate_headroom(self):
        """Calculate headroom based on current token counts."""
        self.total_used_tokens = (self.system_prompt_tokens + 
                                   self.conversation_history_tokens + 
                                   self.current_prompt_tokens + 
                                   self.response_tokens)
        self.headroom_tokens = max(0, self.max_context_tokens - self.total_used_tokens)
        self.headroom_pct = (self.headroom_tokens / self.max_context_tokens) * 100
        self.can_expand_context = self.headroom_pct > 20
        self.should_shrink_context = self.headroom_pct < 10


@dataclass
class TokenBudget:
    """Token budget allocation for different prompt sections."""
    system_prompt: int = 1000      # personality, rules
    perception_status: int = 500   # entity perception
    social_context: int = 300      # social structure info
    behavior_history: int = 200    # past behaviors
    available_for_response: int = 2000  # expected response
    overhead: int = 100            # formatting, etc.
    
    def total_allocated(self) -> int:
        return (self.system_prompt + self.perception_status + 
                self.social_context + self.behavior_history + 
                self.available_for_response + self.overhead)
    
    def fits_in_context(self, max_context: int = 8192) -> bool:
        return self.total_allocated() <= max_context
    
    def utilization_pct(self, max_context: int = 8192) -> float:
        return (self.total_allocated() / max_context) * 100


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
    # New fields for enhanced logging
    prompt_tokens: int = 0
    response_tokens: int = 0
    context_before_tokens: int = 0
    context_after_tokens: int = 0
    context_headroom: int = 8192
    model: str = ""
    temperature: float = 0.0
    cached: bool = False
    # Task-specific fields
    turn_number: int = 0
    call_type: str = ""  # "behavior_generation" | "level_design"

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
            "prompt_tokens": self.prompt_tokens,
            "response_tokens": self.response_tokens,
            "context_before_tokens": self.context_before_tokens,
            "context_after_tokens": self.context_after_tokens,
            "context_headroom": self.context_headroom,
            "model": self.model,
            "temperature": self.temperature,
            "cached": self.cached,
            "turn_number": self.turn_number,
            "call_type": self.call_type,
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
    # New fields for enhanced metrics
    max_context_tokens: int = 8192
    context_pressure_events: int = 0  # times context > 90%
    prompt_token_samples: List[int] = field(default_factory=list)
    response_token_samples: List[int] = field(default_factory=list)
    model_usage: Dict[str, int] = field(default_factory=dict)

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
        # Record new metrics
        if log.prompt_tokens > 0:
            self.prompt_token_samples.append(log.prompt_tokens)
        if log.response_tokens > 0:
            self.response_token_samples.append(log.response_tokens)
        if log.model:
            self.model_usage[log.model] = self.model_usage.get(log.model, 0) + 1
        # Track context pressure events (context > 90% of max)
        if log.context_headroom < self.max_context_tokens * 0.1:
            self.context_pressure_events += 1

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

    @property
    def avg_prompt_tokens(self) -> float:
        """Calculate average prompt tokens."""
        return sum(self.prompt_token_samples) / max(1, len(self.prompt_token_samples))

    @property
    def avg_response_tokens(self) -> float:
        """Calculate average response tokens."""
        return sum(self.response_token_samples) / max(1, len(self.response_token_samples))

    @property
    def max_prompt_tokens_seen(self) -> int:
        """Get the maximum prompt tokens seen in any call."""
        return max(self.prompt_token_samples) if self.prompt_token_samples else 0

    @property
    def context_pressure_rate(self) -> float:
        """Calculate the rate of context pressure events."""
        return self.context_pressure_events / max(1, self.total_calls)

    def p95_latency(self) -> float:
        """Calculate 95th percentile latency."""
        if not self.latencies:
            return 0.0
        sorted_l = sorted(self.latencies)
        idx = int(len(sorted_l) * 0.95)
        return sorted_l[min(idx, len(sorted_l) - 1)]

    def get_context_advice(self) -> str:
        """Advise on whether to expand or shrink context."""
        if self.context_pressure_rate > 0.3:
            return "HIGH PRESSURE: Consider reducing perception/social context or increasing max_context"
        if self.avg_prompt_tokens < self.max_context_tokens * 0.3:
            return "LOW USAGE: Context could be expanded with more detail"
        return "BALANCED: Context usage is within healthy limits"


class LLMLogger:
    """Logs LLM calls to playtest/telemetry/llm_performance.json"""

    def __init__(self, log_dir: str = "playtest/telemetry", log_path: str = None):
        # Support both log_dir (legacy) and log_path (new) for backward compatibility
        if log_path is not None:
            # New parameter takes precedence
            if log_path.endswith('.json'):
                self.log_dir = os.path.dirname(log_path)
                self.log_file = os.path.basename(log_path)
            else:
                self.log_dir = log_path
                self.log_file = "llm_performance.json"
        else:
            self.log_dir = log_dir
            self.log_file = "llm_performance.json"
        self.metrics = LLMPerformanceMetrics()
        self.call_log: List[LLMCallLog] = []
        self._lock = threading.Lock()
        os.makedirs(self.log_dir, exist_ok=True)

    def log_call(self, log: LLMCallLog):
        """Log a call and update metrics (thread-safe)."""
        with self._lock:
            self.call_log.append(log)
            self.metrics.record_call(log)
            self._flush()

    def get_recent_entries(self, limit: int = 5) -> List[LLMCallLog]:
        """Get the most recent log entries."""
        with self._lock:
            return self.call_log[-limit:]

    def _flush(self):
        """Write metrics to file."""
        path = os.path.join(self.log_dir, self.log_file)
        data = {
            "metrics": {
                "total_calls": self.metrics.total_calls,
                "avg_latency_ms": self.metrics.avg_latency_ms,
                "p95_latency_ms": self.metrics.p95_latency(),
                "error_rate": self.metrics.error_rate,
                "avg_tokens": self.metrics.avg_tokens,
                "calls_by_context": self.metrics.calls_by_context,
                "avg_prompt_tokens": self.metrics.avg_prompt_tokens,
                "avg_response_tokens": self.metrics.avg_response_tokens,
                "max_prompt_tokens_seen": self.metrics.max_prompt_tokens_seen,
                "context_pressure_rate": self.metrics.context_pressure_rate,
                "model_usage": self.metrics.model_usage,
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

    def estimate_prompt_tokens(self, prompt: str) -> int:
        """Estimate tokens for a prompt before sending."""
        return estimate_tokens(prompt)

    def check_headroom(self, prompt: str, system_prompt: str = "", 
                       history: str = "") -> ContextWindowDiagnostics:
        """Check context headroom before making a call."""
        diag = ContextWindowDiagnostics()
        diag.system_prompt_tokens = estimate_tokens(system_prompt)
        diag.conversation_history_tokens = estimate_tokens(history)
        diag.current_prompt_tokens = estimate_tokens(prompt)
        diag.calculate_headroom()
        return diag

    def get_performance_report(self) -> str:
        """Generate a human-readable performance report."""
        m = self.metrics
        lines = [
            "=== LLM PERFORMANCE REPORT ===",
            f"Total calls: {m.total_calls}",
            f"Avg latency: {m.avg_latency_ms:.0f}ms",
            f"P95 latency: {m.p95_latency():.0f}ms",
            f"Error rate: {m.error_rate:.1%}",
            f"Avg prompt tokens: {m.avg_prompt_tokens:.0f}",
            f"Avg response tokens: {m.avg_response_tokens:.0f}",
            f"Max prompt tokens: {m.max_prompt_tokens_seen}",
            f"Context pressure rate: {m.context_pressure_rate:.1%}",
            f"Model usage: {m.model_usage}",
            f"Advice: {m.get_context_advice()}",
        ]
        return "\n".join(lines)