"""LLM observability helpers for UI consumption."""

from dataclasses import dataclass
from typing import List, Optional

from src.domain.value_objects.llm_logging import LLMLogger, LLMCallLog


@dataclass
class LLMUIEntry:
    """UI-friendly entry for LLM activity display."""
    turn: int
    call_type: str
    latency_ms: float
    success: bool


def recent_ui_entries(logger: LLMLogger, limit: int = 5) -> List[LLMUIEntry]:
    """Get recent LLM activity entries for UI display.
    
    Args:
        logger: The LLMLogger instance
        limit: Maximum number of entries to return
        
    Returns:
        List of LLMUIEntry objects
    """
    entries = logger.get_recent_entries(limit)
    return [
        LLMUIEntry(
            turn=entry.turn_number,
            call_type=entry.call_type or entry.context,
            latency_ms=entry.latency_ms,
            success=entry.success,
        )
        for entry in entries
    ]