"""Truncation info value object for prompt truncation logging."""

from dataclasses import dataclass
from typing import List


@dataclass
class TruncationInfo:
    """Information about prompt truncation."""
    original_chars: int
    truncated_chars: int
    dropped_sections: List[str]
    was_truncated: bool