"""Tests for ContentSeeder."""

import os
import tempfile
import sqlite3
import pytest
from pathlib import Path
from src.infrastructure.repositories.content_repository import ContentRepository
from src.infrastructure.external.cache_service import CacheService
from src.application.services.content_seeder import ContentSeeder


@pytest.fixture
def test_db():
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
        ("items_arcane|divine", "abc", '[{"name": "Mystic Blade"}]', "qwen", "2026-06-07", 100),
    )
    conn.execute(
        "INSERT INTO generations VALUES (?, ?, ?, ?, ?, ?)",
        ("monsters_undead|demon", "def", '[{"name": "Ghoul"}]', "qwen", "2026-06-07", 50),
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


@pytest.fixture
def seeder(test_conn):
    repo = ContentRepository(test_conn)
    return ContentSeeder(repo)


def test_build_item_prompt_contains_seeds(seeder):
    prompt = seeder.build_item_prompt(tags=["arcane"], count=5)
    assert "Mystic Blade" in prompt
    assert "INSPIRATION" in prompt
    assert "NEW items" in prompt


def test_build_monster_prompt_contains_seeds(seeder):
    prompt = seeder.build_monster_prompt(tags=["undead"], count=4, tier=3)
    assert "Ghoul" in prompt
    assert "TIER: 3" in prompt


def test_build_level_prompt_contains_seeds(seeder):
    prompt = seeder.build_level_prompt(tags=["dungeon"], level_number=1)
    assert "LEVEL NUMBER: 1" in prompt


def test_build_item_prompt_no_seeds():
    """When no seeds exist, prompt should indicate no seeds available."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE generations (
            key TEXT PRIMARY KEY, prompt_hash TEXT, response TEXT,
            model TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            use_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    repo = ContentRepository(conn)
    seeder = ContentSeeder(repo)
    prompt = seeder.build_item_prompt(tags=["arcane"], count=5)
    assert "No seed content available" in prompt
    conn.close()
    os.unlink(path)