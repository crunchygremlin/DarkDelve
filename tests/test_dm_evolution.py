"""Tests for DM context persistence and evolving level design."""

import pytest
import tempfile
import threading
import time
import json
import queue
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

from src.domain.agents.dungeon_master_agent import DungeonMasterAgent
from src.domain.value_objects.llm_logging import LLMLogger, LLMCallLog
from src.domain.value_objects.power_levels import PlayerProfile
from src.domain.services.level_design_service import LevelDesignService
from src.application.services.llm_worker import llm_worker_func


class TestDMContextPersistence:
    """Tests for dm_context accumulation across levels."""

    def _make_agent(self):
        ollama = Mock()
        level_design = Mock()
        with tempfile.TemporaryDirectory() as tmpdir:
            llm_logger = LLMLogger(log_dir=tmpdir)
        agent = DungeonMasterAgent(ollama, level_design, llm_logger)
        return agent

    def test_update_context_appends_level(self):
        """Test that update_context appends to level history."""
        agent = self._make_agent()
        record = {
            "depth": 1,
            "theme_name": "Goblin Warrens",
            "monster_theme": "goblin",
            "monsters_killed": 8,
            "total_monsters": 8,
            "turns_taken": 50,
            "damage_taken": 20,
            "close_calls": 0,
            "difficulty_rating": 3.0,
        }
        agent.update_context(record)
        assert len(agent._level_history) == 1
        assert agent._level_history[0]["depth"] == 1

    def test_update_context_bounds_history(self):
        """Test that level history is bounded to 10 entries."""
        agent = self._make_agent()
        for i in range(15):
            agent.update_context({"depth": i, "theme_name": f"Level {i}"})
        assert len(agent._level_history) == 10
        assert agent._level_history[-1]["depth"] == 14

    def test_update_context_empty_record(self):
        """Test that update_context handles empty record without error."""
        agent = self._make_agent()
        agent.update_context({})
        assert len(agent._level_history) == 1

    def test_level_history_initially_empty(self):
        """Test that _level_history is initialized as empty list."""
        agent = self._make_agent()
        assert agent._level_history == []


class TestEvolutionPrompt:
    """Tests for build_evolution_prompt."""

    def _make_agent(self):
        ollama = Mock()
        level_design = Mock()
        with tempfile.TemporaryDirectory() as tmpdir:
            llm_logger = LLMLogger(log_dir=tmpdir)
        return DungeonMasterAgent(ollama, level_design, llm_logger)

    def test_build_evolution_prompt_contains_previous_levels(self):
        """Test that prompt includes previous level summaries."""
        agent = self._make_agent()
        ctx = {
            "previous_levels": [
                {"depth": 1, "theme": "Goblin Warrens", "monster_theme": "goblin",
                 "monsters_killed": 8, "total_monsters": 8, "damage_taken": 5,
                 "close_calls": 0, "turns_taken": 30, "difficulty_rating": 3.0}
            ],
            "performance_summary": "Player dominated.",
            "difficulty_adjustment": 1.3,
            "narrative_continuity": "Previous levels: Goblin Warrens. Escalate.",
            "target_depth": 2,
        }
        prompt = agent.build_evolution_prompt(ctx, depth=2)
        assert "Goblin Warrens" in prompt
        assert "Player dominated" in prompt
        assert "1.3" in prompt
        assert "Escalate" in prompt
        assert "level 2" in prompt.lower()

    def test_build_evolution_prompt_no_previous(self):
        """Test prompt with no previous levels."""
        agent = self._make_agent()
        ctx = {
            "previous_levels": [],
            "performance_summary": "No previous level data.",
            "difficulty_adjustment": 1.0,
            "narrative_continuity": "First level -- no previous narrative.",
            "target_depth": 1,
        }
        prompt = agent.build_evolution_prompt(ctx, depth=1)
        assert "No previous level data" in prompt

    def test_build_evolution_prompt_difficulty_directions(self):
        """Test that difficulty adjustment maps to correct direction strings."""
        agent = self._make_agent()
        base_ctx = {
            "previous_levels": [],
            "performance_summary": "test",
            "narrative_continuity": "test",
            "target_depth": 2,
        }

        # Dominated -> significantly harder
        ctx = {**base_ctx, "difficulty_adjustment": 1.3}
        prompt = agent.build_evolution_prompt(ctx, 2)
        assert "significantly harder" in prompt

        # Struggled -> easier
        ctx = {**base_ctx, "difficulty_adjustment": 0.8}
        prompt = agent.build_evolution_prompt(ctx, 2)
        assert "easier" in prompt

        # Normal -> similar
        ctx = {**base_ctx, "difficulty_adjustment": 1.0}
        prompt = agent.build_evolution_prompt(ctx, 2)
        assert "similar difficulty" in prompt

        # Slight increase
        ctx = {**base_ctx, "difficulty_adjustment": 1.1}
        prompt = agent.build_evolution_prompt(ctx, 2)
        assert "slightly harder" in prompt


class TestDesignEvolvedLevel:
    """Tests for design_evolved_level."""

    def _make_agent(self, mock_response=None, side_effect=None):
        ollama = Mock()
        if side_effect:
            ollama.generate.side_effect = side_effect
        else:
            ollama.generate.return_value = mock_response or json.dumps({
                "theme_name": "Crypt",
                "description": "A dark crypt.",
                "monster_theme": "undead",
                "monsters": [{"name": "skeleton", "symbol": "s", "tier": "minion",
                              "count": 4, "hp": 10, "power": 3, "defense": 1,
                              "speed": 60, "ai_type": "aggressive"}],
            })
        level_design = Mock()
        llm_logger = Mock()
        llm_logger.estimate_prompt_tokens.return_value = 100
        headroom_mock = Mock()
        headroom_mock.max_context_tokens = 4096
        headroom_mock.headroom_tokens = 3000
        llm_logger.check_headroom.return_value = headroom_mock
        return DungeonMasterAgent(ollama, level_design, llm_logger)

    def test_design_evolved_level_success(self):
        """Test successful evolved level design."""
        agent = self._make_agent()
        ctx = {
            "previous_levels": [],
            "performance_summary": "test",
            "difficulty_adjustment": 1.0,
            "narrative_continuity": "test",
            "target_depth": 2,
        }
        result = agent.design_evolved_level(ctx, 2)
        assert "theme_name" in result
        assert result["theme_name"] == "Crypt"

    def test_design_evolved_level_failure(self):
        """Test evolved level design with LLM failure."""
        agent = self._make_agent(side_effect=Exception("LLM error"))
        ctx = {"previous_levels": [], "performance_summary": "test",
               "difficulty_adjustment": 1.0, "narrative_continuity": "test",
               "target_depth": 2}
        result = agent.design_evolved_level(ctx, 2)
        assert result == {}

    def test_design_evolved_level_invalid_json(self):
        """Test evolved level design with unparseable response."""
        agent = self._make_agent(mock_response="not json at all")
        ctx = {"previous_levels": [], "performance_summary": "test",
               "difficulty_adjustment": 1.0, "narrative_continuity": "test",
               "target_depth": 2}
        result = agent.design_evolved_level(ctx, 2)
        assert result == {}


class TestDifficultyAdjustment:
    """Tests for the difficulty adaptation algorithm."""

    def _make_game_mock(self):
        """Create a minimal mock Game object with dm_context methods."""
        game = Mock()
        game.dm_context = {
            "levels": [],
            "current_level_start_turn": 0,
            "current_level_start_hp": 30,
            "current_level_kills": 0,
            "current_level_damage_taken": 0,
            "current_level_close_calls": 0,
        }
        game.turn = 50
        game.state = Mock()
        game.state.depth = 2
        game.current_theme = Mock()
        game.current_theme.name = "Goblin Warrens"
        game.current_theme.monster_theme = "goblin"
        game.current_theme.difficulty = 3.0
        game.player = Mock()
        game.player.hp = 25
        game.player.max_hp = 30
        from darkdelve import Game
        game._compute_difficulty_adjustment = Game._compute_difficulty_adjustment.__get__(game)
        game._compute_performance_summary = Game._compute_performance_summary.__get__(game)
        game._build_narrative_continuity = Game._build_narrative_continuity.__get__(game)
        game._build_dm_evolution_context = Game._build_dm_evolution_context.__get__(game)
        game._record_level_performance = Game._record_level_performance.__get__(game)
        return game

    def test_dominated_player_increases_difficulty(self):
        """Player who dominated should get harder levels."""
        game = self._make_game_mock()
        level_record = {
            "monsters_killed": 8, "total_monsters": 8,
            "damage_taken": 5, "close_calls": 0
        }
        adjustment = game._compute_difficulty_adjustment(level_record)
        assert adjustment == 1.3

    def test_struggled_player_decreases_difficulty(self):
        """Player who struggled should get easier levels."""
        game = self._make_game_mock()
        level_record = {
            "monsters_killed": 1, "total_monsters": 8,
            "damage_taken": 60, "close_calls": 3
        }
        adjustment = game._compute_difficulty_adjustment(level_record)
        assert adjustment == 0.8

    def test_no_record_returns_default(self):
        """No level record should return 1.0."""
        game = self._make_game_mock()
        adjustment = game._compute_difficulty_adjustment({})
        assert adjustment == 1.0

    def test_no_record_none_returns_default(self):
        """None level record should return 1.0."""
        game = self._make_game_mock()
        adjustment = game._compute_difficulty_adjustment(None)
        assert adjustment == 1.0

    def test_managed_player_normal_difficulty(self):
        """Player who managed (ratio >= 0.5, damage < 40) gets 1.1."""
        game = self._make_game_mock()
        level_record = {
            "monsters_killed": 5, "total_monsters": 8,
            "damage_taken": 30, "close_calls": 1
        }
        # ratio = 0.625, damage = 30 < 40 -> adjustment = 1.1
        adjustment = game._compute_difficulty_adjustment(level_record)
        assert adjustment == 1.1

    def test_performance_summary_dominated(self):
        """Test performance summary for dominant player."""
        game = self._make_game_mock()
        level_record = {
            "monsters_killed": 8, "total_monsters": 8,
            "damage_taken": 5, "close_calls": 0, "turns_taken": 30
        }
        summary = game._compute_performance_summary(level_record)
        assert "dominated" in summary
        assert "8/8" in summary

    def test_performance_summary_struggled(self):
        """Test performance summary for struggling player."""
        game = self._make_game_mock()
        level_record = {
            "monsters_killed": 1, "total_monsters": 8,
            "damage_taken": 60, "close_calls": 3, "turns_taken": 100
        }
        summary = game._compute_performance_summary(level_record)
        assert "struggled" in summary

    def test_performance_summary_no_data(self):
        """Test performance summary with no data."""
        game = self._make_game_mock()
        summary = game._compute_performance_summary({})
        assert "No previous level data" in summary

    def test_narrative_continuity_empty(self):
        """Test narrative continuity with no previous levels."""
        game = self._make_game_mock()
        result = game._build_narrative_continuity([])
        assert "First level" in result

    def test_narrative_continuity_with_levels(self):
        """Test narrative continuity with previous levels at depth 3."""
        game = self._make_game_mock()
        levels = [
            {"depth": 1, "theme_name": "Goblin Warrens", "monster_theme": "goblin"},
            {"depth": 3, "theme_name": "Crypt of Shadows", "monster_theme": "undead"},
        ]
        result = game._build_narrative_continuity(levels)
        assert "Goblin Warrens" in result
        assert "Crypt of Shadows" in result
        # depth 3 -> "Escalate"
        assert "Escalate" in result

    def test_narrative_continuity_deep_levels(self):
        """Test narrative continuity for deep levels."""
        game = self._make_game_mock()
        levels = [
            {"depth": 5, "theme_name": "Abyss", "monster_theme": "demon"},
        ]
        result = game._build_narrative_continuity(levels)
        assert "deepest horrors" in result

    def test_build_dm_evolution_context_no_levels(self):
        """Test evolution context returns None when no previous levels."""
        game = self._make_game_mock()
        result = game._build_dm_evolution_context(depth=2)
        assert result is None

    def test_build_dm_evolution_context_with_levels(self):
        """Test evolution context builds correctly with previous levels."""
        game = self._make_game_mock()
        game.dm_context["levels"] = [
            {"depth": 1, "theme_name": "Goblin Warrens", "monster_theme": "goblin",
             "monsters_killed": 8, "total_monsters": 8, "turns_taken": 30,
             "damage_taken": 5, "close_calls": 0, "difficulty_rating": 3.0}
        ]
        result = game._build_dm_evolution_context(depth=2)
        assert result is not None
        assert result["target_depth"] == 2
        assert len(result["previous_levels"]) == 1
        assert "performance_summary" in result
        assert "difficulty_adjustment" in result
        assert "narrative_continuity" in result

    def test_build_dm_evolution_context_bounds_to_3(self):
        """Test that evolution context only includes last 3 levels."""
        game = self._make_game_mock()
        game.dm_context["levels"] = [
            {"depth": i, "theme_name": f"Level {i}", "monster_theme": "goblin",
             "monsters_killed": 5, "total_monsters": 8, "turns_taken": 30,
             "damage_taken": 20, "close_calls": 0, "difficulty_rating": 3.0}
            for i in range(5)
        ]
        result = game._build_dm_evolution_context(depth=6)
        assert len(result["previous_levels"]) == 3

    def test_record_level_performance(self):
        """Test that _record_level_performance appends to dm_context."""
        game = self._make_game_mock()
        game.dm_context["current_level_kills"] = 5
        game.dm_context["current_level_damage_taken"] = 15
        game.dm_context["current_level_close_calls"] = 1
        game.dm_context["total_level_monsters"] = 8
        game.dm_context["current_level_start_turn"] = 10
        game.turn = 60
        game._record_level_performance()
        assert len(game.dm_context["levels"]) == 1
        record = game.dm_context["levels"][0]
        assert record["monsters_killed"] == 5
        assert record["damage_taken"] == 15
        assert record["close_calls"] == 1
        assert record["turns_taken"] == 50

    def test_record_level_performance_bounds_to_10(self):
        """Test that level history is bounded to 10 entries."""
        game = self._make_game_mock()
        game.dm_context["levels"] = [
            {"depth": i, "theme_name": f"Level {i}", "monster_theme": "goblin",
             "monsters_killed": 5, "total_monsters": 8, "turns_taken": 30,
             "damage_taken": 20, "close_calls": 0, "difficulty_rating": 3.0}
            for i in range(10)
        ]
        game.dm_context["current_level_kills"] = 3
        game.dm_context["current_level_damage_taken"] = 10
        game.dm_context["current_level_close_calls"] = 0
        game.dm_context["total_level_monsters"] = 8
        game._record_level_performance()
        assert len(game.dm_context["levels"]) == 10
        assert game.dm_context["levels"][-1]["monsters_killed"] == 3

    def test_record_level_performance_no_dm_context(self):
        """Test that _record_level_performance handles missing dm_context."""
        game = Mock()
        game.dm_context = None
        from darkdelve import Game
        Game._record_level_performance(game)


class TestBackwardCompatibility:
    """Tests that DM-disabled mode still works."""

    def test_generate_level_without_dm(self):
        """Test that level generation works when DM is disabled."""
        pass

    def test_procedural_fallback_when_llm_unavailable(self):
        """Test that procedural generation is used when LLM fails."""
        pass


class TestLLMEvolvedRosterWorker:
    """Tests for evolved_roster request type in llm_worker."""

    def test_worker_processes_evolved_roster(self):
        """Test that worker handles evolved_roster request type."""
        request_queue = queue.Queue()
        response_queue = queue.Queue()
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = LLMLogger(log_dir=tmpdir)

        dm_agent = Mock(spec=DungeonMasterAgent)
        dm_agent.design_evolved_level.return_value = {
            "theme_name": "Crypt",
            "monsters": [{"name": "skeleton", "tier": "minion", "count": 4}],
        }

        request_queue.put({
            'type': 'evolved_roster',
            'depth': 2,
            'theme': 'undead',
            'evolution_context': {
                'previous_levels': [],
                'performance_summary': 'test',
                'difficulty_adjustment': 1.0,
                'narrative_continuity': 'test',
                'target_depth': 2,
            },
            'turn_number': 1,
            'prompt_summary': 'evolved_roster',
        })
        request_queue.put(None)

        llm_worker_func(request_queue, response_queue, dm_agent, logger, 5)

        assert not response_queue.empty()
        response = response_queue.get_nowait()
        assert response['success'] is True
        dm_agent.design_evolved_level.assert_called_once()

    def test_worker_handles_evolved_roster_failure(self):
        """Test worker handles evolved_roster failure gracefully."""
        request_queue = queue.Queue()
        response_queue = queue.Queue()
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = LLMLogger(log_dir=tmpdir)

        dm_agent = Mock(spec=DungeonMasterAgent)
        dm_agent.design_evolved_level.return_value = {}

        request_queue.put({
            'type': 'evolved_roster',
            'depth': 2,
            'theme': 'undead',
            'evolution_context': {},
            'turn_number': 1,
            'prompt_summary': 'evolved_roster',
        })
        request_queue.put(None)

        llm_worker_func(request_queue, response_queue, dm_agent, logger, 5)

        assert not response_queue.empty()
        response = response_queue.get_nowait()
        assert response['success'] is False


class TestBehaviorWithContextWorker:
    """Tests for behavior_with_context request type."""

    def test_worker_processes_behavior_with_context(self):
        """Test that worker handles behavior_with_context request type."""
        request_queue = queue.Queue()
        response_queue = queue.Queue()
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = LLMLogger(log_dir=tmpdir)

        dm_agent = Mock(spec=DungeonMasterAgent)
        mock_script = Mock()
        mock_script.to_dict.return_value = {"script_id": "test"}
        dm_agent.generate_behavior_script.return_value = mock_script

        request_queue.put({
            'type': 'behavior_with_context',
            'entity_id': 'entity_1',
            'mob_type': 'goblin',
            'perception': {},
            'social_context': 'original context',
            'dm_narrative_context': 'The dungeon grows darker.',
            'valid_conditions': ['can_see_player'],
            'valid_actions': ['attack'],
            'turn_number': 1,
            'prompt_summary': 'behavior_ctx',
        })
        request_queue.put(None)

        llm_worker_func(request_queue, response_queue, dm_agent, logger, 5)

        assert not response_queue.empty()
        response = response_queue.get_nowait()
        assert response['success'] is True
        call_args = dm_agent.generate_behavior_script.call_args
        social_context_used = call_args.kwargs.get('social_context', '')
        assert 'DM Narrative' in social_context_used
        assert 'The dungeon grows darker.' in social_context_used
