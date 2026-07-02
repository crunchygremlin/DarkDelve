"""Tests for LLM worker thread."""

import pytest
import threading
import time
import queue
from unittest.mock import Mock, MagicMock, patch

from src.application.services.llm_worker import llm_worker_func
from src.domain.value_objects.llm_logging import LLMLogger, LLMCallLog
from src.domain.agents.dungeon_master_agent import DungeonMasterAgent
from src.domain.value_objects.behavior_script import BehaviorScript, BehaviorNode, BehaviorAction, NodeType


class TestLLMWorker:
    """Tests for llm_worker_func."""

    def test_worker_processes_behavior_request(self):
        """Test that worker processes a behavior generation request."""
        request_queue = queue.Queue()
        response_queue = queue.Queue()
        logger = LLMLogger(log_path="/tmp/test_llm_worker.json")
        
        # Mock DM agent
        dm_agent = Mock(spec=DungeonMasterAgent)
        mock_script = Mock(spec=BehaviorScript)
        mock_script.to_dict.return_value = {"script_id": "test"}
        dm_agent.generate_behavior_script.return_value = mock_script
        
        # Put a request in the queue
        request = {
            'type': 'behavior',
            'entity_id': 'entity_1',
            'mob_type': 'goblin',
            'perception': {},
            'social_context': '',
            'valid_conditions': ['can_see_player'],
            'valid_actions': ['attack', 'flee'],
            'turn_number': 1,
            'prompt_summary': 'test',
        }
        request_queue.put(request)
        
        # Start worker in a thread
        worker_thread = threading.Thread(
            target=llm_worker_func,
            args=(request_queue, response_queue, dm_agent, logger, 5),
            daemon=True
        )
        worker_thread.start()
        
        # Wait for response
        time.sleep(0.5)
        
        # Check response
        assert not response_queue.empty()
        response = response_queue.get_nowait()
        assert response['entity_id'] == 'entity_1'
        assert response['success'] is True
        
        # Verify DM agent was called
        dm_agent.generate_behavior_script.assert_called_once()

    def test_worker_respects_max_calls(self):
        """Test that worker respects max_calls_per_turn throttle."""
        request_queue = queue.Queue()
        response_queue = queue.Queue()
        logger = LLMLogger(log_path="/tmp/test_llm_worker.json")
        
        dm_agent = Mock(spec=DungeonMasterAgent)
        dm_agent.generate_behavior_script.return_value = Mock(to_dict=lambda: {})
        
        # Put more requests than max_calls
        for i in range(10):
            request_queue.put({
                'type': 'behavior',
                'entity_id': f'entity_{i}',
                'mob_type': 'goblin',
                'perception': {},
                'social_context': '',
                'valid_conditions': [],
                'valid_actions': [],
                'turn_number': 1,
                'prompt_summary': 'test',
            })
        
        # Start worker with max_calls=2
        worker_thread = threading.Thread(
            target=llm_worker_func,
            args=(request_queue, response_queue, dm_agent, logger, 2),
            daemon=True
        )
        worker_thread.start()
        
        # Wait for processing
        time.sleep(0.5)
        
        # Check that some responses indicate max_calls exceeded
        success_count = 0
        fail_count = 0
        while not response_queue.empty():
            resp = response_queue.get_nowait()
            if resp.get('success'):
                success_count += 1
            else:
                fail_count += 1
        
        # Should have some failures due to throttle
        assert fail_count > 0 or success_count <= 2

    def test_worker_handles_errors(self):
        """Test that worker handles exceptions gracefully."""
        request_queue = queue.Queue()
        response_queue = queue.Queue()
        logger = LLMLogger(log_path="/tmp/test_llm_worker.json")
        
        dm_agent = Mock(spec=DungeonMasterAgent)
        dm_agent.generate_behavior_script.side_effect = Exception("Test error")
        
        request_queue.put({
            'type': 'behavior',
            'entity_id': 'entity_1',
            'mob_type': 'goblin',
            'perception': {},
            'social_context': '',
            'valid_conditions': [],
            'valid_actions': [],
            'turn_number': 1,
            'prompt_summary': 'test',
        })
        
        worker_thread = threading.Thread(
            target=llm_worker_func,
            args=(request_queue, response_queue, dm_agent, logger, 5),
            daemon=True
        )
        worker_thread.start()
        
        time.sleep(0.5)
        
        # Should have error response
        assert not response_queue.empty()
        response = response_queue.get_nowait()
        assert response['success'] is False
        assert 'error' in response

    def test_worker_processes_level_design(self):
        """Test that worker processes level design requests."""
        request_queue = queue.Queue()
        response_queue = queue.Queue()
        logger = LLMLogger(log_path="/tmp/test_llm_worker.json")
        
        dm_agent = Mock(spec=DungeonMasterAgent)
        dm_agent.design_level.return_value = {"description": "test level"}
        
        request_queue.put({
            'type': 'level_design',
            'player_profile': None,
            'level_number': 1,
            'map_data': None,
            'turn_number': 1,
            'prompt_summary': 'test',
        })
        
        worker_thread = threading.Thread(
            target=llm_worker_func,
            args=(request_queue, response_queue, dm_agent, logger, 5),
            daemon=True
        )
        worker_thread.start()
        
        time.sleep(0.5)
        
        assert not response_queue.empty()
        response = response_queue.get_nowait()
        assert response['success'] is True
        dm_agent.design_level.assert_called_once()

    def test_worker_logs_calls(self):
        """Test that worker logs LLM calls."""
        request_queue = queue.Queue()
        response_queue = queue.Queue()
        logger = LLMLogger(log_path="/tmp/test_llm_worker.json")
        
        dm_agent = Mock(spec=DungeonMasterAgent)
        dm_agent.generate_behavior_script.return_value = Mock(to_dict=lambda: {})
        
        request_queue.put({
            'type': 'behavior',
            'entity_id': 'entity_1',
            'mob_type': 'goblin',
            'perception': {},
            'social_context': '',
            'valid_conditions': [],
            'valid_actions': [],
            'turn_number': 1,
            'prompt_summary': 'test prompt',
        })
        
        worker_thread = threading.Thread(
            target=llm_worker_func,
            args=(request_queue, response_queue, dm_agent, logger, 5),
            daemon=True
        )
        worker_thread.start()
        
        time.sleep(0.5)
        
        # Check that logger has entries
        assert len(logger.call_log) == 1
        assert logger.call_log[0].turn_number == 1
        assert logger.call_log[0].call_type == "behavior_generation"

    def test_worker_converts_perception_dict_to_object(self):
        """Test that worker converts perception dict to PerceptionStatus object."""
        request_queue = queue.Queue()
        response_queue = queue.Queue()
        logger = LLMLogger(log_path="/tmp/test_llm_worker_perception.json")
        
        dm_agent = Mock(spec=DungeonMasterAgent)
        mock_script = Mock(spec=BehaviorScript)
        mock_script.to_dict.return_value = {"script_id": "test"}
        dm_agent.generate_behavior_script.return_value = mock_script
        
        # Request with perception as a dict (as it comes from the queue)
        perception_dict = {
            "entity_id": "entity_2",
            "can_see_player": True,
            "can_hear_player": False,
            "can_smell_player": True,
            "player_noise_level": 0.5,
            "player_distance_estimate": 10.0,
            "visible_threats": ["threat1"],
            "visible_items": ["item1"],
            "visible_allies": [],
            "visible_enemies": [],
            "environment_danger": 0.7,
            "light_level": 0.3,
            "nearby_traps": 2,
            "nearby_exits": 1,
            "combat_occurring_nearby": True,
            "ally_health_status": "wounded",
            "time_since_player_seen": 5.0,
            "custom_flags": {},
        }
        
        request_queue.put({
            'type': 'behavior',
            'entity_id': 'entity_2',
            'mob_type': 'goblin',
            'perception': perception_dict,
            'social_context': '',
            'valid_conditions': ['can_see_player'],
            'valid_actions': ['attack'],
            'turn_number': 1,
            'prompt_summary': 'test',
        })
        
        worker_thread = threading.Thread(
            target=llm_worker_func,
            args=(request_queue, response_queue, dm_agent, logger, 5),
            daemon=True
        )
        worker_thread.start()
        
        time.sleep(0.5)
        
        # Verify DM agent was called with PerceptionStatus object, not dict
        dm_agent.generate_behavior_script.assert_called_once()
        call_args = dm_agent.generate_behavior_script.call_args
        perception_arg = call_args.kwargs.get('perception')
        
        # The perception should be a PerceptionStatus object, not a dict
        from src.domain.value_objects.perception import PerceptionStatus
        assert isinstance(perception_arg, PerceptionStatus), \
            f"Expected PerceptionStatus object, got {type(perception_arg)}"
        assert perception_arg.can_see_player is True
        assert perception_arg.can_hear_player is False
        assert perception_arg.player_noise_level == 0.5