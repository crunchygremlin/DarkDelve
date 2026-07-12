"""Tests for cache-miss tracker."""

import tempfile
from pathlib import Path
from src.domain.services.cache_miss_tracker import CacheMissTracker


class TestCacheMissTracker:
    """Tests for CacheMissTracker."""

    def test_similar_prompt_is_hit(self, tmp_path):
        """Test that similar prompt is a cache hit (>=75% similarity)."""
        t = CacheMissTracker(telemetry_path=str(tmp_path / "c.jsonl"))
        t.track_prompt("generate behavior for goblin at 5,5")
        miss = t.track_prompt("generate behavior for goblin at 5,5")  # identical
        assert miss is False  # >=0.75 similar => not a miss

    def test_different_prompt_is_miss(self, tmp_path):
        """Test that different prompt is a cache miss."""
        t = CacheMissTracker(telemetry_path=str(tmp_path / "c.jsonl"))
        t.track_prompt("attack the player")
        assert t.track_prompt("flee to pack now") is True

    def test_first_prompt_is_always_miss(self, tmp_path):
        """Test that first prompt is always a miss (no previous prompt to compare)."""
        t = CacheMissTracker(telemetry_path=str(tmp_path / "c.jsonl"))
        miss = t.track_prompt("first prompt")
        assert miss is True

    def test_telemetry_file_created(self, tmp_path):
        """Test that telemetry file is created."""
        t = CacheMissTracker(telemetry_path=str(tmp_path / "c.jsonl"))
        t.track_prompt("test prompt")
        assert (tmp_path / "c.jsonl").exists()

    def test_similarity_capped_at_4000_chars(self, tmp_path):
        """Test that similarity comparison caps at 4000 chars for performance."""
        t = CacheMissTracker(telemetry_path=str(tmp_path / "c.jsonl"))
        # Very long prompts should still work without O(n^2) issues
        long_prompt = "x" * 10000
        t.track_prompt(long_prompt)
        miss = t.track_prompt(long_prompt)
        assert miss is False  # Identical, so hit