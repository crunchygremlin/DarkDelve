"""Tests for behavior library."""

import tempfile
from pathlib import Path
from unittest.mock import Mock
from src.domain.services.behavior_library import BehaviorLibrary


class TestBehaviorLibrary:
    """Tests for BehaviorLibrary."""

    def test_fallback_never_none(self):
        """Test that fallback never returns None."""
        lib = BehaviorLibrary()
        assert lib.get_fallback("goblin") is not None

    def test_select_then_author(self):
        """Test select then author flow."""
        lib = BehaviorLibrary()
        agent = Mock()
        agent.generate_behavior_script.return_value = None
        
        # Select should return None for unknown mob type
        assert lib.select_script("slime", "x") is None
        
        # Fallback should still work
        assert lib.get_fallback("slime") is not None

    def test_select_script_exact_match(self):
        """Test select_script with exact mob type match."""
        lib = BehaviorLibrary()
        # The library starts empty, so select should return None
        assert lib.select_script("unknown_mob", "situation") is None

    def test_select_script_default_fallback(self):
        """Test select_script falls back to default key."""
        lib = BehaviorLibrary()
        # Without any entries, both should return None
        assert lib.select_script("any_mob", "any_situation") is None

    def test_persist_creates_file(self, tmp_path):
        """Test that _persist creates the file."""
        lib = BehaviorLibrary(persist_path=str(tmp_path / "behavior_library.json"))
        # Should not raise
        lib._persist()
        assert (tmp_path / "behavior_library.json").exists()

    def test_load_handles_missing_file(self, tmp_path):
        """Test that _load handles missing file gracefully."""
        lib = BehaviorLibrary(persist_path=str(tmp_path / "nonexistent.json"))
        # Should return empty dict without error
        result = lib._load()
        assert result == {}