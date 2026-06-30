"""Repository for querying seed content from content.db."""

from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SeedContent:
    """A single seed content entry."""
    key: str
    content_type: str       # "items", "monsters", "level"
    raw_json: str
    parsed: Dict[str, Any]
    use_count: int
    model: str

    @classmethod
    def from_row(cls, row: tuple) -> "SeedContent":
        key, _prompt_hash, response, model, _created_at, use_count = row
        # Split key: "items_arcane|divine" -> type="items", tags=["arcane", "divine"]
        parts = key.split("_", 1)
        content_type = parts[0] if len(parts) == 1 else parts[0]
        return cls(
            key=key,
            content_type=content_type,
            raw_json=response,
            parsed=json.loads(response),
            use_count=use_count,
            model=model,
        )


class ContentRepository:
    """Read-only repository for seed content stored in content.db."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize with an existing SQLite connection.
        
        Args:
            conn: An existing sqlite3.Connection to content.db.
        """
        self._conn = conn

    def get_seeds_by_type(self, content_type: str, limit: int = 5) -> List[SeedContent]:
        """Get seeds whose key starts with content_type (e.g. 'items', 'monsters', 'level').
        
        Ordered by use_count DESC so the most-tested seeds appear first.
        """
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT key, prompt_hash, response, model, created_at, use_count "
            "FROM generations WHERE key LIKE ? ORDER BY use_count DESC LIMIT ?",
            (f"{content_type}%", limit),
        )
        return [SeedContent.from_row(row) for row in cursor.fetchall()]

    def get_seeds_by_tags(self, tags: List[str], limit: int = 5) -> List[SeedContent]:
        """Get seeds whose key contains ALL of the given tags.
        
        Example: tags=["undead", "demon"] matches key "monsters_undead|demon|beast_1".
        """
        cursor = self._conn.cursor()
        # Build WHERE clause: key LIKE '%tag1%' AND key LIKE '%tag2%'
        conditions = " AND ".join(["key LIKE ?"] * len(tags))
        params = [f"%{tag}%" for tag in tags] + [limit]
        cursor.execute(
            f"SELECT key, prompt_hash, response, model, created_at, use_count "
            f"FROM generations WHERE {conditions} ORDER BY use_count DESC LIMIT ?",
            params,
        )
        return [SeedContent.from_row(row) for row in cursor.fetchall()]

    def get_most_used(self, limit: int = 10) -> List[SeedContent]:
        """Get the most-used seeds across all types."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT key, prompt_hash, response, model, created_at, use_count "
            "FROM generations ORDER BY use_count DESC LIMIT ?",
            (limit,),
        )
        return [SeedContent.from_row(row) for row in cursor.fetchall()]

    def get_all_keys(self) -> List[str]:
        """Get all seed keys."""
        cursor = self._conn.cursor()
        cursor.execute("SELECT key FROM generations ORDER BY key")
        return [row[0] for row in cursor.fetchall()]

    def close(self) -> None:
        """Close the connection - but don't close the shared CacheService connection."""
        pass  # Connection is managed by CacheService