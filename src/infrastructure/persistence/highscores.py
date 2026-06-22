"""High scores management."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.shared.exceptions.infrastructure_exceptions import PersistenceException


@dataclass
class HighScoreEntry:
    """A single high score entry."""
    name: str
    score: int
    turns: int
    date: str


class HighScores:
    """Manage high scores persistence."""
    
    def __init__(self, highscores_path: Path):
        self.highscores_path = highscores_path
        self._scores: List[HighScoreEntry] = []
        self._load()
    
    def _load(self) -> None:
        """Load high scores from file."""
        if self.highscores_path.exists():
            try:
                with open(self.highscores_path) as f:
                    data = json.load(f)
                    self._scores = [
                        HighScoreEntry(**entry) for entry in data
                    ]
            except Exception:
                self._scores = []
        else:
            self._scores = []
    
    def add_score(self, name: str, score: int, turns: int, date: str) -> None:
        """Add a new high score entry."""
        entry = HighScoreEntry(name=name, score=score, turns=turns, date=date)
        self._scores.append(entry)
        self._scores.sort(key=lambda x: x.score, reverse=True)
        self._save()
    
    def get_top_scores(self, count: int = 10) -> List[HighScoreEntry]:
        """Get top N scores."""
        return self._scores[:count]
    
    def _save(self) -> None:
        """Save high scores to file."""
        try:
            with open(self.highscores_path, 'w') as f:
                json.dump(
                    [asdict(entry) for entry in self._scores],
                    f,
                    indent=2
                )
        except Exception as e:
            raise PersistenceException(f"Failed to save high scores: {e}")