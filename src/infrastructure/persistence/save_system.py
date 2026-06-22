"""Save system for game state persistence."""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

from src.shared.exceptions.infrastructure_exceptions import PersistenceException


class SaveSystem:
    """Manage game save and load operations."""
    
    def __init__(self, saves_path: Path):
        self.saves_path = saves_path
        self.saves_path.mkdir(parents=True, exist_ok=True)
    
    def save(self, game_state: Dict[str, Any], save_id: Optional[str] = None) -> str:
        """Save game state to a file."""
        import uuid
        save_id = save_id or str(uuid.uuid4())
        save_file = self.saves_path / f"save_{save_id}.json"
        
        try:
            with open(save_file, 'w') as f:
                json.dump(game_state, f, indent=2, default=str)
            return save_id
        except Exception as e:
            raise PersistenceException(f"Failed to save game: {e}")
    
    def load(self, save_id: str) -> Optional[Dict[str, Any]]:
        """Load game state from a file."""
        save_file = self.saves_path / f"save_{save_id}.json"
        
        if not save_file.exists():
            return None
        
        try:
            with open(save_file) as f:
                return json.load(f)
        except Exception as e:
            raise PersistenceException(f"Failed to load save {save_id}: {e}")
    
    def delete(self, save_id: str) -> bool:
        """Delete a save file."""
        save_file = self.saves_path / f"save_{save_id}.json"
        
        if save_file.exists():
            try:
                save_file.unlink()
                return True
            except Exception as e:
                raise PersistenceException(f"Failed to delete save {save_id}: {e}")
        return False
    
    def list_saves(self) -> list[str]:
        """List all save IDs."""
        return [f.stem.replace("save_", "") for f in self.saves_path.glob("save_*.json")]