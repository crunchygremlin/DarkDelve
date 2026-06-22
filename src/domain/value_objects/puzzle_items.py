"""Puzzle and trash item value objects."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .item_creation import Item


@dataclass
class PuzzleItem:
    """An item that seems useless now but is needed later."""
    item_id: str
    name: str
    description: str
    found_level: int
    used_level: int
    puzzle_description: str    # what it's used for
    is_identified: bool = False  # player might not know its purpose
    is_collected: bool = False


@dataclass
class PuzzleMechanic:
    """A puzzle that requires specific items."""
    puzzle_id: str
    level_number: int
    required_item_ids: List[str]
    description: str
    reward: str                # what solving it gives
    is_solved: bool = False