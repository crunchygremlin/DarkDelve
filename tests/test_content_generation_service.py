"""Tests for ContentGenerationService."""

import os
import tempfile
import sqlite3
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.infrastructure.repositories.content_repository import ContentRepository
from src.infrastructure.external.cache_service import CacheService
from src.application.services.content_seeder import ContentSeeder
from src.domain.services.content_generation_service import ContentGenerationService


@pytest.fixture
def test_db():
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


def test_generate_game_content_success(test_conn):
    repo = ContentRepository(test_conn)
    seeder = ContentSeeder(repo)
    mock_ollama = MagicMock()
    mock_ollama.generate.side_effect = [
        '{"items": [{"name": "New Sword", "type": "weapon"}]}',
        '{"mobs": [{"name": "New Ghoul", "tier": 3}]}',
        '{"title": "New Level", "description": "test", "features": []}',
    ]
    mock_logger = MagicMock()

    svc = ContentGenerationService(repo, seeder, mock_ollama, mock_logger)
    result = svc.generate_game_content(
        item_tags=["arcane"],
        monster_tags=["undead"],
        level_tags=["dungeon"],
    )
    assert "items" in result
    assert "monsters" in result
    assert "level_descriptions" in result
    assert len(result["items"]) == 1
    assert result["items"][0]["name"] == "New Sword"


def test_generate_game_content_llm_failure(test_conn):
    repo = ContentRepository(test_conn)
    seeder = ContentSeeder(repo)
    mock_ollama = MagicMock()
    mock_ollama.generate.side_effect = Exception("LLM timeout")
    mock_logger = MagicMock()

    svc = ContentGenerationService(repo, seeder, mock_ollama, mock_logger)
    result = svc.generate_game_content(
        item_tags=["arcane"],
        monster_tags=["undead"],
        level_tags=["dungeon"],
    )
    # Should return empty lists, not crash
    assert result["items"] == []
    assert result["monsters"] == []


def test_parse_json_response_valid():
    response = 'Here is JSON: {"key": "value"} done'
    result = ContentGenerationService._parse_json_response(response)
    assert result == {"key": "value"}


def test_parse_json_response_invalid():
    response = "No JSON here"
    result = ContentGenerationService._parse_json_response(response)
    assert result is None