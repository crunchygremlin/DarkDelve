"""Cache service for content caching."""

import hashlib
import sqlite3
from pathlib import Path
from typing import Optional

from src.shared.exceptions.infrastructure_exceptions import CacheException


class CacheService:
    """Persistent SQLite cache for LLM generations."""
    
    def __init__(self, cache_path: Path):
        self.cache_path = cache_path
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(cache_path), check_same_thread=False)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the cache database."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS generations (
                key TEXT PRIMARY KEY,
                prompt_hash TEXT,
                response TEXT,
                model TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                use_count INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()
    
    def get(self, key: str, prompt: str) -> Optional[str]:
        """Get a cached response."""
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        row = self.conn.execute(
            "SELECT response FROM generations WHERE key=? AND prompt_hash=?",
            (key, prompt_hash)
        ).fetchone()
        if row:
            self.conn.execute(
                "UPDATE generations SET use_count=use_count+1 WHERE key=?", (key,)
            )
            self.conn.commit()
            return row[0]
        return None
    
    def set(self, key: str, prompt: str, response: str, model: str) -> None:
        """Cache a response."""
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        self.conn.execute(
            "INSERT OR REPLACE INTO generations (key, prompt_hash, response, model) VALUES (?,?,?,?)",
            (key, prompt_hash, response, model)
        )
        self.conn.commit()
    
    def clear(self) -> None:
        """Clear the cache."""
        self.conn.execute("DELETE FROM generations")
        self.conn.commit()
    
    def close(self) -> None:
        """Close the connection."""
        self.conn.close()