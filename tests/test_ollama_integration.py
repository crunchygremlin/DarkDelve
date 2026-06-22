"""Unit tests for Ollama API integration with mock responses."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from player_agent import PlayerAgent, OllamaConfig, PlayerDecision
from ollama_playtester import PlaytestConfig


class TestOllamaConfig:
    """Tests for OllamaConfig endpoint handling."""

    def test_generate_url_with_openrouter_endpoint(self):
        """Test that OpenRouter endpoint is correctly formatted."""
        config = OllamaConfig(endpoint="https://openrouter.ai/api/v1")
        assert config.generate_url() == "https://openrouter.ai/api/v1/api/generate"

    def test_generate_url_with_trailing_slash(self):
        """Test that trailing slash is handled correctly."""
        config = OllamaConfig(endpoint="https://openrouter.ai/api/v1/")
        assert config.generate_url() == "https://openrouter.ai/api/v1/api/generate"

    def test_generate_url_with_custom_endpoint(self):
        """Test custom endpoint handling."""
        config = OllamaConfig(endpoint="https://custom.api.com/v1")
        assert config.generate_url() == "https://custom.api.com/v1/api/generate"


class TestPlayerAgentErrorHandling:
    """Tests for player agent error handling."""

    def test_sanitize_json_response_empty(self):
        """Test handling of empty response."""
        agent = PlayerAgent()
        data, issues = agent.sanitize_json_response("")
        assert data == {}
        assert "empty Ollama response" in issues

    def test_sanitize_json_response_invalid_json(self):
        """Test handling of invalid JSON."""
        agent = PlayerAgent()
        data, issues = agent.sanitize_json_response("not valid json")
        assert data == {}
        assert any("json parse failed" in issue for issue in issues)

    def test_sanitize_json_response_with_fallback(self):
        """Test handling of JSON with fallback action."""
        agent = PlayerAgent()
        data, issues = agent.sanitize_json_response('{"action": "x", "macro_goal": "test", "reasoning": "test", "telemetry_notes": "test"}')
        assert data == {"action": "x", "macro_goal": "test", "reasoning": "test", "telemetry_notes": "test"}
        # Note: sanitize_json_response only parses JSON, validation happens in validate_response
        assert len(issues) == 0  # No issues during parsing

    def test_validate_response_with_invalid_action(self):
        """Test validation catches invalid action."""
        agent = PlayerAgent()
        data, issues = agent.validate_response({
            "action": "x",
            "macro_goal": "test",
            "reasoning": "test",
            "telemetry_notes": "test"
        })
        assert data["action"] == "e"  # Should fallback to 'e'
        assert any("invalid action" in issue for issue in issues)

    def test_validate_response_missing_fields(self):
        """Test validation with missing fields."""
        agent = PlayerAgent()
        data, issues = agent.validate_response({})
        assert "missing response field" in issues[0]

    def test_validate_response_valid_action(self):
        """Test validation with valid action."""
        agent = PlayerAgent()
        data, issues = agent.validate_response({
            "action": "s",
            "macro_goal": "test",
            "reasoning": "test",
            "telemetry_notes": "test"
        })
        assert data["action"] == "s"
        assert len(issues) == 0


class TestPlayerAgentRequest:
    """Tests for Ollama request handling."""

    @patch('requests.post')
    def test_request_ollama_success(self, mock_post):
        """Test successful Ollama request."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": '{"action": "s", "macro_goal": "test", "reasoning": "test", "telemetry_notes": "test"}'}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        config = OllamaConfig(endpoint="https://openrouter.ai/api/v1")
        agent = PlayerAgent(config=config)
        result = agent.request_ollama("system", "user")
        
        assert result == '{"action": "s", "macro_goal": "test", "reasoning": "test", "telemetry_notes": "test"}'

    @patch('requests.post')
    def test_request_ollama_404_error(self, mock_post):
        """Test handling of 404 error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_post.return_value = mock_response

        config = OllamaConfig(endpoint="https://openrouter.ai/api/v1")
        agent = PlayerAgent(config=config)
        
        with pytest.raises(RuntimeError) as exc_info:
            agent.request_ollama("system", "user")
        
        assert "404" in str(exc_info.value)

    @patch('requests.post')
    def test_request_ollama_timeout(self, mock_post):
        """Test handling of timeout."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()

        config = OllamaConfig(endpoint="https://openrouter.ai/api/v1", timeout=1.0)
        agent = PlayerAgent(config=config)
        
        with pytest.raises(RuntimeError) as exc_info:
            agent.request_ollama("system", "user")
        
        assert "timed out" in str(exc_info.value).lower()

    @patch('requests.post')
    def test_request_ollama_json_parse_error(self, mock_post):
        """Test handling of JSON parse error."""
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("test", "test", 0)
        mock_response.text = "not json"
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        config = OllamaConfig(endpoint="https://openrouter.ai/api/v1")
        agent = PlayerAgent(config=config)
        
        # Should return raw text when JSON parsing fails
        result = agent.request_ollama("system", "user")
        assert result == "not json"


class TestPlaytestConfig:
    """Tests for playtest configuration."""

    def test_default_max_duration(self):
        """Test default max duration is set."""
        config = PlaytestConfig()
        assert config.max_duration_seconds == 600

    def test_default_max_failures(self):
        """Test default max consecutive failures is set."""
        config = PlaytestConfig()
        assert config.max_consecutive_failures == 10

    def test_from_dict_with_new_fields(self):
        """Test loading config from dict with new fields."""
        data = {
            "max_duration_seconds": 300,
            "max_consecutive_failures": 5
        }
        config = PlaytestConfig.from_dict(data)
        assert config.max_duration_seconds == 300
        assert config.max_consecutive_failures == 5