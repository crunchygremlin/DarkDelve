"""Tests for DungeonMasterAgent."""

import pytest
from unittest.mock import Mock, MagicMock
from src.domain.agents.dungeon_master_agent import DungeonMasterAgent
from src.domain.value_objects.perception import PerceptionStatus
from src.domain.value_objects.llm_logging import LLMLogger, LLMCallLog
from src.domain.services.level_design_service import LevelDesignService


class TestDungeonMasterAgent:
    """Tests for DungeonMasterAgent."""

    def test_init(self):
        """Test agent initialization."""
        ollama = Mock()
        level_design = Mock()
        llm_logger = Mock()

        agent = DungeonMasterAgent(
            ollama_service=ollama,
            level_design_service=level_design,
            llm_logger=llm_logger,
            social_service=None
        )

        assert agent.agent_id == "dungeon_master"
        assert agent.ollama == ollama
        assert agent.level_design == level_design
        assert agent.logger == llm_logger
        assert agent.social_service is None

    def test_init_with_social_service(self):
        """Test initialization with social service."""
        ollama = Mock()
        level_design = Mock()
        llm_logger = Mock()
        social_service = Mock()

        agent = DungeonMasterAgent(
            ollama_service=ollama,
            level_design_service=level_design,
            llm_logger=llm_logger,
            social_service=social_service
        )

        assert agent.social_service == social_service

    def test_generate_behavior_script_success(self):
        """Test successful behavior script generation."""
        ollama = Mock()
        ollama.generate.return_value = '''{
            "script_id": "script_test",
            "root": {
                "node_id": "root",
                "node_type": "selector",
                "children": []
            }
        }'''

        level_design = Mock()
        llm_logger = Mock()

        agent = DungeonMasterAgent(
            ollama_service=ollama,
            level_design_service=level_design,
            llm_logger=llm_logger,
            social_service=None
        )

        perception = PerceptionStatus(entity_id="entity_1")
        script = agent.generate_behavior_script(
            entity_id="entity_1",
            mob_type="goblin",
            perception=perception,
            social_context="No social structure",
            valid_conditions=["can_see_player"],
            valid_actions=["attack"]
        )

        assert script is not None
        assert script.entity_id == "entity_1"
        ollama.generate.assert_called_once()
        llm_logger.log_call.assert_called_once()

    def test_generate_behavior_script_failure(self):
        """Test behavior script generation failure handling."""
        ollama = Mock()
        ollama.generate.side_effect = Exception("LLM error")

        level_design = Mock()
        llm_logger = Mock()

        agent = DungeonMasterAgent(
            ollama_service=ollama,
            level_design_service=level_design,
            llm_logger=llm_logger,
            social_service=None
        )

        perception = PerceptionStatus(entity_id="entity_1")
        script = agent.generate_behavior_script(
            entity_id="entity_1",
            mob_type="goblin",
            perception=perception,
            social_context="No social structure",
            valid_conditions=["can_see_player"],
            valid_actions=["attack"]
        )

        assert script is None
        llm_logger.log_call.assert_called_once()
        # Check that the log call was made with success=False
        call_arg = llm_logger.log_call.call_args[0][0]  # First positional argument
        assert call_arg.success is False

    def test_design_level_success(self):
        """Test successful level design."""
        ollama = Mock()
        ollama.generate.return_value = '{"description": "Test level", "rooms": [], "entities": [], "items": []}'

        level_design = Mock()
        level_design._build_level_prompt.return_value = "prompt"
        level_design._parse_level_response.return_value = {
            "description": "Test level",
            "rooms": [],
            "entities": [],
            "items": []
        }

        llm_logger = Mock()

        agent = DungeonMasterAgent(
            ollama_service=ollama,
            level_design_service=level_design,
            llm_logger=llm_logger,
            social_service=None
        )

        from src.domain.value_objects.power_levels import PlayerProfile
        profile = PlayerProfile()
        level_config = agent.design_level(profile, level_number=1)

        assert level_config["description"] == "Test level"
        ollama.generate.assert_called_once()
        llm_logger.log_call.assert_called_once()

    def test_design_level_failure(self):
        """Test level design failure handling."""
        ollama = Mock()
        ollama.generate.side_effect = Exception("LLM error")

        level_design = Mock()
        level_design._build_level_prompt.return_value = "prompt"

        llm_logger = Mock()

        agent = DungeonMasterAgent(
            ollama_service=ollama,
            level_design_service=level_design,
            llm_logger=llm_logger,
            social_service=None
        )

        from src.domain.value_objects.power_levels import PlayerProfile
        profile = PlayerProfile()
        level_config = agent.design_level(profile, level_number=1)

        assert level_config == {}
        llm_logger.log_call.assert_called_once()

    def test_build_behavior_prompt(self):
        """Test behavior prompt building."""
        ollama = Mock()
        level_design = Mock()
        llm_logger = Mock()

        agent = DungeonMasterAgent(
            ollama_service=ollama,
            level_design_service=level_design,
            llm_logger=llm_logger,
            social_service=None
        )

        perception = PerceptionStatus(
            entity_id="entity_1",
            can_see_player=True,
            can_hear_player=False,
            player_noise_level=0.5,
            player_distance_estimate=5.0,
            visible_threats=["threat_1"],
            visible_allies=["ally_1"],
            visible_items=["item_1"],
            environment_danger=0.3,
            light_level=0.8,
            time_since_player_seen=2.0
        )

        prompt = agent._build_behavior_prompt(
            entity_id="entity_1",
            mob_type="goblin",
            perception=perception,
            social_context="Test context",
            valid_conditions=["can_see_player", "health_below"],
            valid_actions=["attack", "flee"]
        )

        assert "entity_1" in prompt
        assert "goblin" in prompt
        assert "can_see_player" in prompt
        assert "attack" in prompt
        assert "Test context" in prompt

    def test_parse_behavior_response_valid(self):
        """Test parsing valid behavior response."""
        ollama = Mock()
        level_design = Mock()
        llm_logger = Mock()

        agent = DungeonMasterAgent(
            ollama_service=ollama,
            level_design_service=level_design,
            llm_logger=llm_logger,
            social_service=None
        )

        response = '''{
            "script_id": "script_test",
            "root": {
                "node_id": "root",
                "node_type": "selector",
                "children": []
            },
            "valid_conditions": ["can_see_player"],
            "valid_actions": ["attack"]
        }'''

        script = agent._parse_behavior_response(
            entity_id="entity_1",
            response=response,
            valid_conditions=["can_see_player"],
            valid_actions=["attack"]
        )

        assert script is not None
        assert script.entity_id == "entity_1"
        assert script.script_id == "script_test"

    def test_parse_behavior_response_invalid_json(self):
        """Test parsing invalid JSON response."""
        ollama = Mock()
        level_design = Mock()
        llm_logger = Mock()

        agent = DungeonMasterAgent(
            ollama_service=ollama,
            level_design_service=level_design,
            llm_logger=llm_logger,
            social_service=None
        )

        script = agent._parse_behavior_response(
            entity_id="entity_1",
            response="not valid json",
            valid_conditions=[],
            valid_actions=[]
        )

        assert script is None

    def test_parse_behavior_response_no_json(self):
        """Test parsing response with no JSON object."""
        ollama = Mock()
        level_design = Mock()
        llm_logger = Mock()

        agent = DungeonMasterAgent(
            ollama_service=ollama,
            level_design_service=level_design,
            llm_logger=llm_logger,
            social_service=None
        )

        script = agent._parse_behavior_response(
            entity_id="entity_1",
            response="no json here",
            valid_conditions=[],
            valid_actions=[]
        )

        assert script is None