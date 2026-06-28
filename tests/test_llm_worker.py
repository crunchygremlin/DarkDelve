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