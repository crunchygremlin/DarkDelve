"""Math utility functions."""

from typing import Tuple


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max."""
    return max(min_val, min(value, max_val))


def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    """Calculate Manhattan distance heuristic between two positions."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def distance(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    """Calculate Euclidean distance between two positions."""
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5