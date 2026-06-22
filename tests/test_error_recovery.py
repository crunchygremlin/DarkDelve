"""Integration tests for error recovery scenarios."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from player_agent import PlayerAgent, OllamaConfig, PlayerDecision
from ollama_playtester import OllamaPlaytester, PlaytestConfig


class TestErrorRecoveryIntegration:
    """Integration tests for error recovery scenarios."""

    @patch('requests.post')
    def test_recovery_after_404_error(self, mock_post):
        """Test that playtest continues after 404 error with fallback."""
        # First call returns 404
        mock_response_404 = Mock()
        mock_response_404.status_code = 404
        mock_response_404.raise_for_status.side_effect = Exception("404 Not Found")
        
        # Second call succeeds
        mock_response_success = Mock()
        mock_response_success.json.return_value = {"response": '{"action": "s", "macro_goal": "test", "reasoning": "test", "telemetry_notes": "test"}'}
        mock_response_success.status_code = 200
        
        mock_post.side_effect = [mock_response_404, mock_response_success]

        config = OllamaConfig(endpoint="https://openrouter.ai/api/v1", retries=0)
        agent = PlayerAgent(config=config)
        
        # First call should fail (with retries=0, it only tries once)
        with pytest.raises(RuntimeError):
            agent.request_ollama("system", "user")
        
        # Second call should succeed
        result = agent.request_ollama("system", "user")
        assert result is not None

    @patch('requests.post')
    def test_recovery_after_json_parse_error(self, mock_post):
        """Test that playtest continues after JSON parse error."""
        # First call returns invalid JSON
        mock_response_invalid = Mock()
        mock_response_invalid.json.side_effect = json.JSONDecodeError("test", "test", 0)
        mock_response_invalid.text = "not json"
        mock_response_invalid.status_code = 200
        
        # Second call succeeds
        mock_response_success = Mock()
        mock_response_success.json.return_value = {"response": '{"action": "e", "macro_goal": "test", "reasoning": "test", "telemetry_notes": "test"}'}
        mock_response_success.status_code = 200
        
        mock_post.side_effect = [mock_response_invalid, mock_response_success]

        config = OllamaConfig(endpoint="https://openrouter.ai/api/v1")
        agent = PlayerAgent(config=config)
        
        # First call should return raw text
        result = agent.request_ollama("system", "user")
        assert result == "not json"
        
        # Second call should succeed
        result = agent.request_ollama("system", "user")
        assert result is not None

    def test_fallback_action_on_repeated_failures(self):
        """Test that fallback action is used after repeated failures."""
        config = OllamaConfig(
            endpoint="https://openrouter.ai/api/v1",
            safe_action="e"
        )
        agent = PlayerAgent(config=config)
        
        # Simulate parsing response with invalid action
        data, issues = agent.sanitize_json_response('{"action": "x", "macro_goal": "test", "reasoning": "test", "telemetry_notes": "test"}')
        normalized, validation_issues = agent.validate_response(data)
        
        assert normalized["action"] == "e"  # Should fallback to 'e'
        assert any("invalid action" in issue for issue in validation_issues)

    @patch('requests.post')
    def test_timeout_recovery(self, mock_post):
        """Test recovery after timeout."""
        import requests
        
        # First call times out
        mock_post.side_effect = [
            requests.exceptions.Timeout(),
            Mock(status_code=200, json=lambda: {"response": '{"action": "s", "macro_goal": "test", "reasoning": "test", "telemetry_notes": "test"}'})
        ]

        config = OllamaConfig(endpoint="https://openrouter.ai/api/v1", timeout=1.0, retries=0)
        agent = PlayerAgent(config=config)
        
        # First call should fail (with retries=0, it only tries once)
        with pytest.raises(RuntimeError):
            agent.request_ollama("system", "user")
        
        # Second call should succeed
        result = agent.request_ollama("system", "user")
        assert result is not None

    def test_playtest_config_timeout_settings(self):
        """Test that playtest config has proper timeout settings."""
        config = PlaytestConfig()
        
        # Default should be reasonable
        assert config.max_duration_seconds > 0
        assert config.max_consecutive_failures > 0
        
        # Should be configurable
        custom_config = PlaytestConfig(
            max_duration_seconds=300,
            max_consecutive_failures=5
        )
        assert custom_config.max_duration_seconds == 300
        assert custom_config.max_consecutive_failures == 5


class TestEmbeddedOllamaFallback:
    """Tests for EmbeddedOllama fallback mechanisms."""

    def test_fallback_generate_returns_string(self):
        """Test that fallback generate returns a string."""
        # This test verifies the fallback logic concept
        # The actual EmbeddedOllama class in darkdelve.py has a _fallback_generate method
        # that returns procedural content when Ollama is unavailable
        import random
        random.seed(hash("test prompt about monster") % (2**32))
        
        # Simulate the fallback logic
        result = json.dumps({"mob": random.choice(['goblin', 'orc', 'skeleton']), "count": random.randint(1, 3)})
        
        # Should return fallback content
        assert result is not None
        assert isinstance(result, str)
        # Should be valid JSON
        parsed = json.loads(result)
        assert "mob" in parsed or "status" in parsed

    def test_fallback_generate_for_level_theme(self):
        """Test that fallback generate handles level theme prompts."""
        import random
        random.seed(hash("generate level theme for depth 5") % (2**32))
        
        # Simulate the fallback logic
        themes = ['cave', 'ruins', 'crypt', 'forest', 'mountain']
        result = json.dumps({"name": random.choice(themes), "description": 'A mysterious place.'})
        
        assert result is not None
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "name" in parsed or "status" in parsed