"""Tests for LLM Map Generator."""

import pytest
import json
from unittest.mock import MagicMock, patch
from src.domain.services.llm_map_generator import LLMMapGenerator
from src.domain.services.map_builder import MapBuilder


class TestLLMMapGenerator:
    """Test suite for LLMMapGenerator."""

    def test_build_map_prompt(self):
        """Test prompt generation."""
        gen = LLMMapGenerator()
        prompt = gen.build_map_prompt("A dark cave with many rooms", 60, 40, 3)

        assert "dark cave" in prompt.lower()
        assert "60" in prompt
        assert "40" in prompt
        assert "depth 3" in prompt.lower() or "3" in prompt

    def test_parse_valid_map_response(self):
        """Test parsing a valid LLM response."""
        gen = LLMMapGenerator()

        valid_json = json.dumps({
            "width": 60,
            "height": 40,
            "rooms": [{"x": 5, "y": 5, "width": 10, "height": 8, "room_id": "r1"}],
            "corridors": [{"start": [15, 9], "end": [25, 9], "width": 1}],
            "stairs": [
                {"x": 7, "y": 7, "direction": "up"},
                {"x": 30, "y": 15, "direction": "down"}
            ],
            "entities": [{"x": 10, "y": 10, "type": "goblin", "name": "Goblin"}]
        })

        response = f"Here is the map:\n{valid_json}\nEnjoy!"
        result = gen.parse_map_response(response)

        assert result is not None
        assert result["width"] == 60
        assert len(result["rooms"]) == 1

    def test_parse_invalid_response_returns_none(self):
        """Test that invalid response returns None."""
        gen = LLMMapGenerator()

        assert gen.parse_map_response("") is None
        assert gen.parse_map_response("No JSON here") is None
        assert gen.parse_map_response("{invalid") is None

    def test_generate_map_no_ollama_returns_none(self):
        """Test that without ollama, generate_map returns None."""
        gen = LLMMapGenerator(ollama_service=None)
        result, used_llm = gen.generate_map("test")

        assert result is None
        assert not used_llm

    def test_generate_map_with_mock_ollama(self):
        """Test map generation with a mock Ollama service."""
        mock_ollama = MagicMock()
        mock_ollama.generate.return_value = json.dumps({
            "width": 60,
            "height": 40,
            "rooms": [
                {"x": 5, "y": 5, "width": 8, "height": 6, "room_id": "r1"},
                {"x": 40, "y": 30, "width": 8, "height": 6, "room_id": "r2"}
            ],
            "corridors": [{"start": [9, 8], "end": [40, 33], "width": 1}],
            "stairs": [
                {"x": 7, "y": 7, "direction": "up"},
                {"x": 42, "y": 32, "direction": "down"}
            ],
            "entities": []
        })

        gen = LLMMapGenerator(ollama_service=mock_ollama)
        result, used_llm = gen.generate_map("A simple dungeon")

        assert result is not None
        assert used_llm
        assert len(result.rooms) == 2

    def test_generate_fallback(self):
        """Test procedural fallback generation."""
        gen = LLMMapGenerator(ollama_service=None)
        builder = gen.generate_fallback(50, 40, room_count=5, seed=42)

        assert builder is not None
        validation = builder.validate_map()
        assert validation["valid"]

    def test_generate_map_async(self):
        """Test async map generation request."""
        from queue import Queue

        mock_ollama = MagicMock()
        gen = LLMMapGenerator(ollama_service=mock_ollama)

        request_queue = Queue()
        gen.generate_map_async(
            description="A test dungeon",
            request_queue=request_queue,
            width=60,
            height=40,
            depth=2,
            turn_number=5,
        )

        # Check that request was enqueued
        assert not request_queue.empty()
        request = request_queue.get()
        assert request["type"] == "map_generation"
        assert request["description"] == "A test dungeon"
        assert request["turn_number"] == 5


class TestLLMMapGeneratorValidation:
    """Test map validation in generator."""

    def test_invalid_map_returns_none(self):
        """Test that invalid map returns None even with valid JSON."""
        mock_ollama = MagicMock()
        mock_ollama.generate.return_value = json.dumps({
            "width": 60,
            "height": 40,
            "rooms": [],  # No rooms = invalid
            "corridors": [],
            "stairs": [],
            "entities": []
        })

        gen = LLMMapGenerator(ollama_service=mock_ollama)
        result, used_llm = gen.generate_map("test")

        assert result is None
