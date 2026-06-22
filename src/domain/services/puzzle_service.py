"""Puzzle service for managing puzzle mechanics."""
from typing import List, Optional
from ..value_objects.puzzle_items import PuzzleMechanic, PuzzleItem
from ..components.puzzle_mechanic import PuzzleMechanicComponent


class PuzzleService:
    """Validates puzzle requirements, tracks solved state, and rewards players."""

    def __init__(self, component: Optional[PuzzleMechanicComponent] = None):
        self.component = component or PuzzleMechanicComponent()

    def add_puzzle(self, puzzle: PuzzleMechanic) -> None:
        """Add a puzzle to track."""
        self.component.add_puzzle(puzzle)

    def check_solution(self, puzzle_id: str, collected_items: List[str]) -> bool:
        """Check if a puzzle is solved based on collected items."""
        return self.component.check_puzzle_solution(puzzle_id, collected_items)

    def get_reward(self, puzzle_id: str) -> Optional[str]:
        """Get the reward for solving a puzzle."""
        return self.component.get_reward_for_puzzle(puzzle_id)

    def is_solved(self, puzzle_id: str) -> bool:
        """Check if a puzzle is solved."""
        return self.component.is_puzzle_solved(puzzle_id)

    def get_all_puzzles(self) -> List[PuzzleMechanic]:
        """Get all tracked puzzles."""
        return self.component.puzzles

    def get_solved_count(self) -> int:
        """Get the count of solved puzzles."""
        return len(self.component.solved_puzzles)