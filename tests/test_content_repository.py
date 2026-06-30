"""Tests for ContentRepository."""

import os
import tempfile
import sqlite3
import pytest
from pathlib import Path
from src.infrastructure.repositories.content_repository import ContentRepository, SeedContent
from src.infrastructure.external.cache_service import CacheService


@pytest.fixture
def test_db():
    """Create a temporary test database with seed data."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE generations (
            key TEXT PRIMARY KEY,
            prompt_hash TEXT,
            response TEXT,
            model TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            use_count INTEGER DEFAULT 0
        )
    """)
    conn.execute(
        "INSERT INTO generations VALUES (?, ?, ?, ?, ?, ?)",
        ("items_arcane|divine", "abc123", '[{"name": "Mystic Blade"}]', "qwen", "2026-06-07", 100),
    )
    conn.execute(
        "INSERT INTO generations VALUES (?, ?, ?, ?, ?, ?)",
        ("monsters_undead|demon", "def456", '[{"name": "Ghoul"}]', "qwen", "2026-06-07", 50),
    )
    conn.execute(
        "INSERT INTO generations VALUES (?, ?, ?, ?, ?, ?)",
        ("items_martial|arcane", "ghi789", '[{"name": "Iron Sword"}]', "qwen", "2026-06-07", 25),
    )
    conn.commit()
    conn.close()
    yield Path(path)
    os.unlink(path)


@pytest.fixture
def test_conn(test_db):
    """Create a database connection with the test database."""
    conn = sqlite3.connect(str(test_db))
    yield conn
    conn.close()


def test_get_seeds_by_type_items(test_conn):
    repo = ContentRepository(test_conn)
    seeds = repo.get_seeds_by_type("items")
    assert len(seeds) == 2
    assert seeds[0].content_type == "items"
    assert seeds[0].use_count >= seeds[1].use_count  # Ordered by use_count DESC


def test_get_seeds_by_type_monsters(test_conn):
    repo = ContentRepository(test_conn)
    seeds = repo.get_seeds_by_type("monsters")
    assert len(seeds) == 1
    assert seeds[0].key == "monsters_undead|demon"


def test_get_seeds_by_tags(test_conn):
    repo = ContentRepository(test_conn)
    seeds = repo.get_seeds_by_tags(["arcane"])
    assert len(seeds) == 2  # Both items_arcane and items_martial|arcane


def test_get_seeds_by_tags_multiple(test_conn):
    repo = ContentRepository(test_conn)
    seeds = repo.get_seeds_by_tags(["arcane", "divine"])
    assert len(seeds) == 1  # Only items_arcane|divine matches both


def test_get_most_used(test_conn):
    repo = ContentRepository(test_conn)
    seeds = repo.get_most_used(limit=2)
    assert len(seeds) == 2
    assert seeds[0].use_count == 100
    assert seeds[1].use_count == 50


def test_get_all_keys(test_conn):
    repo = ContentRepository(test_conn)
    keys = repo.get_all_keys()
    assert len(keys) == 3
    assert "items_arcane|divine" in keys


def test_seed_content_from_row():
    row = ("items_test", "hash123", '{"name": "X"}', "qwen", "2026-06-07", 10)
    seed = SeedContent.from_row(row)
    assert seed.key == "items_test"
    assert seed.content_type == "items"
    assert seed.parsed == {"name": "X"}
    assert seed.use_count == 10


def test_close(test_conn):
    repo = ContentRepository(test_conn)
    repo.close()  # Should not raise