"""Puzzle mechanic component for managing puzzle state."""
from typing import Any, Optional, List
from .component import Component
from ..value_objects.puzzle_items import PuzzleMechanic, PuzzleItem


class PuzzleMechanicComponent(Component):
    """Manages puzzle item placement and resolution logic."""

    def __init__(self, component_id: Optional[str] = None):
        super().__init__(component_id)
        self.puzzles: List[PuzzleMechanic] = []
        self.solved_puzzles: List[str] = []

    def add_puzzle(self, puzzle: PuzzleMechanic) -> None:
        """Add a puzzle to track."""
        self.puzzles.append(puzzle)

    def check_puzzle_solution(self, puzzle_id: str, collected_items: List[str]) -> bool:
        """Check if a puzzle is solved based on collected items."""
        for puzzle in self.puzzles:
            if puzzle.puzzle_id == puzzle_id:
                if all(item_id in collected_items for item_id in puzzle.required_item_ids):
                    puzzle.is_solved = True
                    if puzzle_id not in self.solved_puzzles:
                        self.solved_puzzles.append(puzzle_id)
                    return True
        return False

    def get_reward_for_puzzle(self, puzzle_id: str) -> Optional[str]:
        """Get the reward for solving a puzzle."""
        for puzzle in self.puzzles:
            if puzzle.puzzle_id == puzzle_id and puzzle.is_solved:
                return puzzle.reward
        return None

    def is_puzzle_solved(self, puzzle_id: str) -> bool:
        """Check if a puzzle is solved."""
        return puzzle_id in self.solved_puzzles

    def update(self, delta_time: float, entity: Any) -> None:
        """Update puzzle state."""
        pass

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            "puzzles": [p.__dict__ for p in self.puzzles],
            "solved_puzzles": self.solved_puzzles,
        })
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "PuzzleMechanicComponent":
        """Create from dictionary."""
        component = cls()
        component.enabled = data.get("enabled", True)
        component.puzzles = [PuzzleMechanic(**p) for p in data.get("puzzles", [])]
        component.solved_puzzles = data.get("solved_puzzles", [])
        return component